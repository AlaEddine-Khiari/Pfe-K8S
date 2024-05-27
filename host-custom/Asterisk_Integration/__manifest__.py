{
    "name": "Asterisk Integration",
    "version": "1.0",
    "summary": "Asterisk-Odoo Integration",
    "category": "Phone",
    "license": "AGPL-3",
    "sequence": "10",
    "author": "Pfe Zenoovi (Ala & Dhia)",
    "website": "https://github.com/xxx/xxx",
    "depends": [
        "base_phone",
        "board",
        "contacts",
        "crm",
                ],
    "external_dependencies": {"python": ["requests", "asterisk-ami","pydub"]},
    "data": [
        "views/phone_common.xml",
        "views/asterisk_server.xml",
        "views/res_users.xml",
        "views/sip.xml",
        "views/logs.xml",
        "views/asterisk_queue.xml",
        "views/sms.xml",
        "views/dashboard.xml",
        "views/eventlistnner.xml",
        "wizard/status.xml",
        "data/corn_event.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
    ],
    "demo": [],
    "qweb": [
        "static/src/xml/click2dial.xml",
        "static/src/xml/audio_player.xml",
    ],
    "assets": {
       "web.assets_backend": [
           "Asterisk_Integration/static/src/js/audio_player_widget.js",
       ]
    },
    "application": True,
    "installable": True,
}
