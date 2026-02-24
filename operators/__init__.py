"""Opérateurs de l'addon Dynamic Rig UI."""

from .rig_ops import RIGUI_OT_delete, RIGUI_OT_new
from .rigging_ops import (
    RIGUI_OT_create_custom_shape,
    RIGUI_OT_create_masks,
    RIGUI_OT_symmetrize_collections,
)
from .snap_ops import RIGUI_OT_apply_ik_chains, RIGUI_OT_snap_kinematic
from .toggle_ops import (
    RIGUI_OT_ctrl_box_actions,
    RIGUI_OT_toggle_boxes,
    RIGUI_OT_toggle_masks,
)
from .ui_ops import (
    RIGUI_OT_enum_popup,
    RIGUI_OT_set_int_prop,
    WM_OT_text_popup,
)

# Ordre d'enregistrement : WM en premier (utilisé par les autres via bpy.ops.wm.text_popup)
classes = (
    WM_OT_text_popup,
    RIGUI_OT_toggle_boxes,
    RIGUI_OT_toggle_masks,
    RIGUI_OT_ctrl_box_actions,
    RIGUI_OT_snap_kinematic,
    RIGUI_OT_apply_ik_chains,
    RIGUI_OT_set_int_prop,
    RIGUI_OT_enum_popup,
    RIGUI_OT_new,
    RIGUI_OT_delete,
    RIGUI_OT_create_masks,
    RIGUI_OT_symmetrize_collections,
    RIGUI_OT_create_custom_shape,
)

__all__ = ["classes"]
