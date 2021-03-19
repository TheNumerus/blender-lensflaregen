import time

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
    bl_description = "Removes active ghost"

    remove_id: bpy.props.IntProperty(default=-1, description="Index of ghost to remove")

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

    def execute(self, context):
        props: MasterProperties = context.scene.lens_flare_props

        self.report({'INFO'}, "TEST_PRE")

        active_ghost: GhostProperties = props.ghosts[props.selected_ghost]

        self.report({'INFO'}, "TEST")

        # TODO clean-up
        new_ghost: GhostProperties = props.ghosts.add()

        new_ghost.color = active_ghost.color
        new_ghost.intensity = active_ghost.intensity
        new_ghost.name = active_ghost.name
        new_ghost.offset = active_ghost.offset
        new_ghost.perpendicular_offset = active_ghost.perpendicular_offset
        new_ghost.size = active_ghost.size
        new_ghost.transparent_center = active_ghost.transparent_center

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
            camera = bpy.context.scene.camera
            camera = bpy.data.cameras[camera.name]
            props.camera.rotation = camera.dof.aperture_rotation
            props.camera.blades = camera.dof.aperture_blades

        # handle debug cross
        if props.debug_pos:
            image_processing.draw_debug_cross(props)

            end_time = time.perf_counter()
            self.report({'INFO'}, f"Lens flare total render time: {end_time - start_time}")

            refresh_compositor()

            return {'FINISHED'}

        buffer = ogl.render_lens_flare(props)

        props.image.scale(props.resolution_x, props.resolution_y)
        props.image.pixels = [v for v in buffer]

        end_time = time.perf_counter()
        self.report({'INFO'}, f"Lens flare total render time: {end_time - start_time}")

        refresh_compositor()

        return {'FINISHED'}


class RenderAnimationOperator(bpy.types.Operator):
    bl_label = "Render Lens Flare Animation"
    bl_idname = "render.lens_flare_anim"
    bl_description = "Renders animation with lens flare"

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
