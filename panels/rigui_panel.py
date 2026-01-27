"""Panel pour la gestion des controllers du rig."""

import re

from bpy.types import Panel

from ..utils import (
    any_box_expanded,
    any_collection,
    encode_json,
    get_active_rig,
    get_box_expanded,
    get_collections_dict,
    get_rig_data,
    is_valid_rig,
)

ICONS = (("HIDE_ON", "HIDE_OFF"), ("SOLO_OFF", "SOLO_ON"))


class RIGUI_PT_rigui(Panel):
    """Panel affichant les contrôleurs par catégorie."""

    bl_idname = "RIGUI_PT_rigui"
    bl_label = "Dynamic RigUI - Controllers"
    bl_category = "Item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        armature = get_active_rig(context)
        if armature is None:
            return False
        if context.active_object.type != "ARMATURE":
            return False
        return is_valid_rig(armature)

    def draw(self, context):
        armature = get_active_rig(context)
        rig_id = str(get_rig_data(context, "rig_id"))
        property_bone_name = get_rig_data(context, "prop_posebone_name")

        try:
            property_bone = armature.pose.bones[property_bone_name]
        except (AttributeError, KeyError, TypeError):
            property_bone = None
        if not property_bone:
            self._draw_error(context)
            return None
        collections_list = get_collections_dict(armature)
        """
        [
            print(i, j, str(d["collection"]))
            for i, part in enumerate(collections_list)
            for j, d in enumerate(part)
        ]"""

        layout = self.layout
        panel = layout.column()

        # Dessine chaque groupe
        any_solo = any(
            armature.data.collections[c["collection"]].is_solo if c["collection"] else False
            for p in collections_list
            for c in p
        )

        # Header avec toggle global
        self._draw_header(context, panel, armature, rig_id, collections_list, any_solo)
        panel.separator(factor=1)

        for b in collections_list:
            self._draw_group(
                context,
                panel,
                armature,
                rig_id,
                property_bone,
                b,
                any_solo,
            )
            panel.separator(factor=0.1)

    def _draw_error(self, context):
        panel = self.layout.column()
        panel.alert = True
        panel.label(text="Your property posebone is not existing", icon="ERROR")
        panel.prop(context.active_object.data, '["prop_posebone_name"]', text="Prop bone")

    def _draw_header(self, context, panel, armature, rig_id, box_data, any_solo):
        """Dessine l'en-tête avec les toggles globaux."""
        title = panel.box().row(align=False)
        title.scale_y = 0.8
        # Toggle visibilité de tous les controllers
        any_visible = any_collection(
            armature, box_data, "is_solo" if any_solo else "is_visible", flatten=True
        )
        op = title.operator(
            "rigui.toggle_controllers",
            emboss=False,
            text="CONTROLLERS",
            icon=ICONS[int(any_solo)][int(any_visible)],
        )
        op.parts = encode_json(box_data, flatten=True)

        icon = (
            "DOWNARROW_HLT"
            if any_box_expanded(context.scene, rig_id, "ui_ctrl_", read_only=True)
            else "RIGHTARROW"
        )

        op = title.operator(
            "rigui.toggle_all_boxes",
            emboss=False,
            text="",
            icon=icon,
        )
        op.rig_id = rig_id
        op.prefix = "ui_ctrl_"
        op.parts = ",".join({d["part"] for p in box_data for d in p})

    def _draw_group(self, context, panel, armature, rig_id, property_bone, box_data, any_solo):
        box = panel.box().column(align=True)
        expanded = get_box_expanded(context.scene, rig_id, f"ui_ctrl_{box_data[0]['part']}")

        if any_solo and not any_collection(armature, box_data, "is_solo"):
            box.active = False

        any_visible = any_collection(armature, box_data, "is_solo" if any_solo else "is_visible")

        self._draw_group_header(box, rig_id, box_data, expanded, any_visible, any_solo)
        if expanded:
            box.separator(factor=0.5)
            self._draw_group_content(armature, box, property_bone, box_data, any_solo)
        return box

    def _draw_group_header(self, box_layout, rig_id, box_data, expanded, any_visible, any_solo):
        """Dessine l'en-tête d'un groupe de collections."""
        title_line = box_layout.row(align=True)
        title_line.scale_y = 1.1

        title_eye = title_line.row(align=True)
        title_eye.alignment = "EXPAND"

        title_collapse = title_line.row(align=True)
        title_collapse.alignment = "RIGHT"

        op = title_eye.operator(
            "rigui.toggle_controllers",
            emboss=False,
            text=box_data[0]["part"],
            icon=ICONS[int(any_solo)][int(any_visible)],
        )
        op.parts = encode_json(box_data, flatten=False)

        icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"
        op = title_collapse.operator(
            "rigui.toggle_box",
            emboss=False,
            text="",
            icon=icon,
        )
        op.rig_id = rig_id
        op.box_name = f"ui_ctrl_{box_data[0]['part']}"

    def _draw_group_content(self, armature, box, property_bone, box_data, any_solo):
        col_index = 0
        for r in box_data:
            collection, part, sub_part, side, custom_side, is_prop, is_mask = (
                r["collection"],
                r["part"],
                r["sub_part"],
                r["side"],
                r["custom_side"],
                r["type"] == ":PROP",
                r["type"] == ":MASK",
            )
            if is_prop:
                box_line = box.column(align=False).row(align=True)
                for prop in property_bone.keys():
                    if prop.startswith(f"{part}_{sub_part}"):
                        box_line.prop(
                            property_bone,
                            f'["{prop}"]',
                            text=f"{sub_part} ",
                            slider=True,
                        )
                continue
            elif is_mask:
                mask_modifiers = []
                for child in armature.children:
                    for modifier in child.modifiers:
                        if (
                            modifier.type == "MASK"
                            and modifier.vertex_group[5:].split(".")[0] == collection.split(":")[0]
                        ):
                            mask_modifiers.append(modifier)
                pattern = re.compile(r"^(MASK_)([A-Z0-9_]+)(.([LMR]|(\d)))?$", re.MULTILINE)

                box_line = box.column(align=False).row(align=True)
                box_line.alignment = "EXPAND"
                for vg in {modifier.vertex_group for modifier in mask_modifiers}:
                    masks_data = []
                    for modifier in mask_modifiers:
                        if modifier.vertex_group == vg:
                            match = pattern.match(modifier.vertex_group)
                            if match:
                                masks_data.append(
                                    {
                                        "modifier": modifier,
                                        "vg_name": match.group(0),
                                        "part": match.group(2),
                                        "side": match.group(4),
                                    }
                                )

                    any_visible = any(m["modifier"].show_viewport for m in masks_data)
                    box_line.operator(
                        "rigui.toggle_masks",
                        emboss=True,
                        text="MASK",
                        icon="VIS_SEL_10" if any_visible else "VIS_SEL_00",
                    ).param = vg
                continue

            # Gestion des colonnes selon le côté
            elif (side is None or side == ".L") and custom_side is None:
                box_line = box.row(align=True)
                col_index = 0
            elif custom_side is not None:
                if col_index >= int(custom_side[1:]):
                    box_line = box.row(align=True)
                    col_index = 0
                else:
                    col_index += 1

            # Affiche le toggle de visibilité
            name = sub_part if sub_part else "MAIN"

            if not collection:
                btn = box_line.row(align=True)
                btn.active = False
                btn.enabled = False
                btn.operator(
                    "rigui.toggle_masks",
                    emboss=True,
                    text="",
                )
            else:
                box_line.prop(
                    armature.data.collections[collection],
                    "is_solo" if any_solo else "is_visible",
                    toggle=True,
                    text=name,
                )


# Classes à enregistrer
classes = (RIGUI_PT_rigui,)
