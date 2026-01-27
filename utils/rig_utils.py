"""Utilitaires pour la manipulation du rig."""

import re

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
        List avec les noms des collections.
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


def get_collections_dict(armature: bpy.types.Object) -> list:
    collections_str = "\n" + "\n".join(get_bone_collections_list(armature))
    pattern = re.compile(
        re.compile(
            r"^(?P<part>[A-Z]+)"
            r"(?:_(?P<sub_part>[A-Z0-9_]+))?"
            r"(?:(?P<side>\.[LMRXYZ])|(?P<custom_side>\.\d+)|(?P<type>:[A-Z]+))?$",
            re.MULTILINE,
        )
    )

    matches = pattern.finditer(collections_str)
    data = [{"collection": m.group(0), **m.groupdict()} for m in matches]
    parts = []
    for d in data:
        if d["part"] not in parts:
            parts.append(d["part"])
    ordered = [[] for i in parts]
    ordered_names = []
    for i, p in enumerate(parts):
        for d in data:
            if d["part"] == p:
                if d["side"] is None and d["collection"] not in ordered_names:
                    ordered[i].append(d)
                    ordered_names.append(d["collection"])
                else:
                    if d["collection"] in ordered_names:
                        continue
                    for s in (".L", ".M", ".R"):
                        f = find_dict(data, d["collection"].split(".")[0] + s)
                        if f and f["collection"] not in ordered_names:
                            ordered[i].append(f)
                            ordered_names.append(f["collection"])
                        elif s != ".M":
                            empty = dict(d)
                            empty["collection"] = None
                            empty["side"] = s
                            ordered[i].append(empty)
    return ordered


def find_dict(list: list, value: str) -> dict | None:
    for d in list:
        if d["collection"] == value:
            return d
    return None


def any_collection(
    armature: bpy.types.Object, data: list, prop: str = "is_visible", flatten: bool = False
) -> bool:
    """
    data : list (or list de list) de dictionnaires
    prop : is_visible, is_solo, ...
    """
    if flatten:
        data = [d for p in data for d in p]
    a = any(
        getattr(armature.data.collections[col["collection"]], prop, False)
        for col in data
        if col["collection"] and not col["type"]
    )
    return a


def encode_json(list: list, flatten: bool = False) -> str:
    if flatten:
        list = [d for p in list for d in p]
    text = (
        str(list)
        .replace("'", '"')
        .replace("False", "false")
        .replace("True", "true")
        .replace("None", "null")
    )
    return text
