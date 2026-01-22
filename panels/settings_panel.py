"""Panel des paramètres de l'interface."""

import bpy
from bpy.types import Panel

from ..config import RIG_NAME
from ..utils import get_active_rig


class RIGUI_PT_settings(Panel):
    """Panel pour configurer l'ordre des panels."""

    bl_idname = f"{RIG_NAME.lower()}_PT_settings"
    bl_label = "Rig UI Settings"
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    # Note: pas de parent_id, c'est un panel séparé

    @classmethod
    def poll(cls, context):
        armature = get_active_rig(context)
        if armature is None:
            return False
        try:
            return armature.data.get("rig_id") is not None
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout

        # Bouton reload
        row = layout.box().row()
        row.operator(
            f"{RIG_NAME.lower()}.reload_ui",
            emboss=True,
            text="",
            icon="FILE_REFRESH",
        )

        # Sélecteurs d'ordre des panels
        col = layout.column(align=True)
        settings = context.scene.rigui_settings

        col.prop(settings, "p_A")
        col.prop(settings, "p_B")
        col.prop(settings, "p_C")
        col.prop(settings, "p_D")


# Classes à enregistrer
classes = (RIGUI_PT_settings,)
