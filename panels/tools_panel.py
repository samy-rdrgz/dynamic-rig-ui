"""Panel des outils d'animation et de setup du rig."""

import json

from bpy.types import Panel

from ..config import IK_CHAINS
from ..utils import get_active_rig, is_valid_rig


class RIGUI_PT_tools(Panel):
    """Panel rassemblant les outils d'animation et de setup."""

    bl_idname = "RIGUI_PT_tools"
    bl_label = "DRIGUI - TOOLS"
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        armature = get_active_rig(context)
        if armature is None:
            return False
        if context.active_object.type != "ARMATURE":
            return False
        return is_valid_rig(armature)

    def draw(self, context):
        layout = self.layout
        armature = get_active_rig(context)

        col = layout.column(align=True)

        # Snap IK/FK
        snap_row = col.row(align=True)
        snap_row.enabled = context.mode == "POSE"
        snap_row.scale_y = 1.4
        snap_row.operator(
            "rigui.snap_opposite_kinematic",
            text="SNAP IK / FK",
            icon="SNAP_ON",
        )

        # Aperçu des chaînes configurées
        chains = self._load_chains(armature)
        if chains:
            col.separator(factor=0.3)
            col.scale_y = 0.75
            setup_chains = []
            for limb_name in chains.keys():
                setup_chains.append(limb_name)
            info = col.row()
            info.active = False
            info.label(text=f"work on {', '.join(setup_chains)}", icon="CON_KINEMATIC")
        else:
            col.separator(factor=0.3)
            warning = col.row()
            warning.alert = True
            warning.label(
                text=f'No chains  →  add "{IK_CHAINS}" JSON prop',
                icon="ERROR",
            )

    # -------------------------------------------------------------------------

    @staticmethod
    def _load_chains(armature) -> dict:
        """Lit le JSON des chaînes IK/FK depuis les custom props de l'armature."""
        raw = armature.data.get(IK_CHAINS, "")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}


# Classes à enregistrer
classes = (RIGUI_PT_tools,)
