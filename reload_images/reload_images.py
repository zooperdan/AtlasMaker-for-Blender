bl_info = {
    "name": "Reload All Textures",
    "author": "zooperdan",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "Image Editor > Sidebar > Texture Tools",
    "description": "Adds a button to reload all external image textures.",
    "category": "Material",
}

import bpy

class TEXTURETOOLS_PT_panel(bpy.types.Panel):
    bl_label = "Texture Tools"
    bl_idname = "TEXTURETOOLS_PT_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Texture Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator("image.reload_all_textures", icon='FILE_REFRESH')

class IMAGE_OT_reload_all_textures(bpy.types.Operator):
    bl_idname = "image.reload_all_textures"
    bl_label = "Reload All Textures"
    bl_description = "Force reload of all external texture files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for image in bpy.data.images:
            if image.source == 'FILE':
                image.reload()
                count += 1
        self.report({'INFO'}, f"Reloaded {count} image(s).")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(TEXTURETOOLS_PT_panel)
    bpy.utils.register_class(IMAGE_OT_reload_all_textures)

def unregister():
    bpy.utils.unregister_class(TEXTURETOOLS_PT_panel)
    bpy.utils.unregister_class(IMAGE_OT_reload_all_textures)

if __name__ == "__main__":
    register()
