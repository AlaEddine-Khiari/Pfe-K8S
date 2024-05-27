
{
    "name": "Base Phone",
    "version": "1.0",
    "category": "Phone",
    "license": "AGPL-3",
    "sequence": "15",
    "author": "Pfe Zenoovi (Ala & Dhia)",
    "website": "https://github.com/xxx/xxx",
    "depends": ["phone_validation", "base_setup"],
    "external_dependencies": {"python": ["phonenumbers"]},
    "data": [
        "security/phone_security.xml",
        "security/ir.model.access.csv",
        "wizard/res_config_settings.xml",
        "views/res_users_view.xml",
        "wizard/reformat_all_phonenumbers_view.xml",
        "wizard/number_not_found_view.xml",
        "views/web_phone.xml",
    ],
    "qweb": ["static/src/xml/phone.xml"],
    "installable": True,
}
