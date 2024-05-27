from odoo import api, models
from odoo.exceptions import UserError

class EditAsteriskStatusWizard(models.TransientModel):
    _name = 'edit.asterisk.status.wizard'
    _description = 'Edit Asterisk Status Wizard'

    @api.model
    def action_edit_status(self):
        # Get the current user
        user = self.env.user
        support_queue = self.env['asterisk.queue'].search([('member', '=', user.id)], limit=1)
        if support_queue:
            # Open the specified view for the user
            return {
                'type': 'ir.actions.act_window',
                'name': 'Edit Asterisk Status',
                'view_mode': 'form',
                'res_model': 'asterisk.queue',
                'res_id': support_queue.id,
                'view_id': self.env.ref('Asterisk_Integration.view_queue_form_custom').id,
                'target': 'new',
            }
        else:
            raise UserError("You Are Not In The Support Team")
