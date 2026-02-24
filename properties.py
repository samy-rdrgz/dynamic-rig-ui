"""PropertyGroups pour stocker les inputs utilisateur."""

import bpy
from bpy.types import PropertyGroup


class RIGUI_PG_BoxState(PropertyGroup):
    """État d'une box (expanded/collapsed)."""

    name: bpy.props.StringProperty()
    expanded: bpy.props.BoolProperty(default=True)


class RIGUI_PG_RigUIState(PropertyGroup):
    """État UI complet pour un rig spécifique."""

    rig_id: bpy.props.StringProperty()
    boxes: bpy.props.CollectionProperty(type=RIGUI_PG_BoxState)


# Classes à enregistrer (BoxState avant RigUIState car utilisé comme CollectionProperty)
classes = (RIGUI_PG_BoxState, RIGUI_PG_RigUIState)
