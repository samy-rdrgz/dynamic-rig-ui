import bpy
import re
from mathutils import Euler, Matrix, Vector, Quaternion

# -- RIG VARIABLES --
  # -- Set a rig ID in your armature custom properties using a string
rig_id = "Input_rig_id"
rig_name = "Input_rig_name"
property_bone = "Input_property_bone"

no_body_prefix = [Input_no_body_prefix]
prefix_order = ["ROOT","BODY","CLOTHES","HEAD","HAIR","NECK","SPINE","CHEST","ARM","HAND","PELVIS","LEG","FOOT"]

leg_switch_kin='LEG_FK_IK'
leg_fk = {  'target_C':'MCH_FK_IK_FOOT_IK',
            'target_pole':'MCH_FK_IK_LEG_IK_POLE',
            'A':'LEG_FK',
            'B':'SHIN_FK',
            'C':'FOOT_FK' }
leg_ik = {  'C':'FOOT_IK',
            'pole':'LEG_IK_POLE',
            'target_A':'MCH_LEG_IK',
            'target_B':'MCH_SHIN_IK',
            'target_C':'MCH_FOOT_IK' }
            
arm_switch_kin='ARM_FK_IK'
arm_fk = {  'target_C':'MCH_FK_IK_HAND_IK',
            'target_pole':'MCH_FK_IK_ARM_IK_POLE',
            'A':'ARM_FK',
            'B':'FOREARM_FK',
            'C':'HAND_FK' }          
arm_ik = {  'C':'HAND_IK',
            'pole':'ARM_IK_POLE',
            'target_A':'MCH_ARM_IK',
            'target_B':'MCH_FOREARM_IK',
            'target_C':'MCH_HAND_IK' }

ratio=.6
active_rig = None

# -- MAIN PANEL --
class RIG_UI_PT_main(bpy.types.Panel):
    bl_category = 'Item'
    bl_label = "Bot Anim tools"
    bl_idname = f"{rig_name.lower()}_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        if bpy.context.active_object.type == "ARMATURE" :
            active_rig = bpy.context.active_object
        elif bpy.context.active_object.parent.type == "ARMATURE" :
            active_rig = bpy.context.active_object.parent
        else :
            active_rig = None
        try:
            return (active_rig.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
        
    def draw(self, context):
        layout = self.layout

# -- FONCTIONS --
def show_messagebox(title = "Info", lines=[], icon = 'INFO'):
    """Affiche unne pop up de retour utilisateur / d'erreur.

    Args:
        title (_str_): Titre (premiere ligne) du message.
        lines (_list_): Liste de chaines de characteres structurant les differentes lignes du message.
        icon (_icon_): str id d'une icon Blender
    """
    def draw(self, context):
        layout = self.layout
        for n in lines:
            layout.label(text=n)
    
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

class WM_OT_text_popup(bpy.types.Operator):
    bl_idname = "wm.text_popup"
    bl_label = "Information"
    
    icon: bpy.props.StringProperty(default="INFO")
    title: bpy.props.StringProperty(default="INFO")
    message: bpy.props.StringProperty(default="")

    def draw(self, context):
        layout = self.layout.column()
        layout.scale_y = .7
        layout.label(text=self.title.upper(),icon=self.valid_icon())
        layout.separator(type='LINE')
        
        for line in self.message.split('\n'):
            layout.label(text=line)

    def invoke(self, context, event):
        max_line_length = max(len(line) for line in self.message.split('\n'))*8
        title_line_length = len(self.title)*9+23
        width = min(max(max_line_length,title_line_length),300)  # largeur en pixels
        return context.window_manager.invoke_popup(self, width=width)

    def execute(self, context):
        return {'FINISHED'}
    
    def valid_icon(self):
        valid_icons = bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items.keys()
        return self.icon if self.icon in valid_icons else 'INFO'

# -- USER INPUTS --
def usabled_panels():
    items=[ ('RIG_UI_PT_rigui','Ctrls','','RESTRICT_SELECT_OFF',0), 
            ('RIG_UI_PT_customprops','Props','','OPTIONS',1),
            ('RIG_UI_PT_masks','Masks','','HIDE_OFF',2),
            ('RIG_UI_PT_tools','Tools','','TOOL_SETTINGS',3),
            ('N','-','','PANEL_CLOSE',4)]
    return items

class RIG_UI_PT_variables(bpy.types.PropertyGroup):
    """Creation des variables stockant les inputs utilisateurs.
    """
    #(identifier, name, description, icon, number) 

    p_A: bpy.props.EnumProperty(
            name="",
            description="Panels' order",
            items=usabled_panels(),
            default='RIG_UI_PT_rigui')
    p_B: bpy.props.EnumProperty(
            name="",
            description="Panels' order",
            items=usabled_panels(),
            default='RIG_UI_PT_customprops')
    p_C: bpy.props.EnumProperty(
            name="",
            description="Panels' order",
            items=usabled_panels(),
            default='RIG_UI_PT_tools')
    p_D: bpy.props.EnumProperty(
            name="",
            description="Panels' order",
            items=usabled_panels(),
            default='RIG_UI_PT_masks')

# -- CONTROLLERS' MAIN PANEL --
class RIG_UI_OT_toggle_controllers(bpy.types.Operator):
    bl_idname = f'{rig_name.lower()}.toggle_controllers'
    bl_label = ""
    bl_description = "Toggle visibility of severals bone collection"
    bl_options = {'UNDO', 'INTERNAL'}
    
    param: bpy.props.StringProperty(name="prefix-toggle")
    
    def execute(self, context):
        param = self.param
        active_rig = bpy.context.active_object if bpy.context.active_object.type == "ARMATURE" else bpy.context.active_object.parent 
        property_bone = active_rig.pose.bones["PROPERTIES"]
        list_collections='\n'+'\n'.join([i.name for i in bpy.data.armatures[active_rig.data.name].collections])
        if param == 'all' :
            collections = [bpy.data.armatures[active_rig.data.name].collections[i.group(0)] for i in re.compile(fr'^([A-Z]+)_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?$', re.MULTILINE).finditer(list_collections)]
        else :
            collections = [bpy.data.armatures[active_rig.data.name].collections[i.group(0)] for i in re.compile(fr'^({param})_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?$', re.MULTILINE).finditer(list_collections)]
        
        ctrl_visibility = [i.is_visible for i in collections]
        toggle = False if any(ctrl_visibility) else True

        for i in collections :
            i.is_visible=toggle
        return {"FINISHED"}

class RIG_UI_OT_toggle_boxes(bpy.types.Operator):
    bl_idname = f'{rig_name.lower()}.toggle_boxes'
    bl_label = ""
    bl_description = "Toggle collapsible state of severals boxes"
    bl_options = {'UNDO', 'INTERNAL'}
    
    param: bpy.props.StringProperty(name="prefix-toggle")
    
    def execute(self, context):
        param = self.param
        
        active_rig = bpy.context.active_object if bpy.context.active_object.type == "ARMATURE" else bpy.context.active_object.parent
        boxes=[i for i in list(active_rig.data.keys()) if i.startswith(param)]
        boxes_states=[active_rig.data[i] for i in boxes]
        
        toggle = False if any(boxes_states) else True
        
        for i in boxes :
            active_rig.data[i]=toggle

        return {"FINISHED"}

class RIG_UI_PT_rigui(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Rig UI"
    bl_idname = f'{rig_name.lower()}_PT_rigui'
    bl_parent_id = f'{rig_name.lower()}_PT_main'
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(self, context):
        if bpy.context.active_object.type == "ARMATURE" :
            active_rig = bpy.context.active_object
        else :
            active_rig = None
        try:
            return (active_rig.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        active_rig = bpy.context.active_object if bpy.context.active_object.type == "ARMATURE" else bpy.context.active_object.parent 
        property_bone = active_rig.pose.bones["PROPERTIES"]
        list_collections='\n'+'\n'.join([i.name for i in bpy.data.armatures[active_rig.data.name].collections])
        p=re.compile('^([A-Z]+)_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?(PROP)?$', re.MULTILINE)
        controllers_collections = p.finditer(list_collections)
        collections = [(bpy.data.armatures[active_rig.data.name].collections[i.group(0)],i.group(1),i.group(2),i.group(3),i.group(4),i.group(5)) for i in controllers_collections]

        layout = self.layout
        panel = layout.box().column()
        panel.scale_y=1
        
        collapsible_box = False
        box_title = 'title'
        need_box = None
        col_index = 0

        title=panel.row()
        title.active=False
        icon = 'HIDE_OFF' if any([i.is_visible for i in bpy.data.armatures[active_rig.data.name].collections if i.name.endswith('.PROP')==False and i.name.isupper()] ) else 'HIDE_ON'
        title.operator(f'{rig_name.lower()}.toggle_controllers', emboss=False, text="", icon=icon).param = 'all'
        icon = 'RIGHTARROW' if any([active_rig.data[i] for i in list(active_rig.data.keys()) if i.startswith('ui_ctrl_')])==False else 'DOWNARROW_HLT'
        title.operator(f'{rig_name.lower()}.toggle_boxes', emboss=False, text="", icon=icon).param = f'ui_ctrl_'
        title_txt=title.row()
        title_txt.alert=True
        title_txt.alignment="LEFT"
        title_txt.label(text='CONTROLLERS')
        panel.separator(type='LINE', factor=.2)
        
        for i, (collection, part, sub_part, side, custom_side, is_prop) in enumerate(collections, start=0):
            if box_title != part:
                try : need_box = part == collections [i+1][1]
                except(IndexError): need_box = False
                if need_box :
                    collapsible_box = True
                else : 
                    collapsible_box = False
                panel.separator( factor=1)
                box=panel.row().column(align =True)
                
                title_line=box.row().split(factor=.9)
                title_line.scale_y=.6
                title_eye = title_line.row()
                title_eye.alignment = 'EXPAND'
                title_collapse = title_eye.row()
                title_collapse.alignment = 'RIGHT'
                
                if not collapsible_box :
                    title_eye=title_eye.row()
                    title_eye.active=True
                    title_eye.prop(active_rig.data, f'["ui_ctrl_{part}"]', emboss=False, text=collection.name, icon='REMOVE')
                    title_collapse.prop(collection, 'is_visible', text="", icon='HIDE_ON' if collection.is_visible==False else 'HIDE_OFF', emboss=False)
                
                else :
                    part_collections=[i.group(0) for i in re.compile(fr'^({part})_?([A-Z0-9_]+)?(.[LMR])?.?(\d)?$', re.MULTILINE).finditer(list_collections)]
                    toggle = any([i.is_visible for i in bpy.data.armatures[active_rig.data.name].collections if i.name in part_collections])
                    icon = 'RIGHTARROW'if active_rig.data["ui_ctrl_"+part]==False else 'DOWNARROW_HLT'
                    title_eye.prop(active_rig.data, f'["ui_ctrl_{part}"]', emboss=False, text=part, icon=icon)
                    title_collapse.operator(f'{rig_name.lower()}.toggle_controllers', emboss=False, text="", icon='HIDE_OFF'if toggle else 'HIDE_ON').param = f'{part}'
                
                if active_rig.data["ui_ctrl_"+part] and collapsible_box:
                    box.separator(factor=.5)
                    
            box_title = part
            if collapsible_box and active_rig.data["ui_ctrl_"+part] :
                if is_prop == "PROP" :
                    box.separator(factor=.25)
                    box_line = box.row(align =True)
                    col_index=-1
                    for prop in [j for j in property_bone.keys() if j.startswith(f'{part}_{sub_part}')]:
                        box_line.prop(property_bone, str('["')+prop+str('"]'), text = f'{sub_part} ', slider=True)
                        col_index+=1
                    box.separator(factor=.25)
                elif side is None and custom_side is None:
                    box_line = box.row(align =True)
                    col_index=0
                elif custom_side is not None:
                    if col_index >= int(custom_side):
                        box_line = box.row(align =True)
                        col_index=0
                    else :
                        col_index+=1
                elif side == ".L" :
                    box_line = box.row(align =True)
                    col_index=0
                elif side == ".R" :
                    col_index=1
                
                if is_prop != "PROP" and side == None:
                    name = sub_part if sub_part!=None else "MAIN"
                    box_line.prop(collection, 'is_visible', toggle=True, text=name)
                elif side != None:
                    if side == ".L" :
                        name = sub_part if sub_part!=None else "MAIN"
                        box_line.prop(collection, 'is_visible', toggle=True, text=name)
                        if collection.name[:-1]+"R" in bpy.data.armatures[active_rig.data.name].collections:
                            box_line.prop(bpy.data.armatures[active_rig.data.name].collections[collection.name[:-1]+"R"], 'is_visible', toggle=True, text=name)
                        else :
                            box_line.label()
                    elif side == ".R":
                        if not collection.name[:-1]+"L" in bpy.data.armatures[active_rig.data.name].collections:
                            box_line = box.row(align =True)
                            box_line.label()
                            name = sub_part if sub_part!=None else "MAIN"
                            box_line.prop(collection, 'is_visible', toggle=True, text=name)
                             
# -- CUSTOM PROPS' PANEL --
class RIG_UI_PT_customprops(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Properties"
    bl_idname = f'{rig_name.lower()}_PT_customprops'
    bl_parent_id = f'{rig_name.lower()}_PT_main'
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(self, context):
        if bpy.context.active_object.type == "ARMATURE" :
            active_rig = bpy.context.active_object
        else :
            active_rig = None
        try:
            return (active_rig.data.get("rig_id") == rig_id and bpy.context.object.mode=='POSE')
        except (AttributeError, KeyError, TypeError):
            return False
    
    def draw(self, context):
        ratio=.45
        active_rig = bpy.context.active_object if bpy.context.active_object.type == "ARMATURE" else bpy.context.active_object.parent
        bone = active_rig.pose.bones["PROPERTIES"]
        custom_props = list(bone.keys())
        custom_props = sorted(custom_props, key=str.lower)
        
        order = ["ROOT","HEAD","NECK","BODY","SPINE","CHEST","ARM","HAND","LEG","FOOT"] + no_body_prefix
        ordered = []
        for i in order :
            for j in list(custom_props) : 
                if str(j).startswith(i) :
                    ordered.append(j)
                    custom_props.remove(j)

        custom_props = ordered + custom_props
        list_props='\n'+'\n'.join(custom_props)
        p=re.compile('^([A-Z]+)_([A-Z0-9_]+)(.([LMR]|(\d)))?$', re.MULTILINE)
        props_collections = p.finditer(list_props)
        props = [(i.group(0),i.group(1),i.group(2),i.group(4)) for i in props_collections]
        props_names = [(i.group(0)) for i in p.finditer(list_props)]

        separator=.35
        layout = self.layout
        panel = layout.box().column()
        
        bloc = panel.row()
        bloc.active=False
        row = bloc.split(align=True, factor=ratio)
        row1=row.row()
        row1.alignment = 'LEFT'
        icon = 'RIGHTARROW' if any([active_rig.data[i] for i in list(active_rig.data.keys()) if i.startswith('ui_prop_')])==False else 'DOWNARROW_HLT'
        row1.operator(f'{rig_name.lower()}.toggle_boxes', emboss=False, text="", icon=icon).param = f'ui_prop_'
        row1.alert=True
        row1.label(text="Properties", translate=False)
        row = row.row()
        row.alert=False
        row.active=False
        row.label(text=".Left", translate=False)
        row.label(text=".Right", translate=False)

        box_title = 'title'
        col_index = 10

        for i, (prop_name, part, sub_part, side) in enumerate(props,0):
            empty_space = 0
 
            if box_title != part:
                panel.separator(factor=1, type='SPACE')
                bloc = panel.row().column(align=True)
                titre = bloc.row()
                titre.scale_y = .6
                titre.alignment = 'EXPAND'
                icon = 'RIGHTARROW'if active_rig.data["ui_prop_"+part]==False else 'DOWNARROW_HLT'
                titre.prop(active_rig.data, f'["ui_prop_{part}"]', emboss=False, text=part, icon=icon)
                
                box_title = part
                num_col=10
                if active_rig.data["ui_prop_"+part] :
                    bloc.separator(factor=.4)
                    
            if active_rig.data["ui_prop_"+part] :
                
                if side is None :
                    pass            
                elif side == "L" :
                    num_col=0
                    if not prop_name.replace(".L",".R") in props_names:
                        empty_space=1
                elif side == "R": 
                    if not prop_name.replace(".R",".L") in props_names:
                        empty_space=-1
                        num_col=0
                    else :
                        num_col=1
                
                elif side.isdigit():
                    num_col=int(side)
                
                if num_col == 0 or side is None:
                    bloc.separator(factor=.25)
                    b_row = bloc.row(align=True)
                    split = b_row.split(align=True, factor=ratio)
                    split.alignment = 'RIGHT'
                    split.label(text=sub_part, translate=False)
                    b_row = split.row(align=True)
                    
                    if empty_space == -1 :
                        b_row.label(text='')
                    b_row.prop(bone, f'["{prop_name}"]', text = "", slider=True)
                    if empty_space == 1 :
                        b_row.label(text='')
                    
                elif num_col > 0 :
                    b_row.prop(bone, f'["{prop_name}"]', text = "", slider=True)
                
                num_col=10

# -- MASKS' PANEL --
class RIG_UI_OT_toggle_masks(bpy.types.Operator):
    bl_idname = f'{rig_name.lower()}.toggle_masks'
    bl_label = ""
    bl_description = "Toggle visibility of severals masks modifiers."
    bl_options = {'UNDO', 'INTERNAL'}
    
    param: bpy.props.StringProperty(name="mask vertex group name")
    
    def execute(self, context):
        name = self.param
        
        active_rig = bpy.context.active_object if bpy.context.active_object.type == "ARMATURE" else bpy.context.active_object.parent
        meshes_objs = [i.name for i in active_rig.children]
        modifiers = sum([list(bpy.data.objects[i].modifiers) for i in meshes_objs], [])
        masksModifiers=[i for i in modifiers if i.type=='MASK']
        
        if name !='all':
            masksModifiers=[i for i in masksModifiers if i.vertex_group==name]
        else :
            masksModifiers=[i for i in masksModifiers if i.vertex_group.startswith('MASK_')]
            
        mask_visibility = [i.show_viewport for i in masksModifiers]
        toggle = False if all(mask_visibility) else True
        
        for i in masksModifiers :
            i.show_viewport=toggle
        
        return {"FINISHED"}

class RIG_UI_PT_masks(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Masks"
    bl_idname = f'{rig_name.lower()}_PT_masks'
    bl_parent_id = f'{rig_name.lower()}_PT_main'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        active_rig = bpy.context.active_object if bpy.context.active_object.type == "ARMATURE" else bpy.context.active_object.parent
        meshes_objs = [i.name for i in active_rig.children]
        modifiers = sum([list(bpy.data.objects[i].modifiers) for i in meshes_objs], [])
        masksModifiers=sorted([i for i in modifiers if i.type=='MASK'], key=lambda name: name.vertex_group)
        masksModifiers_names = [i.vertex_group for i in masksModifiers]
        order = prefix_order + no_body_prefix
        ordered = []
        for i in order :
            for j in list(masksModifiers): 
                if j.vertex_group.split("_")[1].startswith(i):
                    ordered.append(j)
                    masksModifiers.remove(j)
                    
        masksModifiers = ordered + masksModifiers
        masksModifiers_names = [i.vertex_group for i in masksModifiers]

        p=re.compile('^(MASK_)([A-Z0-9_]+)(.([LMR]|(\d)))?$', re.MULTILINE)
        masks = [(i,list(p.finditer(i.vertex_group))[0].group(0),list(p.finditer(i.vertex_group))[0].group(2),list(p.finditer(i.vertex_group))[0].group(4)) for i in masksModifiers]
        masks_names = [i[1] for i in masks]
        mask_nb = {'name' : 0}
        for i in masks_names :
            mask_nb[i] = masks_names.count(i)
        
        layout = self.layout
        col = layout.column()
        box = layout.box()
        col = box.column(align=True)
        col.scale_y=.9
        
        under_line=False
        row = col.row().split(factor=ratio)
        row.alignment='RIGHT'
        row.alert = True
        row.label(text='ALL MASKS', translate=False)
        row.alert = False
        row = row.row()
        row.alignment='RIGHT'
        row.separator(factor=1.14)
        toggle = all([i[0].show_viewport for i in masks if i[0].vertex_group.startswith('MASK_')])
        row.operator(f'{rig_name.lower()}.toggle_masks', emboss=False, text="", icon='HIDE_ON' if toggle else 'HIDE_OFF').param = 'all'
        row.separator(factor=1.14)
        col.separator(type='LINE')
        for i, (modifier, vg, part, side) in enumerate(masks,0) :
            if part in no_body_prefix and not(under_line) :
                col.separator(type='LINE')
                under_line=True
            if mask_nb[vg]>0 :
                empty_space=0
                num_col =0
                if side is None :
                    num_col =0
                    empty_space=2
                elif side == "L":
                    num_col=0
                    if not vg.replace(".L",".R") in masksModifiers_names :
                        empty_space=1
                        
                elif side == "R" :
                    if not vg.replace(".R",".L") in masksModifiers_names :
                        empty_space=-1
                        num_col = 0
                    else :
                        num_col = 1
                        
                if num_col == 0 :
                    row = col.row().split(factor=ratio)
                    row.alignment='RIGHT'
                    row.label(text=part, translate=False)
                    row = row.row()
                    row.alignment='RIGHT'
                if empty_space == -1 : 
                    row.label(text="",icon='PANEL_CLOSE', translate=False)
                if mask_nb[vg]>1 :
                    if empty_space==2:
                        row.separator(factor=1.14)
                    toggle = any([i.show_viewport for i in masksModifiers if i.vertex_group==vg])
                    row.operator(f'{rig_name.lower()}.toggle_masks', emboss=False, text="", icon='HIDE_ON' if toggle else 'HIDE_OFF').param = f'{vg}'
                    mask_nb[vg]=0
                else :
                    if empty_space==2:
                        row.separator(factor=1.14)
                    row.prop(modifier, 'show_viewport', text="", icon='HIDE_ON', invert_checkbox=True, emboss=False)
                if empty_space == 1 : 
                    row.label(text="",icon='PANEL_CLOSE', translate=False)
                elif empty_space == 2 :
                    row.separator(factor=1.14)

# -- ANIMATION TOOLS' PANEL --
def get_matrix(armature, source_bone, target_bone):
    # returns final world matrix accounting for offset in rest pose
    # rest post matrices
    source_bone_rest_matrix = source_bone.bone.matrix_local
    target_bone_rest_matrix = target_bone.bone.matrix_local
    # rest pose offset matrix
    offset_matrix = source_bone_rest_matrix.inverted() @ target_bone_rest_matrix
    # world_space_matrices
    source_world_matrix = source_bone.matrix
    #world space matrix
    matrix_final =  source_world_matrix @ offset_matrix
    return matrix_final

class RIG_UI_OT_snap_opposite_kinematic(bpy.types.Operator):
    # -- We create MCH bones that are children of the FK chain to snap our IK controllers to
    bl_idname = f'{rig_name.lower()}.snap_opposite_kinematic'
    bl_label = ""
    bl_description = "Snap limb on opposite kinematic"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
    
    def execute(self, context):
        side = bpy.context.active_pose_bone.name.split('.')[1]
        active_bone=bpy.context.active_pose_bone.name.split('.')[0]
        
        if active_bone in leg_ik.values() or active_bone in leg_fk.values():
            fk,ik,limb,prop=(leg_fk,leg_ik,'LEG',leg_switch_kin)
            kinematic_dir = "ik snap on fk" if active_bone in leg_ik.values() else "fk snap on ik"
                
        elif active_bone in arm_ik.values() or active_bone in arm_fk.values():
            fk,ik,limb,prop=(arm_fk,arm_ik,limb,prop)
            kinematic_dir = "ik snap on fk" if active_bone in arm_ik.values() else "fk snap on ik"
       
        else :
            bpy.ops.wm.text_popup('INVOKE_DEFAULT', icon="ERROR", title="ERROR", message='Select a controller of a switchable kinematic chain.')
            return {'FINISHED'}
        
        armature = bpy.context.active_object
        pose_bones = armature.pose.bones
        #name of the custom properties bone
        properties = pose_bones['PROPERTIES']
    #------------
        if kinematic_dir == "ik snap on fk": 
          # FK BONES TO SNAP TO
            fk_C = pose_bones[f'{fk["target_C"]}.{side}']
            fk_pole = pose_bones[f'{fk["target_pole"]}.{side}']    
          # IK BONES
            ik_C = pose_bones[f'{ik["C"]}.{side}']
            ik_pole = pose_bones[f'{ik["pole"]}.{side}']
                    
            select_set = (ik_C, ik_pole, properties) 
            
            C_matrix = get_matrix(armature, fk_C, ik_C )
            pole_matrix = get_matrix(armature, fk_pole, ik_pole )
            ik_C.matrix = C_matrix
            bpy.context.view_layer.update()
            ik_pole.matrix = pole_matrix
            bpy.context.view_layer.update()
            properties[f'{prop}.{side}'] = 1 # Switch_mode 
   #------------
        if kinematic_dir == "fk snap on ik":
          # FK BONES
            fk_C = pose_bones[f'{fk["C"]}.{side}']
            fk_B = pose_bones[f'{fk["B"]}.{side}']
            fk_A = pose_bones[f'{fk["A"]}.{side}']          
          # IK BONES TO SNAP TO
            ik_C = pose_bones[f'{ik["target_C"]}.{side}']
            ik_B = pose_bones[f'{ik["target_B"]}.{side}']
            ik_A = pose_bones[f'{ik["target_A"]}.{side}']
                    
            select_set = (fk_C, fk_B, fk_A, properties) 
            
            C_matrix = get_matrix(armature, ik_C, fk_C )
            B_matrix = get_matrix(armature, ik_B, fk_B )
            A_matrix = get_matrix(armature, ik_A, fk_A )
            
            fk_A.matrix = A_matrix
            bpy.context.view_layer.update()
            fk_B.matrix = B_matrix
            bpy.context.view_layer.update()
            fk_C.matrix = C_matrix
            bpy.context.view_layer.update()      
            properties[f'{prop}.{side}'] = 0 # Switch_mode
    #------------
        bpy.ops.pose.select_all(action='DESELECT')
        for pbone in select_set:
            armature.data.bones.active = pbone.bone
            if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                try:
                    bpy.ops.anim.keyframe_insert_menu(type='Available')
                except RuntimeError:
                    self.report({'WARNING'}, f'{pbone.name} has no active keyframes')
                    pass        
        
        bpy.ops.wm.text_popup('INVOKE_DEFAULT', icon="CHECKMARK", title="SWITCH DONE", message=f"{side.replace('L','LEFT').replace('R','RIGHT')} {limb}'s {kinematic_dir}")
        return {'FINISHED'}

class RIG_UI_PT_tools(bpy.types.Panel):
    bl_category = 'Item'
    bl_label = "Snap Utilities"
    bl_idname = f'{rig_name.lower()}_PT_tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = f'{rig_name.lower()}_PT_main'
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(self, context):
        if bpy.context.active_object.type == "ARMATURE" :
            active_rig = bpy.context.active_object
        else :
            active_rig = None
        try:
            return (active_rig.data.get("rig_id") == rig_id and bpy.context.object.mode=='POSE')
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        box = col.box()
        titre = box.column()
        titre.separator(factor=4)
        titre.scale_y =.25
        titre.alert=True
        titre = titre.row()
        titre.alignment = 'CENTER'
        titre.label(text='LIMB KINEMATIC')

        row = box.row()
        row.alignment = 'EXPAND'
        row.enabled = bpy.context.mode=='POSE'
        row.operator(f'{rig_name.lower()}.snap_opposite_kinematic', emboss=True, text="SNAP", icon='SNAP_ON')
        
        col.separator(factor=.5, type='SPACE')

# -- RIG UI SETTINGS PANEL --
class RIG_UI_OT_reload_ui(bpy.types.Operator):
    bl_idname = f'{rig_name.lower()}.reload_ui'
    bl_label = "Reload"
    bl_description = "Reload ui with chosen panels order"
    bl_options = {'UNDO', 'INTERNAL'}
        
    def execute(self, context):
        it=bpy.context.scene.my_inputs
        items={ 'RIG_UI_PT_rigui':RIG_UI_PT_rigui, 
            'RIG_UI_PT_customprops':RIG_UI_PT_customprops,
            'RIG_UI_PT_masks':RIG_UI_PT_masks,
            'RIG_UI_PT_tools':RIG_UI_PT_tools,
            'N':None}
        panels = [RIG_UI_PT_main]
        if items[it.p_A] not in panels :
            panels.append(items[it.p_A])
        if items[it.p_B] not in panels :
            panels.append(items[it.p_B])
        if items[it.p_C] not in panels :
            panels.append(items[it.p_C])
        if items[it.p_D] not in panels :
            panels.append(items[it.p_D])
        panels.append(RIG_UI_PT_settings)
        for i in [RIG_UI_PT_main,RIG_UI_PT_rigui,RIG_UI_PT_masks,RIG_UI_PT_tools,RIG_UI_PT_customprops,RIG_UI_PT_settings] : 
            try :bpy.utils.unregister_class(i)
            except (AttributeError, KeyError, TypeError,RuntimeError): pass
        init_ui_properties ()
        for i in panels :
            if i is not None :
                bpy.utils.register_class(i)
        return {'FINISHED'}

class RIG_UI_PT_settings(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Rig UI Settings"
    bl_idname = f'{rig_name.lower()}_PT_settings'
    
    @classmethod
    def poll(self, context):
        if bpy.context.active_object.type == "ARMATURE" :
            active_rig = bpy.context.active_object
        elif bpy.context.active_object.parent.type == "ARMATURE" :
            active_rig = bpy.context.active_object.parent
        else :
            active_rig = None
        try:
            return (active_rig.data.get("rig_id") is not None)
        except (AttributeError, KeyError, TypeError):
            return False
    
    def draw(self, context):
        layout=self.layout
        row=layout.box().row()
        row.operator(f'{rig_name.lower()}.reload_ui', emboss=True, text="", icon='FILE_REFRESH')
        col=layout.column(align=True)
        col.prop(context.scene.my_inputs, "p_A")
        col.prop(context.scene.my_inputs, "p_B")
        col.prop(context.scene.my_inputs, "p_C")
        col.prop(context.scene.my_inputs, "p_D")

# -- BACKEND --
def init_ui_properties ():
    rig=None
    for i in bpy.data.objects:
        if i.type == "ARMATURE" and i.data.get("rig_id") == rig_id :
            rig=i
    property_bone = rig.pose.bones["PROPERTIES"]

    collections = bpy.data.armatures[rig.data.name].collections
    ctrl_list = set([i.name.split("_")[0].split(".")[0] for i in collections if i.name.isupper()])
    prop_list = set([i.split('_')[0] for i in property_bone.keys()] )
    
    for i in ctrl_list :
        if not str("ui_ctrl_"+i)in rig.data.keys():
            rig.data["ui_ctrl_"+i]=True
    for i in prop_list :
        if not str("ui_prop_"+i)in rig.data.keys():
            rig.data["ui_prop_"+i]=True

classes = ( RIG_UI_PT_main,
            RIG_UI_PT_variables,
            WM_OT_text_popup,

            RIG_UI_PT_rigui,
            RIG_UI_OT_toggle_controllers,
            RIG_UI_OT_toggle_boxes,
            
            RIG_UI_OT_snap_opposite_kinematic,
            RIG_UI_PT_tools,
            RIG_UI_PT_customprops,
            
            RIG_UI_OT_toggle_masks,
            RIG_UI_PT_masks,

            RIG_UI_OT_reload_ui,
            RIG_UI_PT_settings
            )

def register():
    for i in classes :
        bpy.utils.register_class(i)
    bpy.types.Scene.my_inputs = bpy.props.PointerProperty(type=RIG_UI_PT_variables)
    
def unregister():
    for i in classes :
        bpy.utils.unregister_class(i)
    del bpy.types.Scene.my_inputs

if __name__ == "__main__":
    init_ui_properties()
    register()