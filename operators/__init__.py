"""Opérateurs de l'addon Rig UI."""

from .snap_ops import RIGUI_OT_snap_kinematic
from .toggle_ops import (
    RIGUI_OT_toggle_all_boxes,
    RIGUI_OT_toggle_box,
    RIGUI_OT_toggle_controllers,
    RIGUI_OT_toggle_masks,
)
from .ui_ops import RIGUI_OT_reload_ui, WM_OT_text_popup

# Toutes les classes à enregistrer
classes = (
    WM_OT_text_popup,
    RIGUI_OT_toggle_controllers,
    RIGUI_OT_toggle_box,
    RIGUI_OT_toggle_all_boxes,
    RIGUI_OT_toggle_masks,
    RIGUI_OT_snap_kinematic,
    RIGUI_OT_reload_ui,
)

__all__ = [
    "RIGUI_OT_snap_kinematic",
    "RIGUI_OT_toggle_controllers",
    "RIGUI_OT_toggle_box",
    "RIGUI_OT_toggle_all_boxes",
    "RIGUI_OT_toggle_masks",
    "RIGUI_OT_reload_ui",
    "WM_OT_text_popup",
    "classes",
]
