"""Opérateurs de setup du rig : masks, collections, custom shapes."""

import bpy
import mathutils
from bpy.types import Operator

from ..utils import show_messagebox


class RIGUI_OT_create_masks(Operator):
    """Crée les modifiers MASK depuis les vertex groups préfixés MASK_.

    Fonctionne sur les meshes sélectionnés ou sur les enfants d'une armature sélectionnée.
    """

    bl_idname = "rigui.create_masks"
    bl_label = "Create Mask Modifiers"
    bl_description = "From vertex groups starting with 'MASK_', create or update mask modifiers"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        # Collecte les meshes cibles
        objs = []
        for obj in context.selected_objects:
            if obj.type == "MESH":
                objs.append(obj)
            elif obj.type == "ARMATURE":
                objs.extend(child for child in obj.children if child.type == "MESH")

        objs = list(dict.fromkeys(objs))  # dédoublonnage en conservant l'ordre

        if not objs:
            show_messagebox(
                "ERROR",
                ["Select mesh objects or an armature with mesh children."],
                icon="ERROR",
            )
            return {"FINISHED"}

        lines = []
        for obj in objs:
            lines.append(f"from object {obj.name.upper()} :")
            existing_mask_modifiers = {m.vertex_group: m for m in obj.modifiers if m.type == "MASK"}
            mask_vertex_groups = [vg for vg in obj.vertex_groups if vg.name.startswith("MASK_")]

            for mask_vg in mask_vertex_groups:
                lines.append(f"  - {mask_vg.name}")

                if mask_vg.name in existing_mask_modifiers:
                    modifier = existing_mask_modifiers[mask_vg.name]
                    modifier.name = mask_vg.name
                else:
                    modifier = obj.modifiers.new(mask_vg.name, type="MASK")
                    modifier.mode = "VERTEX_GROUP"

                modifier.vertex_group = mask_vg.name
                modifier.invert_vertex_group = True
                modifier.show_viewport = False
                modifier.show_render = False
                modifier.show_expanded = False
                modifier.show_in_editmode = False
                modifier.show_on_cage = False

        show_messagebox("Mask modifiers created", lines)
        return {"FINISHED"}


class RIGUI_OT_symmetrize_collections(Operator):
    """Crée les collections miroir manquantes (.L → .R et inversement)."""

    bl_idname = "rigui.symmetrize_collections"
    bl_label = "Symmetrize Collections"
    bl_description = "Find bone collections with .L/.R suffix and create the missing mirror"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        armature = context.active_object.data
        collections = armature.collections_all
        existing = {col.name for col in collections}
        lines = []

        for col in collections:
            if col.name.endswith(".L"):
                mirror_name = col.name[:-2] + ".R"
            elif col.name.endswith(".R"):
                mirror_name = col.name[:-2] + ".L"
            else:
                continue

            if mirror_name not in existing:
                new = armature.collections.new(mirror_name, parent=col.parent)
                parent = col.parent.name if col.parent is not None else "-"
                lines.append(f"{parent} > {new.name}")
                existing.add(mirror_name)

        if lines:
            show_messagebox(f"{len(lines)} collections created", lines, icon="MOD_MIRROR")
        else:
            show_messagebox("No collection to symmetrize", ["All .L/.R pairs already exist."])

        return {"FINISHED"}


class RIGUI_OT_create_custom_shape(Operator):
    """Crée un objet aligné sur le bone actif et l'assigne comme custom shape.

    Si un second bone est sélectionné, il est utilisé comme override transform.
    Gère automatiquement le miroir pour les bones .L / .R.
    """

    bl_idname = "rigui.create_custom_shape"
    bl_label = "Create Custom Shape"
    bl_description = (
        "Create a new object aligned with the active bone and assign it as custom shape.\n"
        "(Select two bones to use the second as override transform)"
    )
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        if context.active_object.mode != "POSE":
            show_messagebox("ERROR", ["Must be in POSE MODE."], icon="ERROR")
            return {"FINISHED"}

        active_bone = context.active_pose_bone
        other_bones = [b for b in context.selected_pose_bones if b != active_bone]
        transform_bone = other_bones[0] if other_bones else active_bone

        # Crée l'objet custom shape (suzanne par défaut, facilement remplaçable)
        bpy.ops.mesh.primitive_monkey_add(
            size=1,
            enter_editmode=False,
            align="WORLD",
            location=transform_bone.bone.head_local,
        )
        shape_obj = context.active_object

        # Nom WGT_ sans préfixes techniques
        clean_name = (
            active_bone.basename.removeprefix("ORG_").removeprefix("MCH_").removeprefix("VIS_")
        )
        shape_obj.name = f"WGT_{clean_name}"

        # Assigne au bone actif
        active_bone.custom_shape = shape_obj
        active_bone.custom_shape_transform = other_bones[0] if other_bones else None

        # Aligne la rotation et l'échelle
        rotation_matrix = mathutils.Matrix(
            (transform_bone.x_axis, transform_bone.y_axis, transform_bone.z_axis)
        ).transposed()
        shape_obj.rotation_mode = "QUATERNION"
        shape_obj.rotation_quaternion = rotation_matrix.to_quaternion()
        shape_obj.scale = (
            active_bone.bone.length,
            active_bone.bone.length,
            active_bone.bone.length,
        )

        lines = [f"{shape_obj.name}  →  {active_bone.name}"]
        if other_bones:
            lines.append(f"(override transform: {other_bones[0].name})")

        # Miroir automatique pour les bones latéraux
        if active_bone.name.endswith((".L", ".R")):
            suffix = active_bone.name[-2:]
            mirror_suf = ".R" if suffix == ".L" else ".L"
            mirror_name = active_bone.name[:-2] + mirror_suf

            try:
                mirror_bone = active_bone.id_data.pose.bones[mirror_name]
                mirror_bone.custom_shape = shape_obj
                mirror_bone.custom_shape_scale_xyz = (-1, 1, 1)
                if other_bones:
                    mirror_transform_name = other_bones[0].name[:-2] + mirror_suf
                    mirror_bone.custom_shape_transform = active_bone.id_data.pose.bones.get(
                        mirror_transform_name
                    )
                lines.append(f"+ mirrored  →  {mirror_name}")
            except KeyError:
                lines.append(f"(no mirror bone found: {mirror_name})")

        elif round(active_bone.bone.head_local[0] * 100) == 0:
            # Bone sur l'axe central : miroir modifier
            mirror_mod = shape_obj.modifiers.new("Mirror", type="MIRROR")
            mirror_mod.use_axis = (True, False, False)
            mirror_mod.use_clip = True
            lines.append("+ mirror modifier (center bone)")

        show_messagebox("Custom shape created", lines, icon="OBJECT_DATA")
        return {"FINISHED"}


# Classes à enregistrer
classes = (
    RIGUI_OT_create_masks,
    RIGUI_OT_symmetrize_collections,
    RIGUI_OT_create_custom_shape,
)
