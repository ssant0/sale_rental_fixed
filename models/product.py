from odoo import fields, models

ACCOUNT_DOMAIN = (
    "[('account_type', 'not in', ('asset_receivable','liability_payable',"
    "'asset_cash','liability_credit_card','off_balance'))]"
)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    rental_ok = fields.Boolean(
        string="Se puede rentar",
        default=False,
        help="Permite usar este producto en cotizaciones de renta. "
        "Un producto rentable también puede venderse.",
    )
    rental_price = fields.Monetary(
        string="Tarifa de renta (por evento)",
        currency_field="currency_id",
        help="Precio fijo por el periodo completo del evento, sin importar su "
        "duración. En cada cotización se puede ajustar manualmente.",
    )
    rental_income_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Cuenta de ingreso de renta",
        company_dependent=True,
        ondelete="restrict",
        domain=ACCOUNT_DOMAIN,
        help="Cuenta de ingreso para las líneas de renta. Si se deja vacía, se "
        "usa la cuenta de ingreso del producto o de su categoría.",
    )
