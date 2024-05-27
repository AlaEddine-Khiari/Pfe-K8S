from odoo import api, models


class IrFieldsConverter(models.AbstractModel):
    _inherit = "ir.fields.converter"

    @api.model
    def _str_to_phone(self, model, field, value):
        return super()._str_to_char(model, field, value)
