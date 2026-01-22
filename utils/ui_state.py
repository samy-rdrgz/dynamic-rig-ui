import bpy


def get_rig_ui_state(scene: bpy.types.Scene, rig_id: str) -> "RIGUI_PG_RigUIState":
    """Récupère ou crée l'état UI pour un rig.

    Args:
        scene: La scène courante.
        rig_id: L'identifiant unique du rig.

    Returns:
        Le PropertyGroup contenant l'état UI du rig.
    """
    # Cherche un état existant
    for state in scene.rigui_states:
        if state.rig_id == rig_id:
            return state

    # Crée un nouvel état
    state = scene.rigui_states.add()
    state.rig_id = rig_id
    return state


def get_box_expanded(
    scene: bpy.types.Scene,
    rig_id: str,
    box_name: str,
    default: bool = True,
) -> bool:
    """Récupère l'état expanded d'une box (lecture seule).

    Safe pour utilisation dans Panel.draw().

    Args:
        scene: La scène courante.
        rig_id: L'identifiant du rig.
        box_name: Le nom de la box (ex: "ui_ctrl_ARM").
        default: Valeur par défaut si non trouvée.

    Returns:
        True si la box est expanded, False sinon.
    """
    # Vérifie que rigui_states existe
    if not hasattr(scene, "rigui_states"):
        return default

    # Cherche le rig state
    for state in scene.rigui_states:
        if state.rig_id == rig_id:
            # Cherche la box
            for box in state.boxes:
                if box.name == box_name:
                    return box.expanded
            # Box pas trouvée → default
            return default

    # Rig state pas trouvé → default
    return default


def get_box_state(scene: bpy.types.Scene, rig_id: str, box_name: str) -> "RIGUI_PG_BoxState | None":
    """Retourne le BoxState ou None (sans créer)."""

    for state in scene.rigui_states:
        if state.rig_id == rig_id:
            for box in state.boxes:
                if box.name == box_name:
                    return box
    return None


def set_box_expanded(scene: bpy.types.Scene, rig_id: str, box_name: str, expanded: bool) -> None:
    """Définit l'état expanded d'une box.

    Args:
        scene: La scène courante.
        rig_id: L'identifiant du rig.
        box_name: Le nom de la box.
        expanded: True pour expand, False pour collapse.
    """
    state = get_rig_ui_state(scene, rig_id)

    for box in state.boxes:
        if box.name == box_name:
            box.expanded = expanded
            return

    # Crée l'entrée
    box = state.boxes.add()
    box.name = box_name
    box.expanded = expanded


def toggle_box(scene: bpy.types.Scene, rig_id: str, box_name: str) -> bool:
    """Toggle l'état d'une box et retourne le nouvel état."""
    current = get_box_expanded(scene, rig_id, box_name)
    set_box_expanded(scene, rig_id, box_name, not current)
    return not current
