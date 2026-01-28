"""Panel pour les propriétés custom du rig."""

import re

from bpy.types import Panel

from ..config import NO_BODY_PREFIX, PROPERTY_BONE, RIG_ID, UI_RATIO_PROPS
from ..core import get_rig_cache
from ..utils import (
    any_box_expanded,
    get_active_rig,
    get_box_expanded,
    get_rig_data,
    is_valid_rig,
)


class RIGUI_PT_customprops(Panel):
    """Panel affichant les propriétés custom organisées par catégorie."""

    bl_idname = "RIGUI_PT_customprops"
    bl_label = "Dynamic RigUI - Properties"
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
        if context.object.mode != "POSE":
            return False
        return is_valid_rig(armature)

    def draw(self, context):
        armature = get_active_rig(context)
        rig_id = str(get_rig_data(context, RIG_ID))
        property_bone_name = get_rig_data(context, PROPERTY_BONE)
        layout = self.layout
        panel = layout.column()
        try:
            property_bone = armature.pose.bones[property_bone_name]
        except (AttributeError, KeyError, TypeError):
            property_bone = None
        if not property_bone:
            panel.alert = True
            panel.label(text="Your property posebone is not existing", icon="ERROR")
            panel.prop(
                context.active_object.data, f'["{PROPERTY_BONE}"]', text="Prop bone"
            )
            return None
        cache = get_rig_cache(armature)

        # Récupère et trie les propriétés
        props_data = self._get_sorted_properties(property_bone)

        # Header
        self._draw_header(context, panel, armature, rig_id, props_data)
        panel.separator(type="LINE", factor=0.2)

        # Contenu
        self._draw_properties(context, panel, armature, property_bone, props_data)

    def _get_sorted_properties(self, bone):
        """Récupère les propriétés triées par ordre de priorité."""
        custom_props = sorted(bone.keys(), key=str.lower)

        # Ordre de priorité
        priority_order = [
            "ROOT",
            "HEAD",
            "NECK",
            "BODY",
            "SPINE",
            "CHEST",
            "ARM",
            "HAND",
            "LEG",
            "FOOT",
        ] + NO_BODY_PREFIX

        ordered = []
        remaining = list(custom_props)

        for prefix in priority_order:
            for prop in list(remaining):
                if str(prop).startswith(prefix):
                    ordered.append(prop)
                    remaining.remove(prop)

        all_props = ordered + remaining

        # Parse les propriétés
        props_str = "\n" + "\n".join(all_props)
        pattern = re.compile(r"^([A-Z]+)_([A-Z0-9_]+)(.([LMR]|(\d)))?$", re.MULTILINE)

        props_data = []
        for match in pattern.finditer(props_str):
            props_data.append(
                {
                    "name": match.group(0),
                    "part": match.group(1),
                    "sub_part": match.group(2),
                    "side": match.group(4),
                }
            )

        return props_data

    def _draw_header(self, context, panel, armature, rig_id, props_data):
        """Dessine l'en-tête du panel."""
        bloc = panel.row()

        row = bloc.split(align=True, factor=UI_RATIO_PROPS)
        row1 = row.row()
        row1.alignment = "LEFT"

        parts = set()
        for d in props_data:
            if d["part"] not in parts:
                parts.add(d["part"])

        icon = (
            "DOWNARROW_HLT"
            if any_box_expanded(context.scene, rig_id, "ui_ctrl_", read_only=True)
            else "RIGHTARROW"
        )

        op = row1.operator(
            "rigui.toggle_boxes",
            emboss=False,
            text="",
            icon=icon,
        )
        op.prefix = "ui_prop_"
        op.parts = ",".join(parts)

        row1.alert = True
        row1.label(text="PROPERTIES")

        # Labels de colonnes
        row2 = row.row()
        row2.active = False
        row2.label(text="LEFT")
        row2.label(text="RIGHT")

    def _draw_properties(self, context, panel, armature, bone, props_data):
        """Dessine les propriétés groupées."""
        current_part = None
        bloc = None
        b_row = None

        # Récupère la liste des noms pour vérifier les côtés
        prop_names = [p["name"] for p in props_data]
        rig_id = str(get_rig_data(context, RIG_ID))
        for data in props_data:
            prop_name = data["name"]
            part = data["part"]
            sub_part = data["sub_part"]
            side = data["side"]

            # Nouveau groupe ?
            if current_part != part:
                panel.separator(factor=1, type="SPACE")
                bloc = panel.row().column(align=True)

                # Titre du groupe
                titre = bloc.row()
                titre.scale_y = 0.6
                titre.alignment = "LEFT"

                expanded = get_box_expanded(context.scene, rig_id, f"ui_prop_{part}")
                icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"

                op = titre.operator(
                    "rigui.toggle_boxes",
                    emboss=False,
                    text=part,
                    icon=icon,
                )
                op.prefix = "ui_prop_"
                op.parts = part

                current_part = part
                if expanded:
                    bloc.separator(factor=1)
                    p_bloc = bloc.column()
                    bloc.separator(factor=2)

            # Contenu (si expanded)
            if not get_box_expanded(context.scene, rig_id, f"ui_prop_{part}"):
                continue

            # Détermine la colonne et l'espace vide
            num_col, empty_space = self._get_column_info(prop_name, side, prop_names)

            if num_col == 0 or side is None:
                b_row = p_bloc.row(align=True)
                split = b_row.split(align=True, factor=UI_RATIO_PROPS)
                split.alignment = "RIGHT"
                split.label(text=sub_part)
                b_row = split.row(align=True)

                if empty_space == -1:
                    b_row.label(text="")

                b_row.prop(bone, f'["{prop_name}"]', text="", slider=True)

                if empty_space == 1:
                    b_row.label(text="")

            elif num_col > 0:
                b_row.prop(bone, f'["{prop_name}"]', text="", slider=True)

    def _get_column_info(self, prop_name, side, prop_names):
        """Détermine la colonne et l'espace vide pour une propriété."""
        if side is None:
            return 0, 0

        if side == "L":
            right_name = prop_name.replace(".L", ".R")
            if right_name not in prop_names:
                return 0, 1  # Espace à droite
            return 0, 0

        if side == "R":
            left_name = prop_name.replace(".R", ".L")
            if left_name not in prop_names:
                return 0, -1  # Espace à gauche
            return 1, 0

        if side.isdigit():
            return int(side), 0

        return 0, 0


# Classes à enregistrer
classes = (RIGUI_PT_customprops,)
