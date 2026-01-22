"""Panel principal de l'addon Rig UI."""

import bpy
from bpy.types import Panel

from ..config import RIG_ID, RIG_NAME
from ..utils import get_active_rig, is_valid_rig


class RIGUI_PT_main(Panel):
    """Panel principal contenant tous les sous-panels."""

    bl_idname = f"{RIG_NAME.lower()}_PT_main"
    bl_label = "Rig UI"
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        armature = get_active_rig(context)
        return is_valid_rig(armature)

    def draw(self, context):
        # Panel vide, sert juste de conteneur
        layout = self.layout


# Classes à enregistrer
classes = (RIGUI_PT_main,)
