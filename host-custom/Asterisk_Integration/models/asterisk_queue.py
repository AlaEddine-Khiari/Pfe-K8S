# -*- coding: utf-8 -*-

from odoo import _, models, fields, api
from asterisk.ami import SimpleAction

from odoo.exceptions import UserError,ValidationError

class AsteriskQueue(models.Model):
    _name = 'asterisk.queue'
    _description='All Logs Of Asterisk Server To Contorl Calls'
    _sql_constraints = [
        ('unique_member', 'UNIQUE(member)', 'Member must be unique in the queue!'),
    ]

    name = fields.Char(string='Queue Name', required=True, default='support', readonly=True)
    member = fields.Many2one('res.users', string='Member', required=True)
    action = fields.Selection([('pause', 'Pause'),
                               ('unpause', 'Unpause')],
                              string='Status')

    #Ensures the uniqueness of each member in the queue to prevent duplicates.
    @api.constrains('member')
    def _check_unique_member(self):
        for record in self:
            existing_record = self.search([('id', '!=', record.id), ('member', '=', record.member.id)])
            if existing_record:
                raise ValidationError(_('Member must be unique in the queue!'))

    #Triggers the execution of telephony actions (pause or unpause) based on user input.
    @api.onchange('action')
    def perform_action(self):
        if self.action:
            self.execute_action()

    #Handles the integration of a new queue member into the Asterisk system upon record creation.
    @api.model
    def create(self, vals):
        # Extract field values from vals
        queue_name = vals.get('name', 'support')
        member_id = vals.get('member')

        if member_id:
            # Retrieve member's resource from res.users model
            member = self.env['res.users'].browse(member_id)
            member_resource = member.resource
            if (not member_resource):
                raise UserError(_("User Don't Have Asterisk Configuration"))
            else:
                # Get the current user's Asterisk server configuration
                user = self.env.user
                ast_server = user.get_asterisk_server_from_user()
                try:
                    # Connect to Asterisk Manager Interface (AMI)
                    client = ast_server._connect_to_ami()

                    if client is None:
                        raise UserError(_("Failed to connect to Asterisk Server"))

                    # Construct and send the Asterisk command
                    asterisk_command = SimpleAction('Command', Command="queue add member SIP/{} to {}".format(member_resource, queue_name))
                    future = client.send_action(asterisk_command)

                    if "Error" in str(future.response):
                        raise UserError(_("Error, Cannot Add Member To Queue"))

                except Exception as e:
                    raise UserError(_("Failed to execute Asterisk command: %s" % str(e)))
                finally:
                    if client:
                        client.logoff()

       # Call super to create the record in the database
        new_record = super(AsteriskQueue, self).create(vals)
        return new_record

    #Removes a member from the Asterisk queue prior to deleting the record from Odoo.
    def unlink(self):
        # Iterate over each record to be deleted
        for record in self:
            # Retrieve necessary information from the record
            queue_name = record.name
            member_resource = record.member.resource

            # Get the current user's Asterisk server configuration
            user = self.env.user
            ast_server = user.get_asterisk_server_from_user()

            try:
                # Connect to Asterisk Manager Interface (AMI)
                client = ast_server._connect_to_ami()

                if client is None:
                    raise UserError(_("Failed to connect to Asterisk Server"))

                # Construct and send the Asterisk command to remove the member from the queue
                asterisk_command = SimpleAction('Command', Command="queue remove member SIP/{} from {}".format(member_resource, queue_name))
                future = client.send_action(asterisk_command)

                if "Error" in str(future.response):
                    raise UserError(_("Error, Cannot Delete Member From Queue"))

            except Exception as e:
                raise UserError(_("Failed to execute Asterisk command: %s" % str(e)))
            finally:
                if client:
                    client.logoff()

        # Call super to proceed with the deletion of the records
        return super(AsteriskQueue, self).unlink()

    #Executes telephony commands via Asterisk based on the selected action for an existing queue member.
    def execute_action(self):
        self.ensure_one()
        user = self.env.user
        ast_server = user.get_asterisk_server_from_user()
        try:
            client = ast_server._connect_to_ami()

            if client is None:
                raise UserError(_("Failed to receive response from Asterisk Server"))
                return
            else:
                if self.action == 'pause':
                    result = SimpleAction('Command', Command='queue pause member SIP/{} queue {}'.format(self.member.resource, self.name))
                elif self.action == 'unpause':
                    result = SimpleAction('Command', Command='queue unpause member SIP/{} queue {}'.format(self.member.resource, self.name))

                future = client.send_action(result)

                if "Error" in str(future.response):
                    raise UserError(_("Error, Modifying Status"))
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Queue',
                            'message': 'Success Modifying Status',
                            'sticky': False
                        }
                    }
        finally:
            if client:
                client.logoff()

    #Retrieves a list of active, unpaused members of a specified queue.
    @api.model
    def get_unpaused_queue_members(self, queue_name):
        """Method to retrieve users of queue members with 'unpause' status in a specific queue."""
        # Search for all queue members in the specified queue with 'unpause' action
        queue_members = self.search([('name', '=', queue_name), ('action', '=', 'unpause')])

        # Ensure queue_members is not empty
        if queue_members:
            # Retrieve all unique member IDs from the queue_members recordset
            users = queue_members.mapped('member')
            return users
        else:
            # If no queue members match the criteria, return an empty list
            return []