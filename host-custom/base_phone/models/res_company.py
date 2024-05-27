from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    number_of_digits_to_match_from_end = fields.Integer(
        string="Number of Digits To Match From End",
        default=8,
        help="In several situations, Odoo will have to find a "
        "Partner/Lead/Employee/... from a phone number presented by the "
        "calling party.",
    )

    _sql_constraints = [
        (
            "number_of_digits_to_match_from_end_positive",
            "CHECK (number_of_digits_to_match_from_end > 0)",
            "The value of the field 'Number of Digits To Match From End' must "
            "be positive.",
        )
    ]
