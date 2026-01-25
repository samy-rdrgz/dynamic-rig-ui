"""Panel des paramètres de l'interface."""

import re

from bpy.types import Panel

from ..utils import get_active_rig, is_valid_rig


class RIGUI_PT_settings(Panel):
    """Panel"""

    bl_idname = "RIGUI_PT_settings"
    bl_label = "Rig UI Settings"
    bl_category = "Dyn RigUI"
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
            col.separator(type="LINE")
            col.label(text=f"Name : {rig.data['rig_name']}")
            col.label(text=f"ID : {rig.data['rig_id']}")
            col.prop(context.active_object.data, '["prop_posebone_name"]', text="Prop bone")

        else:
            col.prop(
                context.scene,
                "rigui_rig_name",
                text="",
                placeholder="Rig ID Name",
                expand=True,
            )
            name = context.scene.rigui_rig_name
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

    def _check_name(self, context, name):
        warnings = ""
        if context.active_object.type != "ARMATURE":
            warnings = "Select your Armature rig Object"
        elif name == "":
            warnings = "Name can't be empty"
        elif len(name) < 3:
            warnings = "Name should have more than 3 characters"
        elif name:
            pattern = "^[A-Z0-9_]+$"
            result = re.fullmatch(pattern, name)
            if result is None:
                warnings = "Name should have only upper case, digits or _."
        return warnings


# Classes à enregistrer
classes = (RIGUI_PT_settings,)
