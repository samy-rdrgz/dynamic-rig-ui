"""Panel pour les propriétés custom du rig."""

import re

from bpy.types import Panel

from ..config import NO_BODY_PREFIX, UI_RATIO_PROPS
from ..utils import get_active_rig, get_box_expanded, get_rig_data, is_valid_rig


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
        b_name = get_rig_data(context, "prop_posebone_name")
        layout = self.layout
        panel = layout.column()
        try:
            bone = armature.pose.bones[b_name]
        except (AttributeError, KeyError, TypeError):
            bone = None
        if not bone:
            panel.alert = True
            panel.label(text="Your property posebone is not existing", icon="ERROR")
            panel.prop(context.active_object.data, '["prop_posebone_name"]', text="Prop bone")

        else:
            # Récupère et trie les propriétés
            props_data = self._get_sorted_properties(bone)

            # Header
            self._draw_header(context, panel, armature)
            panel.separator(type="LINE", factor=0.2)

            # Contenu
            self._draw_properties(context, panel, armature, bone, props_data)

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

    def _draw_header(self, context, panel, armature):
        """Dessine l'en-tête du panel."""
        bloc = panel.row()

        row = bloc.split(align=True, factor=UI_RATIO_PROPS)
        row1 = row.row()
        row1.alignment = "LEFT"

        # Toggle expand/collapse
        for rig_state in context.scene.rigui_states:
            if rig_state.rig_id == get_rig_data(context, "rig_id"):
                rig = rig_state
                break
        if rig:
            any_expanded = any([b.expanded for b in rig.boxes if b.name.startswith("ui_ctrl_")])
        else:
            any_expanded = True
        icon = "DOWNARROW_HLT" if any_expanded else "RIGHTARROW"
        row1.operator(
            f"{str(get_rig_data(context, 'rig_name')).lower()}.toggle_boxes",
            emboss=False,
            text="",
            icon=icon,
        )

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

                expanded = get_box_expanded(
                    context.scene, get_rig_data(context, "rig_id"), f"ui_prop_{part}"
                )
                icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"
                rig_id = get_rig_data(context, "rig_id")
                op = titre.operator(
                    "rigui.toggle_box",
                    emboss=False,
                    text=part,
                    icon=icon,
                )
                op.rig_id = rig_id
                op.box_name = f"ui_prop_{part}"

                current_part = part
                if expanded:
                    bloc.separator(factor=1)
                    p_bloc = bloc.column()
                    bloc.separator(factor=2)

            # Contenu (si expanded)
            if not get_box_expanded(
                context.scene, get_rig_data(context, "rig_id"), f"ui_prop_{part}"
            ):
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
