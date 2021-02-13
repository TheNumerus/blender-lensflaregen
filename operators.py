from .properties import *
import time
import numpy as np
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

    def camera_settings(self, context):
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

    def execute(self, context):
        props: LensFlareProperties = context.scene.lens_flare_props

        start_time = time.perf_counter()

        try:
            blades, rotation = self.camera_settings(context)
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
            max_x, max_y = props.image.size

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

            props.image.pixels = list(buffer)

        props.image.update()

        # force compositing refresh
        bpy.ops.render.render(write_still=True)

        end_time = time.perf_counter()

        self.report({'INFO'}, f"Lens flare total render time: {end_time - start_time}")

        return {'FINISHED'}
