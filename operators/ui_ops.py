"""Opérateurs pour l'interface utilisateur."""

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from ..utils import get_active_rig, get_enum_mapping, get_property_bone


class WM_OT_text_popup(Operator):
    """Displays a configurable information popup."""

    bl_idname = "wm.text_popup"
    bl_label = "Information"

    icon: StringProperty(default="INFO")
    title: StringProperty(default="INFO")
    message: StringProperty(default="")

    def draw(self, context):
        layout = self.layout.column()
        layout.scale_y = 0.7
        layout.label(text=self.title.upper(), icon=self._get_valid_icon())
        layout.separator(type="LINE")
        for line in self.message.split("\n"):
            layout.label(text=line)

    def invoke(self, context, event):
        lines = self.message.split("\n")
        max_line_length = max((len(line) for line in lines), default=0) * 8
        title_length = len(self.title) * 9 + 23
        width = min(max(max_line_length, title_length), 300)
        return context.window_manager.invoke_popup(self, width=width)

    def execute(self, context):
        return {"FINISHED"}

    def _get_valid_icon(self) -> str:
        """Retourne l'icône si valide, sinon INFO."""
        valid_icons = (
            bpy.types.UILayout.bl_rna.functions["label"]
            .parameters["icon"]
            .enum_items.keys()
        )
        return self.icon if self.icon in valid_icons else "INFO"


class RIGUI_OT_set_int_prop(Operator):
    """Set custom prop value."""

    bl_idname = "rigui.set_int_prop"
    bl_label = ""
    bl_options = {"UNDO", "INTERNAL"}

    prop_name: StringProperty()
    value: IntProperty()

    def execute(self, context):
        armature = get_active_rig(context)
        property_bone = get_property_bone(armature)
        if property_bone is None:
            return {"CANCELLED"}

        property_bone[self.prop_name] = self.value

        # Force la mise à jour des drivers
        armature.update_tag()
        context.view_layer.depsgraph.update()

        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        return {"FINISHED"}


class RIGUI_OT_enum_popup(Operator):
    """Select Enum Value for Custom Prop, based on JSON mapping.
    Ctrl+Clic : Displays the rough editable property.
    """

    bl_idname = "rigui.enum_popup"
    bl_label = ""
    bl_options = {"INTERNAL"}

    prop_name: StringProperty()

    def invoke(self, context, event):
        if event.ctrl:
            return context.window_manager.invoke_popup(self, width=200)
        return self.execute(context)

    def execute(self, context):
        # Stocke le nom de prop pour le callback statique
        RIGUI_OT_enum_popup._current_prop = self.prop_name
        context.window_manager.popup_menu(self.draw_menu, title=self.prop_name)
        return {"FINISHED"}

    def draw(self, context):
        """Popup Ctrl+Clic : prop brute éditable."""
        layout = self.layout
        property_bone = get_property_bone(get_active_rig(context))
        layout.prop(property_bone, f'["{self.prop_name}"]', text=self.prop_name)

    @staticmethod
    def draw_menu(menu, context):
        layout = menu.layout
        property_bone = get_property_bone(get_active_rig(context))
        prop_name = RIGUI_OT_enum_popup._current_prop
        mapping = get_enum_mapping(property_bone, prop_name)
        current = property_bone.get(prop_name, 0)

        for value, label in mapping.items():
            op = layout.operator(
                "rigui.set_int_prop",
                text=label,
                icon="REC" if value == current else "BLANK1",
            )
            op.prop_name = prop_name
            op.value = value


# Classes à enregistrer
classes = (
    WM_OT_text_popup,
    RIGUI_OT_set_int_prop,
    RIGUI_OT_enum_popup,
)
