from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

class TestAsteriskIntegration(TransactionCase):
    def setUp(self):
        super(TestAsteriskIntegration, self).setUp()
        # Set up any necessary records or environment
        self.Partner = self.env['res.partner']
        self.partner1 = self.Partner.create({'name': 'John Doe', 'phone': '1234567890'})

        self.AsteriskIntegration = self.env['Asterisk_Integration.model']

    def test_call_functionality(self):
        # Simulate a call initiation and check if it is logged correctly
        self.AsteriskIntegration.make_call(self.partner1.id)
        # Check results (e.g., a new log entry is created)
        log_count = self.env['your.call.log.model'].search_count([('partner_id', '=', self.partner1.id)])
        self.assertEqual(log_count, 1, "Call should be logged")

    def test_update_logs(self):
        # Simulate updating a call log
        call_log = self.env['your.call.log.model'].create({
            'partner_id': self.partner1.id,
            'call_duration': '00:05:00'
        })
        call_log.write({'call_duration': '00:10:00'})
        self.assertEqual(call_log.call_duration, '00:10:00', "Call log should be updated")

    def test_phone_number_validation(self):
        # Test to ensure that only valid phone numbers are accepted
        with self.assertRaises(ValidationError, msg="Should raise an exception for invalid phone number"):
            self.partner1.write({'phone': 'invalid_phone_number'})

    def test_change_partner_phone(self):
        # Test changing a partner's phone number
        self.partner1.write({'phone': '0987654321'})
        self.assertEqual(self.partner1.phone, '0987654321', "Partner's phone number should be updated")

    def test_generate_wav_file(self):
        # Test the generation of a WAV file
        wav_file = self.AsteriskIntegration.generate_wav_file("Hello, this is a test message.")
        self.assertTrue(wav_file, "WAV file should be generated")
        self.assertIn('.wav', wav_file, "Generated file should be a WAV file")

    def test_event_listener(self):
        # Test the event listener for a specific telephony event
        self.AsteriskIntegration.on_event('incoming_call', self.partner1.id)
        # Check if the event has been logged or handled correctly
        event_logged = self.env['your.event.log.model'].search(
            [('partner_id', '=', self.partner1.id), ('event_type', '=', 'incoming_call')])
        self.assertTrue(event_logged, "Event should be logged")

