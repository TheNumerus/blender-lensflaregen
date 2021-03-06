import math
import random
from typing import Any, Dict

import gpu
import bgl
import bpy
import bpy_extras
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from .shaders import Shaders
from .properties import MasterProperties


def render_debug_cross(context, props: MasterProperties) -> (bgl.Buffer, int):
    """
    Render debug cross
    :returns buffer with image and draw call count
    """
    shaders = Shaders()

    offscreen = gpu.types.GPUOffScreen(props.resolution.resolution_x, props.resolution.resolution_y)
    draw_count = 0

    quad_batch = batch_quad(shaders.debug)

    with offscreen.bind():
        # black background
        bgl.glClearColor(0.0, 0.0, 0.0, 1.0)
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)

        shaders.debug.bind()

        for position in props.positions:
            pos = Vector((position.manual_x, position.manual_y))

            # set position from object
            if position.variant == 'auto' and position.auto_object is not None:
                world_pos = position.auto_object.matrix_world.to_translation()
                pos = bpy_extras.object_utils.world_to_camera_view(context.scene, context.scene.camera, world_pos)

            uniforms = {
                "flare_position": pos.xy,
                "aspect_ratio": props.resolution.resolution_x / props.resolution.resolution_y,
            }

            set_float_uniforms(shaders.debug, uniforms)

            quad_batch.draw(shaders.debug)
            draw_count += 1

        # copy rendered image to RAM
        buffer = bgl.Buffer(bgl.GL_FLOAT, props.resolution.resolution_x * props.resolution.resolution_y * 4)
        bgl.glReadBuffer(bgl.GL_BACK)
        bgl.glReadPixels(0, 0, props.resolution.resolution_x, props.resolution.resolution_y, bgl.GL_RGBA, bgl.GL_FLOAT, buffer)

    return buffer, draw_count


def render_lens_flare(context, props: MasterProperties) -> (bgl.Buffer, int):
    """
    Renders lens flare effect to buffer
    :returns buffer with effect
    """
    max_x = props.resolution.resolution_x
    max_y = props.resolution.resolution_y

    # render kinda circles
    blades = props.camera.blades
    if blades == 0:
        blades = 256

    shaders = Shaders()

    offscreen = gpu.types.GPUOffScreen(max_x, max_y)
    ghost_fb = gpu.types.GPUOffScreen(max_x, max_y)

    ghost_batch = batch_from_blades(blades, shaders.ghost)
    quad_batch = batch_quad(shaders.flare)

    draw_count = 0

    noise_tex = NoiseTexture()

    # clear framebuffer
    with offscreen.bind():
        # black background
        bgl.glClearColor(0.0, 0.0, 0.0, 1.0)
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)

    for position in props.positions:
        pos = Vector((position.manual_x, position.manual_y))

        # set position from object
        if position.variant == 'auto' and position.auto_object is not None:
            world_pos = position.auto_object.matrix_world.to_translation()
            pos = bpy_extras.object_utils.world_to_camera_view(context.scene, context.scene.camera, world_pos)

        flare_vector = pos.xy - Vector((0.5, 0.5))
        flare_vector.normalize()

        # first render ghosts one by one
        for ghost in props.ghosts:
            # calculate position
            ghost_x = ((pos.x - 0.5) * 2.0) * ghost.offset
            ghost_y = ((pos.y - 0.5) * 2.0) * ghost.offset
            # add perpendicular offset
            ghost_x += flare_vector.y * ghost.perpendicular_offset
            ghost_y += -flare_vector.x * ghost.perpendicular_offset

            with ghost_fb.bind():
                render_ghost(props, ghost, shaders.ghost, ghost_batch, flare_vector, pos)
                draw_count += 1

            with offscreen.bind():
                # now copy to final buffer
                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, ghost_fb.color_texture)

                # disable wrapping
                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_BORDER)
                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_BORDER)

                border_color = bgl.Buffer(bgl.GL_FLOAT, 4, [0.0, 0.0, 0.0, 1.0])

                bgl.glTexParameterfv(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_BORDER_COLOR, border_color)

                bgl.glActiveTexture(bgl.GL_TEXTURE2)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, props.spectrum_image.bindcode)

                bgl.glActiveTexture(bgl.GL_TEXTURE1)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, noise_tex.gl_code)

                copy_ghost(shaders.copy, quad_batch, ghost, props, Vector((ghost_x, ghost_y)))
                draw_count += 1

        # finally render flare on top
        with offscreen.bind():
            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, noise_tex.gl_code)

            render_flare(props, pos.xy, shaders.flare, quad_batch)
            draw_count += 1

    with offscreen.bind():
        # copy rendered image to RAM
        buffer = bgl.Buffer(bgl.GL_FLOAT, max_x * max_y * 4)
        bgl.glReadBuffer(bgl.GL_BACK)
        bgl.glReadPixels(0, 0, max_x, max_y, bgl.GL_RGBA, bgl.GL_FLOAT, buffer)

    offscreen.free()
    ghost_fb.free()
    noise_tex.free()

    return buffer, draw_count


def render_flare(props: MasterProperties, position, flare_shader, flare_batch):
    """
    Renders flare to active buffer
    """
    # render glare
    flare_color = Vector((props.flare.color[0], props.flare.color[1], props.flare.color[2], 1.0))

    blades = props.camera.blades
    if blades == 0:
        blades = 64

    ratio = props.resolution.resolution_x / props.resolution.resolution_y
    flare_shader.bind()

    flare_uniforms = {
        "color": flare_color,
        "size": props.flare.size,
        "intensity": props.flare.intensity,
        "flare_position": position,
        "aspect_ratio": ratio,
        "blades": blades,
        "ray_intensity": props.flare.rays_intensity,
        "rotation": props.camera.rotation,
        "master_intensity": props.master_intensity,
        "res": [props.resolution.resolution_x / 64, props.resolution.resolution_y / 64],
        "anamorphic": float(props.flare.anamorphic),
    }

    set_float_uniforms(flare_shader, flare_uniforms)

    flare_int_uniforms = {
        "noise": 0
    }

    set_int_uniforms(flare_shader, flare_int_uniforms)

    flare_batch.draw(flare_shader)


def render_ghost(props: MasterProperties, ghost, ghost_shader, ghost_batch, flare_vector, flare_position):
    """
    Renders ghost to active buffer
    """
    # black background
    bgl.glClearColor(0.0, 0.0, 0.0, 1.0)
    bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)

    # calculate position
    ghost_x = ((flare_position.x - 0.5) * 2.0) * ghost.offset
    ghost_y = ((flare_position.y - 0.5) * 2.0) * ghost.offset
    # add perpendicular offset
    ghost_x += flare_vector.y * ghost.perpendicular_offset
    ghost_y += -flare_vector.x * ghost.perpendicular_offset

    ratio = props.resolution.resolution_x / props.resolution.resolution_y

    ghost_shader.bind()

    # transform matrix
    model_matrix = Matrix.Translation((ghost_x, ghost_y, 0.0)) @ Matrix.Scale(ghost.size / 100, 4)

    ghost_uniforms = {
        # move and scale ghosts
        "modelMatrix": model_matrix,
        # rotate ghost
        "rotationMatrix": Matrix.Rotation(props.camera.rotation, 4, 'Z'),
        # set color and intensity
        "color": Vector((ghost.color[0], ghost.color[1], ghost.color[2], 1)),
        # set centers
        "empty": ghost.center_transparency,
        # aspect ratio of destination image
        "aspect_ratio": ratio,
        # anamorphic lens simulation
        "ratio": ghost.ratio,
    }

    set_float_uniforms(ghost_shader, ghost_uniforms)

    ghost_batch.draw(ghost_shader)


def copy_ghost(copy_shader, quad_batch, ghost, props, ghost_pos):
    copy_shader.bind()

    copy_int_uniforms = {
        "ghost": 0,
        "spectral": 2,
        "noise": 1,
        "samples": props.dispersion_samples,
    }

    set_int_uniforms(copy_shader, copy_int_uniforms)

    if ghost.dispersion_center == 'image':
        disperse_center = 0.0
    else:
        disperse_center = 1.0

    copy_float_uniforms = {
        "dispersion": ghost.dispersion,
        "distortion": ghost.distortion,
        "master_intensity": props.master_intensity,
        "intensity": ghost.intensity,
        "res": [props.resolution.resolution_x / 64, props.resolution.resolution_y / 64],
        "use_jitter": float(props.use_jitter),
        "disperse_from_ghost_center": disperse_center,
        "ghost_pos": ghost_pos
    }

    set_float_uniforms(copy_shader, copy_float_uniforms)

    quad_batch.draw(copy_shader)


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


def set_float_uniforms(shader: gpu.types.GPUShader, uniforms: Dict[str, Any]):
    """
    Sets uniforms to shader.
    :param shader shader to set uniforms to
    :param uniforms dictionary of uniforms
    """
    for name, uniform in uniforms.items():
        shader.uniform_float(name, uniform)


def set_int_uniforms(shader: gpu.types.GPUShader, uniforms: Dict[str, Any]):
    """
    Sets uniforms to shader.
    :param shader shader to set uniforms to
    :param uniforms dictionary of uniforms
    """
    for name, uniform in uniforms.items():
        shader.uniform_int(name, uniform)


class NoiseTexture:
    __noise_buf = None

    @classmethod
    def __generate(cls):
        if cls.__noise_buf is not None:
            return
        values = []

        for pixel in range(0, 64 * 64):
            val = random.random()
            values.extend([val, val, val, 1.0])

        cls.__noise_buf = bgl.Buffer(bgl.GL_FLOAT, 64 * 64 * 4, values)

    def __init__(self):
        self.__generate()

        self.__buffer = bgl.Buffer(bgl.GL_INT, 1)
        self.gl_code = self.__buffer.to_list()[0]

        bgl.glGenTextures(1, self.__buffer)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.gl_code)
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA32F, 64, 64, 0, bgl.GL_RGBA, bgl.GL_FLOAT, self.__noise_buf)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)

    def free(self):
        bgl.glDeleteTextures(1, self.__buffer)
