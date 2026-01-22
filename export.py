import bpy
from datetime import datetime
import os


#BOUTONS
class LAT_PT_set_export_filename(bpy.types.Operator):
    """Bouton de creation du dossier d'export et de parametrage du nom des fichiers.
    shoots/dateDuJour_VersionDuFichier/nomDuFichier_nomCameraActive_frame.extension
    """
    bl_idname = "lat.set_export_filename"
    bl_label = "Set Output path"
    bl_description = "Bouton de creation du dossier d'export et de parametrage du nom des fichiers"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        path = bpy.data.filepath
        filename=''
        filepath=''
        isName=True
        for i in range(len(path)-1,-1,-1) :
            if i < len(path)-6 :
                if path[i]=='\\' and isName:
                    isName=False
                else :
                    if isName :
                        filename=path[i]+filename
                    else :
                        filepath=path[i]+filepath
                
        bpy.data.scenes[bpy.context.scene.name].render.use_file_extension=True
        newpath=filepath+"\shoots\\"+datetime.today().strftime('%Y-%m-%d')+filename[-5:]+"\\"
        print(newpath)

        if not os.path.exists(newpath):
            os.makedirs(newpath)
            
        if not bpy.data.scenes[bpy.context.scene.name].render.use_file_extension :
            bpy.data.scenes[bpy.context.scene.name].render.use_file_extension=True
        bpy.data.scenes[bpy.context.scene.name].render.filepath = '//shoots\\' + datetime.today().strftime('%Y-%m-%d')+filename[-5:]+"\\" + filename +"_"+ bpy.context.scene.camera.name+"_###"
        return {'FINISHED'}


#INTERFACE
class LAT_PT_export_panel(bpy.types.Panel):
    """Creer un panneau pour l'interface utilisateur
    """
    bl_label = "Output"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LineArt"
    bl_parent_id = "LAT_PT_main_panel"
    bl_options = {'HIDE_HEADER','HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.operator("lat.set_export_filename", icon='OUTLINER')
        bbox = box.box()
        
        bbox.label(text=str(bpy.data.scenes[bpy.context.scene.name].render.filepath))
        

#BACKEND
classes = [
    LAT_PT_set_export_filename,
    LAT_PT_export_panel
    ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()

