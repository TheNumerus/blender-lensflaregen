import bpy

bl_info = {
    "name": "Lens Flare Generator",
    "description": "Generates lens flare effects from image",
    "blender": (2, 90, 0),
    "category": "Node",
    "author": "Petr Volf",
    "version": (0,1,0),
    "warning": "NEFUNGUJE",
}


class LensFlarePanel(bpy.types.Panel):
    bl_label = "Lens Flare Generators"
    bl_idname = "LensFlarePanel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Lens Flares' 
 
    def draw(self, context):
        layout = self.layout
 
        row = layout.row()
        row.operator('node.lens_flare_operator')


def create_flare_group(context, operator, group_name):
    bpy.context.scene.use_nodes = True
    
    test_group = bpy.data.node_groups.new(group_name, 'CompositorNodeTree')
    
    group_in = test_group.nodes.new('NodeGroupInput')
    group_in.location = (0, 0)
    test_group.inputs.new('NodeSocketColor', 'Image Input')
    test_group.inputs.new('NodeSocketFloatPercentage', 'Position X')
    test_group.inputs.new('NodeSocketFloatPercentage', 'Position Y')

    ellipse = test_group.nodes.new('CompositorNodeEllipseMask')
    ellipse.location = (200, 0)

    group_out = test_group.nodes.new('NodeGroupOutput')
    group_out.location = (400, 0)
    test_group.outputs.new('NodeSocketColor', 'Image Output')

    link = test_group.links.new
    
    link(group_in.outputs[0], ellipse.inputs[0])
    link(ellipse.outputs[0], group_out.inputs[0])
    
    return test_group


class AddLensFlareGroupOperator(bpy.types.Operator):
    bl_label = "Add Lens Flare Node Group"
    bl_idname = "node.lens_flare_operator"
    
    def execute(self, context):
        custom_node_name = "Lens Flare Generator"
        my_group = create_flare_group(self, context, custom_node_name)
        test_node = context.scene.node_tree.nodes.new('CompositorNodeGroup')
        test_node.node_tree = bpy.data.node_groups[my_group.name]
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(LensFlarePanel)
    bpy.utils.register_class(AddLensFlareGroupOperator)


def unregister():
    bpy.utils.unregister_class(LensFlarePanel)
    bpy.utils.unregister_class(AddLensFlareGroupOperator)
