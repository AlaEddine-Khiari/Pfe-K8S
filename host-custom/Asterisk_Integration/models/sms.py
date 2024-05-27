from asterisk.ami import SimpleAction

from odoo import models, fields, _
from odoo.exceptions import UserError


def notify_message(message, message_type='success'):
    notification = {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _('Success') if message_type == 'success' else _('Error'),
            'type': 'success' if message_type == 'success' else 'danger',
            'message': message,
            'sticky': False,
            'next': {'type': 'ir.actions.act_window_close'},
            'closeAfter': 5000  # Close after 5 seconds
        }
    }
    return notification


class AsteriskSMS(models.Model):
    _name = 'asterisk.sms'
    _description = 'Asterisk SMS Integration'

    message_destination = fields.Many2one("res.partner", string='Contact', required=True)
    message_body = fields.Text(string='Message Body', required=True)

    #The function enables sending messages using the Asterisk Manager Interface (AMI) to a specified destination.
    #It first checks if the user has a designated internal number and then validates the destination phone number before proceeding to send the message.
    def send_message(self):
        user = self.env.user
        ast_server = user.get_asterisk_server_from_user()
        client = ast_server._connect_to_ami()

        if not user.internals:
            raise UserError(_("You Don't Have An Internal Number"))

        try:
            client = ast_server._connect_to_ami()
            if not client:
                raise UserError(_("Failed to receive response from Asterisk Server"))
            elif (len(self.message_destination.phone) > 4) or (not self.message_destination.phone):
                raise UserError(_("Destination Don't Have Asterisk Number"))
            else:
                action = SimpleAction(
                    'MessageSend',
                    From=f"sip:{user.resource}",
                    Destination=f"sip:{self.message_destination.phone}",
                    Body=self.message_body,
                )
                future = client.send_action(action)
                if "Success" not in str(future.response):
                    raise UserError("SMS Failed.")
                else:
                    return notify_message("Message sent successfully")
        except Exception as e:
            raise UserError(f"An error occurred: {e}")
        finally:
            if client:
                client.logoff()