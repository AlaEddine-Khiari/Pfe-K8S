odoo.define("Asterisk_Integration.systray.OpenCaller", function (require) {
    "use strict";

    var Widget = require("web.Widget");
    var core = require("web.core");
    var SystrayMenu = require("web.SystrayMenu");

    var _t = core._t;

    var FieldPhone = require("base_phone.updatedphone_widget").FieldPhone;

    FieldPhone.include({
        showDialButton: function () {
            return true;
        },
    });

    var OpenCallerMenu = Widget.extend({
        template: "Asterisk_Integration.systray.OpenCaller",

        events: {
            "click #asterisk-open-caller": "on_open_caller",
        },

        on_open_caller: function (event) {
            event.preventDefault();
            event.stopPropagation();

            var self = this; // Capture 'this' for reference inside the promise callback

            // Make an RPC call to retrieve data
            this._rpc({
                route: "/Asterisk_Integration/get_record_from_my_channel",
                params: {}, // Add any necessary parameters for the RPC call
            }).then(function (result) {
                if (result.error) {
                    // Handle server connection error
                    self.do_warn(_t("Call Error"), result.error, false);
                } else if (result.internalNumber) {
                    // Handle successful response with internal number
                    self.do_notify(
                        _t("Call Info"),
                        _t("Calling Voice Mail"),
                        false
                    );
                } else {
                    // Handle other specific scenarios
                    self.do_warn(
                        _t("Call Error"),
                        _t("You Don't Have An Internal Number"),
                        false
                    );
                }
            }).guardedCatch(function (error) {
                console.error("Error occurred during RPC call:", error);
                self.do_warn(
                    _t("Call Error"),
                    _t("Failed to connect to Asterisk Server"),
                    false
                );
            });
        },
    });

    SystrayMenu.Items.push(OpenCallerMenu);

    return OpenCallerMenu;
});