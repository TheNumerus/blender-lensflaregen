bl_info = {
    "name": "Lens Flare Generator",
    "description": "Generates lens flare effects from image",
    "blender": (2, 92, 0),
    "category": "Node",
    "author": "Petr Volf",
    "version": (0, 2, 0),
    "warning": "Work in Progress version",
}


if "bpy" in locals():
    import importlib
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)
    importlib.reload(ogl)
    importlib.reload(shaders)
else:
    from . import properties
    from . import operators
    from . import panels

import bpy
import bpy.utils.previews

_classes = [
    # properties
    properties.FlareProperties,
    properties.GhostProperties,
    properties.CameraProperties,
    properties.ResolutionProperties,
    properties.MasterProperties,
    # panels
    panels.GhostsUiList,
    panels.MainSettingsPanel,
    panels.ResolutionPanel,
    panels.FlareSettingsPanel,
    panels.GhostsPanel,
    panels.CameraOverridePanel,
    panels.MiscPanel,
    # operators
    operators.AddGhostOperator,
    operators.RemoveGhostOperator,
    operators.DuplicateGhostOperator,
    operators.OGLRenderOperator,
    operators.LoadDefaultSpectrumImageOperator,
    operators.RenderAnimationOperator,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lens_flare_props = bpy.props.PointerProperty(type=properties.MasterProperties)

    coll = bpy.utils.previews.new()
    panels.previews['ghosts'] = coll


def unregister():
    for coll in panels.previews.values():
        bpy.utils.previews.remove(coll)
    panels.previews.clear()

    for cls in _classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lens_flare_props
