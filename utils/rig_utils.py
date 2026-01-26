"""Utilitaires pour la manipulation du rig."""

import bpy
from mathutils import Matrix

from ..config import PROPERTY_BONE


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
    """Vérifie si l'objet est un rig valide avec le bon ID.

    Args:
        obj: L'objet à vérifier.

    Returns:
        True si c'est un rig valide avec le bon rig_id.
    """
    if obj is None:
        return False

    try:
        return obj.data.get("has_dyn_rigui")
    except (AttributeError, KeyError, TypeError):
        return False


def get_rig_data(context: bpy.types.Context, data: str) -> str | int | None:
    """Retourne la  valeur de custom props demandée si trouvée,
    sinon None.

    Args:
        context: Le contexte Blender courant.

    Returns:
        Type de la custom prop si trouvée, sinon None
    """
    obj = get_active_rig(context)
    if obj:
        try:
            return obj.data.get(data)
        except Exception:
            return None
    else:
        return None


def get_property_bone(armature: bpy.types.Object) -> bpy.types.PoseBone | None:
    """Récupère le bone de propriétés du rig.

    Args:
        armature: L'armature contenant le bone.

    Returns:
        Le PoseBone de propriétés ou None.
    """
    return armature.pose.bones.get(PROPERTY_BONE)


def get_bone_collections_list(armature: bpy.types.Object) -> list:
    """Retourne la liste des collections sous forme de string multiligne.

    Utilisé pour le parsing regex des collections.

    Args:
        armature: L'armature source.

    Returns:
        String avec un nom de collection par ligne.
    """
    names = [col.name for col in armature.data.collections]
    return names


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
    # Matrices en rest pose
    source_rest = source_bone.bone.matrix_local
    target_rest = target_bone.bone.matrix_local

    # Matrice d'offset
    offset = source_rest.inverted() @ target_rest

    # Matrice monde finale
    return source_bone.matrix @ offset
