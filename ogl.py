import math
from typing import Any, Dict

import gpu
import bgl
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from . import shaders
from .properties import MasterProperties


def render_lens_flare(props: MasterProperties):
    """
    Renders lens flare effect to buffer
    :returns buffer with effect
    """
    max_x = props.resolution_x
    max_y = props.resolution_y

    ratio = max_x / max_y

    # render kinda circles
    blades = props.camera.blades
    if blades == 0:
        blades = 64

    (flare_vector_x, flare_vector_y) = (props.position_x - 0.5, props.position_y - 0.5);
    flare_vector_len = math.sqrt(pow(flare_vector_x, 2) + pow(flare_vector_y, 2) + 0.0001)
    flare_vector_x /= flare_vector_len
    flare_vector_y /= flare_vector_len

    offscreen = gpu.types.GPUOffScreen(max_x, max_y)
    ghost_fb = gpu.types.GPUOffScreen(max_x, max_y)

    ghost_shader = gpu.types.GPUShader(shaders.vertex_shader_ghost, shaders.fragment_shader_ghost)
    ghost_batch = batch_from_blades(blades, ghost_shader)

    flare_shader = gpu.types.GPUShader(shaders.vertex_shader_quad, shaders.fragment_shader_flare)
    flare_batch = batch_quad(flare_shader)

    copy_shader = gpu.types.GPUShader(shaders.vertex_shader_quad, shaders.fragment_shader_copy_ca)

    # clear framebuffer
    with offscreen.bind():
        # black background
        bgl.glClearColor(0.0, 0.0, 0.0, 1.0)
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)

    # first render ghosts one by one
    for ghost in props.ghosts:
        # calculate position
        ghost_x = ((props.position_x - 0.5) * 2.0) * ghost.offset
        ghost_y = ((props.position_y - 0.5) * 2.0) * ghost.offset
        # add perpendicular offset
        ghost_x += flare_vector_y * ghost.perpendicular_offset
        ghost_y += -flare_vector_x * ghost.perpendicular_offset

        with ghost_fb.bind():
            # black background
            bgl.glClearColor(0.0, 0.0, 0.0, 1.0)
            bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)

            with gpu.matrix.push_pop():
                # reset matrices
                gpu.matrix.load_matrix(Matrix.Identity(4))
                gpu.matrix.load_projection_matrix(Matrix.Identity(4))

                ghost_shader.bind()

                # transform matrix
                model_matrix = Matrix.Translation((ghost_x, ghost_y, 0.0)) @ Matrix.Scale(ghost.size / 100, 4)
                # transparency
                center_transparency = 0.0
                if ghost.transparent_center:
                    center_transparency = 1.0

                ghost_uniforms = {
                    # move and scale ghosts
                    "modelMatrix": model_matrix,
                    # rotate ghost
                    "rotationMatrix": Matrix.Rotation(props.camera.rotation, 4, 'Z'),
                    # set color and intensity
                    "color": Vector((ghost.color[0], ghost.color[1], ghost.color[2], 1)),
                    "master_intensity": props.master_intensity,
                    "intensity": ghost.intensity,
                    # set centers
                    "empty": center_transparency,
                    # aspect ratio of destination image
                    "aspect_ratio": ratio,
                }

                set_uniforms(ghost_shader, ghost_uniforms)

                ghost_batch.draw(ghost_shader)

        with offscreen.bind():
            # now copy to final buffer
            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, ghost_fb.color_texture)

            with gpu.matrix.push_pop():
                copy_shader.bind()
                # reset matrices
                gpu.matrix.load_matrix(Matrix.Identity(4))
                gpu.matrix.load_projection_matrix(Matrix.Identity(4))

                copy_shader.uniform_float("ghost", 0)
                copy_shader.uniform_float("dispersion", ghost.dispersion)

                flare_batch.draw(copy_shader)

    # finally render flare on top
    with offscreen.bind():
        render_flare(props, flare_shader, flare_batch)

        # copy rendered image to RAM
        buffer = bgl.Buffer(bgl.GL_FLOAT, max_x * max_y * 4)
        bgl.glReadBuffer(bgl.GL_BACK)
        bgl.glReadPixels(0, 0, max_x, max_y, bgl.GL_RGBA, bgl.GL_FLOAT, buffer)

    offscreen.free()
    ghost_fb.free()

    return buffer


def render_flare(props: MasterProperties, flare_shader, flare_batch):
    """
    Renders flare to active buffer
    """
    with gpu.matrix.push_pop():
        # reset matrices
        gpu.matrix.load_matrix(Matrix.Identity(4))
        gpu.matrix.load_projection_matrix(Matrix.Identity(4))

        # render glare
        flare_color = Vector((props.flare.color[0], props.flare.color[1], props.flare.color[2], 1.0))
        flare_position = Vector((props.position_x, props.position_y))
        flare_rays = 0.0
        if props.flare.rays:
            flare_rays = 1.0 * props.flare.rays_intensity

        ratio = props.resolution_x / props.resolution_y
        flare_shader.bind()

        flare_uniforms = {
            "color": flare_color,
            "size": props.flare.size,
            "intensity": props.flare.intensity,
            "flare_position": flare_position,
            "aspect_ratio": ratio,
            "blades": float(props.camera.blades),
            "use_rays": flare_rays,
            "rotation": props.camera.rotation,
            "master_intensity": props.master_intensity,
        }

        set_uniforms(flare_shader, flare_uniforms)

        flare_batch.draw(flare_shader)


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


def set_uniforms(shader: gpu.types.GPUShader, uniforms: Dict[str, Any]):
    """
    Sets uniforms to shader.
    :param shader shader to set uniforms to
    :param uniforms dictionary of uniforms
    """
    for name, uniform in uniforms.items():
        shader.uniform_float(name, uniform)