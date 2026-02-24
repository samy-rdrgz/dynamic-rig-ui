"""Opérateur pour snap entre IK et FK."""

import json

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..config import ACTIVE, IK_CHAINS
from ..utils import get_active_rig, get_property_bone


def _load_chains(armature) -> dict:
    """Charge et parse le JSON des chaînes IK/FK depuis les custom props.

    Format attendu dans armature.data[IK_CHAINS] :
    {
        "LEG": {
            "switch_prop": "LEG_FK_IK",
            "fk": {
                "copy_end": "MCH_FK_IK_FOOT_IK",
                "copy_pole": "MCH_FK_IK_LEG_IK_POLE",
                "past_upper": "LEG_FK",
                "past_middle": "SHIN_FK",
                "past_end": "FOOT_FK"
            },
            "ik": {
                "copy_upper": "MCH_LEG_IK",
                "copy_middle": "MCH_SHIN_IK",
                "copy_end": "MCH_FOOT_IK",
                "past_end": "FOOT_IK",
                "past_pole": "LEG_IK_POLE"
            }
        },
        "ARM": { ... }
    }

    Returns:
        Dict parsé ou {} si absent / invalide.
    """
    raw = armature.data.get(IK_CHAINS, "")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _build_bone_lookup(chains: dict) -> dict[str, tuple]:
    """Construit un index bone_name -> (fk, ik, limb, switch_prop, direction).

    Permet de détecter quel membre et quelle direction en O(1).
    """
    lookup = {}
    for chain_name, chain in chains.items():
        fk = chain.get("fk", {})
        ik = chain.get("ik", {})
        switch_prop = chain.get("switch_prop", "")

        for bone_name in ik.values():
            lookup[bone_name] = (fk, ik, chain_name, switch_prop, "ik_to_fk")
        for bone_name in fk.values():
            # Ne pas écraser : un bone MCH peut apparaître dans les deux côtés
            if bone_name not in lookup:
                lookup[bone_name] = (fk, ik, chain_name, switch_prop, "fk_to_ik")

    return lookup


class RIGUI_OT_snap_kinematic(Operator):
    """Snap un membre sur la cinématique opposée (FK->IK ou IK->FK).

    La détection du membre et de la direction est automatique
    selon le bone actif sélectionné.
    """

    bl_idname = "rigui.snap_opposite_kinematic"
    bl_label = "Snap Kinematic"
    bl_description = "Snap limb to opposite kinematic (select any controller of destination chain)"
    bl_options = {"UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        try:
            obj = context.active_object
            return bool(obj and obj.data.get(ACTIVE) and context.mode == "POSE")
        except (AttributeError, TypeError):
            return False

    def execute(self, context):
        active_pose_bone = context.active_pose_bone
        if active_pose_bone is None:
            return self._error("No active pose bone selected.")

        # Décompose "FOOT_IK.L" -> bone_name="FOOT_IK", side="L"
        parts = active_pose_bone.name.rsplit(".", 1)
        if len(parts) == 1:
            bone_name, side = active_pose_bone.name, ""
        elif len(parts) < 2 or (parts[1] not in ("L", "M", "R") and not parts[1].isdigit()):
            return self._error("Bone must have a side suffix (.L or .M or .R or .1/.2/.../.9).")
        else:
            bone_name, side = parts

        armature = get_active_rig(context)
        chains = _load_chains(armature)

        if not chains:
            return self._error(
                f'No IK chains defined.\nAdd a "{IK_CHAINS}" JSON custom prop on the armature.'
            )

        lookup = _build_bone_lookup(chains)
        chain_config = lookup.get(bone_name)

        if chain_config is None:
            return self._error("Select a controller of a switchable kinematic chain.")

        fk, ik, chain_name, switch_prop, direction = chain_config

        property_bone = get_property_bone(armature)
        if property_bone is None:
            return self._error("Property bone not found.")

        pose_bones = armature.pose.bones

        try:
            if direction == "ik_to_fk":
                self._snap_ik_to_fk(armature, pose_bones, property_bone, fk, ik, switch_prop, side)
            else:
                self._snap_fk_to_ik(armature, pose_bones, property_bone, fk, ik, switch_prop, side)
        except KeyError as e:
            return self._error(f"Bone not found: {e}\nCheck your IK chain JSON config.")

        side_label = self._side_label(side)
        direction_label = "IK -> FK" if direction == "ik_to_fk" else "FK -> IK"
        bpy.ops.wm.text_popup(
            "INVOKE_DEFAULT",
            icon="CHECKMARK",
            title="SWITCH DONE",
            message=f"{side_label}  {chain_name}  {direction_label}",
        )

        return {"FINISHED"}

    def _side_label(self, side: str) -> str:
        if side == "L":
            return "LEFT"
        elif side == "M":
            return "MIDDLE"
        elif side == "R":
            return "RIGHT"
        elif side.isdigit():
            return f"VARIANT {side}"
        else:
            return "CHAIN"

    # -------------------------------------------------------------------------

    def _snap_ik_to_fk(self, armature, pose_bones, property_bone, fk, ik, switch_prop, side):
        """Snap les contrôleurs IK sur la position FK actuelle."""
        from ..utils import get_matrix_with_offset

        suffix = f".{side}" if side else ""
        fk_end = pose_bones[f"{fk['copy_end']}{suffix}"]
        fk_pole = pose_bones[f"{fk['copy_pole']}{suffix}"]
        ik_end = pose_bones[f"{ik['past_end']}{suffix}"]
        ik_pole = pose_bones[f"{ik['past_pole']}{suffix}"]

        ik_end.matrix = get_matrix_with_offset(fk_end, ik_end)
        bpy.context.view_layer.update()

        ik_pole.matrix = get_matrix_with_offset(fk_pole, ik_pole)
        bpy.context.view_layer.update()

        property_bone[f"{switch_prop}{suffix}"] = 1

        self._auto_keyframe(armature, [ik_end, ik_pole, property_bone])

    def _snap_fk_to_ik(self, armature, pose_bones, property_bone, fk, ik, switch_prop, side):
        """Snap les contrôleurs FK sur la position IK actuelle, parent -> enfant."""
        from ..utils import get_matrix_with_offset

        suffix = f".{side}" if side else ""
        fk_upper = pose_bones[f"{fk['past_upper']}{suffix}"]
        fk_middle = pose_bones[f"{fk['past_middle']}{suffix}"]
        fk_end = pose_bones[f"{fk['past_end']}{suffix}"]
        ik_upper = pose_bones[f"{ik['copy_upper']}{suffix}"]
        ik_middle = pose_bones[f"{ik['copy_middle']}{suffix}"]
        ik_end = pose_bones[f"{ik['copy_end']}{suffix}"]

        fk_upper.matrix = get_matrix_with_offset(ik_upper, fk_upper)
        bpy.context.view_layer.update()

        fk_middle.matrix = get_matrix_with_offset(ik_middle, fk_middle)
        bpy.context.view_layer.update()

        fk_end.matrix = get_matrix_with_offset(ik_end, fk_end)
        bpy.context.view_layer.update()

        property_bone[f"{switch_prop}{suffix}"] = 0

        self._auto_keyframe(armature, [fk_upper, fk_middle, fk_end, property_bone])

    def _auto_keyframe(self, armature, pose_bones: list):
        """Insère des keyframes sur les bones donnés si l'auto-key est actif."""
        if not bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            return

        bpy.ops.pose.select_all(action="DESELECT")

        for pbone in pose_bones:
            armature.data.bones.active = pbone.bone
            pbone.bone.select = True
            try:
                bpy.ops.anim.keyframe_insert_menu(type="Available")
            except RuntimeError:
                self.report({"WARNING"}, f"{pbone.name}: no keyframeable channel found")
            pbone.bone.select = False

    def _error(self, message: str):
        """Affiche une popup d'erreur et retourne CANCELLED."""
        bpy.ops.wm.text_popup(
            "INVOKE_DEFAULT",
            icon="ERROR",
            title="ERROR",
            message=message,
        )
        return {"CANCELLED"}


class RIGUI_OT_apply_ik_chains(Operator):
    """Applique un Text block JSON comme config IK/FK sur l'armature active."""

    bl_idname = "rigui.apply_ik_chains"
    bl_label = "Apply IK Chains JSON"
    bl_description = "Read a JSON text block and store it in the armature's IK chains property"
    bl_options = {"UNDO", "INTERNAL"}

    text_block: StringProperty(name="Text Block")

    def execute(self, context):
        text = bpy.data.texts.get(self.text_block)
        if text is None:
            self.report({"ERROR"}, f'Text block "{self.text_block}" not found.')
            return {"CANCELLED"}

        raw = text.as_string()

        # Valide le JSON avant d'écrire
        try:
            json.loads(raw)
        except json.JSONDecodeError as e:
            self.report({"ERROR"}, f"Invalid JSON : {e}")
            return {"CANCELLED"}

        armature = get_active_rig(context)
        armature.data[IK_CHAINS] = raw
        self.report({"INFO"}, f'IK chains applied from "{self.text_block}"')
        return {"FINISHED"}


# Classes à enregistrer
classes = (RIGUI_OT_snap_kinematic, RIGUI_OT_apply_ik_chains)
