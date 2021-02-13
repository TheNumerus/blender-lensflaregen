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
from . import image_processing


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


class RenderLensFlareOperator(bpy.types.Operator):
    bl_label = "Render Lens Flare"
    bl_idname = "render.lens_flare_render"
    bl_description = "Renders lens flare into selected image"

    def execute(self, context):
        props: LensFlareProperties = context.scene.lens_flare_props

        start_time = time.perf_counter()

        try:
            blades, rotation = camera_settings(context)
        except Exception as e:
            self.report({'ERROR_INVALID_INPUT'}, e.args[0])
            return {'CANCELLED'}

        # don't render if the is no valid output
        if props.image is None:
            self.report({'ERROR_INVALID_INPUT'}, "No image selected")
            return {'CANCELLED'}

        if props.debug_pos:
            image_processing.draw_debug_cross(props)
        else:
            # TODO move somewhere else
            max_x = props.resolution_x
            max_y = props.resolution_y

            res_buffer = np.full(shape=(max_x * max_y, 4), fill_value=1.0)

            color = props.flare_color
            center_x = max_x / 2
            center_y = max_y / 2

            ratio = max_x / max_y

            flare_x = props.posx * max_x
            flare_y = props.posy * max_y

            render_start = time.perf_counter()

            for i, pixel in enumerate(res_buffer):
                x = i % max_x
                y = i // max_x

                value = image_processing.compute_flare_intensity(x, y, max_x, max_y, props, ratio)
                pixel[0] = color[0] * value * props.flare_intensity
                pixel[1] = color[1] * value * props.flare_intensity
                pixel[2] = color[2] * value * props.flare_intensity

                for ghost in props.ghosts:
                    ghost_x = center_x + (flare_x - center_x) * ghost.offset
                    ghost_y = center_y + (flare_y - center_y) * ghost.offset

                    # TODO this is stupid and has too sharp edges, not even polygonal
                    value = min(max((ghost.size * 100) - ((x - ghost_x) ** 2 + (y - ghost_y) ** 2), 0.0), 1.0)

                    pixel[0] += ghost.color[0] * value
                    pixel[1] += ghost.color[1] * value
                    pixel[2] += ghost.color[2] * value

            self.report({'INFO'}, f"Lens flare only render loop time: {time.perf_counter() - render_start}")

            buffer = np.reshape(res_buffer, (-1))

            props.image.scale(max_x, max_y)
            props.image.pixels = list(buffer)

        props.image.update()

        # force compositing refresh
        bpy.ops.render.render(write_still=True)

        end_time = time.perf_counter()

        self.report({'INFO'}, f"Lens flare total render time: {end_time - start_time}")

        return {'FINISHED'}


class OGLRenderOperator(bpy.types.Operator):
    bl_label = "Render Ghost With OpenGL"
    bl_idname = "render.ghost_ogl_render"
    bl_description = "Renders lens flare ghost into selected image"

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

        max_x = props.resolution_x
        max_y = props.resolution_y

        ratio = max_x / max_y

        if blades == 0:
            blades = 64

        offscreen = gpu.types.GPUOffScreen(max_x, max_y)

        shader = gpu.types.GPUShader(_vertex_shader_ghost, _fragment_shader_ghost)
        ghost_batch = batch_from_blades(blades, shader)

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

                # TODO render glare

                shader.bind()
                # fix aspect ratio
                shader.uniform_float("aspect_ratio", ratio)
                for ghost in props.ghosts:

                    ghost_x = ((props.posx - 0.5) * 2.0) * ghost.offset
                    ghost_y = ((props.posy - 0.5) * 2.0) * ghost.offset
                    # move and scale ghosts
                    shader.uniform_float("modelMatrix", Matrix.Translation((ghost_x, ghost_y, 0.0)) @ Matrix.Scale(ghost.size / 100, 4))
                    # rotate ghost
                    shader.uniform_float("rotationMatrix", Matrix.Rotation(rotation, 4, 'Z'))
                    # set color
                    shader.uniform_float("color", Vector((ghost.color[0], ghost.color[1], ghost.color[2], 1)))

                    # set centers
                    if props.ghosts_empty_center:
                        shader.uniform_float("empty", 1.0)
                    else:
                        shader.uniform_float("empty", 0.0)

                    ghost_batch.draw(shader)

            buffer = bgl.Buffer(bgl.GL_BYTE, max_x * max_y * 4)
            bgl.glReadBuffer(bgl.GL_BACK)
            bgl.glReadPixels(0, 0, max_x, max_y, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer)

        offscreen.free()

        props.image.scale(max_x, max_y)
        props.image.pixels = [v / 255 for v in buffer]

        # force compositing refresh
        bpy.ops.render.render(write_still=True)

        end_time = time.perf_counter()

        self.report({'INFO'}, f"Lens flare total render time: {end_time - start_time}")

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


# shader strings
_vertex_shader_ghost = '''
    uniform mat4 modelMatrix;
    uniform mat4 rotationMatrix;
    uniform float aspect_ratio;

    in vec2 position;
    in vec4 vertColor;

    out vec2 posInterp;
    out vec4 colorInterp;

    void main() {
        posInterp = position;
        colorInterp = vertColor;
        vec4 pos_post_rotation = vec4(position, 0.0, 1.0) * rotationMatrix;
        gl_Position = modelMatrix * vec4(pos_post_rotation.xy * vec2(1.0, aspect_ratio), 0.0, 1.0);
    }
'''

_fragment_shader_ghost = '''
    uniform vec4 color;
    uniform float empty;
    
    in vec2 posInterp;
    in vec4 colorInterp;
    
    out vec4 FragColor;
    
    void main() {
        float center = sqrt(pow(posInterp.x, 2.0) + pow(posInterp.y, 2.0));
        float gauss = 0.4 * pow(2.7, -(pow(center, 2.0) / 0.3));
        float edge = (1.0 - pow(colorInterp.x, 40.0)) - (gauss * empty);
        FragColor = vec4(posInterp, 0.0, 1.0) * 0.05 + color * edge;
    }
'''