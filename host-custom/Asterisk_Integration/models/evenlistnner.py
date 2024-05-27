# -*- coding: utf-8 -*-
import requests
import socket

from odoo import _,models, fields, api, registry
from asterisk.ami import AMIClient

from socket import timeout as SocketTimeoutError
from odoo.exceptions import UserError


class AsteriskListener(models.Model):
    _name = 'asterisk.listener'
    _description = 'Asterisk Event Listener'
    _sql_constraints = [('singleton', 'UNIQUE(id)', 'There can be only one AsteriskListener')]

    host = fields.Char(string="Asterisk Host", required=True, default="192.168.2.50")
    port = fields.Integer(string="Port", default=5038, required=True)
    username = fields.Char(string="Username", required=True, default="odoo")
    secret = fields.Char(string="Secret", required=True, default="odoo")
    is_running = fields.Boolean(string='Running', default=False)

    #Sends a formatted action string to the Asterisk server via a socket connection.
    def send_action(self, sock, action):
        sock.send(action.encode())

    #Receives responses from the Asterisk server, assembling data packets until the end of the message .
    def receive_response(self, sock):
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if response.endswith(b"\r\n\r\n"):
                break
        return response.decode()

    #Parses key-value pairs from the raw response data into a dictionary for easy access to specific data fields.
    def parse_response(self, response):
        data = {}
        lines = response.split("\r\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()
        return data

    #Logs into the Asterisk server using provided credentials; this is a crucial step to authenticate before sending or receiving messages.
    def login(self, sock, username, secret):
        action = f"Action: Login\r\nUsername: {username}\r\nSecret: {secret}\r\n\r\n"
        self.send_action(sock, action)
        response = self.receive_response(sock)
        print(response)

    #Continuously receives messages from the Asterisk server, parsing each and reacting to specific events like new channels. It can trigger external actions like HTTP requests based on the content of these messages.
    def receive_messages(self, sock):
        while True:
            response = self.receive_response(sock)
            data = self.parse_response(response)
            if 'Event' in data and data['Event'] == 'Newchannel':
                exten = data.get('Exten')
                caller_id = data.get('CallerIDNum')
                if exten and caller_id != "<unknown>":
                    print(f"Extension: {exten}, Caller ID: {caller_id}")
                    url = f"http://localhost:8069/incoming-call?exten={exten}&caller={caller_id}"
                    response = requests.get(url)
                    if response.status_code == 200:
                        print("Notification sent successfully.")
                    else:
                        print ("error")

    #Sends a notification within the Odoo environment using the bus service, useful for real-time user alerts about telephony events.
    def process_event_notif(self, message, id):
        self.env['bus.bus'].sendone(
            (self._cr.dbname, 'res.partner', id),
            {
                'type': 'simple_notification',
                'title': _("Incoming call"),
                'message': message,
                'sticky': True,
                'warning': True,
            }
        )

    #Deactivates a scheduled job (cron) that listens for events from the Asterisk server, typically used to safely shut down background operations.
    def stop_listener_cron(self):
        listener_cron = self.env.ref(
            'Asterisk_Integration.cron_asterisk_listener')
        if listener_cron:
            self.is_running = False
            listener_cron.write({'active': False})
            return True
        return False

    #Activates or reactivates the cron job responsible for listening to events from the Asterisk server, including initial authentication checks.
    def start_listener_cron(self):
        listener_cron = self.env.ref(
            'Asterisk_Integration.cron_asterisk_listener')
        if listener_cron:
            try:
                client = AMIClient(address=self.host, port=int(self.port))
                future = client.login(username=self.username, secret=self.secret)
                response = future.response
                client.logoff()
                if "Authentication accepted" not in str(response):
                    raise UserError("Error Credential")
                self.is_running = True
                listener_cron.write({'active': True})
                return True
            except (SocketTimeoutError, ConnectionRefusedError) as e:
                raise UserError("Connection to Server Failed. Please check your Adresse Ip Server Or Port.")
        return False

    #Establishes a socket connection to listen for real-time events from the Asterisk server, handling authentication and message reception in a loop.
    @api.model
    def listen_for_events(self):
        listener = self.create_singleton()
        if listener:
            with api.Environment.manage():
                cr = registry(self.env.cr.dbname).cursor()
                env = api.Environment(cr, self.env.uid, self.env.context)
                listener_env = listener.with_env(env)
                sock = None
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((listener_env.host, listener_env.port))

                    listener_env.login(sock, listener_env.username, listener_env.secret)
                    listener_env.receive_messages(sock)

                except Exception as e:
                    raise UserError(f"Error in Asterisk listener: {e}")
                finally:
                    if sock:
                        sock.close()
                    if cr:
                        cr.close()

    #Enforces a singleton pattern by allowing only one record of this type to exist, ensuring that configuration settings do not conflict.
    @api.model
    def create(self, vals):
        if len(self.search([])) >= 1:
            raise UserError('A record already exists')
        return super(AsteriskListener, self).create(vals)

    #Prevents the deletion of the record, preserving critical configuration data necessary for the application's operation.
    def unlink(self):
        raise UserError('You cannot delete this record')

    @api.model
    def create_singleton(self):
        # Method to ensure only one record of this model exists
        existing_record = self.env['asterisk.listener'].search([], limit=1)
        return existing_record

    def open_form(self):
        # Ensure only one record exists
        listener_record = self.create_singleton()

        # Open the form view for the existing record
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'asterisk.listener',
            'view_mode': 'form',
            'res_id': listener_record.id,
            'target': 'new',
        }
        return action
