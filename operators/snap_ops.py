"""Opérateur pour snap entre IK et FK."""

import bpy
from bpy.types import Operator

from ..config import (
    ARM_FK,
    ARM_IK,
    ARM_SWITCH_PROP,
    LEG_FK,
    LEG_IK,
    LEG_SWITCH_PROP,
    RIG_ID,
    RIG_NAME,
)
from ..utils import get_matrix_with_offset


class RIGUI_OT_snap_kinematic(Operator):
    """Snap un membre sur la cinématique opposée (FK<->IK)."""

    bl_idname = f"{RIG_NAME.lower()}.snap_opposite_kinematic"
    bl_label = "Snap Kinematic"
    bl_description = "Snap limb to opposite kinematic"
    bl_options = {"UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        try:
            return context.active_object.data.get("rig_id") == RIG_ID
        except (AttributeError, KeyError, TypeError):
            return False

    def execute(self, context):
        active_bone = context.active_pose_bone
        if active_bone is None:
            self._show_error("No active pose bone selected.")
            return {"CANCELLED"}

        bone_parts = active_bone.name.split(".")
        if len(bone_parts) < 2:
            self._show_error("Bone must have a side suffix (.L or .R)")
            return {"CANCELLED"}

        side = bone_parts[1]
        bone_name = bone_parts[0]

        # Détermine quel membre et quelle direction
        chain_config = self._get_chain_config(bone_name)
        if chain_config is None:
            self._show_error("Select a controller of a switchable kinematic chain.")
            return {"CANCELLED"}

        fk, ik, limb_name, switch_prop, direction = chain_config
        armature = context.active_object
        pose_bones = armature.pose.bones
        properties = pose_bones["PROPERTIES"]

        if direction == "ik_to_fk":
            self._snap_ik_to_fk(armature, pose_bones, properties, fk, ik, switch_prop, side)
        else:
            self._snap_fk_to_ik(armature, pose_bones, properties, fk, ik, switch_prop, side)

        # Feedback utilisateur
        side_name = "LEFT" if side == "L" else "RIGHT"
        bpy.ops.wm.text_popup(
            "INVOKE_DEFAULT",
            icon="CHECKMARK",
            title="SWITCH DONE",
            message=f"{side_name} {limb_name}'s {direction.replace('_', ' ')}",
        )

        return {"FINISHED"}

    def _get_chain_config(self, bone_name: str):
        """Détermine la configuration de la chaîne selon le bone actif.

        Returns:
            Tuple (fk_dict, ik_dict, limb_name, switch_prop, direction) ou None.
        """
        # Check LEG
        if bone_name in LEG_IK.values():
            return (LEG_FK, LEG_IK, "LEG", LEG_SWITCH_PROP, "ik_to_fk")
        if bone_name in LEG_FK.values():
            return (LEG_FK, LEG_IK, "LEG", LEG_SWITCH_PROP, "fk_to_ik")

        # Check ARM
        if bone_name in ARM_IK.values():
            return (ARM_FK, ARM_IK, "ARM", ARM_SWITCH_PROP, "ik_to_fk")
        if bone_name in ARM_FK.values():
            return (ARM_FK, ARM_IK, "ARM", ARM_SWITCH_PROP, "fk_to_ik")

        return None

    def _snap_ik_to_fk(self, armature, pose_bones, properties, fk, ik, switch_prop, side):
        """Snap les contrôleurs IK sur la position FK."""
        # Bones FK cibles
        fk_c = pose_bones[f"{fk['target_C']}.{side}"]
        fk_pole = pose_bones[f"{fk['target_pole']}.{side}"]

        # Bones IK à déplacer
        ik_c = pose_bones[f"{ik['C']}.{side}"]
        ik_pole = pose_bones[f"{ik['pole']}.{side}"]

        # Applique les matrices
        ik_c.matrix = get_matrix_with_offset(fk_c, ik_c)
        bpy.context.view_layer.update()

        ik_pole.matrix = get_matrix_with_offset(fk_pole, ik_pole)
        bpy.context.view_layer.update()

        # Switch la propriété
        properties[f"{switch_prop}.{side}"] = 1

        # Keyframe si auto-key activé
        self._auto_keyframe([ik_c, ik_pole, properties], armature)

    def _snap_fk_to_ik(self, armature, pose_bones, properties, fk, ik, switch_prop, side):
        """Snap les contrôleurs FK sur la position IK."""
        # Bones FK à déplacer
        fk_a = pose_bones[f"{fk['A']}.{side}"]
        fk_b = pose_bones[f"{fk['B']}.{side}"]
        fk_c = pose_bones[f"{fk['C']}.{side}"]

        # Bones IK cibles
        ik_a = pose_bones[f"{ik['target_A']}.{side}"]
        ik_b = pose_bones[f"{ik['target_B']}.{side}"]
        ik_c = pose_bones[f"{ik['target_C']}.{side}"]

        # Applique les matrices dans l'ordre parent -> enfant
        fk_a.matrix = get_matrix_with_offset(ik_a, fk_a)
        bpy.context.view_layer.update()

        fk_b.matrix = get_matrix_with_offset(ik_b, fk_b)
        bpy.context.view_layer.update()

        fk_c.matrix = get_matrix_with_offset(ik_c, fk_c)
        bpy.context.view_layer.update()

        # Switch la propriété
        properties[f"{switch_prop}.{side}"] = 0

        # Keyframe si auto-key activé
        self._auto_keyframe([fk_a, fk_b, fk_c, properties], armature)

    def _auto_keyframe(self, bones, armature):
        """Ajoute des keyframes si l'auto-key est activé."""
        if not bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            return

        bpy.ops.pose.select_all(action="DESELECT")

        for bone in bones:
            armature.data.bones.active = bone.bone
            try:
                bpy.ops.anim.keyframe_insert_menu(type="Available")
            except RuntimeError:
                self.report({"WARNING"}, f"{bone.name} has no active keyframes")

    def _show_error(self, message: str):
        """Affiche un message d'erreur."""
        bpy.ops.wm.text_popup(
            "INVOKE_DEFAULT",
            icon="ERROR",
            title="ERROR",
            message=message,
        )


# Classes à enregistrer
classes = (RIGUI_OT_snap_kinematic,)
