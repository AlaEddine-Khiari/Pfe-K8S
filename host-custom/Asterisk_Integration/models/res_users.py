import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    internals = fields.Many2one(
        comodel_name="internal.numbers",
        string="Extension",
        copy=False,
        help="Resource extension for the channel type selected. "
    )

    callerid = fields.Char(
        string="Caller ID",
        related='name',
        readonly=True,
        store=True,
        help="Caller ID used for the calls initiated by this user.",
    )

    asterisk_chan_type = fields.Selection(
        [
            ("PJSIP", "PJSIP"),
            ("SIP", "SIP"),
        ],
        string="Asterisk Channel Type",
        default="SIP",
        help="Asterisk channel type, as used in the Asterisk dialplan."
             " If the user has a regular IP phone, the channel type is probably 'SIP'.",
        required=True
    )

    asterisk_server_id = fields.Many2one(
        "asterisk.server",
        string="Asterisk Server",
        help="Asterisk server on which the user's phone is connected. ",
        required=True
    )

    resource = fields.Char(
        string="Resource",
        compute="_compute_resource",
        store=True,
    )

    asterisk_chan_name = fields.Char(
        compute="_compute_asterisk_chan_name",
        store=True,
        string="Asterisk Channel Name",
    )

    internal_number = fields.Char(
        string="Internal Number",
        compute="_compute_internal_number",
        store=True,
    )

    @api.constrains("internals")
    def _check_unique_internals(self):
        for user in self:
            if user.internals:
                # Check if there are other users having the same internal extension
                duplicate_users = self.env['res.users'].search(
                    [('internals', '=', user.internals.id), ('id', '!=', user.id)]
                )
                if duplicate_users:
                    raise ValidationError(
                        _("The extension '%s' is already assigned to another user.") % user.internals.extension
                    )

    @api.constrains("resource", "internal_number", "callerid")
    def _check_validity(self):
        for user in self:
            strings_to_check = [
                (_("Resource Name"), user.resource),
                (_("Internal Number"), user.internal_number),
                (_("Caller ID"), user.callerid),
            ]
            for check_string in strings_to_check:
                if check_string[1]:
                    try:
                        check_string[1].encode("ascii")
                    except UnicodeEncodeError:
                        raise ValidationError(
                            _(
                                "The '%s' for the user '%s' should only have "
                                "ASCII characters"
                            )
                            % (check_string[0], user.name)
                        )

    @api.onchange("internals")
    def _onchange_internals(self):
        self.resource = self.internals.extension
        self.internals.update_note_with_user(self)

    @api.depends("internals")
    def _compute_resource(self):
        for user in self:
            if user.internals:
                user.resource = user.internals.extension
                # Check if the user is a member of any Asterisk queue
                if self._user_in_asterisk_queue(user):
                    raise UserError("User '%s' is a member of an Asterisk queue. Cannot modify the extension." % user.name)
            else:
                user.resource = False

    @api.depends("resource")
    def _compute_internal_number(self):
        for user in self:
            user.internal_number = user.resource

    @api.depends("asterisk_chan_type", "resource")
    def _compute_asterisk_chan_name(self):
        for user in self:
            chan_name = False
            if user.asterisk_chan_type and user.resource:
                chan_name = "%s/%s" % (user.asterisk_chan_type, user.resource)
            user.asterisk_chan_name = chan_name
   
    @api.model
    def get_asterisk_server_from_user(self):
        self.ensure_one()
        # We check if the user has an Asterisk server configured
        if self.asterisk_server_id:
            ast_server = self.asterisk_server_id
        else:
            ast_server = self.env["asterisk.server"].search(
                [
                    "|",
                    ("company_id", "=", self.company_id.id),
                    ("company_id", "=", False),
                ],
                order="company_id",
                limit=1,
            )
            # If the user doesn't have an asterisk server,
            # we take the first one of the user's company
            if not ast_server:
                raise UserError(
                    _("No Asterisk server configured for You.")
                )
        return ast_server
    
    @api.model
    def _user_in_asterisk_queue(self, user):
        # Check if the user is a member of any Asterisk queue
        queue_model = self.env['asterisk.queue']
        existing_queues = queue_model.search([('member', '=', user.id)])
        return bool(existing_queues)