from odoo import models


class PhoneValidationMixin(models.AbstractModel):
    _inherit = "phone.validation.mixin"

    def _phone_get_country(self):
        if "country_id" in self and self.country_id:
            return self.country_id
        if "partner_id" in self and self.partner_id and self.partner_id.country_id:
            return self.partner_id.country_id
        return self.env.company.country_id
