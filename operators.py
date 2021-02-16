import math
from gpu_extras.batch import batch_for_shader

from .properties import *
import time
import numpy as np
import gpu
import bgl
import random
from mathutils import Matrix, Vector, Euler
from gpu_extras.presets import draw_circle_2d
from . import image_processing, shaders


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


class OGLRenderOperator(bpy.types.Operator):
    bl_label = "Render Lens Flare"
    bl_idname = "render.lens_flare_ogl_render"
    bl_description = "Renders lens flare into selected image"

    def execute(self, context):
        props: LensFlareProperties = context.scene.lens_flare_props

        start_time = time.perf_counter()

        if props.image is None:
            self.report({'ERROR_INVALID_INPUT'}, "No image selected")
            return {'CANCELLED'}

        try:
            blades, rotation = camera_settings(context)
        except Exception as e:
            self.report({'ERROR_INVALID_INPUT'}, e.args[0])
            return {'CANCELLED'}

        # handle debug cross
        if props.debug_pos:
            image_processing.draw_debug_cross(props)

            end_time = time.perf_counter()
            self.report({'INFO'}, f"Lens flare total render time: {end_time - start_time}")

            refresh_compositor()

            return {'FINISHED'}

        max_x = props.resolution_x
        max_y = props.resolution_y

        ratio = max_x / max_y

        if blades == 0:
            blades = 64

        offscreen = gpu.types.GPUOffScreen(max_x, max_y)

        ghost_shader = gpu.types.GPUShader(shaders.vertex_shader_ghost, shaders.fragment_shader_ghost)
        ghost_batch = batch_from_blades(blades, ghost_shader)

        flare_shader = gpu.types.GPUShader(shaders.vertex_shader_quad, shaders.fragment_shader_flare)
        flare_batch = batch_quad(flare_shader)

        with offscreen.bind():
            # black background
            bgl.glClearColor(0.0, 0.0, 0.0, 1.0)
            bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)

            with gpu.matrix.push_pop():
                # reset matrices
                gpu.matrix.load_matrix(Matrix.Identity(4))
                gpu.matrix.load_projection_matrix(Matrix.Identity(4))

                # render glare
                flare_color = Vector((props.flare_color[0], props.flare_color[1], props.flare_color[2], 1.0))
                flare_position = Vector((props.posx, props.posy))
                flare_rays = 0.0
                if props.flare_rays:
                    flare_rays = 1.0
                flare_shader.bind()

                flare_shader.uniform_float("color", flare_color)
                flare_shader.uniform_float("size", props.flare_size)
                flare_shader.uniform_float("intensity", props.flare_intensity)
                flare_shader.uniform_float("flare_position", flare_position)
                flare_shader.uniform_float("aspect_ratio", ratio)
                flare_shader.uniform_float("blades", float(blades))
                flare_shader.uniform_float("use_rays", flare_rays)
                flare_shader.uniform_float("rotation", rotation)
                flare_shader.uniform_float("master_intensity", props.master_intensity)

                flare_batch.draw(flare_shader)

                # draw ghosts
                ghost_shader.bind()
                # fix aspect ratio
                ghost_shader.uniform_float("aspect_ratio", ratio)
                for ghost in props.ghosts:

                    ghost_x = ((props.posx - 0.5) * 2.0) * ghost.offset
                    ghost_y = ((props.posy - 0.5) * 2.0) * ghost.offset
                    # move and scale ghosts
                    ghost_shader.uniform_float("modelMatrix", Matrix.Translation((ghost_x, ghost_y, 0.0)) @ Matrix.Scale(ghost.size / 100, 4))
                    # rotate ghost
                    ghost_shader.uniform_float("rotationMatrix", Matrix.Rotation(rotation, 4, 'Z'))
                    # set color
                    ghost_shader.uniform_float("color", Vector((ghost.color[0], ghost.color[1], ghost.color[2], 1)))
                    ghost_shader.uniform_float("master_intensity", props.master_intensity)

                    # set centers
                    if props.ghosts_empty_center:
                        ghost_shader.uniform_float("empty", 1.0)
                    else:
                        ghost_shader.uniform_float("empty", 0.0)

                    ghost_batch.draw(ghost_shader)

            # copy rendered image to RAM
            buffer = bgl.Buffer(bgl.GL_FLOAT, max_x * max_y * 4)
            bgl.glReadBuffer(bgl.GL_BACK)
            bgl.glReadPixels(0, 0, max_x, max_y, bgl.GL_RGBA, bgl.GL_FLOAT, buffer)

        offscreen.free()

        props.image.scale(max_x, max_y)
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
def camera_settings(context):
    """
    Returns camera aperture shape and rotation from active camera, or from override
    :return: blades, rotation
    """
    props: LensFlareProperties = context.scene.lens_flare_props

    # get camera settings from active camera if no override
    if not props.use_override:
        camera = bpy.context.scene.camera
        if camera is None:
            raise Exception("No camera is active")
        camera = bpy.data.cameras[camera.name]

        return camera.dof.aperture_blades, camera.dof.aperture_rotation

    return props.blades, props.rotation


def batch_from_blades(blades: int, shader):
    positions = [(0.0,  0.0)]
    colors = [(0.0, 0.0, 0.0, 1.0)]

    start = Vector((1.0, 0.0))

    # we need one point twice
    for i in range(blades + 1):
        positions.append((start.x, start.y))
        colors.append((1.0, 1.0, 1.0, 1.0))
        start.rotate(Matrix.Rotation(math.radians(360 / blades), 2))

    return batch_for_shader(shader, 'TRI_FAN', {"position": tuple(positions), "vertColor": tuple(colors)})


def batch_quad(shader):
    positions = [(-1.0, -1.0), (-1.0, 1.0), (1.0, -1.0), (1.0, 1.0)]
    uv = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]

    return batch_for_shader(shader, 'TRI_STRIP', {"position": tuple(positions), "uv": tuple(uv)})


def refresh_compositor():
    """
    Quick and dirty way to refresh compositor. Adds new node and immediately removes it.
    """
    tree = bpy.context.scene.node_tree
    node = tree.nodes.new(type='CompositorNodeRGB')
    tree.nodes.remove(node)
