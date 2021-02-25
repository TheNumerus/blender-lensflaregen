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
        col = layout.column(align=True)
        col.prop(props, 'rays_intensity', text='Ray Intensity')


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
    bl_parent_id = "LF_PT_MainSettings"

    active_index = 0

    def draw(self, context):
        layout = self.layout

        props: LensFlareProperties = context.scene.lens_flare_props

        layout.use_property_split = True

        col = layout.column(align=True)
        col.prop(props, "ghosts_empty_center", text="Transparent Centers")

        layout.separator()

        row = layout.row()

        layout.use_property_split = False

        row.template_list("LF_UL_Ghosts", "", props, "ghosts", props, "selected_ghost", rows=3)


        # ghost adding and removal
        col = row.column(align=True)
        col.operator("lens_flare.add_ghost", icon='ADD', text="")
        remove_op = col.operator('lens_flare.remove_ghost', text='', icon='REMOVE')
        remove_op.remove_id = props.selected_ghost

        layout.use_property_split = True
        layout.separator()

        if props.selected_ghost in range(0, len(props.ghosts)):
            ghost = props.ghosts[props.selected_ghost]
            col = layout.column(align=True)
            col.prop(ghost, 'name', text='Name')

            col = layout.column(align=True)
            col.prop(ghost, 'offset', text='Offset')

            col = layout.column(align=True)
            col.prop(ghost, 'color', text='Color')

            col = layout.column(align=True)
            col.prop(ghost, 'size', text='Size')


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


def regenerate_ghost_icons():
    props = bpy.context.scene.lens_flare_props

    for i, ghost in enumerate(props.ghosts):
        if str(i) in previews['ghosts']:
            icon: bpy.types.ImagePreview = previews['ghosts'][str(i)]
        else:
            icon: bpy.types.ImagePreview = previews['ghosts'].new(str(i))
        icon.icon_size = [1, 1]
        icon.icon_pixels_float = [ghost.color.r, ghost.color.g, ghost.color.b]