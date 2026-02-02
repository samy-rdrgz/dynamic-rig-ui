"""Panel pour la gestion des masks."""

from bpy.types import Panel

from ..config import MASK_PATTERN
from ..core import get_rig_cache
from ..utils import get_active_rig, is_valid_rig


class RIGUI_PT_masks(Panel):
    """Panel pour toggle les modifiers mask des meshes enfants."""

    bl_idname = "RIGUI_PT_masks"
    bl_label = ""
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {
        "HEADER_LAYOUT_EXPAND",
    }

    @classmethod
    def poll(cls, context):
        armature = get_active_rig(context)
        return is_valid_rig(armature)

    def draw_header(self, context):
        layout = self.layout.row(align=True)
        layout.alignment = "LEFT"
        armature = get_active_rig(context)
        masks_data = self._collect_masks(armature)
        all_visible = all(
            m["modifier"].show_viewport
            for m in masks_data
            if m["modifier"].vertex_group.startswith("MASK_")
        )
        layout.operator(
            "rigui.toggle_masks",
            emboss=False,
            text="MASKS",
            icon="HIDE_ON" if all_visible else "HIDE_OFF",
        ).param = "all"

    def draw(self, context):
        armature = get_active_rig(context)
        if armature is None:
            return

        # Collecte les modifiers mask
        masks_data = self._collect_masks(armature)
        if not masks_data:
            return

        layout = self.layout

        col = layout.column(align=True).box()

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
        priority = get_rig_cache(armature).parts
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
        masks_data = []

        for modifier in all_masks:
            match = MASK_PATTERN.match(modifier.vertex_group)
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

    def _draw_masks(self, col, armature, masks_data):
        """Dessine les toggles de masks."""

        col.scale_y = 0.6
        col.separator(factor=0.1)
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

            # Skip si déjà traité (pour les duplicates)
            if vg_name in processed_vgs:
                continue

            # Détermine l'espace et la colonne
            num_col, empty_space = self._get_layout_info(vg_name, side, vg_names)

            if num_col == 0:
                _row = col.row(align=True)

                row_b = _row.row(align=True)
                row_b.alignment = "LEFT"
                row_b.scale_x = 0.9
                row_b.label(text=" ")
                row_l = _row.row(align=True)
                row_l.alignment = "CENTER"
                row_l.label(text=f"  {part}")
            if num_col == 1:
                row_b.label(icon="BLANK1")
            if empty_space == -1:
                row_b.label(text="", icon="PANEL_CLOSE")

            # Toggle ou operator selon le nombre d'occurrences
            if vg_counts[vg_name] > 1:
                if empty_space == 2:
                    row_b.label(icon="BLANK1")

                any_visible = any(
                    m["modifier"].show_viewport for m in masks_data if m["vg_name"] == vg_name
                )
                row_b.operator(
                    "rigui.toggle_masks",
                    emboss=False,
                    text="",
                    icon="HIDE_ON" if any_visible else "HIDE_OFF",
                ).param = vg_name

                processed_vgs.add(vg_name)
            else:
                if empty_space == 2:
                    row_b.label(icon="BLANK1")

                row_b.prop(
                    modifier,
                    "show_viewport",
                    text="",
                    icon="HIDE_ON",
                    invert_checkbox=True,
                    emboss=False,
                )

            if empty_space == 1 or empty_space == 2:
                row_b.label(icon="BLANK1")
        col.separator(factor=0.1)

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
