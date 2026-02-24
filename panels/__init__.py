"""Panels de l'addon Dynamic Rig UI."""

from .masks_panel import RIGUI_PT_masks
from .props_panel import RIGUI_PT_customprops
from .rigui_panel import RIGUI_PT_rigui
from .settings_panel import RIGUI_PT_settings
from .tools_panel import RIGUI_PT_tools

# Ordre d'enregistrement : pas de parent/enfant ici, mais settings en dernier
classes = (
    RIGUI_PT_rigui,
    RIGUI_PT_customprops,
    RIGUI_PT_masks,
    RIGUI_PT_tools,
    RIGUI_PT_settings,
)

__all__ = ["classes"]
