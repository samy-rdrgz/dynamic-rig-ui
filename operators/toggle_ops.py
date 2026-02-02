"""Opérateurs pour toggle la visibilité des éléments."""

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator

from ..config import RIG_ID
from ..core import get_collections_by_part
from ..utils import (
    get_active_rig,
    get_box_state,
    get_rig_data,
)


class RIGUI_OT_toggle_boxes(Operator):
    """Toggle toutes les boxes avec un certain préfixe."""

    bl_idname = "rigui.toggle_boxes"
    bl_label = "Toggle All Boxes"
    bl_description = "Toggle all boxes expanded/collapsed state"
    bl_options = {"INTERNAL"}

    prefix: StringProperty()  # ex: "ui_ctrl_" ou "ui_prop_"
    parts: StringProperty()

    def execute(self, context):
        rig_id = str(get_rig_data(context, RIG_ID))
        scene = context.scene
        parts = self.parts.split(",")
        # Trouve toutes les boxes avec ce préfixe
        matching_boxes = [get_box_state(scene, rig_id, self.prefix + i) for i in parts]

        # Détermine l'état cible
        expand = not any(box.expanded for box in matching_boxes)

        for box in matching_boxes:
            box.expanded = expand

        return {"FINISHED"}


class RIGUI_OT_toggle_masks(Operator):
    """Toggle la visibilité des modifiers mask."""

    bl_idname = "rigui.toggle_masks"
    bl_label = "Toggle Masks"
    bl_description = "Toggle visibility of several mask modifiers"
    bl_options = {"UNDO", "INTERNAL"}

    param: StringProperty(name="Mask vertex group name")

    def execute(self, context):
        armature = get_active_rig(context)
        if armature is None:
            return {"CANCELLED"}

        # Collecte tous les modifiers MASK des enfants
        mask_modifiers = []
        for child in armature.children:
            for modifier in child.modifiers:
                if modifier.type == "MASK":
                    mask_modifiers.append(modifier)

        # Filtre selon le paramètre
        if self.param == "all":
            filtered = [m for m in mask_modifiers if m.vertex_group.startswith("MASK_")]
        else:
            filtered = [m for m in mask_modifiers if m.vertex_group == self.param]

        if not filtered:
            return {"CANCELLED"}

        # Détermine l'état cible
        all_visible = all(m.show_viewport for m in filtered)
        target_state = not all_visible

        for modifier in filtered:
            modifier.show_viewport = target_state

        return {"FINISHED"}


class RIGUI_OT_ctrl_box_actions(Operator):
    """Action sur toutes les collections d'une part."""

    bl_idname = "rigui.ctrl_box_actions"
    bl_label = "Action on Part"
    bl_options = {"UNDO", "INTERNAL"}

    prefix: StringProperty(default="ui_ctrl_")
    parts: StringProperty()  # "ARM","LEG", etc.

    is_ctrl_hold: BoolProperty(default=False)
    is_shift_hold: BoolProperty(default=False)
    is_alt_hold: BoolProperty(default=False)

    def invoke(self, context, event):
        self.is_ctrl_hold = event.ctrl
        self.is_shift_hold = event.shift
        self.is_alt_hold = event.alt

        return self.execute(context)

    def execute(self, context):
        armature = get_active_rig(context)
        if self.is_shift_hold:
            bpy.ops.rigui.toggle_boxes(prefix=self.prefix, parts=self.parts)
            return {"FINISHED"}

        attr = "is_solo" if self.is_ctrl_hold else "is_visible"

        collections = get_collections_by_part(armature, self.parts)
        collections = [armature.data.collections[c.name] for c in collections if c.name]
        visible = not any(getattr(c, attr) for c in collections)

        visible = not any(getattr(c, attr) for c in collections)

        for c in collections:
            setattr(c, attr, visible)

        return {"FINISHED"}
