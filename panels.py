import bpy.types

from .properties import *

previews = {}


class MainSettingsPanel(bpy.types.Panel):
    bl_label = "Lens Flare Settings"
    bl_idname = "LF_PT_MainSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'

    def __init__(self):
        regenerate_ghost_icons()

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        props: MasterProperties = context.scene.lens_flare_props

        row = layout.row()
        row.operator('render.lens_flare_ogl_render', icon='RENDER_STILL')
        row = layout.row()
        row.operator('render.lens_flare_anim', icon='RENDER_ANIMATION')

        row = layout.row()
        row.template_ID(props, 'image', new="image.new", text='Output Image')

        col = layout.column(align=True)
        col.prop(props, "master_intensity", text="Master Intensity")


class PositionsUiList(bpy.types.UIList):
    bl_idname = "LF_UL_Positions"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0, flt_flag=0):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon='LIGHT_SUN')
        else:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='LIGHT_SUN')


class PositionPanel(bpy.types.Panel):
    bl_label = "Positions"
    bl_idname = "LF_PT_PositionSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        props: MasterProperties = context.scene.lens_flare_props

        row = layout.row()
        row.template_list("LF_UL_Positions", "", props, "positions", props, "active_object", rows=3)

        # position adding and removal
        col = row.column(align=True)
        col.operator("lens_flare.add_position", icon='ADD', text="")
        remove_op = col.operator('lens_flare.remove_position', text='', icon='REMOVE')
        remove_op.remove_id = props.active_object

        layout.use_property_split = True
        layout.separator()

        if props.active_object in range(0, len(props.positions)):
            position = props.positions[props.active_object]

            col = layout.column(align=True)
            col.prop(position, 'name', text='Name')

            layout.prop(position, 'variant', text='Variant', expand=True)

            if position.variant == 'auto':
                col = layout.column(align=True)
                col.prop(position, 'auto_object', text="Position Object")
            elif position.variant == 'manual':
                col = layout.column(align=True)
                col.prop(position, "manual_x", text="Effect Position X")
                col.prop(position, "manual_y", text="Y")


class ResolutionPanel(bpy.types.Panel):
    bl_label = "Custom Resolution"
    bl_idname = "LF_PT_ResolutionSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        props: MasterProperties = context.scene.lens_flare_props.resolution
        layout.prop(props, 'override_scene_resolution', text='')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        props: MasterProperties = context.scene.lens_flare_props.resolution

        col = layout.column(align=True)
        col.prop(props, "resolution_x", text="Resolution X")
        col.prop(props, "resolution_y", text="Y")


class FlareSettingsPanel(bpy.types.Panel):
    bl_label = "Flare"
    bl_idname = "LF_PT_FlareSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        props: FlareProperties = context.scene.lens_flare_props.flare

        col = layout.column(align=True)
        col.prop(props, 'color', text='Color')
        col = layout.column(align=True)
        col.prop(props, 'size', text='Size')
        col = layout.column(align=True)
        col.prop(props, 'intensity', text='Intensity')
        col = layout.column(align=True)
        col.prop(props, 'rays_intensity', text='Ray Intensity')
        layout.separator()
        col = layout.column(align=True)
        col.prop(props, 'anamorphic', text='Anamorphic Flare')


class GhostsUiList(bpy.types.UIList):
    bl_idname = "LF_UL_Ghosts"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0, flt_flag=0):
        icon = previews['ghosts'][str(index)].icon_id
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon_value=icon)
        else:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class GhostsPanel(bpy.types.Panel):
    bl_label = "Ghosts"
    bl_idname = "LF_PT_Ghosts"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'

    active_index = 0

    def draw(self, context):
        layout = self.layout

        props: MasterProperties = context.scene.lens_flare_props

        row = layout.row()

        layout.use_property_split = False

        row.template_list("LF_UL_Ghosts", "", props, "ghosts", props, "selected_ghost", rows=3)

        # ghost adding and removal
        col = row.column(align=True)
        col.operator("lens_flare.add_ghost", icon='ADD', text="")
        remove_op = col.operator('lens_flare.remove_ghost', text='', icon='REMOVE')
        remove_op.remove_id = props.selected_ghost
        duplicate_op = col.operator('lens_flare.duplicate_ghost', text='', icon='DUPLICATE')
        duplicate_op.duplicate_id = props.selected_ghost

        layout.use_property_split = True
        layout.separator()

        if props.selected_ghost in range(0, len(props.ghosts)):
            ghost = props.ghosts[props.selected_ghost]
            col = layout.column(align=True)
            col.prop(ghost, 'name', text='Name')

            col = layout.column(align=True)
            col.prop(ghost, 'offset', text='Offset')

            col = layout.column(align=True)
            col.prop(ghost, 'perpendicular_offset', text='Perpendicular Offset')

            col = layout.column(align=True)
            col.prop(ghost, 'color', text='Color')

            col = layout.column(align=True)
            col.prop(ghost, 'intensity', text='Intensity')

            col = layout.column(align=True)
            col.prop(ghost, 'size', text='Size')

            col = layout.column(align=True)
            col.prop(ghost, 'dispersion', text='Dispersion')

            layout.prop(ghost, 'dispersion_center', text='Dispersion Center', expand=True)

            col = layout.column(align=True)
            col.prop(ghost, 'distortion', text='Distortion')

            col = layout.column(align=True)
            col.prop(ghost, 'center_transparency', text='Center Transparency')

            col = layout.column(align=True)
            col.prop(ghost, 'ratio', text='Aspect Ratio')


class CameraOverridePanel(bpy.types.Panel):
    bl_label = "Camera Override"
    bl_idname = "LF_PT_CameraOverride"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        props: MasterProperties = context.scene.lens_flare_props
        layout.prop(props.camera, 'use_override', text='')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        props: MasterProperties = context.scene.lens_flare_props
        layout.enabled = props.camera.use_override

        col = layout.column(align=True)
        col.prop(props.camera, 'blades', text='Aperture Blades')
        col = layout.column(align=True)
        col.prop(props.camera, 'rotation', text='Rotation')


class MiscPanel(bpy.types.Panel):
    bl_label = "Miscellaneous Settings"
    bl_idname = "LF_PT_MiscSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        props = context.scene.lens_flare_props

        col = layout.column(align=True)
        col.prop(props, 'dispersion_samples', text='Dispersion Samples')

        col = layout.column(align=True)
        col.prop(props, 'use_jitter', text='Use Jitter')

        row = layout.row()
        row.prop(props, 'spectrum_image', text='Spectrum Image')
        row.operator('lens_flare.load_default_spectrum_image', text='', icon='FILE_IMAGE')

        col = layout.column(align=True)
        col.prop(props, 'debug_pos', text='Render Debug Cross')


def regenerate_ghost_icons():
    props = bpy.context.scene.lens_flare_props

    for i, ghost in enumerate(props.ghosts):
        if str(i) in previews['ghosts']:
            icon: bpy.types.ImagePreview = previews['ghosts'][str(i)]
        else:
            icon: bpy.types.ImagePreview = previews['ghosts'].new(str(i))
        icon.icon_size = [2, 2]
        icon.icon_pixels_float = [ghost.color.r, ghost.color.g, ghost.color.b, 1.0] * 4
