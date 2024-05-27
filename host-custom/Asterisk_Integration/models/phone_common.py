import logging

from asterisk.ami import SimpleAction
from odoo import _, models, api, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PhoneCommon(models.AbstractModel):
    _inherit = "phone.common"

    @api.model
    def find_partner_by_erp_number(self, erp_number):
        partner = self.env['res.partner'].search([
            '|',
            ('phone', '=', erp_number),  # Match against the phone field
            ('mobile', '=', erp_number),  # Match against the mobile field
        ], limit=1)
        return partner

    @api.model
    def click2dial(self, erp_number):
        _logger.debug("Entering click2dial method with erp_number: %s", erp_number)

        if not erp_number:
            _logger.error("Error: Missing phone number in click2dial method.")
            raise UserError(_("Missing phone number"))

        user = self.env.user
        ast_server = user.get_asterisk_server_from_user()
        ast_number = self.convert_to_dial_number(erp_number)
        client = None

        try:
            client = ast_server._connect_to_ami()
            action = SimpleAction(
                'Originate',
                Channel=user.asterisk_chan_name,
                Exten=ast_number,
                Priority=str(ast_server.extension_priority),
                Context=ast_server.context,
                CallerID=f'{user.callerid} <{user.resource}>',
                Async=True,
                Timeout=ast_server.wait_time,
            )
            if client is None:
                _logger.error("Asterisk Click2Dial Failed.")
                raise UserError(_("Failed to receive response from Asterisk Server"))
            else:
                future = client.send_action(action)
                # Get the string representation of future.response
                response_str = str(future.response)

                # Check if "PeerResponse: Success" exists in the response string
                if "Response: Error" in response_str:
                    _logger.error("Asterisk Click2Dial Failed.")
                    raise UserError(_(f"You Don't Have Asterisk Number"))
                else:
                    # Get the current date and time with seconds from Odoo
                    now = fields.Datetime.now()
                    # Search The Partner With His Phone Number
                    partner = self.find_partner_by_erp_number(erp_number)
                    if not partner:
                        _logger.error(f"No partner found with: {erp_number}")
                    elif len(ast_number) < 4:
                        act_form=None
                    else:
                        activity_model = self.env['mail.activity']
                        activity_type = self.env.ref(
                            'mail.mail_activity_data_call')  # Assuming there is an activity type for calls
                        # Get the ID of the 'res.partner' model
                        res_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
                        # Create a new activity record
                        activity_vals = {
                            'res_model_id': res_model.id,
                            'res_id': partner.id,  # Associate the activity with the found partner
                            'activity_type_id': activity_type.id,
                            'summary': now,
                            'date_deadline': fields.Date.context_today(self),
                            'user_id': user.id,
                        }
                        new_activity = activity_model.create(activity_vals)
                        # Open the activity form view for the user to add more details
                        act_form = {
                            'name': 'Phone Call Activity',
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'mail.activity',
                            'res_id': new_activity.id,
                            'views': [(self.env.ref('mail.mail_activity_view_form_popup').id, 'form')],
                            'target': 'new',
                        }
        finally:
            if client:
                client.logoff()
        _logger.debug("Exiting click2dial method")
        return {"dialed_number": ast_number, "action": act_form}

    def convert_to_dial_number(self, erp_number):
        # Remove non-numeric characters
        dial_number = ''.join(filter(str.isdigit, erp_number))
        return dial_number

    @api.model
    def voicemail(self):
        user = self.env.user
        ast_server = user.get_asterisk_server_from_user()

        if not user.resource:
            return {'error': _("You Don't Have An Internal Number")}

        ast_number = f"*{user.resource}"
        try:
            client = ast_server._connect_to_ami()
            if client is None:
                _logger.error("Failed to connect to Asterisk Server")
                return {'error': _("Failed to connect to Asterisk Server")}

            action = SimpleAction(
                "Originate",
                Channel=user.asterisk_chan_name,
                Exten=ast_number,
                Priority=str(ast_server.extension_priority),
                Context=ast_server.context,
                CallerID="Voice Mail",
                Async=True,
                Timeout=ast_server.wait_time,
            )

            future = client.send_action(action)
            response_str = str(future.response)

            if "Response: Error" in response_str:
                _logger.error("Asterisk Voicemail Failed")
                return {'error': _("Asterisk Voicemail Failed")}
            else:
                _logger.info("Asterisk Voicemail initiated successfully.")
                return {'internalNumber': True}

        except Exception as e:
            _logger.error("An error occurred during voicemail: %s", e)
            return {'error': _("An error occurred during voicemail")}


