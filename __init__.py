bl_info = {
    "name": "Lens Flare Generator",
    "description": "Generates lens flare effects from image",
    "blender": (2, 91, 0),
    "category": "Node",
    "author": "Petr Volf",
    "version": (0, 1, 2),
    "warning": "Work in Progress version",
}


if "bpy" in locals():
    import importlib
    importlib.reload(image_processing)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)
else:
    from . import image_processing
    from . import properties
    from . import operators
    from . import panels

import bpy

_classes = [
    # properties
    properties.LensFlareGhostPropertyGroup,
    properties.LensFlareProperties,
    # panels
    panels.MainSettingsPanel,
    panels.FlareSettingsPanel,
    panels.GhostsPanel,
    panels.CameraOverridePanel,
    panels.MiscPanel,
    # operators
    operators.AddGhostOperator,
    operators.RemoveGhostOperator,
    operators.OGLRenderOperator
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lens_flare_props = bpy.props.PointerProperty(type=properties.LensFlareProperties)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lens_flare_props
