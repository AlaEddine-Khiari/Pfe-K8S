# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from asterisk.ami import AMIClient

from socket import timeout as SocketTimeoutError
from odoo.exceptions import UserError, ValidationError

class AsteriskServer(models.Model):
    _name = "asterisk.server"
    _description = "Asterisk Servers"

    name = fields.Char(string="Asterisk Server Name", required=True)

    ip_address = fields.Char(string="Asterisk IP address or DNS", required=True)

    port = fields.Char(
        string="Port",
        required=True,
        default=5038,
        help="TCP port on which the Asterisk REST Interface listens. "
             "Defined in /etc/asterisk/ari.conf on Asterisk.",
    )

    login = fields.Char(
        string="AMI Login",
        required=True,
        help="Login that Odoo will use to communicate with the "
             "Asterisk REST Interface. Refer to /etc/asterisk/ami.conf "
             "on your Asterisk server.",
    )
    password = fields.Char(
        string="AMI Password",
        required=True,
        help="Password that Odoo will use to communicate with the "
             "Asterisk REST Interface. Refer to /etc/asterisk/ami.conf "
             "on your Asterisk server.",
    )
    context = fields.Char(
        string="Dialplan Context",
        required=True,
        default="internal",
        help="Asterisk dialplan context from which the calls will be "
             "made. Refer to /etc/asterisk/extensions.conf on your Asterisk "
             "server.",
    )

    extension_priority = fields.Integer(
        string="Extension Priority",
        required=True,
        default=1,
        help="Priority of the extension in the Asterisk dialplan. Refer "
        "to /etc/asterisk/extensions.conf on your Asterisk server.",
    )

    wait_time = fields.Integer(
        string="Wait Time",
        required=True,
        default=30000,
        help="Amount of time (in seconds) Asterisk will try to reach "
             "the user's phone before hanging up.",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        help="Company who uses the Asterisk server.",
    )

    @api.constrains(
        "wait_time",
        "port",
        "context",
        "login",
        "password",
    )
    #Validates server settings such as wait time, port range, and ensures string fields like login and password only contain ASCII characters, throwing a ValidationError if not.
    def _check_validity(self):
        for server in self:
            login = ("AMI login", server.login)
            password = ("AMI password", server.password)
            dialplan_context = ("Dialplan context", server.context)

            if server.wait_time < 10000 or server.wait_time > 60000:
                raise ValidationError(
                    _(
                        "You should set a 'Wait time' value between 1 and 120 "
                        "seconds for the Asterisk server '%s'" % server.name
                    )
                )

            if server.extension_priority < 1:
                raise ValidationError(
                    _(
                        "The 'extension priority' must be a positive value for "
                        "the Asterisk server '%s'" % server.name
                    )
                )
            
            if int(server.port) > 65535 or int(server.port) < 1:
                raise ValidationError(
                    _(
                        "You should set a TCP port between 1 and 65535 for the "
                        "Asterisk server '%s'" % server.name
                    )
                )
            for check_str in [dialplan_context, login, password]:
                if check_str[1]:
                    try:
                        check_str[1].encode("ascii")
                    except UnicodeEncodeError:
                        raise ValidationError(
                            _(
                                "The '%s' should only have ASCII characters for "
                                "the Asterisk server '%s'" % (check_str[0], server.name)
                            )
                        )

    #Attempts to connect to the configured Asterisk server using the AMI (Asterisk Manager Interface), providing feedback on the success or failure of the connection.
    def test_ami_connection(self):
        self.ensure_one()
        try:
            client = AMIClient(address=self.ip_address, port=int(self.port))
            future = client.login(username=self.login, secret=self.password)
            response = future.response
            client.logoff()
            if response is None:
                raise UserError("Cannot connect to server")
            else:
                raise UserError("%s" % response)
        except (SocketTimeoutError, ConnectionRefusedError) as e:
            raise UserError("Connection to Server Failed. Please check your Adresse Ip Server Or Port.")
            return False

    #Establishes a connection to the Asterisk server's AMI and returns the client object for further interaction, handling common errors like timeouts and connection refusals.
    @api.model
    def _connect_to_ami(self):
        self.ensure_one()
        try:
            client = AMIClient(address=self.ip_address, port=int(self.port))
            future = client.login(username=self.login, secret=self.password)
            response = str(future.response)
            if ("Response: Error" in response) or (future.response is None):
                client = None
            return client
        except (SocketTimeoutError, ConnectionRefusedError) as e:
            client = None
            return client
