from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    rental_fecha_evento = fields.Date(
        related="order_id.fecha_evento", string="Fecha del evento"
    )
    rental_entrega_dt = fields.Datetime(
        related="order_id.entrega_dt", string="Entrega"
    )
    rental_recoleccion_dt = fields.Datetime(
        related="order_id.recoleccion_dt", string="Recolección"
    )
    rental_domicilio_entrega = fields.Char(
        related="order_id.domicilio_entrega", string="Domicilio de entrega"
    )

    def _prepare_invoice_line(self, **optional_values):
        """Aplica la cuenta de ingreso de renta a las líneas facturadas.

        Solo aplica a líneas de renta (no anticipos ni secciones) y únicamente
        si el producto tiene una cuenta de renta definida; si no, se conserva
        la cuenta de ingreso del producto o de su categoría.
        """
        vals = super()._prepare_invoice_line(**optional_values)
        if (
            self.order_id.is_rental
            and not self.is_downpayment
            and not self.display_type
        ):
            account = self.product_id.with_company(
                self.company_id
            ).rental_income_account_id
            if account:
                vals["account_id"] = account.id
        return vals

    def _get_display_price(self):
        """En una cotización de renta el precio base es la tarifa por evento.

        Es el hook oficial para precios que no vienen del tarifario. Se usa la
        tarifa del producto convertida a la moneda de la orden cuando difiere.
        """
        self.ensure_one()
        if (
            self.order_id.is_rental
            and self.product_id
            and self.product_id.rental_ok
        ):
            price = self.product_id.rental_price or 0.0
            company_currency = self.company_id.currency_id
            order_currency = self.currency_id
            if (
                order_currency
                and company_currency
                and order_currency != company_currency
            ):
                price = company_currency._convert(
                    price,
                    order_currency,
                    self.company_id,
                    self.order_id.date_order or fields.Date.context_today(self),
                )
            return price
        return super()._get_display_price()
