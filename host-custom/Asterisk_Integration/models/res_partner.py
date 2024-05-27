from odoo import _, api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    phone = fields.Char(string="Phone", compute="_compute_phone", inverse="_inverse_phone", store=True)

    @api.depends('user_ids.internal_number')
    def _compute_phone(self):
        for partner in self:
            user = partner.user_ids.filtered(lambda u: u.internal_number)
            if user:
                partner.phone = user.internal_number
            else:
                partner.phone = False
    #Provides the inverse logic for the computed phone field. When the phone field on a partner record is updated
    def _inverse_phone(self):
        for partner in self:
            user = partner.user_ids.filtered(lambda u: u.internal_number) #checks if u.internal_number exists
            if user:
                user.internal_number = partner.phone
