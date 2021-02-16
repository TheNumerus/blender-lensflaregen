import bpy


class LensFlareGhostPropertyGroup(bpy.types.PropertyGroup):
    offset: bpy.props.FloatProperty(name="Offset", description="Ghost offset", default=0.0)
    color: bpy.props.FloatVectorProperty(name="Color", description="Ghost color", subtype='COLOR_GAMMA', default=[0.9, 0.9, 0.9], size=3, min=0.0, soft_max=1.0)
    size: bpy.props.FloatProperty(name="Size", description="Ghost Size", default=5.0)


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


class LensFlareProperties(bpy.types.PropertyGroup):
    posx: bpy.props.FloatProperty(name="X", description="Position of light source on X axis", default=0.5)
    posy: bpy.props.FloatProperty(name="Y", description="Position of light source on X axis", default=0.5)
    resolution_x: bpy.props.IntProperty(name="Resolution X", description="Number of horizontal pixels in rendered effect", default=1280, min=0)
    resolution_y: bpy.props.IntProperty(name="Resolution Y", description="Number of vertical pixels in rendered effect", default=720, min=0)
    image: bpy.props.PointerProperty(name="Image", type=bpy.types.Image, description="Image to render to")
    master_intensity: bpy.props.FloatProperty(name="Master Intensity", description="Scales total effect intensity", default=1.0)
    use_override: bpy.props.BoolProperty(name="Camera Override", description="Use custom camera properties", default=True)
    blades: bpy.props.IntProperty(name="Aperture Blades", description="Number of blades in aperture for polygonal bokeh (at least 3)", default=0, min=0, max=16, get=get_blades, set=set_blades)
    rotation: bpy.props.FloatProperty(name="Aperture Rotation", description="Rotation of blades in aperture", default=0, subtype='ANGLE', unit='ROTATION', min=-3.14159, max=3.14159)
    flare_color: bpy.props.FloatVectorProperty(name="Flare Color", description="Color of the main flare", subtype='COLOR_GAMMA', default=[0.9, 0.9, 0.9], size=3, min=0.0, soft_max=1.0)
    flare_size: bpy.props.FloatProperty(name="Flare Size", description="Flare size relative to image size", default=10.0)
    flare_rays: bpy.props.BoolProperty(name="Flare Rays", description="Render rays coming from light source", default=False)
    flare_intensity: bpy.props.FloatProperty(name="Flare Intensity", default=1.0)
    ghosts: bpy.props.CollectionProperty(name="Ghosts", type=LensFlareGhostPropertyGroup)
    ghosts_empty_center: bpy.props.BoolProperty(name="Empty Centers", description="Renders ghosts with more transparent centers", default=False)
    debug_pos: bpy.props.BoolProperty(name="Debug Cross", description="Render only cross with position", default=False)