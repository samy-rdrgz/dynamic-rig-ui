"""Utilitaires pour l'interface utilisateur."""

import bpy

from ..config import RIG_ID


def show_messagebox(
    title: str = "Info",
    lines: list[str] = None, # type: ignore
    icon: str = "INFO",
) -> None:
    """Affiche une popup de retour utilisateur.

    Args:
        title: Titre (première ligne) du message.
        lines: Liste de chaînes structurant les lignes du message.
        icon: ID d'une icône Blender.
    """
    if lines is None:
        lines = []
    if lines is None:
        lines = []

    def draw(self, context):
        layout = self.layout
        for line in lines:
            layout.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def refresh_ui() -> None:
    """Force le rafraîchissement de toutes les zones de l'interface."""
    for area in bpy.context.screen.areas:
        area.tag_redraw()


def init_ui_properties() -> None:
    """Initialise les propriétés UI sur l'armature.

    Crée les propriétés ui_ctrl_* et ui_prop_* nécessaires
    pour les boxes collapsibles de l'interface.
    """
    # Trouve le rig avec le bon ID
    rig = None
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE" and obj.data.get("rig_id") == RIG_ID:
            rig = obj
            break

    if rig is None:
        return

    property_bone = rig.pose.bones.get("PROPERTIES")
    if property_bone is None:
        return

    collections = rig.data.collections

    # Récupère les préfixes uniques des collections
    ctrl_prefixes = set()
    for col in collections:
        if col.name.isupper():
            prefix = col.name.split("_")[0].split(".")[0]
            ctrl_prefixes.add(prefix)

    # Récupère les préfixes uniques des propriétés
    prop_prefixes = set()
    for key in property_bone:
        prefix = key.split("_")[0]
        prop_prefixes.add(prefix)

    # Crée les propriétés manquantes
    for prefix in ctrl_prefixes:
        key = f"ui_ctrl_{prefix}"
        if key not in rig.data:
            rig.data[key] = True

    for prefix in prop_prefixes:
        key = f"ui_prop_{prefix}"
        if key not in rig.data:
            rig.data[key] = True
