"""Panel pour la gestion des controllers du rig."""

import re

from bpy.types import Panel

from ..config import PROPERTY_BONE, RIG_ID
from ..core import get_rig_cache
from ..utils import (
    any_box_expanded,
    any_collection,
    get_active_rig,
    get_box_expanded,
    get_rig_data,
    is_valid_rig,
)

ICONS = (("HIDE_ON", "HIDE_OFF"), ("SOLO_OFF", "SOLO_ON"))


class RIGUI_PT_rigui(Panel):
    """Panel affichant les contrôleurs par catégorie."""

    bl_idname = "RIGUI_PT_rigui"
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
        if armature is None:
            return False
        if context.active_object.type != "ARMATURE":
            return False
        return is_valid_rig(armature)

    def draw_header(self, context):
        """Dessine l'en-tête avec les toggles globaux."""
        armature = get_active_rig(context)
        rig_id = str(get_rig_data(context, RIG_ID))
        property_bone_name = get_rig_data(context, PROPERTY_BONE)

        try:
            property_bone = armature.pose.bones[property_bone_name]
        except (AttributeError, KeyError, TypeError):
            property_bone = None
        if not property_bone:
            self._draw_error(context)
            return None
        cache = get_rig_cache(armature)
        hierarchy = cache.hierarchy

        layout = self.layout
        layout = layout.row(align=True)

        layout.alignment = "LEFT"

        # Dessine chaque groupe
        any_solo = any(
            armature.data.collections[c.name].is_solo for p in hierarchy for c in p if c.name
        )

        # Toggle visibilité de tous les controllers
        parts_str = ",".join(cache.parts)
        btn_1 = layout.row(align=True)
        btn_1.active = False
        icon = (
            "DOWNARROW_HLT"
            if any_box_expanded(context.scene, rig_id, "ui_ctrl_", read_only=True)
            else "RIGHTARROW"
        )
        op = btn_1.operator(
            "rigui.toggle_boxes",
            emboss=False,
            text="",
            icon=icon,
        )
        op.prefix = "ui_ctrl_"
        op.parts = parts_str

        any_visible = any(
            armature.data.collections[c.name].is_solo
            if any_solo
            else armature.data.collections[c.name].is_visible
            for b in hierarchy
            for c in b
            if c.name != ""
        )

        op = layout.operator(
            "rigui.ctrl_box_actions",
            emboss=False,
            text="CONTROLLERS",
            icon=ICONS[int(any_solo)][int(any_visible)],
        )
        op.parts = parts_str

    def draw(self, context):
        armature = get_active_rig(context)
        rig_id = str(get_rig_data(context, RIG_ID))
        property_bone_name = get_rig_data(context, PROPERTY_BONE)

        try:
            property_bone = armature.pose.bones[property_bone_name]
        except (AttributeError, KeyError, TypeError):
            property_bone = None
        if not property_bone:
            self._draw_error(context)
            return None
        cache = get_rig_cache(armature)
        hierarchy = cache.hierarchy

        layout = self.layout
        panel = layout.column()
        panel.scale_y = 0.8

        # Dessine chaque groupe
        any_solo = any(
            armature.data.collections[c.name].is_solo for p in hierarchy for c in p if c.name
        )

        # Header avec toggle global
        # self._draw_header(context, panel, armature, rig_id, cache, hierarchy, any_solo)

        for b in hierarchy:
            self._draw_group(
                context,
                panel,
                armature,
                rig_id,
                property_bone,
                b,
                any_solo,
            )
            panel.separator(factor=0.1)

    def _draw_error(self, context):
        panel = self.layout.column()
        panel.alert = True
        panel.label(text="Your property posebone is not existing", icon="ERROR")
        panel.prop(context.active_object.data, '["prop_posebone_name"]', text="Prop bone")

    def _draw_group(self, context, panel, armature, rig_id, property_bone, box_data, any_solo):
        box = panel.box().column(align=True)
        expanded = get_box_expanded(context.scene, rig_id, f"ui_ctrl_{box_data[0].part}")

        if any_solo and not any_collection(armature, box_data, "is_solo"):
            box.active = False

        any_visible = any_collection(armature, box_data, "is_solo" if any_solo else "is_visible")

        self._draw_group_header(box, rig_id, box_data, expanded, any_visible, any_solo)
        if expanded:
            box.separator(factor=0.5)
            self._draw_group_content(armature, box, property_bone, box_data, any_solo)
        return box

    def _draw_group_header(self, box_layout, rig_id, box_data, expanded, any_visible, any_solo):
        """Dessine l'en-tête d'un groupe de collections."""
        title_line = box_layout.row(align=True)
        title_line.scale_y = 1.1

        title_eye = title_line.row(align=True)
        title_eye.alignment = "EXPAND"

        title_collapse = title_line.row(align=True)
        title_collapse.alignment = "RIGHT"

        op = title_eye.operator(
            "rigui.ctrl_box_actions",
            emboss=False,
            text=box_data[0].part,
            icon=ICONS[int(any_solo)][int(any_visible)],
        )
        op.parts = box_data[0].part

        icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"
        op = title_collapse.operator(
            "rigui.toggle_boxes",
            emboss=False,
            text="",
            icon=icon,
        )
        op.prefix = "ui_ctrl_"
        op.parts = box_data[0].part

    def _draw_group_content(self, armature, box, property_bone, box_data, any_solo):
        box = box.column(align=True)
        box.scale_y = 1.3
        col_index = 0
        for r in box_data:
            if r.is_prop:
                box_line = box.column(align=False).row(align=True)
                for prop in property_bone.keys():
                    if prop.startswith(f"{r.part}_{r.sub_part}"):
                        box_line.prop(
                            property_bone,
                            f'["{prop}"]',
                            text=f"{r.sub_part} ",
                            slider=True,
                        )
                continue
            elif r.is_mask:
                mask_modifiers = []
                for child in armature.children:
                    for modifier in child.modifiers:
                        if (
                            modifier.type == "MASK"
                            and modifier.vertex_group[5:].split(".")[0] == r.name.split(":")[0]
                        ):
                            mask_modifiers.append(modifier)
                pattern = re.compile(r"^(MASK_)([A-Z0-9_]+)(.([LMR]|(\d)))?$", re.MULTILINE)

                box_line = box.column(align=False).row(align=True)
                box_line.alignment = "EXPAND"
                for vg in {modifier.vertex_group for modifier in mask_modifiers}:
                    masks_data = []
                    for modifier in mask_modifiers:
                        if modifier.vertex_group == vg:
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

                    any_visible = any(m["modifier"].show_viewport for m in masks_data)
                    box_line.operator(
                        "rigui.toggle_masks",
                        emboss=True,
                        text="MASK",
                        icon="VIS_SEL_10" if any_visible else "VIS_SEL_00",
                    ).param = vg
                continue

            # Gestion des colonnes selon le côté
            elif (not r.has_side or r.side == ".L") and r.custom_side == "":
                box_line = box.row(align=True)
                col_index = 0

            elif not r.has_side:
                if col_index >= int(str(r.custom_side)[1:]):
                    box_line = box.row(align=True)
                    col_index = 0
                else:
                    col_index += 1

            # Affiche le toggle de visibilité
            name = r.sub_part if r.sub_part else "MAIN"

            if r.name == "":
                btn = box_line.row(align=True)
                btn.active = False
                btn.enabled = False
                btn.operator(
                    "rigui.toggle_masks",
                    emboss=True,
                    text="",
                )
            else:
                box_line.prop(
                    armature.data.collections[r.name],
                    "is_solo" if any_solo else "is_visible",
                    toggle=True,
                    text=name,
                )


# Classes à enregistrer
classes = (RIGUI_PT_rigui,)
