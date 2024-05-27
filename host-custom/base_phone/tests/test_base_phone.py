from odoo.tests.common import TransactionCase


class TestBasePhone(TransactionCase):
    def setUp(self):
        super(TestBasePhone, self).setUp()
        self.fr_country_id = self.env.ref("base.fr").id
        self.phco = self.env["phone.common"]
        self.env.company.write({"country_id": self.fr_country_id})
        self.akretion = self.env["res.partner"].create(
            {
                "name": "Ala Tunisia",
                "country_id": self.fr_country_id,
                "phone": "+216 26454831",
            }
        )

    def test_get_phone_model(self):
        res = self.phco._get_phone_models()
        self.assertIsInstance(res, list)
        rpo = self.env["res.partner"]
        self.assertTrue(any([x["object"] == rpo for x in res]))
        for entry in res:
            self.assertIsInstance(entry.get("fields"), list)

    def test_lookup(self):
        res = self.phco.get_record_from_phone_number("26454831")
        self.assertIsInstance(res, tuple)
        self.assertEqual(res[0], "res.partner")
        self.assertEqual(res[1], self.akretion.id)
        self.assertEqual(
            res[2], self.akretion.with_context(callerid=True).name_get()[0][1]
        )
        res = self.phco.get_record_from_phone_number("23916552")
        self.assertFalse(res)

    def test_to_dial(self):
        phone_to_dial = self.phco.convert_to_dial_number("+216 26454831")
        self.assertEqual(phone_to_dial, "26454831")
        phone_to_dial = self.phco.convert_to_dial_number("+32 455 78 99 88")
        self.assertEqual(phone_to_dial, "0032455789988")

    def test_partner_phone_formatting(self):
        rpo = self.env["res.partner"]
        # Create an existing partner without country
        partner1 = rpo.create(
            {
                "name": "Dhia Othmani",
                "phone": "71256963",
                "mobile": "21924299",
            }
        )
        partner1._onchange_phone_validation()
        partner1._onchange_mobile_validation()
        self.assertEqual(partner1.phone, "+216 71256963")
        self.assertEqual(partner1.mobile, "+216 21924299")
        # Create a partner with country
        parent_partner2 = rpo.create(
            {
                "name": "C2C",
                "country_id": self.env.ref("base.ch").id,
                "is_company": True,
            }
        )
        partner2 = rpo.create(
            {
                "name": "Joël Grand-Guillaume",
                "parent_id": parent_partner2.id,
                "phone": "(0) 21 619 10 10",
                "mobile": "(0) 79 606 42 42",
            }
        )
        partner2._onchange_phone_validation()
        partner2._onchange_mobile_validation()
        self.assertEqual(partner2.country_id, self.env.ref("base.ch"))
        self.assertEqual(partner2.phone, "+41 21 619 10 10")
        self.assertEqual(partner2.mobile, "+41 79 606 42 42")
        # Write on an existing partner
        partner3 = rpo.create(
            {
                "name": "Belgian corp",
                "country_id": self.env.ref("base.be").id,
                "is_company": True,
            }
        )
        partner3.write({"phone": "(0) 2 391 43 74"})
        partner3._onchange_phone_validation()
        self.assertEqual(partner3.phone, "+32 2 391 43 74")
        # Write on an existing partner with country at the same time
        partner3.write(
            {
                "phone": "04 72 89 32 43",
                "country_id": self.fr_country_id,
            }
        )
        partner3._onchange_phone_validation()
        self.assertEqual(partner3.phone, "+33 4 72 89 32 43")
        # Test get_name_from_phone_number
        pco = self.env["phone.common"]
        name = pco.get_name_from_phone_number("0642774266")
        self.assertEqual(name, "Pierre Paillet")
        name2 = pco.get_name_from_phone_number("0041216191010")
        self.assertEqual(name2, "C2C, Joël Grand-Guillaume")
