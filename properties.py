import bpy
from bpy.props import \
    FloatProperty,\
    FloatVectorProperty,\
    StringProperty,\
    BoolProperty,\
    PointerProperty,\
    IntProperty,\
    CollectionProperty
from .panels import regenerate_ghost_icons


def get_ghost_color(self):
    if 'color' not in self:
        self['color'] = [0.9, 0.9, 0.9]
    return self['color']


def set_ghost_color(self, value):
    self['color'] = value
    regenerate_ghost_icons()


class GhostProperties(bpy.types.PropertyGroup):
    offset: FloatProperty(
        name="Offset",
        description="Ghost offset",
        default=0.0,
        soft_min=-1.0,
        soft_max=1.0,
    )
    perpendicular_offset: FloatProperty(
        name="Offset",
        description="Ghost offsetfrom the main axis",
        default=0.0,
        soft_min=-1.0,
        soft_max=1.0,
    )
    color: FloatVectorProperty(
        name="Color",
        description="Ghost color",
        subtype='COLOR_GAMMA',
        default=[0.9, 0.9, 0.9],
        size=3,
        min=0.0,
        soft_max=1.0,
        get=get_ghost_color,
        set=set_ghost_color,
    )
    size: FloatProperty(
        name="Size",
        description="Ghost Size",
        default=5.0,
        min=0.0,
    )
    name: StringProperty(
        name="Name",
        description="Ghost Name",
        default="New Ghost",
    )
    transparent_center: BoolProperty(
        name="Transparent Center",
        description="Renders ghost with more transparent center",
        default=True,
    )
    intensity: FloatProperty(
        name="Ghost Intensity",
        description="Intensity of the ghost artifact",
        default=1.0,
        min=0.0,
    )
    dispersion: FloatProperty(
        name="Ghost dispersion",
        description="Intensity of ghost dispersion (1.0 is no dispersion)",
        default=1.0,
        min=0.01,
        max=1.99,
    )


class FlareProperties(bpy.types.PropertyGroup):
    color: FloatVectorProperty(
        name="Flare Color",
        description="Color of the main flare",
        subtype='COLOR_GAMMA',
        default=[0.9, 0.9, 0.9],
        size=3,
        min=0.0,
        soft_max=1.0,
    )
    size: FloatProperty(
        name="Flare Size",
        description="Flare size relative to image size",
        default=10.0,
        min=0.0,
    )
    intensity: FloatProperty(
        name="Flare Intensity",
        description="Intensity of flare effect",
        default=1.0,
        min=0.0,
    )
    # these two control rays
    rays: BoolProperty(
        name="Flare Rays",
        description="Render rays coming from light source",
        default=False,
    )
    rays_intensity: FloatProperty(
        name="Rays Intensity",
        description="Intensity of ray effect",
        default=1.0,
        min=0.0,
    )


def get_blades(self):
    if 'blades' not in self:
        self['blades'] = 0
    return self['blades']


def set_blades(self, value):
    # same behaviour as default input on camera
    if 3 > value > 0:
        if self["blades"] == 0:
            self["blades"] = 3
        else:
            self["blades"] = 0
    else:
        self['blades'] = value


class CameraProperties(bpy.types.PropertyGroup):
    anamorphic: bpy.props.BoolProperty(
        name="Anamorphic Lens",
        description="Use anamorphic rays and flare",
        default=False,
    )
    use_override: bpy.props.BoolProperty(
        name="Camera Override",
        description="Use custom camera properties",
        default=True,
    )
    blades: bpy.props.IntProperty(
        name="Aperture Blades",
        description="Number of blades in aperture for polygonal bokeh (at least 3)",
        default=0,
        min=0,
        max=16,
        get=get_blades,
        set=set_blades,
    )
    rotation: bpy.props.FloatProperty(
        name="Aperture Rotation",
        description="Rotation of blades in aperture",
        default=0,
        subtype='ANGLE',
        unit='ROTATION',
        min=-3.14159,
        max=3.14159,
    )


class MasterProperties(bpy.types.PropertyGroup):
    position_x: FloatProperty(
        name="X",
        description="Position of light source on X axis",
        default=0.5,
        soft_min=0.0,
        soft_max=1.0,
    )
    position_y: FloatProperty(
        name="Y",
        description="Position of light source on X axis",
        default=0.5,
        soft_min=0.0,
        soft_max=1.0,
    )
    resolution_x: IntProperty(
        name="Resolution X",
        description="Number of horizontal pixels in rendered effect",
        default=1280,
        min=0,
        subtype='PIXEL',
    )
    resolution_y: IntProperty(
        name="Resolution Y",
        description="Number of vertical pixels in rendered effect",
        default=720,
        min=0,
        subtype='PIXEL',
    )
    image: PointerProperty(
        name="Image",
        description="Image to render to",
        type=bpy.types.Image,
    )
    master_intensity: FloatProperty(
        name="Master Intensity",
        description="Scales total effect intensity",
        default=1.0,
        min=0.0,
    )
    # quality control
    dispersion_samples: IntProperty(
        name="Dispersion Samples",
        description="Sets the quality of dispersion effect",
        default=16,
        min=8,
    )
    # prop groups
    flare: PointerProperty(
        name="Flare",
        type=FlareProperties,
    )
    camera: PointerProperty(
        name="Camera",
        type=CameraProperties,
    )
    # ghost props
    ghosts: CollectionProperty(
        name="Ghosts",
        type=GhostProperties,
    )
    selected_ghost: IntProperty(
        name="Active ghost number",
        min=0,
    )
    # debug props
    debug_pos: BoolProperty(
        name="Debug Cross",
        description="Render only cross with position",
        default=False,
    )
