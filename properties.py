"""PropertyGroups pour stocker les inputs utilisateur."""

import bpy
from bpy.props import EnumProperty
from bpy.types import PropertyGroup


def _get_panel_items():
    """Retourne les items pour les EnumProperty de sélection de panels."""
    return [
        ("RIG_UI_PT_rigui", "Ctrls", "", "RESTRICT_SELECT_OFF", 0),
        ("RIG_UI_PT_customprops", "Props", "", "OPTIONS", 1),
        ("RIG_UI_PT_masks", "Masks", "", "HIDE_OFF", 2),
        ("RIG_UI_PT_tools", "Tools", "", "TOOL_SETTINGS", 3),
        ("N", "-", "", "PANEL_CLOSE", 4),
    ]


class RIGUI_PG_settings(PropertyGroup):
    """Propriétés pour l'ordre des panels dans l'UI."""

    p_A: EnumProperty(
        name="Panel A",
        description="Premier panel affiché",
        items=_get_panel_items(),
        default="RIG_UI_PT_rigui",
    )

    p_B: EnumProperty(
        name="Panel B",
        description="Deuxième panel affiché",
        items=_get_panel_items(),
        default="RIG_UI_PT_customprops",
    )

    p_C: EnumProperty(
        name="Panel C",
        description="Troisième panel affiché",
        items=_get_panel_items(),
        default="RIG_UI_PT_tools",
    )

    p_D: EnumProperty(
        name="Panel D",
        description="Quatrième panel affiché",
        items=_get_panel_items(),
        default="RIG_UI_PT_masks",
    )


class RIGUI_PG_BoxState(bpy.types.PropertyGroup):
    """État d'une box (expanded/collapsed)."""

    name: bpy.props.StringProperty()  # "ui_ctrl_ARM", "ui_prop_LEG"
    expanded: bpy.props.BoolProperty(default=True)


class RIGUI_PG_RigUIState(bpy.types.PropertyGroup):
    """État UI complet pour un rig spécifique."""

    rig_id: bpy.props.StringProperty()

    # États des boxes
    boxes: bpy.props.CollectionProperty(type=RIGUI_PG_BoxState)

    # Ordre des panels (stocké en JSON ou simple string)
    panel_A: bpy.props.StringProperty(default="RIG_UI_PT_rigui")
    panel_B: bpy.props.StringProperty(default="RIG_UI_PT_customprops")
    panel_C: bpy.props.StringProperty(default="RIG_UI_PT_tools")
    panel_D: bpy.props.StringProperty(default="RIG_UI_PT_masks")


# Classes à enregistrer
classes = (RIGUI_PG_settings, RIGUI_PG_BoxState, RIGUI_PG_RigUIState)
