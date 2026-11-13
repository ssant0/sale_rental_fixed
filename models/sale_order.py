import logging
import math
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_rental = fields.Boolean(
        string="Es renta",
        default=False,
        copy=True,
        index=True,
        tracking=True,
        help="La orden es de renta. Una cotización es de venta o de renta, "
        "nunca las dos.",
    )
    fecha_evento = fields.Date(string="Fecha del evento")
    entrega_dt = fields.Datetime(string="Entrega")
    recoleccion_dt = fields.Datetime(string="Recolección")
    domicilio_entrega = fields.Char(
        string="Domicilio de entrega",
        help="Domicilio donde se entrega la renta. Se captura en cada "
        "cotización porque un mismo cliente puede recibir en distintos "
        "domicilios; no se toma de la dirección del contacto.",
    )
    rental_status = fields.Selection(
        selection=[
            ("pending", "Por entregar"),
            ("active", "Activo"),
            ("returned", "Devuelto"),
            ("closed", "Cerrado"),
        ],
        string="Estado de renta",
        default="pending",
        copy=False,
        tracking=True,
        help="Ciclo operativo de la renta: entregar, devolver y cerrar.",
    )
    rental_cancel_reason = fields.Text(string="Motivo de cancelación")
    rental_is_late = fields.Boolean(
        string="Retraso",
        compute="_compute_rental_is_late",
        search="_search_rental_is_late",
    )
    rental_late_notified = fields.Boolean(
        string="Retraso notificado", copy=False, readonly=True
    )
    rental_reminder_sent = fields.Boolean(
        string="Recordatorio enviado", copy=False, readonly=True
    )

    @api.constrains("is_rental", "order_line")
    def _check_rental_lines(self):
        """Una cotización de renta solo admite productos rentables."""
        for order in self.filtered("is_rental"):
            invalid = order.order_line.filtered(
                lambda line: not line.display_type
                and not line.is_downpayment
                and line.product_id
                and not line.product_id.rental_ok
            )
            if invalid:
                raise ValidationError(
                    _(
                        "Las cotizaciones de renta solo pueden incluir productos "
                        "rentables. Revisa: %s",
                        ", ".join(invalid.mapped("product_id.display_name")),
                    )
                )

    @api.constrains("is_rental", "fecha_evento", "entrega_dt", "recoleccion_dt")
    def _check_rental_dates(self):
        for order in self.filtered("is_rental"):
            if (
                order.entrega_dt
                and order.recoleccion_dt
                and order.recoleccion_dt < order.entrega_dt
            ):
                raise ValidationError(
                    _("La recolección no puede ser anterior a la entrega.")
                )

    @api.depends("is_rental", "state", "rental_status", "recoleccion_dt")
    def _compute_rental_is_late(self):
        now = fields.Datetime.now()
        for order in self:
            order.rental_is_late = bool(
                order.is_rental
                and order.state == "sale"
                and order.rental_status in ("pending", "active")
                and order.recoleccion_dt
                and order.recoleccion_dt < now
            )

    def _search_rental_is_late(self, operator, value):
        late_domain = [
            ("is_rental", "=", True),
            ("state", "=", "sale"),
            ("rental_status", "in", ["pending", "active"]),
            ("recoleccion_dt", "<", fields.Datetime.now()),
        ]
        negated = ["!", "&", "&", "&"] + late_domain
        try:
            values = (
                set(value)
                if not isinstance(value, (str, bytes, bool, int, float))
                else {value}
            )
        except TypeError:
            values = {value}
        if values == {True, False}:
            return []
        want_true = True in values
        if operator in ("=", "in"):
            return late_domain if want_true else negated
        if operator in ("!=", "not in"):
            return negated if want_true else late_domain
        return []

    def write(self, vals):
        if "recoleccion_dt" in vals:
            # Si cambia la fecha de recolección, se vuelven a habilitar los
            # avisos para la nueva fecha.
            vals = dict(
                vals,
                rental_late_notified=False,
                rental_reminder_sent=False,
            )
        if "is_rental" in vals:
            blocked = self.filtered(
                lambda order: order.state in ("sale", "done")
                and order.is_rental != vals["is_rental"]
            )
            if blocked:
                raise ValidationError(
                    _(
                        "No puedes cambiar el tipo de una orden confirmada. "
                        "Cancélala y vuelve a cotización para cambiar entre "
                        "venta y renta."
                    )
                )
        res = super().write(vals)
        if "is_rental" in vals:
            # Al convertir una cotización, los precios se recalculan: tarifa de
            # renta en modo renta y precio de venta/tarifario en modo venta.
            self.order_line.with_context(
                force_price_recomputation=True
            )._compute_price_unit()
        return res

    def action_confirm(self):
        missing = self.filtered("is_rental").filtered(
            lambda order: not (
                order.fecha_evento
                and order.entrega_dt
                and order.recoleccion_dt
                and order.domicilio_entrega
            )
        )
        if missing:
            raise ValidationError(
                _(
                    "Antes de confirmar una renta captura la fecha del evento, "
                    "la entrega, la recolección y el domicilio de entrega: %s",
                    ", ".join(missing.mapped("name")),
                )
            )
        return super().action_confirm()

    # ------------------------------------------------------------------
    # PDF de confirmación
    # ------------------------------------------------------------------

    def _rental_signature_layout(self):
        """Posición de la firma del cliente dentro del PDF de confirmación.

        Devuelve ``{"spacer_mm": float, "new_page": bool}``. El espaciador va
        en el flujo normal del documento, así que nunca se encima con la tabla.
        Se calcula a partir del formato de papel y de una estimación del
        contenido para que la firma quede al pie de la última página; cuando no
        cabe en la página actual, ``new_page`` fuerza una página nueva y la
        firma queda al pie de esa página.
        """
        self.ensure_one()
        if not self.is_rental or self.state not in ("sale", "done"):
            return {"spacer_mm": 0.0, "new_page": False}

        # Fila de fecha/vendedor, encabezado de tabla, totales y holguras.
        content_mm = 59.0
        for line in self._get_order_lines_to_report():
            chars = len(line.name or "")
            if line.display_type:
                content_mm += 7.0 + 3.0 * max(
                    0, math.ceil(chars / 80.0) - 1
                )
                continue
            content_mm += 10.5 + 5.0 * max(
                0, math.ceil(chars / 65.0) - 1
            )

        content_mm += 16.0  # fila con las fechas de la renta
        if self.domicilio_entrega:
            chars = len(self.domicilio_entrega)
            content_mm += 14.0 + 5.0 * max(
                0, math.ceil(chars / 65.0) - 1
            )
        for note in (
            self.note,
            self.payment_term_id.note,
            self.fiscal_position_id.note,
        ):
            if note:
                chars = len(note)
                content_mm += 10.0 + 5.0 * max(
                    0, math.ceil(chars / 60.0) - 1
                )

        report = self.env.ref(
            "sale_rental_fixed.action_report_rental_order",
            raise_if_not_found=False,
        )
        paperformat = (
            report.get_paperformat()
            if report
            else self.env.company.paperformat_id
        )
        page_height = (
            paperformat.print_page_height if paperformat else 0.0
        ) or 297.0
        margin_top = paperformat.margin_top if paperformat else 0.0
        margin_bottom = paperformat.margin_bottom if paperformat else 0.0
        body_height = max(page_height - margin_top - margin_bottom, 80.0)

        # La primera página gasta espacio en el bloque del cliente y el
        # título; las siguientes usan todo el cuerpo.
        first_page = max(body_height - 30.0, 80.0)
        if content_mm <= first_page:
            remaining = first_page - content_mm
        else:
            remaining = body_height - (
                (content_mm - first_page) % body_height
            )

        signature_mm = 30.0
        gap_mm = 8.0
        same_page_min = signature_mm + 4.0  # margen ante estimaciones cortas
        if remaining >= same_page_min:
            return {
                "spacer_mm": max(remaining - signature_mm - gap_mm, 0.0),
                "new_page": False,
            }
        # No cabe al pie de la página actual: página nueva y firma al pie.
        return {
            "spacer_mm": max(body_height - signature_mm - gap_mm, 0.0),
            "new_page": True,
        }

    # ------------------------------------------------------------------
    # Ciclo operativo de la renta
    # ------------------------------------------------------------------

    def action_rental_deliver(self):
        """Valida la entrega (salida de stock) y marca la renta como activa."""
        for order in self:
            order._check_rental_action("deliver")
            pickings = order.picking_ids.filtered(
                lambda p: p.picking_type_code == "outgoing"
                and p.state not in ("done", "cancel")
            )
            for picking in pickings:
                order._rental_validate_picking(picking)
            order.rental_status = "active"
        return True

    def action_rental_return(self):
        """Genera y valida la devolución (entrada de stock)."""
        for order in self:
            order._check_rental_action("return")
            deliveries = order.picking_ids.filtered(
                lambda p: p.picking_type_code == "outgoing" and p.state == "done"
            )
            for delivery in deliveries:
                wizard = (
                    self.env["stock.return.picking"]
                    .with_context(
                        active_id=delivery.id,
                        active_model="stock.picking",
                    )
                    .create({})
                )
                for return_line in wizard.product_return_moves:
                    return_line.quantity = return_line.move_quantity
                return_picking = wizard._create_return()
                order._rental_validate_picking(return_picking)
            order.rental_status = "returned"
        return True

    def action_rental_close(self):
        """Cierra la renta una vez devuelta."""
        for order in self:
            if order.rental_status != "returned":
                raise UserError(
                    _("Solo se puede cerrar una renta que ya fue devuelta.")
                )
            order.rental_status = "closed"
        return True

    def _check_rental_action(self, action):
        self.ensure_one()
        if not self.is_rental or self.state != "sale":
            raise UserError(
                _("Esta acción solo aplica a rentas confirmadas.")
            )
        expected = {"deliver": "pending", "return": "active"}[action]
        if self.rental_status != expected:
            raise UserError(
                _("La renta no está en el estado correcto para esta acción.")
            )

    def _rental_validate_picking(self, picking):
        picking.action_assign()
        for move in picking.move_ids.filtered(lambda m: m.state != "done"):
            move.quantity = move.product_uom_qty
            move.picked = True
        result = picking.with_context(skip_backorder=True).button_validate()
        if isinstance(result, dict) or picking.state != "done":
            raise UserError(
                _(
                    "No se pudo validar automáticamente %(picking)s. "
                    "Valídala manualmente desde Inventario y vuelve a intentar.",
                    picking=picking.name,
                )
            )

    # ------------------------------------------------------------------
    # Notificaciones
    # ------------------------------------------------------------------

    def _cron_rental_notifications(self):
        """Envía recordatorios de recolección y alertas de retraso."""
        now = fields.Datetime.now()
        horizon = now + timedelta(days=1)
        orders = self.search(
            [
                ("is_rental", "=", True),
                ("state", "=", "sale"),
                ("rental_status", "in", ["pending", "active"]),
                ("recoleccion_dt", "!=", False),
            ]
        )
        reminder_template = self.env.ref(
            "sale_rental_fixed.mail_template_rental_return_reminder"
        )
        late_template = self.env.ref("sale_rental_fixed.mail_template_rental_late")
        for order in orders:
            emails = order._rental_notification_emails()
            if not emails:
                continue
            if order.recoleccion_dt < now and not order.rental_late_notified:
                if order._send_rental_notification(late_template, emails):
                    order.rental_late_notified = True
            elif (
                now <= order.recoleccion_dt <= horizon
                and not order.rental_reminder_sent
            ):
                if order._send_rental_notification(reminder_template, emails):
                    order.rental_reminder_sent = True

    def _rental_notification_emails(self):
        """Correos del administrador de rentas y del creador/vendedor."""
        self.ensure_one()
        manager_group = self.env.ref("sale_rental_fixed.group_rental_manager")
        users = manager_group.user_ids | self.create_uid | self.user_id
        emails = []
        for user in users.filtered(lambda u: u.active and u.email):
            if user.email not in emails:
                emails.append(user.email)
        return emails

    def _send_rental_notification(self, template, emails):
        self.ensure_one()
        try:
            template.send_mail(
                self.id,
                email_values={"email_to": ", ".join(emails)},
            )
            return True
        except Exception as exc:  # pragma: no cover - defensivo
            _logger.warning(
                "No se pudo enviar la notificación de renta %s: %s",
                self.name,
                exc,
            )
            return False
