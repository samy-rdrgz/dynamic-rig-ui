"""Panels de l'addon Rig UI."""

from .main_panel import RIGUI_PT_main
from .masks_panel import RIGUI_PT_masks
from .props_panel import RIGUI_PT_customprops
from .rigui_panel import RIGUI_PT_rigui
from .settings_panel import RIGUI_PT_settings
from .tools_panel import RIGUI_PT_tools

# Classes à enregistrer (ordre important : parent avant enfants)
classes = (
    RIGUI_PT_main,
    RIGUI_PT_rigui,
    RIGUI_PT_customprops,
    RIGUI_PT_masks,
    RIGUI_PT_tools,
    RIGUI_PT_settings,
)

__all__ = [
    "RIGUI_PT_main",
    "RIGUI_PT_rigui",
    "RIGUI_PT_customprops",
    "RIGUI_PT_masks",
    "RIGUI_PT_tools",
    "RIGUI_PT_settings",
    "classes",
]
