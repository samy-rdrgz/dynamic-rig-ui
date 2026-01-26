"""Panel pour la gestion des controllers du rig."""

import re

from bpy.types import Panel

from ..utils import (
    get_active_rig,
    get_bone_collections_list,
    get_box_expanded,
    get_rig_data,
    is_valid_rig,
)


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

        b_name = get_rig_data(context, "prop_posebone_name")

        try:
            property_bone = armature.pose.bones[b_name]
        except (AttributeError, KeyError, TypeError):
            property_bone = None
        if not property_bone:
            panel = self.layout.column()
            panel.alert = True
            panel.label(text="Your property posebone is not existing", icon="ERROR")
            panel.prop(context.active_object.data, '["prop_posebone_name"]', text="Prop bone")
            return None

        collections_list = get_bone_collections_list(armature)

        parts = []
        for i in collections_list:
            part = i.split("_")[0].split(".")[0]
            if part not in parts:
                parts.append(part)

        collections_str = []
        for i in parts:
            for j in collections_list:
                if j.startswith(i) and j not in collections_str:
                    side = j.split(".")[-1]
                    if side == "L":
                        collections_str.append(j)
                        if j.replace(".L", ".R") in collections_list:
                            collections_str.append(j.replace(".L", ".R"))
                        else:
                            collections_str.append(j.replace(".L", ".Z"))
                    elif side == "R":
                        if j.replace(".R", ".L") in collections_list:
                            collections_str.append(j.replace(".R", ".L"))
                        else:
                            collections_str.append(j.replace(".R", ".X"))
                        collections_str.append(j)
                    else:
                        collections_str.append(j)

        collections_str = "\n" + "\n".join(collections_str)

        # Parse les collections
        pattern = re.compile(
            r"^([A-Z]+)_?([A-Z0-9_]+)?(.[LMRXYZ])?.?(\d)?(PROP)?$",
            re.MULTILINE,
        )
        matches = pattern.finditer(collections_str)

        collections_data = []
        for match in matches:
            col_name = match.group(0)
            empty = match.group(3) == ".X" or match.group(3) == ".Y" or match.group(3) == ".Z"
            if col_name in armature.data.collections or empty:
                col = None if empty else armature.data.collections[col_name]
                collections_data.append(
                    {
                        "collection": col,
                        "part": match.group(1),
                        "sub_part": match.group(2),
                        "side": match.group(3),
                        "custom_side": match.group(4),
                        "is_prop": match.group(5) == "PROP",
                    }
                )
        boxes_data = [[]]
        index = 0
        for i in collections_data:
            if boxes_data == [[]] or boxes_data[index][0]["part"] == i["part"]:
                boxes_data[index].append(i)
            else:
                boxes_data.append([])
                index += 1
                boxes_data[index].append(i)

        layout = self.layout
        panel = layout.column()

        # Header avec toggle global
        self._draw_header(context, panel, armature, rig_id, collections_data)
        panel.separator(type="LINE", factor=0.2)

        # Dessine chaque groupe
        any_solo = any(
            [c["collection"].is_solo if c["collection"] else False for c in sum(boxes_data, [])]
        )
        for b in boxes_data:
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

    def _draw_header(self, context, panel, armature, rig_id, collections_data):
        """Dessine l'en-tête avec les toggles globaux."""
        title = panel.row()

        # Toggle visibilité de tous les controllers
        any_visible = any(
            col.is_visible
            for col in armature.data.collections
            if not col.name.endswith(".PROP") and col.name.isupper()
        )
        icon = "HIDE_OFF" if any_visible else "HIDE_ON"
        op = title.operator(
            "rigui.toggle_controllers",
            emboss=False,
            text="",
            icon=icon,
        )
        part_param = [dict(i) for i in collections_data]
        for i in reversed(part_param):
            if i["collection"]:
                i["armature"] = i["collection"].id_data.name
                i["collection"] = i["collection"].name
            else:
                part_param.remove(i)

        part_param = (
            str(part_param)
            .replace("'", '"')
            .replace("False", "false")
            .replace("True", "true")
            .replace("None", "null")
        )
        op.parts = part_param

        # Toggle expand/collapse de toutes les boxes
        # Vérifie si au moins une box est expanded
        parts = set(d["part"] for d in collections_data)
        any_expanded = any(
            get_box_expanded(context.scene, rig_id, f"ui_ctrl_{part}") for part in parts
        )
        icon = "DOWNARROW_HLT" if any_expanded else "RIGHTARROW"
        op = title.operator(
            "rigui.toggle_all_boxes",
            emboss=False,
            text="",
            icon=icon,
        )
        op.rig_id = rig_id
        op.prefix = "ui_ctrl_"
        op.parts = ",".join(parts)

        # Titre
        title_txt = title.row()
        title_txt.alert = True
        title_txt.alignment = "LEFT"
        title_txt.label(text="CONTROLLERS")

    def _draw_group(self, context, panel, armature, rig_id, property_bone, box_data, any_solo):
        box = panel.column(align=True)
        expanded = get_box_expanded(context.scene, rig_id, f"ui_ctrl_{box_data[0]['part']}")
        any_in = any([c["collection"].is_solo if c["collection"] else False for c in box_data])
        if any_solo and not any_in:
            box.active = False

        self._draw_group_header(
            context,
            box,
            rig_id,
            box_data,
        )
        if expanded:
            self._draw_group_content(box, property_bone, box_data)
        return box

    def _draw_group_content(self, box, property_bone, box_data):
        col_index = 0

        for r in box_data:
            collection, part, sub_part, side, custom_side, is_prop = (
                r["collection"],
                r["part"],
                r["sub_part"],
                r["side"],
                r["custom_side"],
                r["is_prop"],
            )
            if is_prop:
                box.separator(factor=0.25)
                box_line = box.row(align=True)
                for prop in property_bone.keys():
                    if prop.startswith(f"{part}_{sub_part}"):
                        box_line.prop(
                            property_bone,
                            f'["{prop}"]',
                            text=f"{sub_part} ",
                            slider=True,
                        )
                box.separator(factor=0.25)
                continue

            # Gestion des colonnes selon le côté
            elif (side is None or side == ".L" or side == ".X") and custom_side is None:
                box_line = box.row(align=True)
                col_index = 0
            elif custom_side is not None:
                if col_index >= int(custom_side):
                    box_line = box.row(align=True)
                    col_index = 0
                else:
                    col_index += 1

            # Affiche le toggle de visibilité
            name = sub_part if sub_part else "MAIN"

            if not collection:
                box_line.label()
            else:
                box_line.prop(collection, "is_visible", toggle=True, text=name)

    def _draw_group_header(
        self,
        context,
        box,
        rig_id,
        part,
    ):
        """Dessine l'en-tête d'un groupe de collections."""
        title_line = box.row(align=True)
        title_line.scale_y = 1.2
        # title_line.scale_y = 0.6

        title_eye = title_line.row(align=True)
        title_eye.alignment = "EXPAND"

        title_collapse = title_line.row(align=True)
        title_collapse.alignment = "RIGHT"

        # Groupe avec plusieurs collections
        x = r"""
        pattern = rf"^({part})_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?$"
        part_collections = [
            m.group(0) for m in re.compile(pattern, re.MULTILINE).finditer(collections_str)
        ]
        any_visible = any(
            col.is_visible for col in armature.data.collections if col.name in part_collections
        )"""
        any_visible = True

        # LECTURE de l'état (safe dans draw)
        expanded = get_box_expanded(context.scene, rig_id, f"ui_ctrl_{part[0]['part']}")
        icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"

        # ÉCRITURE via operator (pas de prop sur box_state !)
        op = title_collapse.operator(
            "rigui.toggle_box",
            emboss=True,
            text="",
            icon=icon,
        )
        op.rig_id = rig_id
        op.box_name = f"ui_ctrl_{part[0]['part']}"

        # Toggle visibilité des collections du groupe
        op = title_eye.operator(
            "rigui.toggle_controllers",
            emboss=True,
            text=part[0]["part"],
            icon="HIDE_OFF" if any_visible else "HIDE_ON",
        )

        part_param = [dict(i) for i in part]
        for i in reversed(part_param):
            if i["collection"]:
                i["armature"] = i["collection"].id_data.name
                i["collection"] = i["collection"].name
            else:
                part_param.remove(i)

        part_param = (
            str(part_param)
            .replace("'", '"')
            .replace("False", "false")
            .replace("True", "true")
            .replace("None", "null")
        )
        op.parts = str(part_param)


# Classes à enregistrer
classes = (RIGUI_PT_rigui,)
