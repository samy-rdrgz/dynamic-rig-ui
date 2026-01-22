"""Opérateurs pour toggle la visibilité des éléments."""

import re

from bpy.props import StringProperty
from bpy.types import Operator

from ..config import RIG_NAME
from ..utils import get_active_rig, get_bone_collections_list


class RIGUI_OT_toggle_controllers(Operator):
    """Toggle la visibilité de plusieurs bone collections."""

    bl_idname = f"{RIG_NAME.lower()}.toggle_controllers"
    bl_label = "Toggle Controllers"
    bl_description = "Toggle visibility of several bone collections"
    bl_options = {"UNDO", "INTERNAL"}

    param: StringProperty(name="Prefix to toggle")

    def execute(self, context):
        armature = get_active_rig(context)
        if armature is None:
            return {"CANCELLED"}

        collections_str = get_bone_collections_list(armature)

        # Sélectionne les collections selon le préfixe
        if self.param == "all":
            pattern = r"^([A-Z]+)_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?$"
        else:
            pattern = rf"^({self.param})_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?$"

        regex = re.compile(pattern, re.MULTILINE)
        matches = regex.finditer(collections_str)

        collections = [
            armature.data.collections[match.group(0)]
            for match in matches
            if match.group(0) in armature.data.collections
        ]

        if not collections:
            return {"CANCELLED"}

        # Détermine l'état cible (toggle)
        any_visible = any(col.is_visible for col in collections)
        target_state = not any_visible

        for col in collections:
            col.is_visible = target_state

        return {"FINISHED"}


class RIGUI_OT_toggle_boxes(Operator):
    """Toggle l'état collapsed des boxes de l'UI."""

    bl_idname = f"{RIG_NAME.lower()}.toggle_boxes"
    bl_label = "Toggle Boxes"
    bl_description = "Toggle collapsible state of several boxes"
    bl_options = {"UNDO", "INTERNAL"}

    param: StringProperty(name="Prefix to toggle")

    def execute(self, context):
        armature = get_active_rig(context)
        if armature is None:
            return {"CANCELLED"}

        # Trouve toutes les propriétés qui commencent par le préfixe
        box_keys = [key for key in armature.data if key.startswith(self.param)]

        if not box_keys:
            return {"CANCELLED"}

        # Détermine l'état cible
        any_expanded = any(armature.data[key] for key in box_keys)
        target_state = not any_expanded

        for key in box_keys:
            armature.data[key] = target_state

        return {"FINISHED"}


class RIGUI_OT_toggle_masks(Operator):
    """Toggle la visibilité des modifiers mask."""

    bl_idname = f"{RIG_NAME.lower()}.toggle_masks"
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
    RIGUI_OT_toggle_boxes,
    RIGUI_OT_toggle_masks,
)
