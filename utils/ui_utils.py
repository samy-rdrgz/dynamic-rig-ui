"""Utilitaires pour l'interface utilisateur."""

import bpy


def show_messagebox(
    title: str = "Info",
    lines: list[str] = None,  # type: ignore
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
