"""
Rig UI - Interface utilisateur pour rigs Blender.

Addon pour gérer facilement les controllers, propriétés custom,
masks et outils de snap IK/FK sur un rig.
"""

bl_info = {
    "name": "Dynamic Rig UI",
    "author": "Samy RODRIGUEZ",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Item",
    "description": "Custom rig UI with controllers, properties and tools",
    "category": "Rigging",
}

import contextlib

import bpy

from .operators import classes as operator_classes
from .panels import classes as panel_classes
from .properties import RIGUI_PG_BoxState, RIGUI_PG_RigUIState, RIGUI_PG_settings
from .utils import init_ui_properties

# Ordre d'enregistrement : PropertyGroups -> Operators -> Panels
_classes = (
    RIGUI_PG_BoxState,
    RIGUI_PG_RigUIState,
    RIGUI_PG_settings,
    *operator_classes,
    *panel_classes,
)


def register():
    """Enregistre toutes les classes de l'addon."""
    for cls in _classes:
        bpy.utils.register_class(cls)

    # Enregistre la propriété sur Scene
    bpy.types.Scene.rigui_settings = bpy.props.PointerProperty(type=RIGUI_PG_settings)
    bpy.types.Scene.rigui_states = bpy.props.CollectionProperty(type=RIGUI_PG_RigUIState)


def unregister():
    """Désenregistre toutes les classes de l'addon."""
    # Supprime la propriété
    if hasattr(bpy.types.Scene, "rigui_settings"):
        del bpy.types.Scene.rigui_settings

    # Désenregistre dans l'ordre inverse
    for cls in reversed(_classes):
        with contextlib.suppress(RuntimeError):
            bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
