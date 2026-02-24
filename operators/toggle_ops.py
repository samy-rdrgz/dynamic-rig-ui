"""Opérateurs pour toggle la visibilité des collections et des masks."""

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
    """Toggle l'état expanded/collapsed de boxes avec un préfixe donné."""

    bl_idname = "rigui.toggle_boxes"
    bl_label = "Toggle All Boxes"
    bl_description = "Toggle all boxes expanded/collapsed state"
    bl_options = {"INTERNAL"}

    prefix: StringProperty()  # ex: "ui_ctrl_" ou "ui_prop_"
    parts: StringProperty()  # ex: "ARM,LEG"

    def execute(self, context):
        rig_id = str(get_rig_data(context, RIG_ID))
        scene = context.scene
        parts = self.parts.split(",")

        matching_boxes = [get_box_state(scene, rig_id, self.prefix + part) for part in parts]

        # Si au moins une box est ouverte → tout fermer, sinon tout ouvrir
        expand = not any(box.expanded for box in matching_boxes)

        for box in matching_boxes:
            box.expanded = expand

        return {"FINISHED"}


class RIGUI_OT_toggle_masks(Operator):
    """Toggle la visibilité des modifiers MASK des meshes enfants."""

    bl_idname = "rigui.toggle_masks"
    bl_label = "Toggle Masks"
    bl_description = "Toggle visibility of mask modifiers"
    bl_options = {"UNDO", "INTERNAL"}

    param: StringProperty(name="Vertex group name (or 'all')")

    def execute(self, context):
        armature = get_active_rig(context)
        if armature is None:
            return {"CANCELLED"}

        mask_modifiers = [
            modifier
            for child in armature.children
            for modifier in child.modifiers
            if modifier.type == "MASK"
        ]

        if self.param == "all":
            filtered = [m for m in mask_modifiers if m.vertex_group.startswith("MASK_")]
        else:
            filtered = [m for m in mask_modifiers if m.vertex_group == self.param]

        if not filtered:
            return {"CANCELLED"}

        target_state = not all(m.show_viewport for m in filtered)

        for modifier in filtered:
            modifier.show_viewport = target_state

        return {"FINISHED"}


class RIGUI_OT_ctrl_box_actions(Operator):
    """Action sur toutes les collections d'une part (visibilité / solo / toggle boxes)."""

    bl_idname = "rigui.ctrl_box_actions"
    bl_label = "Action on Part"
    bl_options = {"UNDO", "INTERNAL"}

    prefix: StringProperty(default="ui_ctrl_")
    parts: StringProperty()  # "ARM", "ARM,LEG", etc.

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

        # Shift : toggle expanded/collapsed des boxes
        if self.is_shift_hold:
            bpy.ops.rigui.toggle_boxes(prefix=self.prefix, parts=self.parts)
            return {"FINISHED"}

        # Ctrl : solo  /  clic normal : visibilité
        attr = "is_solo" if self.is_ctrl_hold else "is_visible"

        collections = get_collections_by_part(armature, self.parts)
        collections = [armature.data.collections[c.name] for c in collections if c.name]

        visible = not any(getattr(c, attr) for c in collections)

        for c in collections:
            setattr(c, attr, visible)

        return {"FINISHED"}
