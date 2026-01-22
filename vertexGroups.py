import bpy
from .lib import show_messagebox


# VARIABLES D'INPUT
class LAT_PT_variables(bpy.types.PropertyGroup):
    """Creation des variables stockant les inputs utilisateurs.
    """
    outline_tckns_value: bpy.props.FloatProperty(name="",description="Enter a float value", default=1.0,min=0.0,max=1.0)
    outline_tckns_bool: bpy.props.BoolProperty(name="OutlineTckns",description="Activate or deactivate",default=False)

    inline_tckns_value: bpy.props.FloatProperty(name="",description="Enter a float value", default=1.0,min=0.0,max=1.0)
    inline_tckns_bool: bpy.props.BoolProperty(name="InlineTckns",description="Activate or deactivate",default=False)

    boolean_value: bpy.props.IntProperty(name="",description="Enter a float value", default=1,min=0,max=1)
    boolean_bool: bpy.props.BoolProperty(name="Boolean",description="Activate or deactivate",default=False)

    noinline_value: bpy.props.IntProperty(name="",description="Enter a float value", default=1,min=0,max=1)
    noinline_bool: bpy.props.BoolProperty(name="NoInline",description="Activate or deactivate",default=False)

    nooutline_value: bpy.props.IntProperty(name="",description="Enter a float value", default=1,min=0,max=1)
    nooutline_bool: bpy.props.BoolProperty(name="NoOutline",description="Activate or deactivate",default=False)

    linedetail_value: bpy.props.IntProperty(name="",description="Enter a float value", default=1,min=0,max=1)
    linedetail_bool: bpy.props.BoolProperty(name="LineDetail",description="Activate or deactivate",default=False)

    color_vect: bpy.props.FloatVectorProperty(name="",subtype='COLOR', size=3, default=(0.0,0.0,0.0),min=0,max=1)
    color_bool: bpy.props.BoolProperty(name="LineColor",description="Activate or deactivate",default=False)

    overwrite_bool: bpy.props.BoolProperty(name="Overwrite",description="If vertex group already exist, overwrite with new weight",default=False)

    vg_from_list: bpy.props.EnumProperty(name= "", description="Select an option",
                                   items=[('lat_vg_outline_tckns','lat_vg_outline_tckns',''),
                                          ('lat_vg_inline_tckns','lat_vg_inline_tckns',''),
                                          ('lat_vg_boolean','lat_vg_boolean',''),
                                          ('lat_vg_noInline','lat_vg_noInline',''),
                                          ('lat_vg_noOutline','lat_vg_noOutline',''),
                                          ('lat_vg_lineDetail','lat_vg_lineDetail','')])
    
    vg_to_list: bpy.props.EnumProperty(name= "", description="Select an option",
                                   items=[('lat_vg_outline_tckns','lat_vg_outline_tckns',''),
                                          ('lat_vg_inline_tckns','lat_vg_inline_tckns',''),
                                          ('lat_vg_boolean','lat_vg_boolean',''),
                                          ('lat_vg_noInline','lat_vg_noInline',''),
                                          ('lat_vg_noOutline','lat_vg_noOutline',''),
                                          ('lat_vg_lineDetail','lat_vg_lineDetail','')])

    filter_str: bpy.props.StringProperty(name="Filter",description="Enter a string", default='filter')
    

# BOUTONS
class LAT_PT_reset_button(bpy.types.Operator):
    """Bouton de reset des variables d'inputs.
    """
    bl_idname = "lat.reset_button"
    bl_label = "Reset"
    bl_description = "Reset des variables d'inputs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        var=[
            'outline_tckns_value',
            'inline_tckns_value',
            'boolean_value',
            'noinline_value',
            'nooutline_value',
            'linedetail_value',
            'color_vect',

            'outline_tckns_bool',
            'inline_tckns_bool',
            'boolean_bool',
            'noinline_bool',
            'nooutline_bool',
            'linedetail_bool',
            'color_bool',
            
            'vg_from_list',
            'vg_to_list',

            'overwrite_bool',
            'filter_str'
            ]
        for i in var :
            context.scene.my_inputs.property_unset(i)
        
        return {'FINISHED'}

class LAT_PT_create_vg_button(bpy.types.Operator):
    """Bouton de creation des vertexs groups.
    """
    bl_idname = "lat.create_vg_button"
    bl_label = "Create selected"
    bl_description = "Creation des VertexGroups"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Execution du bouton.
        """
        # Recuperer les valeurs entrees par l'utilisateur
        les_groups=[[
            'lat_vg_outline_tckns',
            'lat_vg_inline_tckns',
            'lat_vg_boolean',
            'lat_vg_noInline',
            'lat_vg_noOutline',
            'lat_vg_lineDetail',
        ],[    
            context.scene.my_inputs.outline_tckns_value,
            context.scene.my_inputs.inline_tckns_value,
            context.scene.my_inputs.boolean_value,
            context.scene.my_inputs.noinline_value,
            context.scene.my_inputs.nooutline_value,
            context.scene.my_inputs.linedetail_value
        ],[
            context.scene.my_inputs.outline_tckns_bool,
            context.scene.my_inputs.inline_tckns_bool,
            context.scene.my_inputs.boolean_bool,
            context.scene.my_inputs.noinline_bool,
            context.scene.my_inputs.nooutline_bool,
            context.scene.my_inputs.linedetail_bool
        ]]
        overwrite = context.scene.my_inputs.overwrite_bool
        color = list(context.scene.my_inputs.color_vect)

        color_bool=context.scene.my_inputs.color_bool
        
        # Utiliser la valeur float dans une fonction
        for i in range(6):
            self.set_vertex_group(les_groups, i, overwrite)
        self.set_vertex_color(color, color_bool, overwrite)
        return {'FINISHED'}

    def set_vertex_group(self, doc, id, ow):
        """Creation d'un VertexGroup sur tous les objets selectionnes.

        Args:
            doc (_dict_list_): Dictionnaires des valeurs correspondantes aux VG existants (nom, valeur, boolean d'activation)
            id (_int_): Index du doc referancant le VG en cours de creation
            ow (_bool_): Boolean d'overwrite ou non, si le VG existe deja sur l'objet
        """

        selectobj = bpy.context.selected_objects
        for obj in selectobj:
            vID=[vert.index for vert in obj.data.vertices]

            if doc[2][id]==True:
                if not doc[0][id] in obj.vertex_groups:
                    obj.vertex_groups.new(name = doc[0][id])
                    ow=True
                if ow :
                    obj.vertex_groups[doc[0][id]].add(vID,doc[1][id],'REPLACE')


    def set_vertex_color(self, color, bool, ow):
        """Creation d'un VertexColor sur tous les objets selectionnes.

        Args:
            color (_list_): Couleur RGB ou RGBA
            bool (_type_): Boolean de la creation de ce VertexColor ou non
            ow (_bool_): Boolean d'overwrite ou non, si le VG existe deja sur l'objet
        """
        if bool :
            #Rajout de la valeur Alpha si manquante
            if len(color)==3:
                color.append(1.0)

            for obj in bpy.context.selected_objects:
                if not "lat_vc_color" in obj.data.attributes:
                    obj.data.attributes.new(name="lat_vc_color", type='FLOAT_COLOR', domain='POINT')
                    vc=obj.data.attributes.get("lat_vc_color")
                    for j in range(len(vc.data)):
                        vc.data[j].color = color
                else:
                    if ow :
                        vc=obj.data.attributes.get("lat_vc_color")
                        for j in range(len(vc.data)):
                            vc.data[j].color = color

class LAT_PT_transfer_weight_button(bpy.types.Operator):
    """Bouton de transfert de vertex weight (des vertex selectionnes).
    """
    bl_idname = "lat.transfer_weight_button"
    bl_label = "Copy & transfer selected vertices weight"
    bl_description = "Transfert de vertex weight (des vertices selectionnes)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = bpy.context.view_layer.objects.active
        vg_A = context.scene.my_inputs.vg_from_list
        vg_B = context.scene.my_inputs.vg_to_list
        if vg_A == vg_B :
            show_messagebox('Copy Error',["Select differents VertexGroups"],'ERROR')
            return {'FINISHED'}

        if vg_A in obj.vertex_groups and vg_B in obj.vertex_groups :
                wasMode=bpy.context.object.mode
                mesh=obj.data

                if wasMode != 'OBJECT' :
                    bpy.ops.object.mode_set(mode='OBJECT')
                    
                selected_verts = [v for v in mesh.vertices if v.select]
                if len(selected_verts)==0:
                    show_messagebox('Copy Error',["Select some vertices in EditMode"],'ERROR')
                    return()
                
                for v in selected_verts :
                    vglist=[]
                    for g in mesh.vertices[v.index].groups :
                        vglist.append(obj.vertex_groups[g.group].name)
                        if obj.vertex_groups[g.group].name == vg_A :
                            vgfromid=g
                    if vg_A in vglist :
                        obj.vertex_groups[vg_B].add([v.index],vgfromid.weight,'REPLACE')
                    else :
                        obj.vertex_groups[vg_B].add([v.index],0,'REPLACE')

                bpy.ops.object.mode_set(mode=wasMode)
                show_messagebox('Copy success',[str(len(selected_verts))+' weight copied', 'from '+vg_A+' to '+vg_B])
                return {'FINISHED'}
        
        else :
            show_messagebox('Copy Error',["Need two VertexGroups", " - " +vg_A, " - " +vg_B],'ERROR')
            return {'FINISHED'}

class LAT_PT_set_obj_id_button(bpy.types.Operator):
    """Bouton de creation du VertexGroup ObjID.
    """
    bl_idname = "lat.set_obj_id_button"
    bl_label = "Generate objID"
    bl_description = "Creation du VertexGroup ObjID"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Execution du bouon.
        D'apres la collection 'assets', et ses sous collections directes,
        defini une valeur unique sur l'ensemble des meshs composant un meme objet.
        """
        
        coll=None
        if not 'assets' in bpy.context.scene.collection.children:
            show_messagebox('Error',["There's no collection called 'assets'"],'ERROR')
            return {'FINISHED'}
        coll=bpy.context.scene.collection.children['assets']
        objNumber=len(coll.children)
        if objNumber == 0 :
            show_messagebox('Error',["There's no objects in 'assets' collection"],'ERROR')
            return {'FINISHED'}
        objIndex=1
        objID=objIndex/objNumber
        m=[]
        for oc in coll.children:
            meshs=0
            for o in oc.all_objects :
                if o.type=='MESH':
                    meshs+=1
                    vID=[vert.index for vert in o.data.vertices]
                    if not 'lat_vg_objID' in o.vertex_groups :
                        o.vertex_groups.new(name = 'lat_vg_objID')
                    o.vertex_groups['lat_vg_objID'].add(vID,objID,'REPLACE')
            m.append('- '+str(oc.name) +' ('+ str(meshs)+' mesh.s)')        
            objIndex=objIndex+1
            objID=objIndex/objNumber
        m.append('objID DONE')
        show_messagebox('There is '+ str(objNumber) +' objects', m, 'INFO')
        return {'FINISHED'}

class LAT_PT_clean_vg_button(bpy.types.Operator):
    """Bouton de suppression de VertexGroups (selection par chaine de caracteres).
    """
    bl_idname = "lat.clean_vg_button"
    bl_label = "Clean VGroups"
    bl_description = "Suppression de VertexGroups (selection par chaine de caracteres)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Fonction du bouton.
        Parcours tous les VG des objs selectionnes.
        Si le nom du VG comptient la chaine de caractere rentree dans le champs d'input, supprime le VG.
        """
        deleted=[]
        deletedNb=0
        filter = context.scene.my_inputs.filter_str
        for obj in bpy.context.selected_objects:
            for vg in obj.vertex_groups :
                if filter in vg.name:
                    if not vg.name in deleted :
                        deleted.append(vg.name)
                    deletedNb+=1
                    obj.vertex_groups.remove(vg)
        show_messagebox(str(deletedNb) +' vertexGroups deleted :', deleted, 'INFO')
        return {'FINISHED'}

        
#INTERFACE
class LAT_PT_set_weight_panel(bpy.types.Panel):
    """Creer un panneau pour l'interface utilisateur
    """
    bl_label = "Set Weights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LineArt"
    bl_parent_id = "LAT_PT_main_panel"
    bl_options = {'HIDE_HEADER','HEADER_LAYOUT_EXPAND'}

    def draw(self, context):

        layout = self.layout
        scene = context.scene
        my_inputs = scene.my_inputs

        
        col = layout.column(align=True)

        #CREATE VG
        box = col.box()
        bbox=box.box()
        grid = bbox.grid_flow(columns=1, even_columns=True, align=True)
        grid.operator("lat.reset_button", icon='FILE_REFRESH')
        
        grid=box.grid_flow(row_major=False, columns=2, even_rows=False, even_columns=False, align=True)
    
        grid.label(text='VGroups', icon='GROUP_VERTEX')
        grid.separator(factor=1, type='SPACE')
        grid.prop(my_inputs, "outline_tckns_bool")
        grid.prop(my_inputs, "inline_tckns_bool")
        grid.prop(my_inputs, "boolean_bool")
        grid.prop(my_inputs, "noinline_bool")
        grid.prop(my_inputs, "nooutline_bool")
        grid.prop(my_inputs, "linedetail_bool")
        grid.prop(my_inputs, "color_bool")

        grid.label(text='Weight', icon='MOD_VERTEX_WEIGHT')
        grid.separator(factor=1, type='SPACE')
        grid.prop(my_inputs, "outline_tckns_value")
        grid.prop(my_inputs, "inline_tckns_value")
        grid.prop(my_inputs, "boolean_value")
        grid.prop(my_inputs, "noinline_value")
        grid.prop(my_inputs, "nooutline_value")
        grid.prop(my_inputs, "linedetail_value")
        grid.prop(my_inputs, "color_vect")

        bbox = box.box()
        grid = bbox.grid_flow(columns=2, even_columns=True, align=True)
        grid.prop(my_inputs, "overwrite_bool")
        grid.operator("lat.create_vg_button", icon='ADD')

        #TRANSFER WEIGHT
        grid = col.grid_flow(columns=1, even_columns=True, align=True)
        grid.separator(factor=1.5, type='SPACE')

        box = col.box()
        grid = box.grid_flow(columns=2, even_columns=True, align=True)
        grid.label(text='Copy from ...', icon='GROUP_VERTEX')
        grid.prop(my_inputs, "vg_from_list")
        grid.label(text='and paste on...')
        grid.prop(my_inputs, "vg_to_list")
        grid = box.grid_flow(columns=1, even_columns=True, align=True)
        grid.operator("lat.transfer_weight_button", icon='COPYDOWN')

        #OBJID
        grid = col.grid_flow(columns=1, align=True)
        grid.separator(factor=1.5, type='SPACE')

        box = col.box()
        grid = box.grid_flow(columns=1, align=True)
        grid.operator("lat.set_obj_id_button", icon='COPY_ID')

        #CLEAN VG
        grid = col.grid_flow(columns=1, align=True)
        grid.separator(factor=1.5, type='SPACE')

        box = col.box()
        grid = box.grid_flow(columns=2, even_columns=True, align=True)
        grid.prop(my_inputs, "filter_str")
        grid.operator("lat.clean_vg_button", icon='TRASH')


#BACKEND
classes = [
    LAT_PT_variables,

    LAT_PT_reset_button,
    LAT_PT_create_vg_button,
    LAT_PT_transfer_weight_button,
    LAT_PT_set_obj_id_button,
    LAT_PT_clean_vg_button,
    LAT_PT_set_weight_panel
    ]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.my_inputs = bpy.props.PointerProperty(type=LAT_PT_variables)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.my_inputs

if __name__ == "__main__":
    register()