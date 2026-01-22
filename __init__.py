bl_info = {
    "name": "guercoeur",
    "description": "Tools liés à la création de line art en Géometry Node. Gestion de Vertex Groups et de fichiers liés.",
    "author": "Loops creative studio",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "https://book.loopscreativestudio.com/",
    "tracker_url": "https://book.loopscreativestudio.com/",
    "category": "Development"
    }

import bpy
from . import vertexGroups
from . import reload
from . import export


#INTERFACE
class LAT_PT_main_panel(bpy.types.Panel):
    """Creation d'un Sous-Panel dans le 'N' panel de la vue 3D, pour contenir l'interface de l'addon.
    """
    bl_label = "Tools"  
    bl_space_type = "VIEW_3D"  
    bl_region_type = "UI"
    bl_category = "LineArt"
    #bl_context = "objectmode"
    bl_idname = "LAT_PT_main_panel"
    bl_options = {'HEADER_LAYOUT_EXPAND'}
    
    def draw(self, context):
        pass


#BACKEND
def register():
    bpy.utils.register_class(LAT_PT_main_panel)
    export.register()
    reload.register()
    vertexGroups.register()

def unregister():
    bpy.utils.unregister_class(LAT_PT_main_panel)
    export.unregister()
    reload.unregister()
    vertexGroups.unregister()

if __name__ == "__main__":
    register()
