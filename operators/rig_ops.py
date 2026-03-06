"""Opérateurs pour l'ajout et la suppression de Dynamic RigUI sur une armature."""

import random
import string

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..config import ACTIVE, IK_CHAINS, PROPERTY_BONE, RIG_ID, RIG_NAME
from ..core import _cache


class RIGUI_OT_new(Operator):
    """Initializes Dynamic RigUI on the active armature."""

    bl_idname = "rigui.new"
    bl_label = "Add Dynamic RigUI"
    bl_description = "Initialize Dynamic RigUI on the active armature"
    bl_options = {"UNDO", "INTERNAL"}

    rig_name: StringProperty(name="Rig name")

    def execute(self, context):
        obj = context.active_object

        # Génère un ID unique, vérifie les collisions avec les armatures existantes
        existing_ids = {
            arm.get(RIG_ID) for arm in bpy.data.armatures if arm.get(RIG_ID)
        }
        while True:
            random_id = "".join(random.choices(string.ascii_letters, k=12))
            if random_id not in existing_ids:
                break

        obj.data[ACTIVE] = True
        obj.data[RIG_NAME] = self.rig_name
        obj.data[RIG_ID] = random_id
        obj.data[PROPERTY_BONE] = "PROPERTIES"

        return {"FINISHED"}


class RIGUI_OT_delete(Operator):
    """Removes Dynamic RigUI from the active armature."""

    bl_idname = "rigui.delete"
    bl_label = "Remove Dynamic RigUI"
    bl_description = "Remove Dynamic RigUI data from the active armature"
    bl_options = {"UNDO", "INTERNAL"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        obj = context.active_object
        rig_id = obj.data.get(RIG_ID)

        # Nettoie le cache global
        if rig_id and rig_id in _cache:
            del _cache[rig_id]

        # Supprime les custom props Dynamic RigUI
        for key in (ACTIVE, RIG_NAME, RIG_ID, PROPERTY_BONE, IK_CHAINS):
            if key in obj.data:
                del obj.data[key]

        return {"FINISHED"}


# Classes à enregistrer
classes = (RIGUI_OT_new, RIGUI_OT_delete)
