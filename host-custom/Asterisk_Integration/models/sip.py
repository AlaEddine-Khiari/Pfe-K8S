# -*- coding: utf-8 -*-
import requests
import logging

from asterisk.ami import SimpleAction
from odoo import _, api, fields, models
from odoo.exceptions import UserError,ValidationError

_logger = logging.getLogger(__name__)

class InternalNumbers(models.Model):
    _name = 'internal.numbers'
    _description = 'SIP Numbers for Internal Users'
    _rec_name = 'extension'
    _sql_constraints = [
        ('extension_unique', 'UNIQUE(extension)', 'Extension must be unique.'),
    ]
    
    extension = fields.Char(
        string='SIP Extension',
        required=True,
        help="The SIP extension number for the user.",
    )

    secret = fields.Char(
        string='Secret',
        required=True,
        help="The secret associated with the SIP extension."
    )

    note = fields.Text(
        string='Note',
        required=False,
        help="Additional notes or comments related to the SIP extension."
    )

    status = fields.Selection(
        [('not_updated', 'Not Updated'), ('updated', 'Updated')],
        string='Status',
        default='not_updated',
        readonly=True,
        store=True,
        help="Status indicating whether the record has been updated with asterisk server."
    )
    
    @api.constrains('extension')
    def _check_unique_extension(self):
        # Check if any other record exists with the same extension
        duplicates = self.search([('extension', '=', self.extension)])
        if len(duplicates) > 1:
            raise ValidationError("Extension must be unique.")
    
    @api.constrains('extension')
    def _check_extension_format(self):
        for record in self:
            if record.extension:
                if not record.extension.isdigit():
                    raise ValidationError("Extension must contain only digits.")
                if len(record.extension) > 3:
                    raise ValidationError("Extension cannot exceed 3 characters.")

    def update_note_with_user(self, user):
        self.note = f"Assigned to {user.name}"

    def apply_changes(self):
        url = f'http://{self.env.user.get_asterisk_server_from_user().ip_address}:5000/apply'
        if not (self.env.user.get_asterisk_server_from_user()):
            raise UserError(_("No Server Configured"))
        else:
            try:
                res = requests.get(url, timeout=10)
                if res.status_code != 200:
                    raise UserError(_("Apply Changes Failed! Verify The Service"))
                self.restart_asterisk_server()
                # If no errors occurred, return a success message

                # Update status of all records to 'updated'
                self.update({'status': 'updated'})

                # Display success notification
                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Server',
                            'message': 'Updated Successfully, Refresh Page',
                            'sticky': False
                    }
                }
            except Exception as e:
                raise UserError(_(f"Apply Changes Failed! No Server Connection{e}"))
    
    @api.model
    def restart_asterisk_server(self):
        user = self.env.user
        ast_server = user.get_asterisk_server_from_user()

        try:
            client = ast_server._connect_to_ami()
            action = SimpleAction('Command', Command='core reload')
            if client is None:
                raise UserError(_("Failed to receive response from Asterisk Server"))
            else:
                future = client.send_action(action)
                if "Success" not in str(future.response) :
                    raise UserError("Asterisk Server Restart Failed.")
        except Exception as e:
            raise UserError(f"An error occurred: {e}")
        finally:
            if client:
                client.logoff()
    
    def unlink(self):
        # Check if any user is using this SIP number
        for number in self:
            users_with_extension = self.env['res.users'].search([('internals.extension', '=', number.extension)])
            if users_with_extension:
                raise UserError(_("Cannot delete SIP number '%s'. It is currently in use by user: %s" % (number.extension, ', '.join(users_with_extension.mapped('name')))))
        
        # If no users are using this SIP number, proceed with deletion
        return super(InternalNumbers, self).unlink()

    def write(self, values):
        # Check if 'extension' or 'secret' fields are being modified
        if 'extension' in values or 'secret' in values:
            # Check if any user is using the SIP number being modified
            for number in self:
                users_with_extension = self.env['res.users'].search([('internals.extension', '=', number.extension)])
                if users_with_extension:
                    raise UserError(_("Cannot modify SIP number '%s'. It is currently in use by user(s): %s" % (
                        number.extension, ', '.join(users_with_extension.mapped('name')))))

            # Always set 'status' field to 'not_updated' on modification
            values['status'] = 'not_updated'
        return super(InternalNumbers, self).write(values)