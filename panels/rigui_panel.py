"""Panel principal : controllers, masks inline et custom props inline."""

import re

from bpy.types import Panel

from ..config import PROPERTY_BONE, RIG_ID
from ..core import get_rig_cache
from ..utils import (
    any_box_expanded,
    any_collection,
    get_active_rig,
    get_box_expanded,
    get_enum_mapping,
    get_rig_data,
    is_valid_rig,
)

# (any_solo=False/True, any_visible=False/True)
ICONS = (("HIDE_ON", "HIDE_OFF"), ("SOLO_OFF", "SOLO_ON"))


class RIGUI_PT_rigui(Panel):
    """Panel affichant les contrôleurs par catégorie."""

    bl_idname = "RIGUI_PT_rigui"
    bl_label = ""
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HEADER_LAYOUT_EXPAND"}

    @classmethod
    def poll(cls, context):
        armature = get_active_rig(context)
        if armature is None:
            return False
        if context.active_object.type != "ARMATURE":
            return False
        return is_valid_rig(armature)

    def draw_header(self, context):
        armature = get_active_rig(context)
        rig_id = str(get_rig_data(context, RIG_ID))
        cache = get_rig_cache(armature)
        hierarchy = cache.hierarchy

        layout = self.layout.row(align=True)
        layout.alignment = "LEFT"

        any_solo = any(
            armature.data.collections[col.name].is_solo
            for part in hierarchy
            for col in part
            if col.name
        )
        parts_str = ",".join(cache.parts)

        # Bouton collapse/expand global
        btn_collapse = layout.row(align=True)
        btn_collapse.active = False
        icon = (
            "DOWNARROW_HLT"
            if any_box_expanded(context.scene, rig_id, "ui_ctrl_", read_only=True)
            else "RIGHTARROW"
        )
        op = btn_collapse.operator(
            "rigui.toggle_boxes", emboss=False, text="", icon=icon
        )
        op.prefix = "ui_ctrl_"
        op.parts = parts_str

        # Bouton visibilité/solo global
        any_visible = any(
            armature.data.collections[col.name].is_solo
            if any_solo
            else armature.data.collections[col.name].is_visible
            for part in hierarchy
            for col in part
            if col.name
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

        if property_bone_name:
            try:
                property_bone = armature.pose.bones[property_bone_name]
            except (AttributeError, KeyError, TypeError):
                property_bone = None
            if not property_bone:
                self._draw_error(context)
                return
        else:
            property_bone = None

        cache = get_rig_cache(armature)
        hierarchy = cache.hierarchy
        props_hierarchy = cache.props_hierarchy

        layout = self.layout
        panel = layout.column()
        panel.scale_y = 0.8

        any_solo = any(
            armature.data.collections[col.name].is_solo
            for part in hierarchy
            for col in part
            if col.name
        )

        for box_group in hierarchy:
            if not box_group:
                continue
            if len(box_group) > 1 or not box_group[0].is_order:
                self._draw_group(
                    context,
                    panel,
                    armature,
                    rig_id,
                    property_bone,
                    box_group,
                    any_solo,
                    props_hierarchy,
                )
                panel.separator(factor=0.1)

    def _draw_error(self, context):
        panel = self.layout.column()
        panel.alert = True
        panel.label(text="Property bone not found", icon="ERROR")
        panel.prop(context.active_object.data, f'["{PROPERTY_BONE}"]', text="Prop bone")

    def _draw_group(
        self,
        context,
        panel,
        armature,
        rig_id,
        property_bone,
        box_group,
        any_solo,
        props_hierarchy,
    ):
        box = panel.box().column(align=True)
        expanded = get_box_expanded(
            context.scene, rig_id, f"ui_ctrl_{box_group[0].part}"
        )

        if any_solo and not any_collection(armature, box_group, "is_solo"):
            box.active = False

        any_visible = any_collection(
            armature, box_group, "is_solo" if any_solo else "is_visible"
        )

        self._draw_group_header(box, rig_id, box_group, expanded, any_visible, any_solo)

        if expanded:
            box.separator(factor=0.5)
            self._draw_group_content(
                armature, box, property_bone, box_group, any_solo, props_hierarchy
            )
        return box

    def _draw_group_header(
        self, box_layout, rig_id, box_group, expanded, any_visible, any_solo
    ):
        title_line = box_layout.row(align=True)
        title_line.scale_y = 1.1

        title_eye = title_line.row(align=True)
        title_eye.alignment = "EXPAND"
        title_collapse = title_line.row(align=True)
        title_collapse.alignment = "RIGHT"

        op = title_eye.operator(
            "rigui.ctrl_box_actions",
            emboss=False,
            text=box_group[0].part,
            icon=ICONS[int(any_solo)][int(any_visible)],
        )
        op.parts = box_group[0].part

        icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"
        op = title_collapse.operator(
            "rigui.toggle_boxes", emboss=False, text="", icon=icon
        )
        op.prefix = "ui_ctrl_"
        op.parts = box_group[0].part

    def _draw_group_content(
        self, armature, box, property_bone, box_group, any_solo, props_hierarchy
    ):
        content = box.column(align=True)
        content.scale_y = 1.3
        is_custom_row = False
        col_index = 0
        flat_props = [prop for part in props_hierarchy for prop in part]
        row = content.column(align=False).row(align=True)
        for col_data in box_group:
            # --- Inline custom props (:PROP) ---
            if col_data.is_prop:
                row = content.column(align=False).row(align=True)
                for prop in flat_props:
                    if (
                        prop.part == col_data.part
                        and prop.sub_part == col_data.sub_part
                    ):
                        mapping = get_enum_mapping(property_bone, prop.name)
                        if mapping:
                            prec = (
                                property_bone.id_properties_ui(prop.name)
                                .as_dict()
                                .get("precision", 3)
                            )
                            current = property_bone.get(prop.name, 0)
                            label = mapping.get(current, str(round(current, prec)))
                            op = row.operator(
                                "rigui.enum_popup", text=label, icon="DOWNARROW_HLT"
                            )
                            op.prop_name = prop.name
                        else:
                            row.prop(
                                property_bone, f'["{prop.name}"]', text="", slider=True
                            )
                continue

            # --- Inline masks (:MASK) ---
            if col_data.is_mask:
                mask_modifiers = [
                    modifier
                    for child in armature.children
                    for modifier in child.modifiers
                    if (
                        modifier.type == "MASK"
                        and modifier.vertex_group[5:].split(".")[0]
                        == col_data.name.split(":")[0]
                    )
                ]
                mask_pattern = re.compile(
                    r"^(MASK_)([A-Z0-9_]+)(.([LMR]|(\d)))?$", re.MULTILINE
                )
                row = content.column(align=False).row(align=True)
                row.alignment = "EXPAND"

                for vg_name in {m.vertex_group for m in mask_modifiers}:
                    vg_masks = []
                    for modifier in mask_modifiers:
                        if modifier.vertex_group == vg_name:
                            match = mask_pattern.match(modifier.vertex_group)
                            if match:
                                vg_masks.append({"modifier": modifier})

                    any_visible = any(m["modifier"].show_viewport for m in vg_masks)
                    row.operator(
                        "rigui.toggle_masks",
                        emboss=True,
                        text="MASK",
                        icon="HIDE_ON" if any_visible else "HIDE_OFF",
                    ).param = vg_name
                continue

            # --- Gestion colonnes L/R / custom_side ---

            if (
                not col_data.has_side
                or col_data.side == ".L"
                or (col_data.custom_side and int(col_data.custom_side[1:]) <= col_index)
                or (col_data.custom_side and not is_custom_row)
            ):
                row = content.row(align=True)
                col_index = 0

            elif col_data.custom_side:
                col_index += 1

            is_custom_row = col_data.custom_side != ""

            # --- Bouton visibilité ---
            label = col_data.sub_part if col_data.sub_part else "MAIN"

            if col_data.name == "":
                # Fake bone (miroir absent) : placeholder grisé
                btn = row.row(align=True)
                btn.active = False
                btn.enabled = False
                btn.operator("rigui.toggle_masks", emboss=True, text="")
            else:
                row.prop(
                    armature.data.collections[col_data.name],
                    "is_solo" if any_solo else "is_visible",
                    toggle=True,
                    text=label,
                )


# Classes à enregistrer
classes = (RIGUI_PT_rigui,)
