from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "phone.validation.mixin"]
    _phone_name_sequence = 10
    _phone_name_fields = ["phone", "mobile"]

    def name_get(self):
        if self._context.get("callerid"):
            res = []
            for partner in self:
                if partner.parent_id and partner.parent_id.is_company:
                    name = "{}, {}".format(partner.parent_id.name, partner.name)
                else:
                    name = partner.name
                res.append((partner.id, name))
            return res
        else:
            return super().name_get()
