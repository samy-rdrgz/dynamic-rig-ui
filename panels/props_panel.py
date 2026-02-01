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
            panel.prop(context.active_object.data, f'["{PROPERTY_BONE}"]', text="Prop bone")
            return None
        cache = get_rig_cache(armature)
        boxes = cache.p_hierarchy
        for b_data in boxes:
            self._draw_group(context, panel, armature, rig_id, property_bone, b_data)
            # self._draw_box(context,panel,rig_id,property_bone,b_data)
        s = panel.row()
        s.scale_y = 0.4
        s.scale_x = 6.0
        s.active = False
        s.prop(context.scene, "column_factor", text="", slider=True)

    def draw_header(self, context):
        """Dessine l'en-tête du panel."""

        armature = get_active_rig(context)
        rig_id = str(get_rig_data(context, RIG_ID))

        cache = get_rig_cache(armature)
        parts = cache.p_parts

        icon = (
            "DOWNARROW_HLT"
            if any_box_expanded(context.scene, rig_id, "ui_prop_", read_only=True)
            else "RIGHTARROW"
        )

        op = self.layout.operator(
            "rigui.toggle_boxes",
            emboss=False,
            text="PROPERTIES",
            icon=icon,
        )
        op.prefix = "ui_prop_"
        op.parts = ",".join(parts)

    def _draw_group(self, context, panel, armature, rig_id, property_bone, box_data):
        box = panel.box().column(align=True)
        expanded = get_box_expanded(context.scene, rig_id, f"ui_prop_{box_data[0].part}")

        self._draw_group_header(box, box_data, expanded)
        if expanded:
            box.separator(factor=0.5)
            self._draw_group_content(context, box, property_bone, box_data)
        return box

    def _draw_group_header(self, box_layout, box_data, expanded):
        """Dessine l'en-tête d'un groupe de collections."""
        title_line = box_layout.row(align=True)
        title_line.scale_y = 1.1
        title_line.alignment = "LEFT"

        icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"
        op = title_line.operator(
            "rigui.toggle_boxes",
            emboss=False,
            text=box_data[0].part,
            icon=icon,
        )
        op.prefix = "ui_prop_"
        op.parts = box_data[0].part

    def _draw_group_content(self, context, box, property_bone, box_data):
        for p in box_data:
            if not p.has_side or p.side == ".L":
                row = box.split(factor=context.scene.column_factor)
                row.label(text=p.sub_part.replace("_", " ").capitalize())
                row = row.row(align=True)

            if p.fake:
                row.label(text="")
            else:
                desc = get_enum_mapping(property_bone, p.name)
                if property_bone.id_properties_ui(p.name).as_dict().get("step") == 1 and desc:
                    current = property_bone.get(p.name, 0)
                    label = desc.get(current, str(current))
                    op = row.operator("rigui.enum_popup", text=label, icon="DOWNARROW_HLT")
                    op.prop_name = p.name

                else:
                    row.prop(property_bone, f'["{p.name}"]', text="", slider=True)


# Classes à enregistrer
classes = (RIGUI_PT_customprops,)
