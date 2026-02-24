"""Panel pour les propriétés custom du rig."""

from bpy.types import Panel

from ..config import PROPERTY_BONE, RIG_ID
from ..core import get_rig_cache
from ..utils import (
    any_box_expanded,
    get_active_rig,
    get_box_expanded,
    get_enum_mapping,
    get_rig_data,
    is_valid_rig,
)


class RIGUI_PT_customprops(Panel):
    """Panel affichant les propriétés custom organisées par catégorie."""

    bl_idname = "RIGUI_PT_customprops"
    bl_label = ""
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

    def draw_header(self, context):
        armature = get_active_rig(context)
        rig_id = str(get_rig_data(context, RIG_ID))
        cache = get_rig_cache(armature)

        icon = (
            "DOWNARROW_HLT"
            if any_box_expanded(context.scene, rig_id, "ui_prop_", read_only=True)
            else "RIGHTARROW"
        )
        op = self.layout.operator("rigui.toggle_boxes", emboss=False, text="PROPERTIES", icon=icon)
        op.prefix = "ui_prop_"
        op.parts = ",".join(cache.props_parts)

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
            panel.label(text="Property bone not found", icon="ERROR")
            panel.prop(context.active_object.data, f'["{PROPERTY_BONE}"]', text="Prop bone")
            return

        cache = get_rig_cache(armature)

        for group_data in cache.props_hierarchy:
            self._draw_group(context, panel, armature, rig_id, property_bone, group_data)

    def _draw_group(self, context, panel, armature, rig_id, property_bone, group_data):
        box = panel.box().column(align=True)
        expanded = get_box_expanded(context.scene, rig_id, f"ui_prop_{group_data[0].part}")

        self._draw_group_header(box, group_data, expanded)
        if expanded:
            box.separator(factor=0.5)
            self._draw_group_content(context, box, property_bone, group_data)
        return box

    def _draw_group_header(self, box_layout, group_data, expanded):
        title_line = box_layout.row(align=True)
        title_line.scale_y = 1.1
        title_line.alignment = "LEFT"

        icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"
        op = title_line.operator(
            "rigui.toggle_boxes", emboss=False, text=group_data[0].part, icon=icon
        )
        op.prefix = "ui_prop_"
        op.parts = group_data[0].part

    def _draw_group_content(self, context, box, property_bone, group_data):
        for prop_data in group_data:
            if not prop_data.has_side or prop_data.side == ".L":
                row = box.split(factor=0.4)
                row.label(text=prop_data.sub_part.replace("_", " ").capitalize())
                row = row.row(align=True)

            if prop_data.fake:
                row.label(text="")
            else:
                mapping = get_enum_mapping(property_bone, prop_data.name)
                if mapping:
                    current = property_bone.get(prop_data.name, 0)
                    label = mapping.get(current, str(current))
                    op = row.operator("rigui.enum_popup", text=label, icon="DOWNARROW_HLT")
                    op.prop_name = prop_data.name
                else:
                    row.prop(property_bone, f'["{prop_data.name}"]', text="", slider=True)


# Classes à enregistrer
classes = (RIGUI_PT_customprops,)
