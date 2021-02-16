from .properties import *


class MainSettingsPanel(bpy.types.Panel):
    bl_label = "Lens Flare Settings"
    bl_idname = "LF_PT_MainSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        props = context.scene.lens_flare_props

        row = layout.row()
        row.operator('render.lens_flare_ogl_render', icon='RENDER_STILL')
        row = layout.row()
        row.operator('render.lens_flare_anim', icon='RENDER_ANIMATION')

        row = layout.row()
        row.prop(props, 'image')
        row.operator('image.new', text='', icon='ADD')

        col = layout.column(align=True)
        col.prop(props, "resolution_x", text="Resolution X")
        col.prop(props, "resolution_y", text="Y")

        col = layout.column(align=True)
        col.prop(props, "posx", text="Effect Position X")
        col.prop(props, "posy", text="Y")

        col = layout.column(align=True)
        col.prop(props, "master_intensity", text="Master Intensity")


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
        col.prop(props, 'flare_color', text='Color')
        col = layout.column(align=True)
        col.prop(props, 'flare_size', text='Size')
        col = layout.column(align=True)
        col.prop(props, 'flare_intensity', text='Intensity')
        col = layout.column(align=True)
        col.prop(props, 'flare_rays', text='Rays')


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
        layout.use_property_split = True

        props = context.scene.lens_flare_props

        row = layout.row()
        row.operator('lens_flare.add_ghost')

        col = layout.column(align=True)
        col.prop(props, "ghosts_empty_center", text="Transparent Centers")

        layout.use_property_split = False

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

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        props = context.scene.lens_flare_props
        layout.enabled = props.use_override

        col = layout.column(align=True)
        col.prop(props, 'blades', text='Aperture Blades')
        col = layout.column(align=True)
        col.prop(props, 'rotation', text='Rotation')


class MiscPanel(bpy.types.Panel):
    bl_label = "Miscellaneous Settings"
    bl_idname = "LF_PT_MiscSettings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares'
    bl_parent_id = "LF_PT_MainSettings"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        props = context.scene.lens_flare_props

        col = layout.column(align=True)
        col.prop(props, 'debug_pos', text='Debug Cross')
