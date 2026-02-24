"""Panel des paramètres de l'interface."""

import re

import bpy
from bpy.types import Panel

from ..config import PROPERTY_BONE, RIG_ID, RIG_NAME
from ..utils import get_active_rig, is_valid_rig


class RIGUI_PT_settings(Panel):
    """Panel de configuration : initialisation et paramètres du rig."""

    bl_idname = "RIGUI_PT_settings"
    bl_label = "Rig UI Settings"
    bl_category = "DRigUI"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        if is_valid_rig(context.active_object):
            rig = get_active_rig(context)
            info = col.column(align=True)
            info.scale_y = 0.8
            info.separator(type="LINE")
            info.label(text=f"Name : {rig.data[RIG_NAME]}")
            info.label(text=f"ID   : {rig.data[RIG_ID]}")
            info.prop(context.active_object.data, f'["{PROPERTY_BONE}"]', text="Prop bone")

            col.separator(factor=1.5)

            # Sélecteur de text block + bouton apply
            ik_col = col.column(align=True)
            ik_col.label(text="Apply IK/FK chains from JSON Text Block")
            ik_row = ik_col.row(align=True)
            ik_row.prop_search(
                data=context.scene,
                property="input_name",  # réutilise input_name comme champ temporaire
                search_data=bpy.data,
                search_property="texts",
                text="",
                icon="TEXT",
            )
            op = ik_row.operator("rigui.apply_ik_chains", text="", icon="IMPORT")
            op.text_block = context.scene.input_name

            col.separator(factor=1.5)

            # Bouton suppression
            remove_row = col.row()
            remove_row.alert = True
            remove_row.operator(
                "rigui.delete",
                text="Remove this Dynamic RigUI",
                icon="TRASH",
            )

            tools_col = col.column()
            self._draw_setup_section(context, tools_col, rig)

        else:
            col.prop(
                context.scene,
                "input_name",
                text="",
                placeholder="Rig ID Name",
                expand=True,
            )
            name = context.scene.input_name
            warnings = self._check_name(context, name)

            btn = col.row()
            btn.enabled = warnings == ""
            btn.operator(
                "rigui.new",
                emboss=True,
                text="New",
                icon="ADD",
            ).rig_name = str(name)

            if warnings:
                w = col.row()
                w.alert = True
                w.label(text=warnings, icon="CANCEL")

    def _check_name(self, context, name) -> str:
        if context.active_object.type != "ARMATURE":
            return "Select your Armature rig Object"
        if name == "":
            return "Name can't be empty"
        if len(name) < 3:
            return "Name should have more than 3 characters"
        if not re.fullmatch(r"^[A-Z0-9_]+$", name):
            return "Name should have only uppercase letters, digits or _"
        return ""

    # -------------------------------------------------------------------------
    # SETUP TOOLS
    # -------------------------------------------------------------------------

    def _draw_setup_section(self, context, layout, armature):
        """Section outils de setup (masks, collections, custom shapes)."""
        layout.separator(factor=3, type="SPACE")
        layout.separator(factor=1, type="LINE")
        box = layout.column()
        header = box.row()
        header.alignment = "LEFT"
        header.label(text="SETUP TOOLS", icon="MODIFIER")

        col = box.column(align=True)

        # --- Masks ---
        mask_row = col.row(align=True)
        mask_row.operator(
            "rigui.create_masks",
            text="Create Mask Modifiers",
            icon="MOD_MASK",
        )

        col.separator(factor=0.4)

        # --- Collections ---
        sym_row = col.row(align=True)
        sym_row.enabled = context.active_object.type == "ARMATURE"
        sym_row.operator(
            "rigui.symmetrize_collections",
            text="Symmetrize Collections",
            icon="MOD_MIRROR",
        )

        col.separator(factor=0.4)

        # --- Custom shape ---
        shape_row = col.row(align=True)
        shape_row.enabled = context.mode == "POSE"
        shape_row.operator(
            "rigui.create_custom_shape",
            text="Create Custom Shape",
            icon="MESH_MONKEY",
        )
        hint = col.row()
        hint.active = False
        hint.label(text="Select 2 bones for override transform", icon="INFO")


# Classes à enregistrer
classes = (RIGUI_PT_settings,)
