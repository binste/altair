"""Utilities for registering and working with themes"""

from .plugin_registry import PluginRegistry, PluginEnabler
from typing import Callable

ThemeType = Callable[..., dict]


class ThemeRegistry(PluginRegistry[ThemeType]):
    # TODO how to make a useful docstring listing all params?
    # Could fonts be partial points? Otherwise always round down?
    def modify(self, font_scale=None):
        current_state = self._get_state()
        config = {**current_state["_options"], **current_state["_global_settings"]}
        
        if font_scale is not None:
            config = self._scale_font(config)

        # Register the modified theme under a new name
        if self.active.split("_")[-1] == "modified":
            updated_theme_name = self.active
        else:
            updated_theme_name = f"{self.active}_modified"
        self.register(updated_theme_name, lambda: {"config": config})

        # Enable the newly registered theme
        return PluginEnabler(self, updated_theme_name)

    def _scale_font(self, config):
        # scale font and append to dict
        # I think all font options are defined here https://github.com/vega/vega/blob/main/packages/vega-parser/src/config.js#L82-L129=
        return config
