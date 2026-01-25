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
            bone = armature.pose.bones[b_name]
        except (AttributeError, KeyError, TypeError):
            bone = None
        if not bone:
            panel = self.layout.column()
            panel.alert = True
            panel.label(text="Your property posebone is not existing", icon="ERROR")
            panel.prop(context.active_object.data, '["prop_posebone_name"]', text="Prop bone")
            return None

        property_bone = armature.pose.bones["PROPERTIES"]
        collections_str = get_bone_collections_list(armature)

        # Parse les collections
        pattern = re.compile(
            r"^([A-Z]+)_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?(PROP)?$",
            re.MULTILINE,
        )
        matches = pattern.finditer(collections_str)

        collections_data = []
        for match in matches:
            col_name = match.group(0)
            if col_name in armature.data.collections:
                collections_data.append(
                    {
                        "collection": armature.data.collections[col_name],
                        "part": match.group(1),
                        "sub_part": match.group(2),
                        "side": match.group(3),
                        "custom_side": match.group(4),
                        "is_prop": match.group(5) == "PROP",
                    }
                )

        layout = self.layout
        panel = layout.column()

        # Header avec toggle global
        self._draw_header(context, panel, armature, rig_id, collections_data)
        panel.separator(type="LINE", factor=0.2)

        # Dessine chaque groupe
        self._draw_collections(
            context,
            panel,
            armature,
            rig_id,
            property_bone,
            collections_data,
            collections_str,
        )

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
        title.operator(
            "rigui.toggle_controllers",
            emboss=False,
            text="",
            icon=icon,
        ).param = "all"

        # Toggle expand/collapse de toutes les boxes
        # Vérifie si au moins une box est expanded
        parts = set(d["part"] for d in collections_data)
        all_parts = [i["part"] for i in collections_data]
        multi_parts = list(set([i for i in all_parts if all_parts.count(i) > 1]))
        any_expanded = any(
            get_box_expanded(context.scene, rig_id, f"ui_ctrl_{part}") for part in multi_parts
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
        op.parts = ",".join(multi_parts)

        # Titre
        title_txt = title.row()
        title_txt.alert = True
        title_txt.alignment = "LEFT"
        title_txt.label(text="CONTROLLERS")

    def _draw_collections(
        self,
        context,
        panel,
        armature,
        rig_id,
        property_bone,
        collections_data,
        collections_str,
    ):
        """Dessine les collections groupées par partie du corps."""
        current_part = None
        box = None
        box_line = None
        col_index = 0
        is_collapsible = False

        for i, data in enumerate(collections_data):
            collection = data["collection"]
            part = data["part"]
            sub_part = data["sub_part"]
            side = data["side"]
            custom_side = data["custom_side"]
            is_prop = data["is_prop"]

            # Nouveau groupe ?
            if current_part != part:
                # Détermine si ce groupe a plusieurs éléments
                try:
                    next_same_part = collections_data[i + 1]["part"] == part
                except IndexError:
                    next_same_part = False

                is_collapsible = next_same_part
                panel.separator(factor=1)
                box = panel.row().column(align=True)

                self._draw_group_header(
                    context,
                    box,
                    armature,
                    rig_id,
                    collection,
                    part,
                    is_collapsible,
                    collections_str,
                )

                # Espace après le header si expanded
                expanded = get_box_expanded(context.scene, rig_id, f"ui_ctrl_{part}")
                if is_collapsible and expanded:
                    box.separator(factor=0.5)

                current_part = part
                col_index = 0

            # Contenu du groupe (si collapsible et expanded)
            expanded = get_box_expanded(context.scene, rig_id, f"ui_ctrl_{part}")
            if is_collapsible and expanded:
                box_line, col_index = self._draw_collection_item(
                    box,
                    box_line,
                    armature,
                    property_bone,
                    collection,
                    part,
                    sub_part,
                    side,
                    custom_side,
                    is_prop,
                    col_index,
                )

    def _draw_group_header(
        self,
        context,
        box,
        armature,
        rig_id,
        collection,
        part,
        is_collapsible,
        collections_str,
    ):
        """Dessine l'en-tête d'un groupe de collections."""
        title_line = box.row().split(factor=0.9)
        title_line.scale_y = 0.6

        title_eye = title_line.row()
        title_eye.alignment = "LEFT"
        title_collapse = title_eye.row()
        title_collapse.alignment = "RIGHT"

        if not is_collapsible:
            # Groupe simple (une seule collection) - pas de toggle expand
            title_eye = title_eye.row()
            title_eye.active = True
            title_eye.label(text=collection.name, icon="REMOVE")
            title_collapse.prop(
                collection,
                "is_visible",
                text="",
                icon="HIDE_OFF" if collection.is_visible else "HIDE_ON",
                emboss=False,
            )
        else:
            # Groupe avec plusieurs collections
            pattern = rf"^({part})_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?$"
            part_collections = [
                m.group(0) for m in re.compile(pattern, re.MULTILINE).finditer(collections_str)
            ]
            any_visible = any(
                col.is_visible for col in armature.data.collections if col.name in part_collections
            )

            # LECTURE de l'état (safe dans draw)
            expanded = get_box_expanded(context.scene, rig_id, f"ui_ctrl_{part}")
            icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"

            # ÉCRITURE via operator (pas de prop sur box_state !)
            op = title_eye.operator(
                "rigui.toggle_box",
                emboss=False,
                text=part,
                icon=icon,
            )
            op.rig_id = rig_id
            op.box_name = f"ui_ctrl_{part}"

            # Toggle visibilité des collections du groupe
            title_collapse.operator(
                "rigui.toggle_controllers",
                emboss=False,
                text="",
                icon="HIDE_OFF" if any_visible else "HIDE_ON",
            ).param = part

    def _draw_collection_item(
        self,
        box,
        box_line,
        armature,
        property_bone,
        collection,
        part,
        sub_part,
        side,
        custom_side,
        is_prop,
        col_index,
    ):
        """Dessine un élément de collection."""
        # Propriété custom ?
        if is_prop:
            box.separator(factor=0.25)
            row = box.row(align=True)
            for prop in property_bone.keys():
                if prop.startswith(f"{part}_{sub_part}"):
                    row.prop(
                        property_bone,
                        f'["{prop}"]',
                        text=f"{sub_part} ",
                        slider=True,
                    )
            box.separator(factor=0.25)
            return box_line, -1

        # Gestion des colonnes selon le côté
        if side is None and custom_side is None:
            box_line = box.row(align=True)
            col_index = 0
        elif custom_side is not None:
            if col_index >= int(custom_side):
                box_line = box.row(align=True)
                col_index = 0
            else:
                col_index += 1
        elif side == ".L":
            box_line = box.row(align=True)
            col_index = 0
        elif side == ".R":
            col_index = 1

        # Affiche le toggle de visibilité
        name = sub_part if sub_part else "MAIN"

        if side is None:
            box_line.prop(collection, "is_visible", toggle=True, text=name)
        elif side == ".L":
            box_line.prop(collection, "is_visible", toggle=True, text=name)
            # Cherche le côté droit correspondant
            right_name = collection.name[:-1] + "R"
            if right_name in armature.data.collections:
                box_line.prop(
                    armature.data.collections[right_name],
                    "is_visible",
                    toggle=True,
                    text=name,
                )
            else:
                box_line.label()
        elif side == ".R":
            # Vérifie si le côté gauche existe
            left_name = collection.name[:-1] + "L"
            if left_name not in armature.data.collections:
                box_line = box.row(align=True)
                box_line.label()
                box_line.prop(collection, "is_visible", toggle=True, text=name)

        return box_line, col_index


# Classes à enregistrer
classes = (RIGUI_PT_rigui,)
