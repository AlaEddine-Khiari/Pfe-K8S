from odoo import http,_
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class AsteriskIntegrationController(http.Controller):

    @http.route("/Asterisk_Integration/get_record_from_my_channel", type="json", auth="user")
    def get_record_from_my_channel(self, **kw):
        try:
            record = request.env["phone.common"].voicemail()
            return record
        except Exception as e:
            _logger.error("Error occurred during voicemail: %s", e)
            return False

    @http.route('/incoming-call', type='http', auth='public', website=False)
    def handle_notif_route(self, **kw):
        try:
            exten = kw.get('exten')
            caller = kw.get('caller')
            if not (exten and caller):
                return "Extension and Caller required."
            elif exten == "39100200":
                # Retrieve users with status 'unpause' from AsteriskQueue in external call
                users =request.env['asterisk.queue'].sudo().get_unpaused_queue_members('support')
            else:
                # Search for User in res users in internal call
                users = request.env['res.users'].sudo().search([('resource', '=', str(exten))], limit=1)
            for user in users:
                partner_id = user.partner_id.id
                message = _(f"Incoming call from {caller} Check Your Softphone!")
                request.env['bus.bus'].sendone(
                    (request._cr.dbname, 'res.partner', partner_id),
                    {
                        'type': 'simple_notification',
                        'title': _("Incoming call"),
                        'message': message,
                        'sticky': True,
                        'warning': True,
                    }
                )
            return "{'status': 'success'}"
        except Exception as e:
            return "Error: {}".format(str(e))

