"""Utilitaires pour la manipulation du rig."""

import bpy
from mathutils import Matrix

from ..config import ACTIVE, PROPERTY_BONE


def get_active_rig(context: bpy.types.Context) -> bpy.types.Object | None:
    """Récupère le rig actif depuis le contexte.

    Cherche d'abord si l'objet actif est une armature,
    sinon vérifie si son parent est une armature.

    Args:
        context: Le contexte Blender courant.

    Returns:
        L'armature active ou None si non trouvée.
    """
    obj = context.active_object
    if obj is None:
        return None

    if obj.type == "ARMATURE":
        return obj

    if obj.parent and obj.parent.type == "ARMATURE":
        return obj.parent

    return None


def is_valid_rig(obj: bpy.types.Object | None) -> bool:
    """Vérifie si l'objet est un rig valide activé pour Dynamic RigUI.

    Args:
        obj: L'objet à vérifier.

    Returns:
        True si c'est une armature avec le flag ACTIVE.
    """
    if obj is None:
        return False

    try:
        return bool(obj.data.get(ACTIVE))
    except (AttributeError, KeyError, TypeError):
        return False


def get_rig_data(context: bpy.types.Context, data: str) -> str | int | None:
    """Retourne la valeur d'une custom prop de l'armature active.

    Args:
        context: Le contexte Blender courant.
        data: La clé de la custom prop.

    Returns:
        La valeur de la prop si trouvée, sinon None.
    """
    obj = get_active_rig(context)
    if obj:
        try:
            return obj.data.get(data)
        except Exception:
            return None
    return None


def get_property_bone(armature: bpy.types.Object) -> bpy.types.PoseBone | None:
    """Récupère le bone de propriétés du rig.

    Lit le nom du bone directement depuis armature.data, sans dépendre de bpy.context.

    Args:
        armature: L'armature contenant le bone.

    Returns:
        Le PoseBone de propriétés ou None.
    """
    property_bone_name = armature.data.get(PROPERTY_BONE)
    if not property_bone_name:
        return None
    try:
        return armature.pose.bones[property_bone_name]
    except (AttributeError, KeyError, TypeError):
        return None


def get_matrix_with_offset(
    source_bone: bpy.types.PoseBone,
    target_bone: bpy.types.PoseBone,
) -> Matrix:
    """Calcule la matrice finale en tenant compte de l'offset en rest pose.

    Args:
        source_bone: Le bone source (celui qu'on lit).
        target_bone: Le bone cible (celui qu'on veut matcher).

    Returns:
        La matrice monde finale pour le bone cible.
    """
    source_rest = source_bone.bone.matrix_local
    target_rest = target_bone.bone.matrix_local
    offset = source_rest.inverted() @ target_rest
    return source_bone.matrix @ offset


def any_collection(
    armature: bpy.types.Object,
    data: list,
    prop: str = "is_visible",
    flatten: bool = False,
) -> bool:
    """Vérifie si au moins une collection (non-type) a la propriété à True.

    Args:
        armature: L'armature contenant les collections.
        data: list ou list de list de CollectionData.
        prop: "is_visible", "is_solo", etc.
        flatten: Si True, aplatit une list de list.
    """
    if flatten:
        data = [d for p in data for d in p]
    return any(
        getattr(armature.data.collections[col.name], prop, False)
        for col in data
        if col.name and not col.col_type
    )
