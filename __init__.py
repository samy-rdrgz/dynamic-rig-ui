"""
Dynamic Rig UI - Interface utilisateur dynamique pour rigs Blender.

Génère automatiquement une UI depuis les bone collections, custom properties,
mask modifiers, et fournit des outils de snap IK/FK et de setup de rig.
"""

bl_info = {
    "name": "Dynamic Rig UI",
    "author": "Samy RODRIGUEZ",
    "version": (1, 0, 1),
    "blender": (5, 0, 0),
    "blender_version_min": "5.0.0",
    "location": "View3D > Sidebar > Item  |  View3D > Sidebar > DRigUI",
    "description": "Dynamic rig UI driven by bone collections, custom properties and JSON config",
    "category": "Rigging",
}

import contextlib

import bpy

from .core import _cache
from .core import classes as core_classes
from .operators import classes as operator_classes
from .panels import classes as panel_classes
from .properties import RIGUI_PG_BoxState, RIGUI_PG_RigUIState

# Ordre d'enregistrement : PropertyGroups → Operators → Panels
_classes = (
    RIGUI_PG_BoxState,
    RIGUI_PG_RigUIState,
    *operator_classes,
    *core_classes,
    *panel_classes,
)


def register():
    """Enregistre toutes les classes et propriétés Scene de l'addon."""
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.input_name = bpy.props.StringProperty(name="Rig name")
    bpy.types.Scene.rigui_states = bpy.props.CollectionProperty(
        type=RIGUI_PG_RigUIState
    )


def unregister():
    """Désenregistre toutes les classes et nettoie les propriétés Scene."""
    # Nettoie le cache global
    _cache.clear()

    # Supprime les propriétés Scene
    for prop in ("rigui_settings", "rigui_states", "input_name"):
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)

    # Désenregistre dans l'ordre inverse
    for cls in reversed(_classes):
        with contextlib.suppress(RuntimeError):
            bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
