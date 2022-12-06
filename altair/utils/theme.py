"""Utilities for registering and working with themes"""
from .plugin_registry import PluginRegistry, PluginEnabler
from typing import Callable

ThemeType = Callable[..., dict]


class ThemeRegistry(PluginRegistry[ThemeType]):
    def modify(self, font_scale=None):
        config = self.get()()["config"]

        if font_scale is not None:
            config = self._scale_font(config, font_scale)

        # Register the modified theme under a new name
        if self.active.split("_")[-1] == "modified":
            updated_theme_name = self.active
        else:
            updated_theme_name = f"{self.active}_modified"
        self.register(updated_theme_name, lambda: {"config": config})

        # Enable the newly registered theme
        return PluginEnabler(self, updated_theme_name)

    def _scale_font(self, config, font_scale):
        # TODO: # Could fonts be partial points? Otherwise always round down?
        # scale font and append to dict
        # I think all font options are defined here https://github.com/vega/vega/blob/main/packages/vega-parser/src/config.js#L82-L129=
        defaults = {
            "title": {"fontSize": 13},
            "legend": {"titleFontSize": 11, "labelFontSize": 10},
        }
        # Can exist for both axes or set together
        can_be_duplicated = {"axis": {"titleFontSize": 11, "labelFontSize": 10}}
        # TODO: Update default values above
        # TODO: Facet header titles, subtitles?, etc.
        config = _scale_config_values(config, defaults, font_scale)
        return config


def _scale_config_values(config, defaults, scale_factor):
    for k, v in defaults.items():
        if isinstance(v, dict):
            config[k] = _scale_config_values(config.get(k, {}), v, scale_factor)
        else:
            config[k] = config.get(k, v) * scale_factor
    return config
