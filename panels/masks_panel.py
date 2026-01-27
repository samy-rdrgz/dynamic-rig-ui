"""Panel pour la gestion des masks."""

import re

from bpy.types import Panel

from ..config import NO_BODY_PREFIX, PREFIX_ORDER, UI_RATIO
from ..utils import get_active_rig, is_valid_rig


class RIGUI_PT_masks(Panel):
    """Panel pour toggle les modifiers mask des meshes enfants."""

    bl_idname = "RIGUI_PT_masks"
    bl_label = "Dynamic RigUI - Masks"
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        armature = get_active_rig(context)
        return is_valid_rig(armature)

    def draw(self, context):
        armature = get_active_rig(context)
        if armature is None:
            return

        # Collecte les modifiers mask
        masks_data = self._collect_masks(armature)
        if not masks_data:
            return

        layout = self.layout
        col = layout.box().column(align=True)
        col.scale_y = 0.9

        # Header
        self._draw_header(col, masks_data)
        col.separator(type="LINE")

        # Contenu
        self._draw_masks(col, armature, masks_data)

    def _collect_masks(self, armature) -> list[dict]:
        """Collecte et trie tous les modifiers mask."""
        # Récupère tous les modifiers MASK des enfants
        mask_modifiers = []
        for child in armature.children:
            for modifier in child.modifiers:
                if modifier.type == "MASK":
                    mask_modifiers.append(modifier)

        # Trie par nom de vertex group
        mask_modifiers.sort(key=lambda m: m.vertex_group)

        # Applique l'ordre de priorité
        priority = PREFIX_ORDER + NO_BODY_PREFIX
        ordered = []
        remaining = list(mask_modifiers)

        for prefix in priority:
            for mod in list(remaining):
                parts = mod.vertex_group.split("_")
                if len(parts) > 1 and parts[1].startswith(prefix):
                    ordered.append(mod)
                    remaining.remove(mod)

        all_masks = ordered + remaining

        # Parse les données
        pattern = re.compile(r"^(MASK_)([A-Z0-9_]+)(.([LMR]|(\d)))?$", re.MULTILINE)
        masks_data = []

        for modifier in all_masks:
            match = pattern.match(modifier.vertex_group)
            if match:
                masks_data.append(
                    {
                        "modifier": modifier,
                        "vg_name": match.group(0),
                        "part": match.group(2),
                        "side": match.group(4),
                    }
                )

        return masks_data

    def _draw_header(self, col, masks_data):
        """Dessine l'en-tête avec toggle global."""
        row = col.row().split(factor=UI_RATIO)
        row.alignment = "LEFT"
        row.alert = True
        row.label(text="ALL MASKS")
        row.alert = False

        row2 = row.row()
        row2.alignment = "RIGHT"
        row2.separator(factor=1.14)

        # Toggle all
        all_visible = all(
            m["modifier"].show_viewport
            for m in masks_data
            if m["modifier"].vertex_group.startswith("MASK_")
        )
        row2.operator(
            "rigui.toggle_masks",
            emboss=False,
            text="",
            icon="HIDE_ON" if all_visible else "HIDE_OFF",
        ).param = "all"

        row2.separator(factor=1.14)

    def _draw_masks(self, col, armature, masks_data):
        """Dessine les toggles de masks."""
        # Compte les occurrences de chaque vertex group
        vg_counts = {}
        vg_names = [m["vg_name"] for m in masks_data]
        for name in vg_names:
            vg_counts[name] = vg_names.count(name)

        # Track pour la ligne de séparation
        drew_separator = False
        processed_vgs = set()

        for data in masks_data:
            modifier = data["modifier"]
            vg_name = data["vg_name"]
            part = data["part"]
            side = data["side"]

            # Ligne de séparation pour les non-body parts
            if part in NO_BODY_PREFIX and not drew_separator:
                col.separator(type="LINE")
                drew_separator = True

            # Skip si déjà traité (pour les duplicates)
            if vg_name in processed_vgs:
                continue

            # Détermine l'espace et la colonne
            num_col, empty_space = self._get_layout_info(vg_name, side, vg_names)

            if num_col == 0:
                row = col.row().split()
                row.alignment = "LEFT"
                row.label(text=part)
                row = row.row()
                row.alignment = "RIGHT"

            if empty_space == -1:
                row.label(text="", icon="PANEL_CLOSE")

            # Toggle ou operator selon le nombre d'occurrences
            if vg_counts[vg_name] > 1:
                if empty_space == 2:
                    row.separator(factor=1.14)

                any_visible = any(
                    m["modifier"].show_viewport for m in masks_data if m["vg_name"] == vg_name
                )
                row.operator(
                    "rigui.toggle_masks",
                    emboss=False,
                    text="",
                    icon="HIDE_ON" if any_visible else "HIDE_OFF",
                ).param = vg_name

                processed_vgs.add(vg_name)
            else:
                if empty_space == 2:
                    row.separator(factor=1.14)

                row.prop(
                    modifier,
                    "show_viewport",
                    text="",
                    icon="HIDE_ON",
                    invert_checkbox=True,
                    emboss=False,
                )

            if empty_space == 1 or empty_space == 2:
                row.separator(factor=1.14)

    def _get_layout_info(self, vg_name, side, vg_names):
        """Détermine la colonne et l'espace vide."""
        if side is None:
            return 0, 2  # Centré

        if side == "L":
            right_name = vg_name.replace(".L", ".R")
            if right_name not in vg_names:
                return 0, 1  # Espace à droite
            return 0, 0

        if side == "R":
            left_name = vg_name.replace(".R", ".L")
            if left_name not in vg_names:
                return 0, -1  # Espace à gauche
            return 1, 0

        return 0, 0


# Classes à enregistrer
classes = (RIGUI_PT_masks,)
