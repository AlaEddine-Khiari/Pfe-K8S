from odoo import _, api, models, fields
from odoo.exceptions import UserError
from io import BytesIO
from pydub import AudioSegment
import os
import requests
import logging

_logger = logging.getLogger(__name__)

class CDRLog(models.Model):
    _name = 'cdr.log'
    _description = 'Call Detail Record Asterisk'
    _readonly = True

    timestamp = fields.Datetime(string='Timestamp', readonly=True, store=True)
    source = fields.Char(string='Caller', readonly=True, store=True)
    destination = fields.Char(string='Destination Number', readonly=True, store=True)
    status = fields.Char(string='Call Status', readonly=True, store=True)
    duration = fields.Char(string='Call Duration', readonly=True, store=True)
    call_recording = fields.Binary(string='Call Recording File', readonly=True, store=True, attachment=False)
    file_path = fields.Char(string='File Path', readonly=True, default=False)
    audio_player_html = fields.Html(string='Listen To Recoding', sanitize = False, compute = 'get_audio_html')



    #method to update logs from an external service
    @api.model
    def update_logs(self):
        url = f'http://{self.env.user.get_asterisk_server_from_user().ip_address}:4000/apply'
        if not (self.env.user.get_asterisk_server_from_user()):
            raise UserError(_("No Server Configured"))
        else:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    raise UserError(_("Error verifying service"))

                # If no errors occurred, return a success message
                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Server',
                            'message': 'Logs Updated Refresh Page',
                            'sticky': False
                    }
                }
            except Exception as e:
                raise UserError(_("Error connecting to server: %s" % str(e)))
    
    def convert_recording(self):
        self.ensure_one()
        # Check if call recording exists
        if not self.call_recording:
            raise UserError("No Call Recording Available.")

        try:
            # Convert binary data to audio
            audio = AudioSegment.from_file(BytesIO(self.call_recording), format="wav")

            # Save audio to a temporary file
            self.file_path = "/Asterisk_Integration/static/audio/" + str(self.id) + ".wav"
            temp_file = "/mnt/extra-addons/" + self.file_path
            audio.export(temp_file, format="wav")

            # Delete binary data from the database
            self.write({'call_recording': False})

        except Exception as e:
            raise UserError(_("Error converting audio: %s" % str(e)))

    @api.depends('file_path') 
    def get_audio_html(self):
        for record in self: 
            if not record.file_path:
                record.audio_player_html = 'No audio file available.'
            else:
                record.audio_player_html = f'<audio controls><source src="{record.file_path}" type="audio/wav">Your browser does not support the audio element.</audio>'
        
    def delete_temp_file(self):
        self.ensure_one()
        temp_file = "/mnt/extra-addons/" + self.file_path
        try:
            if self.file_path and os.path.exists(temp_file):
                os.remove(temp_file)
                # Clear the file_path field after deleting the file
                self.file_path = False
        except Exception as e:
            raise UserError(_("Error deleting temporary file: %s" % str(e)))
        
    def unlink(self):
        for record in self:
            if record.file_path:
                try:
                    record.delete_temp_file()  # Call the delete_temp_file method
                except Exception as e:
                    raise UserError(_("Error deleting file: %s" % str(e)))
        return super(CDRLog, self).unlink()