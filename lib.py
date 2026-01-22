import bpy

#FONCTIONS
def show_messagebox(title = "Info", lines=[], icon = 'INFO'):
    """Affiche unne pop up de retour utilisateur / d'erreur.

    Args:
        title (_str_): Titre (premiere ligne) du message.
        lines (_list_): Liste de chaines de characteres structurant les differentes lignes du message.
        icon (_icon_): str id d'une icon Blender
    """
    def draw(self, context):
        for n in lines:
            self.layout.label(text=n)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)