import time

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
    "version": (0, 1, 0),
    "warning": "Work in Progress version",
}


class MainSettingsPanel(bpy.types.Panel):
    bl_label = "Lens Flare Settings"
    bl_idname = "LF_PT_MainSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
 
    def draw(self, context):
        layout = self.layout

        props = context.scene.lens_flare_props
 
        row = layout.row()
        row.prop(props, 'image')

        row = layout.row()
        row.operator('render.lens_flare_render')

        row = layout.row()
        row.prop(props, "posx")
        row.prop(props, "posy")


class FlareSettingsPanel(bpy.types.Panel):
    bl_label = "Flare"
    bl_idname = "LF_PT_FlareSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_parent_id = "LF_PT_MainSettings"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        props = context.scene.lens_flare_props

        col = layout.column(align=True)
        col.prop(props, 'flare_color', text='Flare Color')
        col = layout.column(align=True)
        col.prop(props, 'flare_size', text='Flare Size')


class GhostsPanel(bpy.types.Panel):
    bl_label = "Ghosts"
    bl_idname = "LF_PT_Ghosts"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_parent_id = "LF_PT_MainSettings"

    active_index = 0

    def draw(self, context):
        layout = self.layout

        props = context.scene.lens_flare_props

        row = layout.row()
        row.operator('lens_flare.add_ghost')

        row = layout.row()

        for i, ghost in enumerate(props.ghosts):
            box = layout.box()
            row = box.row(align=True)

            row.prop(ghost, 'offset')
            row.prop(ghost, 'color', text='')
            row.prop(ghost, 'size')
            remove_op = row.operator('lens_flare.remove_ghost', text='', icon='X')
            remove_op.remove_id = i


class CameraOverridePanel(bpy.types.Panel):
    bl_label = "Camera Override"
    bl_idname = "LF_PT_CameraOverride"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_parent_id = "LF_PT_MainSettings"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.prop(context.scene.lens_flare_props, 'use_override', text='')

    # @classmethod
    # def poll(cls, context):
    #    return (context.object is not None)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        props = context.scene.lens_flare_props
        layout.enabled = props.use_override

        col = layout.column(align=True)
        col.prop(props, 'blades', text='Aperture Blades')
        col = layout.column(align=True)
        col.prop(props, 'rotation', text='Rotation')


class RenderLensFlareOperator(bpy.types.Operator):
    bl_label = "Render Lens Flare"
    bl_idname = "render.lens_flare_render"
    bl_description = "Renders lens flare into selected image"

    def execute(self, context):
        props: LensFlareProperties = context.scene.lens_flare_props

        start_time = time.perf_counter()

        # don't render if the is no valid output
        if props.image is None:
            self.report({'ERROR_INVALID_INPUT'}, "No image selected")
            return {'CANCELLED'}
        max_x, max_y = props.image.size

        buffer = np.array(props.image.pixels)
        res_buffer = np.reshape(buffer, (-1, 4))

        color = props.flare_color
        center_x = max_x / 2
        center_y = max_y / 2

        ratio = max_x / max_y

        flare_x = props.posx * max_x
        flare_y = props.posy * max_y

        for i, pixel in enumerate(res_buffer):
            x = i % max_x
            y = i // max_x
            value = image_processing.compute_flare_intensity(x, y, max_x, max_y, props, ratio)
            pixel[0] = color[0] * value
            pixel[1] = color[1] * value
            pixel[2] = color[2] * value

            for ghost in props.ghosts:
                ghost_x = center_x + (flare_x - center_x) * ghost.offset
                ghost_y = center_y + (flare_y - center_y) * ghost.offset

                value = min(max((ghost.size * 100) - ((x - ghost_x) ** 2 + (y - ghost_y) ** 2), 0.0), 1.0)

                pixel[0] += ghost.color[0] * value
                pixel[1] += ghost.color[1] * value
                pixel[2] += ghost.color[2] * value

        buffer = np.reshape(res_buffer, (-1))

        props.image.pixels = list(buffer)
        props.image.update()

        # force compositing refresh
        bpy.ops.render.render(write_still=True)

        end_time = time.perf_counter()

        self.report({'INFO'}, f"Lens flare render time: {end_time - start_time}")

        return {'FINISHED'}


class AddGhostOperator(bpy.types.Operator):
    bl_label = "Create new ghost"
    bl_idname = "lens_flare.add_ghost"
    bl_description = "Creates new ghost"

    def execute(self, context):
        props: LensFlareProperties = context.scene.lens_flare_props

        props.ghosts.add()

        return {'FINISHED'}


class RemoveGhostOperator(bpy.types.Operator):
    bl_label = "Deletes ghost"
    bl_idname = "lens_flare.remove_ghost"
    bl_description = "Creates new ghost"

    remove_id: bpy.props.IntProperty(default=-1, description="Index of ghost to remove")

    def execute(self, context):
        props: LensFlareProperties = context.scene.lens_flare_props

        if self.remove_id == -1:
            self.report({'ERROR_INVALID_INPUT'}, "Invalid ID of ghost to delete")
            return {'CANCELLED'}

        props.ghosts.remove(self.remove_id)

        return {'FINISHED'}


class LensFlareGhostPropertyGroup(bpy.types.PropertyGroup):
    offset: bpy.props.FloatProperty(name="Offset", description="Ghost offset", default=0.0)
    color: bpy.props.FloatVectorProperty(name="Color", description="Ghost color", subtype='COLOR_GAMMA', default=[0.9, 0.9, 0.9], size=3, min=0.0, soft_max=1.0)
    size: bpy.props.FloatProperty(name="Size", description="Ghost Size", default=0.5)


class LensFlareProperties(bpy.types.PropertyGroup):
    posx: bpy.props.FloatProperty(name="X", description="Position of light source on X axis", default=0.5)
    posy: bpy.props.FloatProperty(name="Y", description="Position of light source on X axis", default=0.5)
    image: bpy.props.PointerProperty(name="Image", type=bpy.types.Image, description="Image to render to")
    use_override: bpy.props.BoolProperty(name="Camera Override", description="Use custom camera properties", default=False)
    blades: bpy.props.IntProperty(name="Aperture Blades", description="Number of blades in aperture for polygonal bokeh (at least 3)", default=6, min=3)
    rotation: bpy.props.FloatProperty(name="Aperture Rotation", description="Rotation of blades in aperture", default=0, subtype='ANGLE', unit='ROTATION')
    flare_color: bpy.props.FloatVectorProperty(name="Flare Color", description="Color of the main flare", subtype='COLOR_GAMMA', default=[0.9, 0.9, 0.9], size=3, min=0.0, soft_max=1.0)
    flare_size: bpy.props.FloatProperty(name="Flare Size", description="Flare size relative to image size", default=0.5)
    ghosts: bpy.props.CollectionProperty(name="Ghosts", type=LensFlareGhostPropertyGroup)


_classes = [
    # properties
    LensFlareGhostPropertyGroup,
    LensFlareProperties,
    # panels
    MainSettingsPanel,
    FlareSettingsPanel,
    GhostsPanel,
    CameraOverridePanel,
    # operators
    RenderLensFlareOperator,
    AddGhostOperator,
    RemoveGhostOperator
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lens_flare_props = bpy.props.PointerProperty(type=LensFlareProperties)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lens_flare_props
