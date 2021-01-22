import bpy
import numpy as np
from . import image_processing

if "bpy" in locals():
    import importlib
    importlib.reload(image_processing)

bl_info = {
    "name": "Lens Flare Generator",
    "description": "Generates lens flare effects from image",
    "blender": (2, 91, 0),
    "category": "Node",
    "author": "Petr Volf",
    "version": (0,1,0),
    "warning": "Work in Progress version",
}


class LensFlareMainSettingsPanel(bpy.types.Panel):
    bl_label = "Lens Flare Settings"
    bl_idname = "LensFlareMainSettingsPanel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
 
    def draw(self, context):
        layout = self.layout

        props = context.scene.lens_flare_props
 
        row = layout.row()
        row.prop(props, 'image')

        row = layout.row()
        row.operator('node.lens_flare_render')

        row = layout.row()
        row.prop(props, "posx")
        row.prop(props, "posy")

class LensFlarePanel(bpy.types.Panel):
    bl_label = "Flare"
    bl_idname = "LensFlarePanel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_parent_id = "LensFlareMainSettingsPanel"

    def draw(self, context):
        layout = self.layout

        props = context.scene.lens_flare_props

        row = layout.row()
        row.prop(props, 'flare_color')
        row = layout.row()
        row.prop(props, 'flare_size')

class LensFlareGhostsPanel(bpy.types.Panel):
    bl_label = "Ghosts"
    bl_idname = "LensFlareGhostsPanel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_parent_id = "LensFlareMainSettingsPanel"

    def draw(self, context):
        layout = self.layout

        props = context.scene.lens_flare_props

        row = layout.row()
        row.operator('node.add_ghost')

        row = layout.row()
        row.prop(props, 'ghosts')


class RenderLensFlareOperator(bpy.types.Operator):
    bl_label = "Render Lens Flare"
    bl_idname = "node.lens_flare_render"
    bl_description = "Renders lens flare into selected image"

    def execute(self, context):
        props: LensFlareProperties = context.scene.lens_flare_props

        # don't render if the is no valid output
        if props.image is None:
            self.report({'ERROR_INVALID_INPUT'}, "No image selected")
            return {'CANCELLED'}
        max_x, max_y = props.image.size

        buffer = np.array(props.image.pixels)
        res_buffer = np.reshape(buffer, (-1, 4))

        color = props.flare_color

        ratio = max_x / max_y

        for i, pixel in enumerate(res_buffer):
            x = i % max_x
            y = i // max_x
            value = image_processing.compute_flare_intensity(x, y, max_x, max_y, props, ratio)
            pixel[0] = color[0] * value
            pixel[1] = color[1] * value
            pixel[2] = color[2] * value

        buffer = np.reshape(res_buffer, (-1))

        props.image.pixels = list(buffer)

        return {'FINISHED'}

class AddGhostOperator(bpy.types.Operator):
    bl_label = "Create new ghost"
    bl_idname = "node.add_ghost"
    bl_description = "Creates new ghost"

    def execute(self, context):
        props: LensFlareProperties = context.scene.lens_flare_props

        props.ghosts.add()

        return {'FINISHED'}

class LensFlareGhostPropertyGroup(bpy.types.PropertyGroup):
    offset: bpy.props.FloatProperty(name="Offset", description="Ghost offset", default=0.0)
    color: bpy.props.FloatVectorProperty(name="Color", description="Ghost color", subtype='COLOR_GAMMA', default=[0.9, 0.9, 0.9, 1.0], size=4)
    size: bpy.props.FloatProperty(name="Size", description="Ghost Size", default=0.5)

class LensFlareProperties(bpy.types.PropertyGroup):
    posx: bpy.props.FloatProperty(name="X", description="Position of light source on X axis", default=0.5)
    posy: bpy.props.FloatProperty(name="Y", description="Position of light source on X axis", default=0.5)
    image: bpy.props.PointerProperty(name="Image", type=bpy.types.Image, description="Image to render to")
    flare_color: bpy.props.FloatVectorProperty(name="Flare Color", description="Color of the main flare", subtype='COLOR_GAMMA', default=[0.9, 0.9, 0.9, 1.0], size=4)
    flare_size: bpy.props.FloatProperty(name="Flare Size", description="Flare size relative to image size", default=0.5)
    ghosts: bpy.props.CollectionProperty(name="Ghosts", type=LensFlareGhostPropertyGroup)

_classes = [
    # properties
    LensFlareGhostPropertyGroup,
    LensFlareProperties,
    # panels
    LensFlareMainSettingsPanel,
    LensFlarePanel,
    LensFlareGhostsPanel,
    # operators
    RenderLensFlareOperator,
    AddGhostOperator
]

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lens_flare_props = bpy.props.PointerProperty(type=LensFlareProperties)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lens_flare_props
