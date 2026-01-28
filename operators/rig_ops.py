"""Opérateurs pour l'ajout ou l'édition de dynamic rigui"""

import random
import string

from bpy.props import StringProperty
from bpy.types import Operator

from ..config import ACTIVE, PROPERTY_BONE, RIG_ID, RIG_NAME


class RIGUI_OT_new(Operator):
    """Recharge l'UI avec l'ordre des panels choisi."""

    bl_idname = "rigui.new"
    bl_label = "Add new rigui"
    bl_description = "Reload UI with chosen panels order"
    bl_options = {"UNDO", "INTERNAL"}

    rig_name: StringProperty(name="Rig name")

    def execute(self, context):
        obj = context.active_object

        obj.data[ACTIVE] = True
        obj.data[RIG_NAME] = self.rig_name

        random_id = "".join(random.choices(string.ascii_letters, k=12))
        obj.data[RIG_ID] = random_id
        obj.data[PROPERTY_BONE] = "PROPERTIES"

        return {"FINISHED"}


# Classes à enregistrer
classes = (RIGUI_OT_new,)
