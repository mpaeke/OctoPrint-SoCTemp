# coding=utf-8
from __future__ import absolute_import

import sys
import re
import platform
import octoprint.plugin
from octoprint.util import RepeatedTimer

class SoCTempPlugin(octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.StartupPlugin,
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.TemplatePlugin):
    temp = 0
    color = "black"

    def get_settings_defaults(self):
        return dict(rate=10.0,
                    emoji="&#127819; ",  # 127818
                    tsp1=50,
                    tsp2=65,
                    socfile="/opt/vc/bin/vcgencmd")

    def interval(self):
        return float(self._settings.get(['rate']))

    def on_after_startup(self):
        t = RepeatedTimer(self.interval, self.check_temp)
        t.start()
        self._logger.info("SoCTemp READY")

    def get_template_configs(self):
        return [
            dict(type='navbar', custom_bindings=True),
            dict(type='settings', custom_bindings=False)
        ]

    def set_text_color(self):
        atemp = float(self.temp)
        tsp1 = float(self._settings.get(['tsp1']))
        tsp2 = float(self._settings.get(['tsp2']))
        if tsp1 == 0 or tsp2 == 0:
            self.color = "inherit"
            return
        if atemp < tsp1:
            self.color = "green"
        elif atemp >= tsp1 and atemp < tsp2:
            self.color = "orange"
        elif atemp >= tsp2:
            self.color = "red"

    def check_temp(self):
        self.temp_cmd = '/opt/vc/bin/vcgencmd measure_temp'
        self.parse_pattern = '=(.*)\''
        from sarge import run, Capture
        import os.path
        try:
            soc_file = self._settings.get(["socfile"])
            if os.path.isfile(soc_file):
                p = run(self.temp_cmd, stdout=Capture())
                p = p.stdout.text
                match = re.search(self.parse_pattern, p)
            else:
                self._logger.error("SoCTemp: can't determine the temperature,"
                                   + " are you sure you're using RasPi?")
                return

            self.temp = match.group(1)

            self.set_text_color()
            self._plugin_manager.send_plugin_message(self._identifier,
                                                     dict(soctemp=self.temp,
                                                          emoji=self._settings.get(["emoji"]),
                                                          color=self.color
                                                         )
                                                    )
            self._logger.debug("SoCTemp REFRESH")
        except Exception as e:
            self._logger.warning("SoCTemp REFRESH FAILED: {0}".format(e))

    def get_assets(self):
        return dict(
            js=["js/soctemp.js"]
        )

    def get_update_information(self):
        return dict(
            soctemp=dict(
                displayName="SoCTemp Plugin",
                displayVersion=self._plugin_version,

                type="github_release",
                user="mpaeke",
                repo="OctoPrint-SoCTemp",
                current=self._plugin_version,

                pip="https://github.com/mpaeke/OctoPrint-SoCTemp/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "SoCTemp Plugin"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SoCTempPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config":
            __plugin_implementation__.get_update_information
    }
