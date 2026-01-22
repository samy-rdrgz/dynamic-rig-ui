"""Panel pour les propriétés custom du rig."""

import re

from bpy.types import Panel

from ..config import NO_BODY_PREFIX, RIG_NAME, UI_RATIO_PROPS
from ..utils import get_active_rig, is_valid_rig


class RIGUI_PT_customprops(Panel):
    """Panel affichant les propriétés custom organisées par catégorie."""

    bl_idname = "RIGUI_PT_customprops"
    bl_label = "Properties"
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "RIGUI_PT_main"
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
        armature = get_active_rig(context)
        bone = armature.pose.bones["PROPERTIES"]

        # Récupère et trie les propriétés
        props_data = self._get_sorted_properties(bone)

        layout = self.layout
        panel = layout.box().column()

        # Header
        self._draw_header(panel, armature)

        # Contenu
        self._draw_properties(panel, armature, bone, props_data)

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

    def _draw_header(self, panel, armature):
        """Dessine l'en-tête du panel."""
        bloc = panel.row()
        bloc.active = False

        row = bloc.split(align=True, factor=UI_RATIO_PROPS)
        row1 = row.row()
        row1.alignment = "LEFT"

        # Toggle expand/collapse
        any_expanded = any(
            armature.data[key] for key in armature.data if key.startswith("ui_prop_")
        )
        icon = "DOWNARROW_HLT" if any_expanded else "RIGHTARROW"
        row1.operator(
            f"{RIG_NAME.lower()}.toggle_boxes",
            emboss=False,
            text="",
            icon=icon,
        ).param = "ui_prop_"

        row1.alert = True
        row1.label(text="Properties")

        # Labels de colonnes
        row2 = row.row()
        row2.active = False
        row2.label(text=".Left")
        row2.label(text=".Right")

    def _draw_properties(self, panel, armature, bone, props_data):
        """Dessine les propriétés groupées."""
        current_part = None
        bloc = None
        b_row = None

        # Récupère la liste des noms pour vérifier les côtés
        prop_names = [p["name"] for p in props_data]

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
                titre.alignment = "EXPAND"

                expanded = armature.data.get(f"ui_prop_{part}", False)
                icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"
                titre.prop(
                    armature.data,
                    f'["ui_prop_{part}"]',
                    emboss=False,
                    text=part,
                    icon=icon,
                )

                current_part = part
                if expanded:
                    bloc.separator(factor=0.4)

            # Contenu (si expanded)
            if not armature.data.get(f"ui_prop_{part}", False):
                continue

            # Détermine la colonne et l'espace vide
            num_col, empty_space = self._get_column_info(prop_name, side, prop_names)

            if num_col == 0 or side is None:
                bloc.separator(factor=0.25)
                b_row = bloc.row(align=True)
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
