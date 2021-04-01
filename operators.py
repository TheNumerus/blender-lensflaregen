import time
import os

from .properties import *
from . import image_processing, ogl


class AddGhostOperator(bpy.types.Operator):
    bl_label = "Create new ghost"
    bl_idname = "lens_flare.add_ghost"
    bl_description = "Creates new ghost"

    def execute(self, context):
        props: MasterProperties = context.scene.lens_flare_props

        props.ghosts.add()

        return {'FINISHED'}


class RemoveGhostOperator(bpy.types.Operator):
    bl_label = "Delete ghost"
    bl_idname = "lens_flare.remove_ghost"
    bl_description = "Removes ghost"

    remove_id: bpy.props.IntProperty(default=-1, description="Index of ghost to remove")

    @classmethod
    def poll(cls, context):
        props: MasterProperties = context.scene.lens_flare_props

        if len(props.ghosts) == 0:
            return False

        return True

    def execute(self, context):
        props: MasterProperties = context.scene.lens_flare_props

        if self.remove_id == -1:
            self.report({'ERROR_INVALID_INPUT'}, "Invalid ID of ghost to delete")
            return {'CANCELLED'}

        # move active selector
        if len(props.ghosts) != 1 and props.selected_ghost == (len(props.ghosts) - 1):
            props.selected_ghost = props.selected_ghost - 1

        props.ghosts.remove(self.remove_id)

        return {'FINISHED'}


class DuplicateGhostOperator(bpy.types.Operator):
    bl_label = "Duplicate ghost"
    bl_idname = "lens_flare.duplicate_ghost"
    bl_description = "Creates new ghost with same values as the active ghost"

    duplicate_id: bpy.props.IntProperty(default=-1, description="Index of ghost to duplicate")

    @classmethod
    def poll(cls, context):
        props: MasterProperties = context.scene.lens_flare_props

        if len(props.ghosts) == 0:
            return False

        return True

    def execute(self, context):
        props: MasterProperties = context.scene.lens_flare_props

        if self.duplicate_id == -1:
            self.report({'ERROR_INVALID_INPUT'}, "Invalid ID of ghost to duplicate")
            return {'CANCELLED'}

        new_ghost: GhostProperties = props.ghosts.add()

        # TODO clean-up
        # for some reason, this crashes when `props.ghosts[self.duplicate_id]` is in temp variable
        new_ghost.color = props.ghosts[self.duplicate_id].color
        new_ghost.intensity = props.ghosts[self.duplicate_id].intensity
        new_ghost.name = props.ghosts[self.duplicate_id].name
        new_ghost.offset = props.ghosts[self.duplicate_id].offset
        new_ghost.perpendicular_offset = props.ghosts[self.duplicate_id].perpendicular_offset
        new_ghost.size = props.ghosts[self.duplicate_id].size
        new_ghost.transparent_center = props.ghosts[self.duplicate_id].transparent_center
        new_ghost.dispersion = props.ghosts[self.duplicate_id].dispersion

        return {'FINISHED'}


class OGLRenderOperator(bpy.types.Operator):
    bl_label = "Render Lens Flare"
    bl_idname = "render.lens_flare_ogl_render"
    bl_description = "Renders lens flare into selected image"

    @classmethod
    def poll(cls, context):
        props: MasterProperties = context.scene.lens_flare_props
        if props.camera.use_override:
            return props.image is not None
        else:
            return props.image is not None and context.scene.camera is not None

    def execute(self, context):
        props: MasterProperties = context.scene.lens_flare_props

        start_time = time.perf_counter()

        # set values from camera
        if not props.camera.use_override:
            camera = context.scene.camera
            camera = bpy.data.cameras[camera.name]
            props.camera.rotation = camera.dof.aperture_rotation
            props.camera.blades = camera.dof.aperture_blades

        # set values from scene
        if not props.resolution.override_scene_resolution:
            props.resolution.resolution_x = context.scene.render.resolution_x
            props.resolution.resolution_y = context.scene.render.resolution_y

        # handle debug cross
        if props.debug_pos:
            image_processing.draw_debug_cross(props)

            end_time = time.perf_counter()
            self.report({'INFO'}, f"Lens flare total render time: {end_time - start_time}")

            refresh_compositor()

            return {'FINISHED'}

        # load default if none is specified
        if props.spectrum_image is None:
            bpy.ops.lens_flare.load_default_spectrum_image()

        props.spectrum_image.gl_load()

        buffer, draw_calls = ogl.render_lens_flare(props)

        props.image.scale(props.resolution.resolution_x, props.resolution.resolution_y)
        props.image.pixels.foreach_set(buffer)

        end_time = time.perf_counter()
        self.report({'INFO'}, f"Lens flare total render time: {end_time - start_time}")
        self.report({'INFO'}, f"Lens flare draw calls: {draw_calls}")

        refresh_compositor()

        return {'FINISHED'}


class RenderAnimationOperator(bpy.types.Operator):
    bl_label = "Render Lens Flare Animation"
    bl_idname = "render.lens_flare_anim"
    bl_description = "Renders animation with lens flare"

    @classmethod
    def poll(cls, context):
        return bpy.ops.render.lens_flare_ogl_render.poll()

    def execute(self, context):
        start = context.scene.frame_start
        end = context.scene.frame_end
        step = context.scene.frame_step
        bpy.context.scene.frame_set(start)

        current = bpy.context.scene.frame_current
        filepath_base = bpy.context.scene.render.filepath
        bpy.context.scene.render.image_settings.file_format = 'PNG'

        while True:
            bpy.ops.render.lens_flare_ogl_render()
            bpy.context.scene.render.filepath = f"{filepath_base}{current}.png"
            bpy.ops.render.render(write_still=True)

            bpy.context.scene.frame_set(current + step)
            current = bpy.context.scene.frame_current
            if current > end:
                break

        bpy.context.scene.render.filepath = filepath_base

        return {'FINISHED'}


class LoadDefaultSpectrumImageOperator(bpy.types.Operator):
    bl_label = "Load Default Spectrum Image"
    bl_idname = "lens_flare.load_default_spectrum_image"
    bl_description = "Loads default spectrum image"

    def execute(self, context):
        props: MasterProperties = context.scene.lens_flare_props

        img_path = os.path.join(os.path.dirname(__file__), 'images/spectral.png')
        spectral_img = bpy.data.images.load(img_path, check_existing=True)
        spectral_img.gl_load()
        props.spectrum_image = spectral_img

        return {'FINISHED'}


# Operator helpers
def refresh_compositor():
    """
    Quick and dirty way to refresh compositor. Adds new node and immediately removes it.
    """
    tree = bpy.context.scene.node_tree
    # if user does not have any nodes, no need to refresh, also,
    if tree is None:
        return
    node = tree.nodes.new(type='CompositorNodeRGB')
    tree.nodes.remove(node)
