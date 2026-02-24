"""Utilitaires pour l'interface utilisateur."""

import json

import bpy


def show_messagebox(
    title: str = "Info",
    lines: list[str] = None,  # type: ignore
    icon: str = "INFO",
) -> None:
    """Affiche une popup de retour utilisateur.

    Args:
        title: Titre de la popup.
        lines: Liste de lignes à afficher.
        icon: ID d'une icône Blender.
    """
    if lines is None:
        lines = []

    def draw(self, context):
        layout = self.layout
        for line in lines:
            layout.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def get_enum_mapping(pose_bone, prop: str) -> dict[int, str]:
    """Lit le mapping entier→label depuis la description JSON d'une custom prop.

    Le JSON est stocké dans le champ description de la UI property.
    Format attendu : {"0": "FK", "1": "IK"}

    Args:
        pose_bone: Le PoseBone portant la propriété.
        prop: Le nom de la custom prop.

    Returns:
        Dict {int: str} ou {} si absent/invalide.
    """
    try:
        ui = pose_bone.id_properties_ui(prop).as_dict()
        desc = ui.get("description", "")
        data = json.loads(desc)
        return {int(k): v for k, v in data.items()}
    except Exception:
        return {}
