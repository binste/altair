"""Utilities for registering and working with themes"""

from .plugin_registry import PluginRegistry, PluginEnabler
from typing import Callable

ThemeType = Callable[..., dict]


class ThemeRegistry(PluginRegistry[ThemeType]):
    # The name could be update / edit / modify
    # TODO how to make a useful docstring listing all params?
    # docs mention that **config can be passed
    # does this need to accept the **options kwds?? then we can't use **kwds which is convenient here, maybe optins_dict?
    # also add scaling of all graphical elements?
    # Could fonts be partial points? Otherwise always round down?
    # if this is added in VL in the future, we can likely keep this interface the same, forward compatible
    def modify(self, font_scale=None, **config):
        if font_scale is not None:
            config = self._scale_font()

        # Register the modified theme under a new name
        if self.active.split("_")[-1] == "modified":
            updated_theme_name = self.active
        else:
            updated_theme_name = "{}_modified".format(self.active)
        self.register(updated_theme_name, lambda: {"config": config})

        # Enable the newly registered theme
        return PluginEnabler(self, updated_theme_name)

    def _scale_font(self, config):
        # scale font and append to dict
        # I think all font options are defined here https://github.com/vega/vega/blob/main/packages/vega-parser/src/config.js#L82-L129=
        return config
