"""Opérateurs pour toggle la visibilité des éléments."""

import json

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator

from ..utils import (
    get_active_rig,
    get_box_state,
)


class RIGUI_OT_toggle_controllers(Operator):
    """Toggle la visibilité de plusieurs bone collections."""

    bl_idname = "rigui.toggle_controllers"
    bl_label = "Toggle Controllers"
    bl_description = "Toggle visibility of several bone collections"
    bl_options = {"UNDO", "INTERNAL"}

    parts: StringProperty(name="Prefix to toggle")
    toggle_solo: BoolProperty(default=False)
    is_shift_hold: BoolProperty(default=False)
    is_alt_hold: BoolProperty(default=False)

    def invoke(self, context, event):
        self.toggle_solo = False
        if event.ctrl == True:
            self.toggle_solo = True

        return self.execute(context)

    def execute(self, context):
        armature = get_active_rig(context)
        if armature is None:
            return {"CANCELLED"}

        data = json.loads(self.parts)
        collections = [
            bpy.data.armatures[d["armature"]].collections_all[d["collection"]] for d in data
        ]
        attr = "is_solo" if self.toggle_solo else "is_visible"
        visible = not any(getattr(c, attr) for c in collections)

        for c in collections:
            setattr(c, attr, visible)

        return {"FINISHED"}


class RIGUI_OT_toggle_box(Operator):
    """Toggle l'état expanded/collapsed d'une box."""

    bl_idname = "rigui.toggle_box"
    bl_label = "Toggle Box"
    bl_description = "Toggle box expanded/collapsed state"
    bl_options = {"INTERNAL"}  # Pas d'UNDO pour l'UI

    rig_id: StringProperty()
    box_name: StringProperty()

    def execute(self, context):
        scene = context.scene

        # Trouve ou crée le rig state
        rig_state = None
        for state in scene.rigui_states:
            if state.rig_id == self.rig_id:
                rig_state = state
                break

        if rig_state is None:
            rig_state = scene.rigui_states.add()
            rig_state.rig_id = self.rig_id

        # Trouve ou crée la box
        box_state = None
        for box in rig_state.boxes:
            if box.name == self.box_name:
                box_state = box
                break

        if box_state is None:
            box_state = rig_state.boxes.add()
            box_state.name = self.box_name
            box_state.expanded = True

        # Toggle !
        box_state.expanded = not box_state.expanded

        return {"FINISHED"}


class RIGUI_OT_toggle_all_boxes(Operator):
    """Toggle toutes les boxes avec un certain préfixe."""

    bl_idname = "rigui.toggle_all_boxes"
    bl_label = "Toggle All Boxes"
    bl_description = "Toggle all boxes expanded/collapsed state"
    bl_options = {"INTERNAL"}

    rig_id: StringProperty()
    prefix: StringProperty()  # ex: "ui_ctrl_" ou "ui_prop_"
    parts: StringProperty()

    def execute(self, context):
        scene = context.scene
        parts = self.parts.split(",")
        # Trouve toutes les boxes avec ce préfixe
        matching_boxes = [get_box_state(scene, self.rig_id, self.prefix + i) for i in parts]
        if not matching_boxes:
            return {"CANCELLED"}

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


# Classes à enregistrer
classes = (
    RIGUI_OT_toggle_controllers,
    RIGUI_OT_toggle_box,
    RIGUI_OT_toggle_all_boxes,
    RIGUI_OT_toggle_masks,
)
