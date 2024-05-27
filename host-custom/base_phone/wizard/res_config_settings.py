
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    number_of_digits_to_match_from_end = fields.Integer(
        related="company_id.number_of_digits_to_match_from_end", readonly=False
    )
