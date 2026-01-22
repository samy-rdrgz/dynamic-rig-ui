import bpy
from .lib import show_messagebox


#BOUTONS
class LAT_PT_reload_gn_button(bpy.types.Operator):
    """Bouton de reload du geonode (doit contenir 'gn_artline' dans le nom du fichier).
    """
    bl_idname = "lat.reload_gn_button"
    bl_label = "Reload Geonode file"
    bl_description = "Bouton de reload du fichier contenant le geonode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        files=[]
        for i in bpy.data.libraries:
            if 'gn_artline' in i.name:
                files.append(i.name)
                i.reload()
        if len(files) == 0 :
            show_messagebox('No files to reload', ["Need 'gn_artline' in linked file name"], 'ERROR')
        else :
            show_messagebox(str(len(files)) +' file.s reloaded :', files, 'INFO')
        return {'FINISHED'}


#INTERFACE
class LAT_PT_geonode_panel(bpy.types.Panel):
    """Creer un panneau pour l'interface utilisateur
    """
    bl_label = "Geometry Node"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LineArt"
    bl_parent_id = "LAT_PT_main_panel"
    bl_options = {'HIDE_HEADER','HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.operator("lat.reload_gn_button", icon='FILE_REFRESH')


#BACKEND
classes = [
    LAT_PT_geonode_panel,
    LAT_PT_reload_gn_button
    ]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()

