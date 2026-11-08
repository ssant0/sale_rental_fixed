from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self, *args, **kwargs):
        """Sincroniza el estado de la renta al validar el picking.

        La entrega y la devolución pueden validarse desde el botón de la
        cotización o desde el picking estándar (icono del camión). Este hook
        mantiene ambos caminos conectados con `rental_status`.
        """
        res = super()._action_done(*args, **kwargs)
        self._sync_rental_status()
        return res

    def _sync_rental_status(self):
        for picking in self:
            order = picking._get_rental_order()
            if not order or not order.is_rental or order.state not in ("sale", "done"):
                continue
            is_return = bool(picking.return_id) or picking.location_id.usage == "customer"
            if is_return:
                if order.rental_status == "active":
                    order.rental_status = "returned"
            elif picking.picking_type_code == "outgoing":
                if order.rental_status == "pending":
                    order.rental_status = "active"

    def _get_rental_order(self):
        self.ensure_one()
        order = self.sale_id or self.return_id.sale_id
        if not order:
            order = self.move_ids.sale_line_id.order_id[:1]
        return order
