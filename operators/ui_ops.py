"""Opérateurs pour l'interface utilisateur."""

import contextlib

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..config import RIG_NAME


class WM_OT_text_popup(Operator):
    """Affiche une popup d'information configurable."""

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
        # Calcule la largeur optimale
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
            bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items.keys()
        )
        return self.icon if self.icon in valid_icons else "INFO"


class RIGUI_OT_reload_ui(Operator):
    """Recharge l'UI avec l'ordre des panels choisi."""

    bl_idname = f"{RIG_NAME.lower()}.reload_ui"
    bl_label = "Reload UI"
    bl_description = "Reload UI with chosen panels order"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        # Import ici pour éviter les imports circulaires
        from ..panels import (
            RIGUI_PT_customprops,
            RIGUI_PT_main,
            RIGUI_PT_masks,
            RIGUI_PT_rigui,
            RIGUI_PT_settings,
            RIGUI_PT_tools,
        )

        settings = context.scene.rigui_settings

        panel_map = {
            "RIG_UI_PT_rigui": RIGUI_PT_rigui,
            "RIG_UI_PT_customprops": RIGUI_PT_customprops,
            "RIG_UI_PT_masks": RIGUI_PT_masks,
            "RIG_UI_PT_tools": RIGUI_PT_tools,
            "N": None,
        }

        # Construit la liste des panels à afficher
        panels_to_register = [RIGUI_PT_main]

        for panel_id in [settings.p_A, settings.p_B, settings.p_C, settings.p_D]:
            panel_class = panel_map.get(panel_id)
            if panel_class and panel_class not in panels_to_register:
                panels_to_register.append(panel_class)

        panels_to_register.append(RIGUI_PT_settings)

        # Désenregistre tous les panels
        all_panels = [
            RIGUI_PT_main,
            RIGUI_PT_rigui,
            RIGUI_PT_masks,
            RIGUI_PT_tools,
            RIGUI_PT_customprops,
            RIGUI_PT_settings,
        ]

        for panel in all_panels:
            with contextlib.suppress(RuntimeError, ValueError):
                bpy.utils.unregister_class(panel)

        # Réinitialise les propriétés UI
        # init_ui_properties()

        # Réenregistre dans l'ordre voulu
        for panel in panels_to_register:
            if panel is not None:
                bpy.utils.register_class(panel)

        return {"FINISHED"}


# Classes à enregistrer
classes = (
    WM_OT_text_popup,
    RIGUI_OT_reload_ui,
)
