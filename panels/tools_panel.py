"""Panel des outils d'animation."""

from bpy.types import Panel

from ..config import RIG_NAME
from ..utils import get_active_rig, is_valid_rig


class RIGUI_PT_tools(Panel):
    """Panel avec les outils de snap IK/FK."""

    bl_idname = f"{RIG_NAME.lower()}_PT_tools"
    bl_label = "Snap Utilities"
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = f"{RIG_NAME.lower()}_PT_main"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        armature = get_active_rig(context)
        if armature is None:
            return False
        if context.active_object.type != "ARMATURE":
            return False
        if context.object.mode != "POSE":
            return False
        return is_valid_rig(armature)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        box = col.box()

        # Titre
        titre = box.column()
        titre.separator(factor=4)
        titre.scale_y = 0.25
        titre.alert = True
        titre_row = titre.row()
        titre_row.alignment = "CENTER"
        titre_row.label(text="LIMB KINEMATIC")

        # Bouton snap
        row = box.row()
        row.alignment = "EXPAND"
        row.enabled = context.mode == "POSE"
        row.operator(
            f"{RIG_NAME.lower()}.snap_opposite_kinematic",
            emboss=True,
            text="SNAP",
            icon="SNAP_ON",
        )

        col.separator(factor=0.5, type="SPACE")


# Classes à enregistrer
classes = (RIGUI_PT_tools,)
