import bpy
import math
from mathutils import Vector, Euler

# --- Global Settings ---
FPS = 30
TOTAL_FRAMES = math.ceil(138 * FPS)  # 1:38 duration

# Animation durations (in frames)
FADE_DURATION = 0.75 * FPS  # 0.75 seconds
SLIDE_DURATION = 0.75 * FPS  # 0.75 seconds
SHORT_ANIM_DURATION = 0.5 * FPS  # 0.5 seconds
LONG_TRANSITION_DURATION = 1.5 * FPS  # 1.5 seconds
GLOW_PULSE_DURATION = 0.5 * FPS  # 0.5 seconds
DRAW_DURATION = 2 * FPS  # For graph drawing

# Easing types
EASE_IN_OUT = 'QUARTIC'
EASE_OUT = 'QUARTIC_OUT'
EASE_IN = 'QUARTIC_IN'
LINEAR = 'LINEAR'

# Global variable to hold collections for easier access
collections = {}

# --- Utility Functions ---

def clean_scene():
    """Deletes all objects in the current scene."""
    # Ensure no objects are in edit mode
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    # Select all objects and delete
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clear all collections except the master scene collection
    for collection in bpy.data.collections:
        if collection.name != "Scene Collection":
            bpy.data.collections.remove(collection)

    # Reset frame to 0
    bpy.context.scene.frame_set(0)

def setup_collections():
    """Sets up a structured collection hierarchy."""
    scene_col = bpy.context.scene.collection
    
    # Define collection names
    collection_names = [
        "_WORLD",
        "_MATH_ELEMENTS",
        "_CAMERA_RIG",
        "_LIGHTS",
        "_TEMP_ASSETS" # For temporary objects
    ]

    # Create and link collections
    for name in collection_names:
        if name not in bpy.data.collections:
            new_col = bpy.data.collections.new(name)
            scene_col.children.link(new_col)
            collections[name] = new_col
        else:
            collections[name] = bpy.data.collections[name] # Use existing

def add_object_to_collection(obj, collection_name):
    """Adds an object to a specified collection and removes it from the default."""
    if collection_name not in collections:
        print(f"Warning: Collection '{collection_name}' not found. Object '{obj.name}' not added.")
        return

    # Remove from all current collections it's linked to, except the target one
    # Iterate over a copy of the list because we're modifying it
    for col in list(obj.users_collection):
        if col != collections[collection_name]:
            col.objects.unlink(obj)

    # Link to the specified collection if not already linked
    if obj not in collections[collection_name].objects:
        collections[collection_name].objects.link(obj)

def set_active_object(obj):
    """Sets an object as active and selected."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def create_material(name, color=(0.8, 0.8, 0.8, 1), emission_strength=0.0, roughness=0.8, metallic=0.0, transmission=0.0, ior=1.45, blend_method='OPAQUE', use_nodes=True):
    """Creates or retrieves a Principled BSDF material."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = use_nodes
        
        if use_nodes:
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if bsdf is None:
                bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
                mat.node_tree.links.new(bsdf.outputs['BSDF'], mat.node_tree.nodes['Material Output'].inputs['Surface'])
            
            bsdf.inputs['Base Color'].default_value = color
            bsdf.inputs['Roughness'].default_value = roughness
            bsdf.inputs['Metallic'].default_value = metallic
            bsdf.inputs['Transmission'].default_value = transmission
            bsdf.inputs['IOR'].default_value = ior
            bsdf.inputs['Emission Strength'].default_value = emission_strength
            bsdf.inputs['Emission Color'].default_value = color[:3] + (1,) # Use base color for emission

            if blend_method != 'OPAQUE':
                mat.blend_method = blend_method
                mat.shadow_method = 'HASHED' # For better transparency shadows
    else: # Update existing material properties
        if use_nodes:
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if bsdf:
                bsdf.inputs['Base Color'].default_value = color
                bsdf.inputs['Roughness'].default_value = roughness
                bsdf.inputs['Metallic'].default_value = metallic
                bsdf.inputs['Transmission'].default_value = transmission
                bsdf.inputs['IOR'].default_value = ior
                bsdf.inputs['Emission Strength'].default_value = emission_strength
                bsdf.inputs['Emission Color'].default_value = color[:3] + (1,)

        mat.blend_method = blend_method
        mat.shadow_method = 'HASHED' if blend_method != 'OPAQUE' else 'OPAQUE'

    return mat

def animate_property(obj, property_path, start_frame, end_frame, start_value, end_value, easing='LINEAR', data_path_index=-1):
    """Animates a single property of an object."""
    # Set initial value and keyframe
    if data_path_index == -1:
        setattr(obj, property_path, start_value)
    else:
        current_value = list(getattr(obj, property_path))
        current_value[data_path_index] = start_value
        setattr(obj, property_path, current_value)

    obj.keyframe_insert(data_path=property_path, frame=start_frame, index=data_path_index)

    # Set final value and keyframe
    if data_path_index == -1:
        setattr(obj, property_path, end_value)
    else:
        current_value = list(getattr(obj, property_path))
        current_value[data_path_index] = end_value
        setattr(obj, property_path, current_value)

    obj.keyframe_insert(data_path=property_path, frame=end_frame, index=data_path_index)

    # Set easing for the fcurve
    fcurves = obj.animation_data.action.fcurves
    if data_path_index != -1:
        fcurve = fcurves.find(property_path, index=data_path_index)
    else:
        fcurve = fcurves.find(property_path)
    
    if fcurve:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'BEZIER'
            kf.easing = easing

def animate_fade(obj, start_frame, duration, fade_in=True, use_material_alpha=True):
    """Animates an object's visibility or material alpha."""
    end_frame = start_frame + duration
    
    # Animate material alpha
    if use_material_alpha and obj.data and obj.data.materials:
        mat = obj.data.materials[0]
        if mat.use_nodes:
            principled_node = mat.node_tree.nodes.get('Principled BSDF')
            if principled_node and 'Alpha' in principled_node.inputs:
                mat.blend_method = 'BLEND'
                mat.shadow_method = 'HASHED'
                
                if fade_in:
                    animate_property(principled_node.inputs['Alpha'], 'default_value', start_frame, end_frame, 0.0, 1.0, EASE_IN_OUT)
                else:
                    animate_property(principled_node.inputs['Alpha'], 'default_value', start_frame, end_frame, 1.0, 0.0, EASE_IN_OUT)
                
                mat.keyframe_insert(data_path='blend_method', frame=start_frame)
                mat.keyframe_insert(data_path='shadow_method', frame=start_frame)
                mat.keyframe_insert(data_path='blend_method', frame=end_frame)
                mat.keyframe_insert(data_path='shadow_method', frame=end_frame)

    # Animate object visibility
    obj.hide_render = True
    obj.hide_viewport = True
    obj.keyframe_insert(data_path='hide_render', frame=start_frame - 1)
    obj.keyframe_insert(data_path='hide_viewport', frame=start_frame - 1)
    
    obj.hide_render = False
    obj.hide_viewport = False
    obj.keyframe_insert(data_path='hide_render', frame=start_frame)
    obj.keyframe_insert(data_path='hide_viewport', frame=start_frame)
    
    if not fade_in:
        obj.hide_render = False
        obj.hide_viewport = False
        obj.keyframe_insert(data_path='hide_render', frame=end_frame)
        obj.keyframe_insert(data_path='hide_viewport', frame=end_frame)

        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=end_frame + 1)
        obj.keyframe_insert(data_path='hide_viewport', frame=end_frame + 1)
    else: # For fade-in, ensure it stays visible after it appears
        obj.hide_render = False
        obj.hide_viewport = False
        obj.keyframe_insert(data_path='hide_render', frame=end_frame)
        obj.keyframe_insert(data_path='hide_viewport', frame=end_frame)


def animate_slide(obj, start_frame, duration, start_loc, end_loc, easing='QUARTIC'):
    """Animates an object's location."""
    end_frame = start_frame + duration
    obj.location = start_loc
    obj.keyframe_insert(data_path='location', frame=start_frame)
    obj.location = end_loc
    obj.keyframe_insert(data_path='location', frame=end_frame)
    
    for i in range(3): # X, Y, Z
        fcurve = obj.animation_data.action.fcurves.find('location', index=i)
        if fcurve:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'BEZIER'
                kf.easing = easing

def animate_scale(obj, start_frame, duration, start_scale, end_scale, easing='QUARTIC'):
    """Animates an object's scale."""
    end_frame = start_frame + duration
    obj.scale = Vector((start_scale, start_scale, start_scale))
    obj.keyframe_insert(data_path='scale', frame=start_frame)
    obj.scale = Vector((end_scale, end_scale, end_scale))
    obj.keyframe_insert(data_path='scale', frame=end_frame)
    
    for i in range(3): # X, Y, Z
        fcurve = obj.animation_data.action.fcurves.find('scale', index=i)
        if fcurve:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'BEZIER'
                kf.easing = easing

def animate_glow(obj, start_frame, duration, max_strength=5.0, min_strength=0.0):
    """Animates the emission strength of an object's material."""
    if not obj.data or not obj.data.materials:
        # print(f"Warning: {obj.name} has no materials for glow animation.")
        return

    mat = obj.data.materials[0]
    if not mat.use_nodes:
        # print(f"Warning: Material for {obj.name} does not use nodes for glow animation.")
        return

    principled_node = mat.node_tree.nodes.get('Principled BSDF')
    if not principled_node:
        # print(f"Warning: Principled BSDF node not found for {obj.name}'s material.")
        return

    if 'Emission Strength' not in principled_node.inputs:
        # print(f"Error: 'Emission Strength' input not found on Principled BSDF for {obj.name}.")
        return

    # Store initial strength to restore
    initial_strength = principled_node.inputs['Emission Strength'].default_value
    
    # Keyframe initial state (before glow)
    principled_node.inputs['Emission Strength'].default_value = initial_strength
    principled_node.inputs['Emission Strength'].keyframe_insert(data_path='default_value', frame=start_frame - 1)

    # Glow up
    principled_node.inputs['Emission Strength'].default_value = max_strength
    principled_node.inputs['Emission Strength'].keyframe_insert(data_path='default_value', frame=start_frame + duration / 2)

    # Glow down
    principled_node.inputs['Emission Strength'].default_value = min_strength
    principled_node.inputs['Emission Strength'].keyframe_insert(data_path='default_value', frame=start_frame + duration)
    
    # Set easing
    fcurve = principled_node.animation_data.action.fcurves.find('inputs[19].default_value') # Index for Emission Strength
    if fcurve:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'BEZIER'
            kf.easing = EASE_IN_OUT

    # Restore original strength after animation
    principled_node.inputs['Emission Strength'].default_value = initial_strength
    principled_node.inputs['Emission Strength'].keyframe_insert(data_path='default_value', frame=start_frame + duration + 1)


def animate_camera_motion(camera_obj, start_frame, duration, target_loc, target_rot_euler, target_focal_length=None, easing='QUARTIC'):
    """Animates camera location, rotation, and optionally focal length."""
    end_frame = start_frame + duration

    # Location
    camera_obj.keyframe_insert(data_path='location', frame=start_frame)
    camera_obj.location = target_loc
    camera_obj.keyframe_insert(data_path='location', frame=end_frame)
    for i in range(3):
        fcurve = camera_obj.animation_data.action.fcurves.find('location', index=i)
        if fcurve:
            for kf in fcurve.keyframe_points: kf.interpolation = 'BEZIER'; kf.easing = easing

    # Rotation
    camera_obj.keyframe_insert(data_path='rotation_euler', frame=start_frame)
    camera_obj.rotation_euler = target_rot_euler
    camera_obj.keyframe_insert(data_path='rotation_euler', frame=end_frame)
    for i in range(3):
        fcurve = camera_obj.animation_data.action.fcurves.find('rotation_euler', index=i)
        if fcurve:
            for kf in fcurve.keyframe_points: kf.interpolation = 'BEZIER'; kf.easing = easing

    # Focal Length (Zoom)
    if target_focal_length is not None and camera_obj.data:
        camera_obj.data.keyframe_insert(data_path='lens', frame=start_frame)
        camera_obj.data.lens = target_focal_length
        camera_obj.data.keyframe_insert(data_path='lens', frame=end_frame)
        fcurve = camera_obj.data.animation_data.action.fcurves.find('lens')
        if fcurve:
            for kf in fcurve.keyframe_points: kf.interpolation = 'BEZIER'; kf.easing = easing

# --- Material Definitions ---
# These will be created/retrieved by main()
MAT_WHITEBOARD = None
MAT_VAR_CUBE = None
MAT_CONST_BLOCK = None
MAT_OP_ARROW = None
MAT_EQ_BAR = None
MAT_FRAC_LINE = None
MAT_TEXT_WHITE = None
MAT_TEXT_DARK = None
MAT_CANCEL_X = None
MAT_HOLE_EFFECT = None
MAT_GRAPH_AXES = None
MAT_FUNC_LINE = None
MAT_DIMMED = None
MAT_SOLVED_TEXT = None
MAT_END_CARD = None

def define_materials():
    global MAT_WHITEBOARD, MAT_VAR_CUBE, MAT_CONST_BLOCK, MAT_OP_ARROW, MAT_EQ_BAR, MAT_FRAC_LINE, \
           MAT_TEXT_WHITE, MAT_TEXT_DARK, MAT_CANCEL_X, MAT_HOLE_EFFECT, MAT_GRAPH_AXES, \
           MAT_FUNC_LINE, MAT_DIMMED, MAT_SOLVED_TEXT, MAT_END_CARD
           
    MAT_WHITEBOARD = create_material("MAT_Whiteboard", color=(0.95, 0.95, 0.95, 1), roughness=0.6, emission_strength=0.0)
    MAT_VAR_CUBE = create_material("MAT_VariableCube", color=(0.1, 0.5, 0.7, 1), metallic=0.1, roughness=0.2, ior=1.4, transmission=0.8, blend_method='BLEND')
    MAT_CONST_BLOCK = create_material("MAT_ConstantBlock", color=(0.7, 0.7, 0.7, 1), roughness=0.8)
    MAT_OP_ARROW = create_material("MAT_OperationArrow", color=(0.8, 0.8, 0.1, 1), emission_strength=5.0)
    MAT_EQ_BAR = create_material("MAT_EqualsBar", color=(0.5, 0.1, 0.9, 1), emission_strength=5.0)
    MAT_FRAC_LINE = create_material("MAT_FractionLine", color=(1.0, 1.0, 1.0, 1), emission_strength=0.5)
    MAT_TEXT_WHITE = create_material("MAT_TextWhite", color=(1.0, 1.0, 1.0, 1), emission_strength=0.5)
    MAT_TEXT_DARK = create_material("MAT_TextDark", color=(0.1, 0.1, 0.1, 1), emission_strength=0.0)
    MAT_CANCEL_X = create_material("MAT_CancelX", color=(0.9, 0.2, 0.1, 1), emission_strength=8.0, blend_method='BLEND')
    MAT_HOLE_EFFECT = create_material("MAT_HoleEffect", color=(0.05, 0.05, 0.05, 1), emission_strength=0.1)
    MAT_GRAPH_AXES = create_material("MAT_GraphAxes", color=(0.2, 0.2, 0.2, 1), roughness=0.8)
    MAT_FUNC_LINE = create_material("MAT_FunctionLine", color=(0.2, 1.0, 0.2, 1), emission_strength=4.0)
    MAT_DIMMED = create_material("MAT_Dimmed", color=(0.5, 0.5, 0.5, 1), roughness=0.8, emission_strength=0.0)
    MAT_SOLVED_TEXT = create_material("MAT_SolvedText", color=(0.1, 0.9, 0.1, 1), emission_strength=5.0)
    MAT_END_CARD = create_material("MAT_EndCard", color=(0.2, 0.2, 0.8, 1), emission_strength=2.0)


# --- Asset Creation Functions ---

def create_whiteboard_bg():
    """Creates the whiteboard background."""
    bpy.ops.mesh.primitive_plane_add(size=20, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    whiteboard = bpy.context.object
    whiteboard.name = "WhiteboardBG"
    set_active_object(whiteboard)
    
    whiteboard.data.materials.append(MAT_WHITEBOARD)

    # Add subtle grid pattern using nodes
    if MAT_WHITEBOARD.use_nodes:
        tree = MAT_WHITEBOARD.node_tree
        nodes = tree.nodes
        links = tree.links

        # Clear existing nodes except Material Output and Principled BSDF
        for node in nodes:
            if node.name not in ['Material Output', 'Principled BSDF']:
                nodes.remove(node)

        principled_node = nodes['Principled BSDF']
        output_node = nodes['Material Output']

        # Checker Texture for grid
        checker_node = nodes.new(type='ShaderNodeTexChecker')
        checker_node.location = (-600, 200)
        checker_node.inputs['Scale'].default_value = 10.0 # Adjust for desired grid density

        # Light Gray Emission for grid lines
        emission_node = nodes.new(type='ShaderNodeEmission')
        emission_node.location = (-600, 0)
        emission_node.inputs['Color'].default_value = (0.05, 0.05, 0.05, 1) # Very subtle gray glow
        emission_node.inputs['Strength'].default_value = 0.5 # Low strength

        # Mix Shader to combine whiteboard material and grid emission
        mix_shader_node = nodes.new(type='ShaderNodeMixShader')
        mix_shader_node.location = (-200, 0)

        # Link up the nodes
        links.new(principled_node.outputs['BSDF'], mix_shader_node.inputs[1])
        links.new(emission_node.outputs['Emission'], mix_shader_node.inputs[2])
        links.new(checker_node.outputs['Color'], mix_shader_node.inputs['Fac']) # Use checker color as factor

        links.new(mix_shader_node.outputs['Shader'], output_node.inputs['Surface'])

    add_object_to_collection(whiteboard, collections["_WORLD"].name)
    return whiteboard

def create_text_display(name, text_string, location=(0,0,0), size=1.0, align_x='CENTER', align_y='CENTER', material=None, parent_obj=None, extrusion=0.0):
    """Creates a text object."""
    bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=location)
    text_obj = bpy.context.object
    text_obj.name = name
    set_active_object(text_obj)

    text_obj.data.body = text_string
    text_obj.data.align_x = align_x
    text_obj.data.align_y = align_y
    text_obj.data.size = size
    text_obj.data.extrude = extrusion # For 3D text

    if material:
        text_obj.data.materials.append(material)
    else:
        text_obj.data.materials.append(MAT_TEXT_WHITE)

    if parent_obj:
        text_obj.parent = parent_obj

    add_object_to_collection(text_obj, collections["_MATH_ELEMENTS"].name)
    return text_obj

def create_variable_cube(name, label, location=(0,0,0), size=1.0):
    """Creates a VariableCube with a text label."""
    bpy.ops.mesh.primitive_cube_add(size=size, enter_editmode=False, align='WORLD', location=location)
    cube_obj = bpy.context.object
    cube_obj.name = name
    set_active_object(cube_obj)
    bpy.ops.object.shade_smooth() # Smooth shading
    
    # Apply bevel modifier
    bpy.ops.object.modifier_add(type='BEVEL')
    cube_obj.modifiers['Bevel'].width = 0.05 * size
    cube_obj.modifiers['Bevel'].segments = 4

    cube_obj.data.materials.append(MAT_VAR_CUBE)
    
    # Create label text and parent it
    label_text_obj = create_text_display(f"{name}_Label", label, 
                                          location=(0,0,size/2 + 0.01), # Slightly in front of cube center
                                          size=size*0.7, parent_obj=cube_obj, material=MAT_TEXT_WHITE)
    label_text_obj.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ') # Face camera
    
    add_object_to_collection(cube_obj, collections["_MATH_ELEMENTS"].name)
    add_object_to_collection(label_text_obj, collections["_MATH_ELEMENTS"].name)
    return cube_obj

def create_constant_block(name, value, location=(0,0,0), size_x=1.0, size_y=0.5, size_z=0.2):
    """Creates a ConstantBlock with a text value."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, align='WORLD', location=location)
    block_obj = bpy.context.object
    block_obj.name = name
    set_active_object(block_obj)
    block_obj.scale = Vector((size_x, size_y, size_z)) # Make it a prism

    block_obj.data.materials.append(MAT_CONST_BLOCK)

    # Create value text and parent it
    value_text_obj = create_text_display(f"{name}_Value", str(value), 
                                          location=(0,0,size_z/2 + 0.01), # Slightly in front
                                          size=size_z*0.8, parent_obj=block_obj, material=MAT_TEXT_DARK)
    value_text_obj.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ') # Face camera
    
    add_object_to_collection(block_obj, collections["_MATH_ELEMENTS"].name)
    add_object_to_collection(value_text_obj, collections["_MATH_ELEMENTS"].name)
    return block_obj

def create_operation_arrow(name, symbol, location=(0,0,0), rotation_z=0, scale=1.0):
    """Creates an arrow with a symbol."""
    # Create an arrow mesh
    bpy.ops.mesh.primitive_cone_add(radius1=0.1, depth=0.3, vertices=16, location=(0,0,0))
    cone = bpy.context.object
    cone.name = f"{name}_Head"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0, vertices=16, location=(0,0,-0.5))
    cylinder = bpy.context.object
    cylinder.name = f"{name}_Shaft"

    # Join them
    set_active_object(cone) # Activate cone first
    cylinder.select_set(True) # Select cylinder
    bpy.ops.object.join()
    
    arrow_obj = bpy.context.active_object
    arrow_obj.name = name
    
    # Scale and position
    arrow_obj.scale = Vector((scale, scale, scale))
    arrow_obj.location = location
    arrow_obj.rotation_euler = Euler((math.radians(90), 0, math.radians(rotation_z)), 'XYZ') # Point along X by default, rotate Z

    arrow_obj.data.materials.append(MAT_OP_ARROW)

    # Create symbol text and parent
    symbol_text_obj = create_text_display(f"{name}_Symbol", symbol, 
                                          location=(0,0,0.2), size=scale*0.7, parent_obj=arrow_obj, material=MAT_OP_ARROW)
    symbol_text_obj.rotation_euler = Euler((math.radians(-90), 0, 0), 'XYZ') # Align text to face camera
    
    add_object_to_collection(arrow_obj, collections["_MATH_ELEMENTS"].name)
    add_object_to_collection(symbol_text_obj, collections["_MATH_ELEMENTS"].name)
    return arrow_obj

def create_equals_bar(name, location=(0,0,0), is_not_equal=False, length=1.0):
    """Creates an equals or not equals bar."""
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=location)
    parent_empty = bpy.context.object
    parent_empty.name = f"{name}_Parent"
    add_object_to_collection(parent_empty, collections["_MATH_ELEMENTS"].name)

    # Create two horizontal bars
    bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, align='WORLD', location=(0, 0, 0.15))
    bar1 = bpy.context.object
    bar1.name = f"{name}_Bar1"
    set_active_object(bar1)
    bar1.scale = Vector((length, 0.1, 0.05))
    bar1.parent = parent_empty
    bar1.data.materials.append(MAT_EQ_BAR)
    add_object_to_collection(bar1, collections["_MATH_ELEMENTS"].name)

    bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, align='WORLD', location=(0, 0, -0.15))
    bar2 = bpy.context.object
    bar2.name = f"{name}_Bar2"
    set_active_object(bar2)
    bar2.scale = Vector((length, 0.1, 0.05))
    bar2.parent = parent_empty
    bar2.data.materials.append(MAT_EQ_BAR)
    add_object_to_collection(bar2, collections["_MATH_ELEMENTS"].name)
    
    # Add diagonal bar for NotEqualsBar
    if is_not_equal:
        bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, align='WORLD', location=(0,0,0))
        diagonal_bar = bpy.context.object
        diagonal_bar.name = f"{name}_Diagonal"
        set_active_object(diagonal_bar)
        diagonal_bar.scale = Vector((length * 0.1, 0.1, 0.05)) # Thinner
        diagonal_bar.rotation_euler = Euler((0, math.radians(-45), 0), 'XYZ') # Diagonal
        diagonal_bar.parent = parent_empty
        diagonal_bar.data.materials.append(MAT_EQ_BAR)
        add_object_to_collection(diagonal_bar, collections["_MATH_ELEMENTS"].name)

    return parent_empty # Return the parent empty for easy animation

def create_fraction_line(name, start_loc, end_loc, thickness=0.05):
    """Creates a fraction line using a curve."""
    curve_data = bpy.data.curves.new(name=f"{name}_Curve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2

    # Add spline
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(1) # Add one extra point for total of 2
    spline.bezier_points[0].co = start_loc
    spline.bezier_points[1].co = end_loc
    
    # Set handles to vector for straight line
    spline.bezier_points[0].handle_right_type = 'VECTOR'
    spline.bezier_points[0].handle_left_type = 'VECTOR'
    spline.bezier_points[1].handle_right_type = 'VECTOR'
    spline.bezier_points[1].handle_left_type = 'VECTOR'

    # Set bevel for thickness
    curve_data.bevel_depth = thickness / 2
    curve_data.bevel_resolution = 4
    
    frac_line_obj = bpy.data.objects.new(name, curve_data)
    frac_line_obj.data.materials.append(MAT_FRAC_LINE)
    
    add_object_to_collection(frac_line_obj, collections["_MATH_ELEMENTS"].name)
    return frac_line_obj

def create_cancel_x_effect(name, location=(0,0,0), size=1.0):
    """Creates a glowing 'X' mesh for cancellation effect."""
    # Parent empty for the X
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=location)
    x_parent = bpy.context.object
    x_parent.name = name
    add_object_to_collection(x_parent, collections["_MATH_ELEMENTS"].name)

    # Create two planes for the 'X'
    bpy.ops.mesh.primitive_plane_add(size=size, enter_editmode=False, align='WORLD', location=(0,0,0))
    plane1 = bpy.context.object
    plane1.name = f"{name}_Plane1"
    set_active_object(plane1)
    plane1.rotation_euler = Euler((0, 0, math.radians(45)), 'XYZ')
    plane1.scale = Vector((1, 0.1, 1)) # Make it a bar
    plane1.parent = x_parent
    plane1.data.materials.append(MAT_CANCEL_X)
    add_object_to_collection(plane1, collections["_MATH_ELEMENTS"].name)

    bpy.ops.mesh.primitive_plane_add(size=size, enter_editmode=False, align='WORLD', location=(0,0,0))
    plane2 = bpy.context.object
    plane2.name = f"{name}_Plane2"
    set_active_object(plane2)
    plane2.rotation_euler = Euler((0, 0, math.radians(-45)), 'XYZ')
    plane2.scale = Vector((1, 0.1, 1)) # Make it a bar
    plane2.parent = x_parent
    plane2.data.materials.append(MAT_CANCEL_X)
    add_object_to_collection(plane2, collections["_MATH_ELEMENTS"].name)

    return x_parent

def create_hole_effect(name, location=(0,0,0), size=0.2):
    """Creates a small, pulsating disc/sphere for a hole effect."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size/2, segments=32, ring_count=16, enter_editmode=False, align='WORLD', location=location)
    hole_obj = bpy.context.object
    hole_obj.name = name
    set_active_object(hole_obj)
    bpy.ops.object.shade_smooth()

    hole_obj.data.materials.append(MAT_HOLE_EFFECT)
    add_object_to_collection(hole_obj, collections["_MATH_ELEMENTS"].name)
    return hole_obj

def create_graph_axes(name, location=(0,0,0), size=5.0):
    """Creates X-Y graph axes."""
    # Group under an empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=location)
    axes_parent = bpy.context.object
    axes_parent.name = name
    add_object_to_collection(axes_parent, collections["_MATH_ELEMENTS"].name)

    # X-axis
    curve_data_x = bpy.data.curves.new(name=f"{name}_XAxis_Curve", type='CURVE')
    curve_data_x.dimensions = '3D'
    curve_data_x.bevel_depth = 0.02
    curve_data_x.bevel_resolution = 2
    spline_x = curve_data_x.splines.new('BEZIER')
    spline_x.bezier_points.add(1)
    spline_x.bezier_points[0].co = Vector((-size/2, 0, 0))
    spline_x.bezier_points[1].co = Vector((size/2, 0, 0))
    spline_x.bezier_points[0].handle_right_type = 'VECTOR'
    spline_x.bezier_points[1].handle_left_type = 'VECTOR'
    x_axis = bpy.data.objects.new(f"{name}_XAxis", curve_data_x)
    x_axis.parent = axes_parent
    x_axis.data.materials.append(MAT_GRAPH_AXES)
    add_object_to_collection(x_axis, collections["_MATH_ELEMENTS"].name)

    # Y-axis
    curve_data_y = bpy.data.curves.new(name=f"{name}_YAxis_Curve", type='CURVE')
    curve_data_y.dimensions = '3D'
    curve_data_y.bevel_depth = 0.02
    curve_data_y.bevel_resolution = 2
    spline_y = curve_data_y.splines.new('BEZIER')
    spline_y.bezier_points.add(1)
    spline_y.bezier_points[0].co = Vector((0, -size/2, 0))
    spline_y.bezier_points[1].co = Vector((0, size/2, 0))
    spline_y.bezier_points[0].handle_right_type = 'VECTOR'
    spline_y.bezier_points[1].handle_left_type = 'VECTOR'
    y_axis = bpy.data.objects.new(f"{name}_YAxis", curve_data_y)
    y_axis.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ') # Rotate to be vertical
    y_axis.parent = axes_parent
    y_axis.data.materials.append(MAT_GRAPH_AXES)
    add_object_to_collection(y_axis, collections["_MATH_ELEMENTS"].name)

    # Labels (parented to axes_parent, so their locations are relative)
    create_text_display(f"{name}_X_Label", "x", location=(size/2 + 0.2, 0.05, 0), size=0.5, parent_obj=axes_parent, material=MAT_TEXT_DARK)
    create_text_display(f"{name}_Y_Label", "y", location=(0, size/2 + 0.2, 0.05), size=0.5, parent_obj=axes_parent, material=MAT_TEXT_DARK, align_x='LEFT')

    return axes_parent

def create_function_line(name, func_expr, x_range=(-5, 5), z_scale=1.0, location=(0,0,0)):
    """Creates a function line as a curve that can be animated with Trim Curve."""
    curve_data = bpy.data.curves.new(name=f"{name}_CurveData", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 32 # Number of points to sample the function

    spline = curve_data.splines.new('NURBS')
    spline.points.add(curve_data.resolution_u - 1) # Add points (already has 1)

    x_min, x_max = x_range
    for i in range(curve_data.resolution_u):
        x = x_min + (x_max - x_min) * (i / (curve_data.resolution_u - 1))
        
        # Evaluate function f(x) = x/4 + 3
        try:
            # Safely evaluate the expression. Using math.nan to handle potential division by zero.
            y = (x / 4) + 3
            if abs(y) > 100: # Clamp very large values to prevent huge lines
                y = 100 * math.copysign(1, y)
        except ZeroDivisionError:
            y = float('nan')
        except Exception as e:
            print(f"Error evaluating function for x={x}: {e}")
            y = float('nan')
        
        # In Blender, Y is usually vertical, Z is depth. But for a whiteboard on XY, we might use Z as vertical.
        # Given the camera setup, Z will be vertical on the board. So, map math Y to Blender Z.
        if not math.isnan(y):
            spline.points[i].co = Vector((x, 0, y)) # X is x-axis, Y is 0 (depth), Z is y-axis for math graph
        else:
            # For discontinuity, if possible, split the curve or place points far away
            spline.points[i].co = Vector((x, 0, 1e5)) # Put point very high to "break" the line visually

        spline.points[i].weight = 1.0 # For NURBS points

    spline.use_endpoint_v = True
    spline.use_endpoint_u = True

    # Set bevel for thickness
    curve_data.bevel_depth = 0.05
    curve_data.bevel_resolution = 4
    
    func_line_obj = bpy.data.objects.new(name, curve_data)
    func_line_obj.location = location # Base location for the graph
    func_line_obj.data.materials.append(MAT_FUNC_LINE)
    
    # Add Trim Curve modifier
    mod = func_line_obj.modifiers.new(name="Trim_Curve", type='CURVE_TRIM')
    mod.trim_mode = 'FACTOR'
    mod.start = 0.0
    mod.end = 0.0 # Start trimmed
    
    add_object_to_collection(func_line_obj, collections["_MATH_ELEMENTS"].name)
    return func_line_obj

# --- Main Setup and Animation Sequence ---

def main():
    clean_scene()
    setup_collections() # Set up global collections
    define_materials() # Define all materials

    # --- Scene Setup ---
    # Camera
    cam_data = bpy.data.cameras.new("MainCamera")
    camera_obj = bpy.data.objects.new("MainCamera", cam_data)
    camera_obj.location = (0, -10, 5)
    camera_obj.rotation_euler = Euler((math.radians(70), 0, 0), 'XYZ') # Looking down at whiteboard
    camera_obj.data.lens = 35 # Standard focal length
    bpy.context.scene.camera = camera_obj
    add_object_to_collection(camera_obj, collections["_CAMERA_RIG"].name)

    # Lights (Area Lights)
    light_data1 = bpy.data.lights.new(name="AreaLight1", type='AREA')
    light_data1.energy = 500
    light_data1.size = 5
    light_obj1 = bpy.data.objects.new(name="AreaLight1", object_data=light_data1)
    light_obj1.location = (5, -5, 10)
    light_obj1.rotation_euler = Euler((math.radians(45), math.radians(10), math.radians(-45)), 'XYZ')
    add_object_to_collection(light_obj1, collections["_LIGHTS"].name)

    light_data2 = bpy.data.lights.new(name="AreaLight2", type='AREA')
    light_data2.energy = 500
    light_data2.size = 5
    light_obj2 = bpy.data.objects.new(name="AreaLight2", object_data=light_data2)
    light_obj2.location = (-5, -5, 10)
    light_obj2.rotation_euler = Euler((math.radians(45), math.radians(-10), math.radians(45)), 'XYZ')
    add_object_to_collection(light_obj2, collections["_LIGHTS"].name)

    # Whiteboard Background
    whiteboard_bg = create_whiteboard_bg()

    # Set up render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'
    bpy.context.scene.render.filepath = "//render/" # Output to a 'render' folder in the blend file directory
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = TOTAL_FRAMES

    # Ensure all objects start hidden unless explicitly shown at frame 0
    for obj in bpy.data.objects:
        if obj.name not in [camera_obj.name, light_obj1.name, light_obj2.name, whiteboard_bg.name]:
            obj.hide_render = True
            obj.hide_viewport = True
            obj.keyframe_insert(data_path='hide_render', frame=0)
            obj.keyframe_insert(data_path='hide_viewport', frame=0)

    # --- Time Markers (in frames) ---
    F = FPS # shorthand for frames per second
    
    t = 0 * F # Current time pointer
    
    # 0:00-0:03: Camera pan left, Title card fade in
    cam_start_loc = camera_obj.location.copy()
    cam_start_rot = camera_obj.rotation_euler.copy()
    cam_end_loc_pan_left = Vector((-3, -10, 5))
    cam_end_rot_pan_left = Euler((math.radians(70), 0, -math.radians(5)), 'XYZ') # Slight pan angle

    title_card = create_text_display("TXT_TitleCard", "Cinematic Math: Elementary Algebra - Solving Functions",
                                     location=(0, -0.1, 0), size=1.0, extrusion=0.05, material=MAT_TEXT_WHITE)
    
    animate_camera_motion(camera_obj, t, 3*F, cam_end_loc_pan_left, cam_end_rot_pan_left)
    animate_fade(title_card, t, FADE_DURATION, fade_in=True)
    t += 3 * F
    
    # 0:03-0:06: Title card fades out. "Problem:" slides in. Function materializes.
    animate_fade(title_card, t, FADE_DURATION, fade_in=False)
    
    problem_text = create_text_display("TXT_Problem", "Problem:", location=(-6, 0.1, 4), size=0.8, align_x='LEFT')
    animate_slide(problem_text, t + FADE_DURATION, SLIDE_DURATION, Vector((-10, 0.1, 4)), Vector((-6, 0.1, 4)))
    
    # Initial function elements
    fx_eq_text = create_text_display("TXT_FX_Eq", "f(x) =", location=(-4.5, 0.1, 2), size=0.7)
    x_squared_text = create_text_display("TXT_X_Squared", "x²", location=(-3.0, 0.1, 2.3), size=0.7)
    four_x_text = create_text_display("TXT_4X", "4x", location=(-2.9, 0.1, 1.7), size=0.7)
    initial_frac_line = create_fraction_line("FRAC_Initial", Vector((-3.0, 0.1, 2)), Vector((-2.0, 0.1, 2)))
    plus_op_text = create_text_display("TXT_PlusOp", "+", location=(-1.8, 0.1, 2), size=0.7)
    three_const_text = create_text_display("TXT_ThreeConst", "3", location=(-1.2, 0.1, 2), size=0.7)

    all_initial_func_parts = [fx_eq_text, x_squared_text, four_x_text, initial_frac_line, plus_op_text, three_const_text]

    # Materialize line-by-line
    # Hide all parts initially for the animation
    for obj in all_initial_func_parts:
        # Set alpha to 0 for fade in
        if obj.data and obj.data.materials and obj.data.materials[0].use_nodes:
            principled_node = obj.data.materials[0].node_tree.nodes.get('Principled BSDF')
            if principled_node: principled_node.inputs['Alpha'].default_value = 0.0
            obj.data.materials[0].blend_method = 'BLEND'
            obj.data.materials[0].shadow_method = 'HASHED'
            obj.data.materials[0].keyframe_insert(data_path='blend_method', frame=t + FADE_DURATION)
            obj.data.materials[0].keyframe_insert(data_path='shadow_method', frame=t + FADE_DURATION)
        
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=t + FADE_DURATION - 1)
        obj.keyframe_insert(data_path='hide_viewport', frame=t + FADE_DURATION - 1)

    # Fading in sequentially
    current_text_t = t + FADE_DURATION + SHORT_ANIM_DURATION # After "Problem:" slides in
    
    animate_fade(fx_eq_text, current_text_t, SHORT_ANIM_DURATION, fade_in=True)
    current_text_t += SHORT_ANIM_DURATION * 0.5
    animate_fade(x_squared_text, current_text_t, SHORT_ANIM_DURATION, fade_in=True)
    current_text_t += SHORT_ANIM_DURATION * 0.5
    animate_fade(initial_frac_line, current_text_t, SHORT_ANIM_DURATION, fade_in=True)
    current_text_t += SHORT_ANIM_DURATION * 0.5
    animate_fade(four_x_text, current_text_t, SHORT_ANIM_DURATION, fade_in=True)
    current_text_t += SHORT_ANIM_DURATION * 0.5
    animate_fade(plus_op_text, current_text_t, SHORT_ANIM_DURATION, fade_in=True)
    current_text_t += SHORT_ANIM_DURATION * 0.5
    animate_fade(three_const_text, current_text_t, SHORT_ANIM_DURATION, fade_in=True)

    t = 6 * F # End of initial setup
    
    # 0:06-0:09: "Step 1" slides in. Camera zooms in. Right side dims.
    step1_text = create_text_display("TXT_Step1", "Step 1: Simplify the expression.", 
                                     location=(-6, 0.1, 0), size=0.6, align_x='LEFT')
    animate_slide(step1_text, t, SLIDE_DURATION, Vector((-10, 0.1, 0)), Vector((-6, 0.1, 0)))

    # Camera zoom in
    cam_zoom_loc = Vector((-1.5, -6, 2.5))
    cam_zoom_rot = Euler((math.radians(75), 0, 0), 'XYZ')
    animate_camera_motion(camera_obj, t, 3*F, cam_zoom_loc, cam_zoom_rot, target_focal_length=50) # Zoom in
    
    # Dim `+` and `3`
    for obj in [plus_op_text, three_const_text]:
        if obj.data and obj.data.materials:
            # For the text objects, switch material to MAT_DIMMED and animate.
            # Make a unique material for each object for independent animation
            dim_mat_name = f"MAT_DIMMED_{obj.name}"
            dim_mat = create_material(dim_mat_name, color=(0.5, 0.5, 0.5, 1), roughness=0.8, emission_strength=0.0)
            
            # Switch materials: current material at start_frame-1, dimmed material at start_frame
            obj.data.materials.append(dim_mat)
            obj.active_material_index = 0 # Default is 0
            obj.keyframe_insert(data_path='active_material_index', frame=t) # Keep original material active
            obj.active_material_index = len(obj.data.materials) - 1 # Switch to dimmed
            obj.keyframe_insert(data_path='active_material_index', frame=t + 2*F) # Switch to dimmed material

    t = 9 * F

    # 0:09-0:12: Fraction glows and enlarges.
    for obj in [x_squared_text, initial_frac_line, four_x_text]:
        animate_glow(obj, t, GLOW_PULSE_DURATION*2, max_strength=2.0, min_strength=0.0)
        animate_scale(obj, t, FADE_DURATION, 1.0, 1.1)
    
    t = 12 * F

    # 0:12-0:15: VariableCube(x²) appears above FractionLine. ConstantBlock(4) & VariableCube(x) below.
    # Scale back the original elements
    for obj in [x_squared_text, initial_frac_line, four_x_text]:
        animate_scale(obj, t - FADE_DURATION, FADE_DURATION, 1.1, 1.0)
    
    # New positions for the breakdown
    x_sq_loc = Vector((-3.0, 0.1, 3.0))
    four_loc = Vector((-3.5, 0.1, 1.0))
    x_loc_denom = Vector((-2.5, 0.1, 1.0))
    mult_arrow_loc = Vector((-3.0, 0.1, 1.0))
    frac_line_loc_start = Vector((-3.5, 0.1, 2.0))
    frac_line_loc_end = Vector((-2.0, 0.1, 2.0))

    vc_x_squared = create_variable_cube("VC_X_Squared", "x²", location=x_sq_loc, size=0.8)
    cb_four = create_constant_block("CB_Four", "4", location=four_loc, size_x=0.8, size_y=0.4, size_z=0.2)
    vc_x_denom = create_variable_cube("VC_X_Denom", "x", location=x_loc_denom, size=0.6)
    arr_mult = create_operation_arrow("ARR_Mult_Denom", "✖️", location=mult_arrow_loc, scale=0.5)
    
    # Hide new elements initially
    for obj in [vc_x_squared, cb_four, vc_x_denom, arr_mult]:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=t-1)
        obj.keyframe_insert(data_path='hide_viewport', frame=t-1)
    
    # Fade out old text
    animate_fade(x_squared_text, t, FADE_DURATION, fade_in=False)
    animate_fade(four_x_text, t, FADE_DURATION, fade_in=False)
    # The initial_frac_line stays, adjust its Z slightly
    animate_property(initial_frac_line, 'location', t, t + FADE_DURATION, initial_frac_line.location, initial_frac_line.location + Vector((0,0,0.01))) # Push forward slightly for visibility

    # Fade in new objects
    animate_fade(vc_x_squared, t + FADE_DURATION * 0.5, FADE_DURATION, fade_in=True)
    animate_fade(cb_four, t + FADE_DURATION * 0.5, FADE_DURATION, fade_in=True)
    animate_fade(vc_x_denom, t + FADE_DURATION * 0.5, FADE_DURATION, fade_in=True)
    animate_fade(arr_mult, t + FADE_DURATION * 0.5, FADE_DURATION, fade_in=True)
    
    t = 15 * F

    # 0:15-0:18: VariableCube(x²) splits into two VariableCube(x)
    # Fade out VC_X_Squared
    animate_fade(vc_x_squared, t, FADE_DURATION, fade_in=False)
    
    # Create two new 'x' cubes and a multiply arrow
    vc_x_num1 = create_variable_cube("VC_X_Num1", "x", location=x_sq_loc + Vector((-0.5, 0, 0)), size=0.6)
    arr_mult_num = create_operation_arrow("ARR_Mult_Num", "✖️", location=x_sq_loc, scale=0.5)
    vc_x_num2 = create_variable_cube("VC_X_Num2", "x", location=x_sq_loc + Vector((0.5, 0, 0)), size=0.6)

    # Make frac line longer
    current_frac_p0_co = initial_frac_line.data.splines[0].bezier_points[0].co.copy()
    current_frac_p1_co = initial_frac_line.data.splines[0].bezier_points[1].co.copy()
    
    animate_property(initial_frac_line.data.splines[0].bezier_points[0], 'co', t, t + FADE_DURATION, current_frac_p0_co, current_frac_p0_co - Vector((0.5,0,0)))
    animate_property(initial_frac_line.data.splines[0].bezier_points[1], 'co', t, t + FADE_DURATION, current_frac_p1_co, current_frac_p1_co + Vector((0.5,0,0)))
    
    # Fade in new elements
    for obj in [vc_x_num1, arr_mult_num, vc_x_num2]:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=t-1)
        obj.keyframe_insert(data_path='hide_viewport', frame=t-1)
        animate_fade(obj, t + FADE_DURATION * 0.5, FADE_DURATION, fade_in=True)
    
    t = 18 * F

    # 0:18-0:22: Cancel one x from numerator and denominator. "Provided x != 0" appears.
    # Glow the selected 'x' cubes
    animate_glow(vc_x_num2, t, GLOW_PULSE_DURATION, max_strength=5.0)
    animate_glow(vc_x_denom, t, GLOW_PULSE_DURATION, max_strength=5.0)

    # Create CancelXEffect
    cancel_x_effect = create_cancel_x_effect("FX_CancelX", location=(x_sq_loc.x + 0.5, x_sq_loc.y, x_sq_loc.z - 0.5), size=1.5)
    cancel_x_effect.hide_render = True
    cancel_x_effect.hide_viewport = True
    cancel_x_effect.keyframe_insert(data_path='hide_render', frame=t-1)
    cancel_x_effect.keyframe_insert(data_path='hide_viewport', frame=t-1)
    
    # Animate CancelXEffect: fade in, scale pulse, fade out
    animate_fade(cancel_x_effect, t, SHORT_ANIM_DURATION, fade_in=True)
    animate_scale(cancel_x_effect, t, SHORT_ANIM_DURATION, 0.5, 1.2)
    animate_scale(cancel_x_effect, t + SHORT_ANIM_DURATION, SHORT_ANIM_DURATION, 1.2, 0.0) # Shrink and disappear
    animate_fade(cancel_x_effect, t + SHORT_ANIM_DURATION, SHORT_ANIM_DURATION, fade_in=False)

    # Simultaneously shrink and fade out the cancelled cubes
    animate_scale(vc_x_num2, t, SHORT_ANIM_DURATION, 0.6, 0.0)
    animate_fade(vc_x_num2, t + SHORT_ANIM_DURATION * 0.5, SHORT_ANIM_DURATION, fade_in=False)
    
    animate_scale(vc_x_denom, t, SHORT_ANIM_DURATION, 0.6, 0.0)
    animate_fade(vc_x_denom, t + SHORT_ANIM_DURATION * 0.5, SHORT_ANIM_DURATION, fade_in=False)

    # "Provided x != 0" text
    provided_text = create_text_display("TXT_ProvidedX", "Provided x ≠ 0", location=(0, 0.1, -1), size=0.5)
    animate_fade(provided_text, t + SHORT_ANIM_DURATION, FADE_DURATION, fade_in=True)
    animate_fade(provided_text, t + SHORT_ANIM_DURATION + FADE_DURATION + F, FADE_DURATION, fade_in=False) # Fade out after a second
    
    t = 22 * F

    # 0:22-0:25: Remaining elements re-align and compress into x/4.
    # The remaining elements are vc_x_num1 and cb_four
    # They should move to the position of FractionBlock(x/4)
    # The fraction line also needs to shrink back to its original length.

    # Final simplified fraction position
    simplified_frac_loc = Vector((-3.0, 0.1, 2.0))
    
    # vc_x_num1 (remaining x) moves to numerator pos
    animate_slide(vc_x_num1, t, SLIDE_DURATION, vc_x_num1.location.copy(), simplified_frac_loc + Vector((0, 0, 0.3)))
    animate_scale(vc_x_num1, t, SLIDE_DURATION, vc_x_num1.scale.x, 0.7) # Slightly larger

    # cb_four (remaining 4) moves to denominator pos
    animate_slide(cb_four, t, SLIDE_DURATION, cb_four.location.copy(), simplified_frac_loc + Vector((0, 0, -0.3)))
    animate_scale(cb_four, t, SLIDE_DURATION, cb_four.scale.x, 0.7) # Slightly larger

    # Fraction line shrinks
    animate_property(initial_frac_line.data.splines[0].bezier_points[0], 'co', t, t + SLIDE_DURATION, initial_frac_line.data.splines[0].bezier_points[0].co.copy(), frac_line_loc_start)
    animate_property(initial_frac_line.data.splines[0].bezier_points[1], 'co', t, t + SLIDE_DURATION, initial_frac_line.data.splines[0].bezier_points[1].co.copy(), frac_line_loc_end)
    
    # Fade out the numerator multiply arrow
    animate_fade(arr_mult_num, t, FADE_DURATION, fade_in=False)

    t = 25 * F

    # 0:25-0:28: x/4 slides back into main equation. + and 3 glow back.
    # Group the simplified fraction components temporarily for easy slide
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=simplified_frac_loc)
    frac_group_empty = bpy.context.object
    frac_group_empty.name = "GRP_SimplifiedFraction"
    add_object_to_collection(frac_group_empty, collections["_MATH_ELEMENTS"].name)

    # Parent objects to the empty
    set_active_object(frac_group_empty)
    vc_x_num1.parent = frac_group_empty
    cb_four.parent = frac_group_empty
    initial_frac_line.parent = frac_group_empty

    # The elements are already in the correct simplified form at `simplified_frac_loc`.
    # They effectively just "solidify" in place as part of the equation.
    # So, no slide animation for frac_group_empty itself.
    
    # + and 3 glow back
    for obj in [plus_op_text, three_const_text]:
        if obj.data and obj.data.materials and len(obj.data.materials) > 1:
            # Switch back to original material (index 0)
            obj.active_material_index = 1 # Current dimmed
            obj.keyframe_insert(data_path='active_material_index', frame=t)
            obj.active_material_index = 0 # Original
            obj.keyframe_insert(data_path='active_material_index', frame=t + FADE_DURATION)
            # Add a slight glow pulse on the original material
            animate_glow(obj, t + FADE_DURATION, GLOW_PULSE_DURATION, max_strength=0.5, min_strength=0.0)
    
    # Hide arr_mult_denom (4x was replaced)
    animate_fade(arr_mult, t, FADE_DURATION, fade_in=False)
    
    t = 28 * F

    # 0:28-0:31: Simplified function glows. "Simplified Form:" appears.
    simplified_form_text = create_text_display("TXT_SimplifiedForm", "Simplified Form:", location=(-2.0, 0.1, 3.5), size=0.6)
    animate_fade(simplified_form_text, t, FADE_DURATION, fade_in=True)

    # Glow simplified components
    for obj in [fx_eq_text, frac_group_empty, plus_op_text, three_const_text]:
        if isinstance(obj, bpy.types.Object) and obj.type == 'EMPTY': # Grouped fraction
            for child in obj.children:
                animate_glow(child, t, GLOW_PULSE_DURATION, max_strength=1.5, min_strength=0.0)
        else:
            animate_glow(obj, t, GLOW_PULSE_DURATION, max_strength=1.5, min_strength=0.0)

    t = 31 * F

    # 0:31-0:34: Camera zooms out/pans right. "Step 2" slides in. Original function fades back.
    cam_start_loc_zoom_out = camera_obj.location.copy()
    cam_start_rot_zoom_out = camera_obj.rotation_euler.copy()
    cam_zoom_out_loc = Vector((0, -10, 5))
    cam_zoom_out_rot = Euler((math.radians(70), 0, 0), 'XYZ')
    animate_camera_motion(camera_obj, t, 3*F, cam_zoom_out_loc, cam_zoom_out_rot, target_focal_length=35)

    step2_text = create_text_display("TXT_Step2", "Step 2: Determine the Domain.", 
                                     location=(-6, 0.1, 0), size=0.6, align_x='LEFT')
    animate_slide(step2_text, t, SLIDE_DURATION, Vector((-10, 0.1, 0)), Vector((-6, 0.1, 0)))

    # Original function fades back into view (elements currently hidden/faded out)
    # Re-use original elements that were faded out.
    # The elements that were "replaced" are x_squared_text and four_x_text
    # They need to be visible again.
    
    # Ensure they are active and parented correctly if they were part of a group
    for obj in all_initial_func_parts:
        if obj.data and obj.data.materials:
            if obj.active_material_index > 0: # If it has a dimmed material, revert
                 obj.active_material_index = 0
                 obj.keyframe_insert(data_path='active_material_index', frame=t) # Ensure original material at this point
        
        animate_fade(obj, t + SLIDE_DURATION * 0.5, FADE_DURATION, fade_in=True)
        # Restore any scale changes
        animate_scale(obj, t + SLIDE_DURATION * 0.5, FADE_DURATION, obj.scale.x, 1.0)

    t = 34 * F

    # 0:34-0:37: Denominator glows and pulsates. "Crucial Rule" appears.
    animate_glow(four_x_text, t, GLOW_PULSE_DURATION*2, max_strength=2.0)
    
    crucial_rule_text = create_text_display("TXT_CrucialRule", "Crucial Rule: Denominator cannot be zero!", location=(0, 0.1, -1), size=0.6)
    animate_fade(crucial_rule_text, t + GLOW_PULSE_DURATION, FADE_DURATION, fade_in=True)

    t = 37 * F

    # 0:37-0:40: 4x ≠ 0 forms.
    # Fade out "Crucial Rule"
    animate_fade(crucial_rule_text, t, FADE_DURATION, fade_in=False)

    # Bring 4x into center, create NotEqualsBar and 0
    # Create new blocks/text for interaction
    cb_four_interact = create_constant_block("CB_Four_Interact", "4", location=(0, 0.1, 0), size_x=0.8, size_y=0.4, size_z=0.2)
    vc_x_interact = create_variable_cube("VC_X_Interact", "x", location=(1.0, 0.1, 0), size=0.6)
    arr_mult_interact = create_operation_arrow("ARR_Mult_Interact", "✖️", location=(0.5, 0.1, 0), scale=0.5)
    ne_bar = create_equals_bar("NE_Bar", location=(2.0, 0.1, 0), is_not_equal=True)
    cb_zero = create_constant_block("CB_Zero", "0", location=(3.0, 0.1, 0), size_x=0.8, size_y=0.4, size_z=0.2)
    
    # Hide initially
    for obj in [cb_four_interact, vc_x_interact, arr_mult_interact, ne_bar, cb_zero]:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=t-1)
        obj.keyframe_insert(data_path='hide_viewport', frame=t-1)

    # Fade in these elements at center.
    animate_fade(cb_four_interact, t, FADE_DURATION, fade_in=True)
    animate_fade(vc_x_interact, t + FADE_DURATION * 0.2, FADE_DURATION, fade_in=True)
    animate_fade(arr_mult_interact, t + FADE_DURATION * 0.4, FADE_DURATION, fade_in=True)
    animate_fade(ne_bar, t + FADE_DURATION * 0.6, FADE_DURATION, fade_in=True)
    animate_fade(cb_zero, t + FADE_DURATION * 0.8, FADE_DURATION, fade_in=True)

    t = 40 * F

    # 0:40-0:44: Divide by 4 animation.
    # Duplicate operation arrow and constant block for both sides
    arr_div1 = create_operation_arrow("ARR_Div1", "➗", location=(-0.5, 0.1, -1), rotation_z=90, scale=0.5) # Below 4x
    cb_four_div1 = create_constant_block("CB_Four_Div1", "4", location=(0.0, 0.1, -1), size_x=0.8, size_y=0.4, size_z=0.2)

    arr_div2 = create_operation_arrow("ARR_Div2", "➗", location=(2.5, 0.1, -1), rotation_z=90, scale=0.5) # Below 0
    cb_four_div2 = create_constant_block("CB_Four_Div2", "4", location=(3.0, 0.1, -1), size_x=0.8, size_y=0.4, size_z=0.2)

    # Hide initially
    for obj in [arr_div1, cb_four_div1, arr_div2, cb_four_div2]:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=t-1)
        obj.keyframe_insert(data_path='hide_viewport', frame=t-1)
        animate_fade(obj, t, FADE_DURATION, fade_in=True)

    # Animate division: left side shrinks and dissolves
    animate_scale(cb_four_interact, t + FADE_DURATION, SHORT_ANIM_DURATION, cb_four_interact.scale.x, 0.0)
    animate_fade(cb_four_interact, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)
    animate_scale(arr_mult_interact, t + FADE_DURATION, SHORT_ANIM_DURATION, arr_mult_interact.scale.x, 0.0)
    animate_fade(arr_mult_interact, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)

    animate_fade(arr_div1, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(cb_four_div1, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)

    t = 44 * F

    # 0:44-0:47: 0/4 simplifies to 0. x != 0 glows.
    # Fade out 0 and /4
    animate_fade(arr_div2, t, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(cb_four_div2, t, SHORT_ANIM_DURATION, fade_in=False)

    # Shift x and != 0 to new position
    animate_slide(vc_x_interact, t, SHORT_ANIM_DURATION, vc_x_interact.location.copy(), Vector((0.0, 0.1, 0)))
    animate_slide(ne_bar, t, SHORT_ANIM_DURATION, ne_bar.location.copy(), Vector((1.0, 0.1, 0)))
    animate_slide(cb_zero, t, SHORT_ANIM_DURATION, cb_zero.location.copy(), Vector((2.0, 0.1, 0)))
    
    # Glow final result
    for obj in [vc_x_interact, ne_bar, cb_zero]:
        animate_glow(obj, t + SHORT_ANIM_DURATION, GLOW_PULSE_DURATION, max_strength=5.0)

    t = 47 * F

    # 0:47-0:50: GraphAxes fades in. FunctionLine draws itself.
    graph_axes = create_graph_axes("GraphAxes", location=(5, 0.1, 0), size=6.0)
    animate_fade(graph_axes, t, FADE_DURATION, fade_in=True)

    # Function: f(x) = x/4 + 3
    func_line_obj = create_function_line("FUNC_Line", "x/4 + 3", x_range=(-10, 10), location=(5, 0.1, 0))
    
    # Animate Trim Curve to draw the line
    mod = func_line_obj.modifiers.get("Trim_Curve")
    if mod:
        animate_property(mod, 'end', t + FADE_DURATION, t + FADE_DURATION + DRAW_DURATION, 0.0, 1.0, LINE)
    
    t = 50 * F

    # 0:50-0:53: Pulsating HoleEffect at (0, 3) on the line.
    # The coordinate (0,3) in math maps to (0,0,3) in Blender (x, y_depth, z_height) for this setup
    hole_effect = create_hole_effect("HoleEffect", location=(5 + 0, 0.1, 3.05), size=0.3) # Offset Z slightly
    
    # Animate hole effect pulse
    animate_fade(hole_effect, t, SHORT_ANIM_DURATION, fade_in=True)
    animate_scale(hole_effect, t, GLOW_PULSE_DURATION, 0.1, 0.4)
    animate_scale(hole_effect, t + GLOW_PULSE_DURATION, GLOW_PULSE_DURATION, 0.4, 0.2)
    
    t = 53 * F

    # 0:53-0:57: "Domain: All real numbers x ≠ 0" and interval notation fade in.
    domain_text_line1 = create_text_display("TXT_Domain1", "Domain: All real numbers x ≠ 0", location=(0, 0.1, -3.0), size=0.5)
    domain_text_line2 = create_text_display("TXT_Domain2", "$(-\infty, 0) \cup (0, \infty)$", location=(0, 0.1, -3.5), size=0.5)
    
    animate_fade(domain_text_line1, t, FADE_DURATION, fade_in=True)
    animate_fade(domain_text_line2, t + FADE_DURATION * 0.5, FADE_DURATION, fade_in=True)

    t = 57 * F

    # 0:57-1:00: Camera zooms out to show full whiteboard. "Summary of Solution:" appears.
    cam_final_zoom_out_loc = Vector((0, -15, 7))
    cam_final_zoom_out_rot = Euler((math.radians(70), 0, 0), 'XYZ')
    animate_camera_motion(camera_obj, t, 3*F, cam_final_zoom_out_loc, cam_final_zoom_out_rot, target_focal_length=20)

    summary_text = create_text_display("TXT_Summary", "Summary of Solution:", location=(0, 0.1, 4.5), size=0.7)
    animate_fade(summary_text, t + FADE_DURATION, FADE_DURATION, fade_in=True)

    t = 60 * F

    # 1:00-1:05: Simplified function and domain statement highlighted.
    # Simplified function is: fx_eq_text, frac_group_empty, plus_op_text, three_const_text
    # Domain statement is: vc_x_interact, ne_bar, cb_zero, domain_text_line1, domain_text_line2
    
    # Glow these objects
    for obj in [fx_eq_text, frac_group_empty, plus_op_text, three_const_text, vc_x_interact, ne_bar, cb_zero, domain_text_line1, domain_text_line2]:
        if isinstance(obj, bpy.types.Object) and obj.type == 'EMPTY': # Grouped object
            for child in obj.children:
                animate_glow(child, t, GLOW_PULSE_DURATION, max_strength=2.0, min_strength=0.0)
        else:
            animate_glow(obj, t, GLOW_PULSE_DURATION, max_strength=2.0, min_strength=0.0)
    
    t = 65 * F

    # 1:05-1:08: "Additional Interpretation: Finding the Root" slides in. Simplified function appears in center.
    # Fade out all current results, keep whiteboard.
    # First, unparent elements from frac_group_empty to allow individual manipulation
    if frac_group_empty and frac_group_empty.name in bpy.data.objects:
        for child in list(frac_group_empty.children): # Use list() to iterate over a copy
            child.parent = None
            # Keep child's world position after unparenting
            child.matrix_world.translation = frac_group_empty.matrix_world @ child.location
    
    # Fade out all previously shown elements
    elements_to_fade_out = [
        fx_eq_text, initial_frac_line, plus_op_text, three_const_text, # previously part of func_group_empty
        x_squared_text, four_x_text, # original function text
        summary_text, graph_axes, func_line_obj, hole_effect, 
        vc_x_interact, ne_bar, cb_zero, domain_text_line1, domain_text_line2, step1_text, step2_text, problem_text
    ]
    
    for obj in elements_to_fade_out:
        if obj and obj.name in bpy.data.objects: # Check if object still exists
            animate_fade(obj, t, FADE_DURATION, fade_in=False)

    # Delete the empty group after unparenting
    if frac_group_empty and frac_group_empty.name in bpy.data.objects:
        bpy.data.objects.remove(frac_group_empty, do_unlink=True)

    # Move simplified function to center for new focus
    target_simplified_loc = Vector((0, 0.1, 1))
    
    # Re-position them as individual elements. These were already created, just moved/unparented
    # vc_x_num1 is the remaining 'x'
    # cb_four is the remaining '4'
    # initial_frac_line is the original fraction line
    
    animate_slide(vc_x_num1, t + FADE_DURATION, FADE_DURATION, vc_x_num1.location.copy(), target_simplified_loc + Vector((-1.0, 0, 0.3)))
    animate_slide(cb_four, t + FADE_DURATION, FADE_DURATION, cb_four.location.copy(), target_simplified_loc + Vector((-1.0, 0, -0.3)))
    
    # Current frac line points after scaling/unparenting might be complex, so re-set based on target_simplified_loc
    initial_frac_line.data.splines[0].bezier_points[0].co = target_simplified_loc + Vector((-1.5, 0, 0))
    initial_frac_line.data.splines[0].bezier_points[1].co = target_simplified_loc + Vector((-0.5, 0, 0))
    initial_frac_line.keyframe_insert(data_path='data.splines[0].bezier_points[0].co', frame=t + FADE_DURATION)
    initial_frac_line.keyframe_insert(data_path='data.splines[0].bezier_points[1].co', frame=t + FADE_DURATION)


    animate_slide(fx_eq_text, t + FADE_DURATION, FADE_DURATION, fx_eq_text.location.copy(), target_simplified_loc + Vector((-2.5, 0, 0)))
    animate_slide(plus_op_text, t + FADE_DURATION, FADE_DURATION, plus_op_text.location.copy(), target_simplified_loc + Vector((0.0, 0, 0)))
    animate_slide(three_const_text, t + FADE_DURATION, FADE_DURATION, three_const_text.location.copy(), target_simplified_loc + Vector((0.5, 0, 0)))

    for obj in [fx_eq_text, vc_x_num1, cb_four, initial_frac_line, plus_op_text, three_const_text]:
        animate_fade(obj, t + FADE_DURATION, FADE_DURATION, fade_in=True)
        animate_scale(obj, t + FADE_DURATION, FADE_DURATION, obj.scale.x, 1.0)
        if obj.data and obj.data.materials and obj.active_material_index > 0:
            obj.active_material_index = 0
            obj.keyframe_insert(data_path='active_material_index', frame=t + FADE_DURATION) # Revert to original material


    additional_text = create_text_display("TXT_Additional", "Additional Interpretation: Finding the Root (where f(x)=0)", 
                                        location=(0, 0.1, 4), size=0.6)
    animate_slide(additional_text, t, SLIDE_DURATION, Vector((-10, 0.1, 4)), Vector((0, 0.1, 4)))

    t = 68 * F

    # 1:08-1:11: f(x) fades out, replaced by 0 and = bar.
    animate_fade(fx_eq_text, t, FADE_DURATION, fade_in=False)

    eq_bar_root = create_equals_bar("EQ_Bar_Root", location=(fx_eq_text.location.x + 1.0, 0.1, fx_eq_text.location.z), length=0.8)
    cb_zero_root = create_constant_block("CB_Zero_Root", "0", location=(fx_eq_text.location.x + 2.0, 0.1, fx_eq_text.location.z), size_x=0.8, size_y=0.4, size_z=0.2)

    for obj in [eq_bar_root, cb_zero_root]:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=t-1)
        obj.keyframe_insert(data_path='hide_viewport', frame=t-1)
        animate_fade(obj, t + FADE_DURATION * 0.5, FADE_DURATION, fade_in=True)

    t = 71 * F

    # 1:11-1:15: Subtract 3 animation.
    animate_glow(three_const_text, t, GLOW_PULSE_DURATION, max_strength=5.0)

    # Duplicate op arrow and const block for both sides
    arr_minus1 = create_operation_arrow("ARR_Minus1", "-", location=(plus_op_text.location.x + 1.0, 0.1, plus_op_text.location.z), scale=0.5)
    cb_three_minus1 = create_constant_block("CB_Three_Minus1", "3", location=(three_const_text.location.x + 1.0, 0.1, three_const_text.location.z), size_x=0.8, size_y=0.4, size_z=0.2)
    
    arr_minus2 = create_operation_arrow("ARR_Minus2", "-", location=(cb_zero_root.location.x + 1.0, 0.1, cb_zero_root.location.z), scale=0.5)
    cb_three_minus2 = create_constant_block("CB_Three_Minus2", "3", location=(cb_zero_root.location.x + 1.5, 0.1, cb_zero_root.location.z), size_x=0.8, size_y=0.4, size_z=0.2)
    
    for obj in [arr_minus1, cb_three_minus1, arr_minus2, cb_three_minus2]:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=t-1)
        obj.keyframe_insert(data_path='hide_viewport', frame=t-1)
        animate_fade(obj, t, FADE_DURATION, fade_in=True)

    # Animate left side disappearing
    animate_fade(plus_op_text, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(three_const_text, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(arr_minus1, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(cb_three_minus1, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)

    t = 75 * F

    # 1:15-1:18: 0 - 3 = -3.
    # cb_zero_root (now 0) transforms to -3
    cb_zero_root_value = bpy.data.objects.get("CB_Zero_Root_Value")
    if cb_zero_root_value: 
        cb_zero_root_value.data.body = "-3" # Update text
        # Ensure it has the dark text material
        if MAT_TEXT_DARK not in cb_zero_root_value.data.materials:
            cb_zero_root_value.data.materials.append(MAT_TEXT_DARK)
        cb_zero_root_value.active_material_index = cb_zero_root_value.data.materials.find(MAT_TEXT_DARK.name)
        cb_zero_root_value.keyframe_insert(data_path='active_material_index', frame=t)


    animate_fade(arr_minus2, t, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(cb_three_minus2, t, SHORT_ANIM_DURATION, fade_in=False)
    
    # Relocate elements to fill gap
    animate_slide(cb_zero_root, t, SHORT_ANIM_DURATION, cb_zero_root.location.copy(), eq_bar_root.location + Vector((0.0, 0, 0)))
    
    # Move x/4 and equals bar to new positions
    animate_slide(vc_x_num1, t, SHORT_ANIM_DURATION, vc_x_num1.location.copy(), vc_x_num1.location + Vector((-0.7, 0, 0)))
    animate_property(initial_frac_line.data.splines[0].bezier_points[0], 'co', t, t + SHORT_ANIM_DURATION, initial_frac_line.data.splines[0].bezier_points[0].co.copy(), initial_frac_line.data.splines[0].bezier_points[0].co.copy() + Vector((-0.7,0,0)))
    animate_property(initial_frac_line.data.splines[0].bezier_points[1], 'co', t, t + SHORT_ANIM_DURATION, initial_frac_line.data.splines[0].bezier_points[1].co.copy(), initial_frac_line.data.splines[0].bezier_points[1].co.copy() + Vector((-0.7,0,0)))
    animate_slide(cb_four, t, SHORT_ANIM_DURATION, cb_four.location.copy(), cb_four.location + Vector((-0.7, 0, 0)))
    
    animate_slide(eq_bar_root, t, SHORT_ANIM_DURATION, eq_bar_root.location.copy(), eq_bar_root.location + Vector((-0.7, 0, 0)))

    t = 78 * F

    # 1:18-1:22: Multiply by 4 animation.
    animate_glow(vc_x_num1, t, GLOW_PULSE_DURATION, max_strength=5.0) # Glow x/4 (numerator)
    animate_glow(cb_four, t, GLOW_PULSE_DURATION, max_strength=5.0) # Glow x/4 (denominator)

    # Create multiply by 4 on both sides
    arr_mult_root1 = create_operation_arrow("ARR_Mult_Root1", "✖️", location=(vc_x_num1.location.x - 0.5, 0.1, vc_x_num1.location.z), scale=0.5)
    cb_four_mult1 = create_constant_block("CB_Four_Mult1", "4", location=(vc_x_num1.location.x - 1.0, 0.1, vc_x_num1.location.z), size_x=0.8, size_y=0.4, size_z=0.2)
    
    arr_mult_root2 = create_operation_arrow("ARR_Mult_Root2", "✖️", location=(cb_zero_root.location.x + 1.0, 0.1, cb_zero_root.location.z), scale=0.5)
    cb_four_mult2 = create_constant_block("CB_Four_Mult2", "4", location=(cb_zero_root.location.x + 1.5, 0.1, cb_zero_root.location.z), size_x=0.8, size_y=0.4, size_z=0.2)

    for obj in [arr_mult_root1, cb_four_mult1, arr_mult_root2, cb_four_mult2]:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path='hide_render', frame=t-1)
        obj.keyframe_insert(data_path='hide_viewport', frame=t-1)
        animate_fade(obj, t, FADE_DURATION, fade_in=True)
    
    # Left side disappears (denominator and multiply by 4)
    animate_fade(arr_mult_root1, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(cb_four_mult1, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(initial_frac_line, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False) # Fraction line disappears
    animate_fade(cb_four, t + FADE_DURATION, SHORT_ANIM_DURATION, fade_in=False) # Denominator 4 disappears

    t = 82 * F

    # 1:22-1:25: -3 * 4 = -12. x = -12 glows.
    # Fade out multiply arrow and 4
    animate_fade(arr_mult_root2, t, SHORT_ANIM_DURATION, fade_in=False)
    animate_fade(cb_four_mult2, t, SHORT_ANIM_DURATION, fade_in=False)

    # -3 * 4 = -12. cb_zero_root (now -3) transforms to -12
    if cb_zero_root_value: cb_zero_root_value.data.body = "-12"
    
    # Shift x and equals bar to the left
    animate_slide(vc_x_num1, t, SHORT_ANIM_DURATION, vc_x_num1.location.copy(), cb_zero_root.location + Vector((-2.0, 0, 0)))
    animate_slide(eq_bar_root, t, SHORT_ANIM_DURATION, eq_bar_root.location.copy(), cb_zero_root.location + Vector((-1.0, 0, 0)))
    animate_slide(cb_zero_root, t, SHORT_ANIM_DURATION, cb_zero_root.location.copy(), cb_zero_root.location + Vector((0, 0, 0))) # It stays, just update content and glow

    # Glow final root
    for obj in [vc_x_num1, eq_bar_root, cb_zero_root]:
        animate_glow(obj, t + SHORT_ANIM_DURATION, GLOW_PULSE_DURATION, max_strength=5.0)

    t = 85 * F

    # 1:25-1:28: -12 slides towards GraphAxes, stops away from HoleEffect.
    # Re-show graph axes, func line, hole effect (they were faded out from 1:05)
    # The existing graph_axes, func_line_obj, hole_effect objects will be re-used, not new ones.
    
    for obj in [graph_axes, func_line_obj, hole_effect]:
        animate_fade(obj, t, FADE_DURATION, fade_in=True)
        if obj.name == func_line_obj.name: # Ensure line is fully drawn if not already
             mod = obj.modifiers.get("Trim_Curve")
             if mod: mod.end = 1.0; mod.keyframe_insert(data_path='end', frame=t)


    # Slide -12 (cb_zero_root) towards graph
    current_root_loc = cb_zero_root.location.copy()
    target_root_loc = Vector((graph_axes.location.x - 3, 0.1, graph_axes.location.z - 2)) # Example: near x=-12 on graph
    animate_slide(cb_zero_root, t, SLIDE_DURATION, current_root_loc, target_root_loc)

    t = 88 * F

    # 1:28-1:30: "Valid Root: x = -12 (within domain)" appears.
    valid_root_text = create_text_display("TXT_ValidRoot", "Valid Root: x = -12 (within domain)", location=(0, 0.1, -3.0), size=0.5)
    animate_fade(valid_root_text, t, FADE_DURATION, fade_in=True)

    t = 90 * F

    # 1:30-1:35: Camera pulls back to reveal entire whiteboard, key results highlighted. "Solved!" appears.
    # Fade out current root explanation
    elements_to_fade_out_final_pullback = [
        valid_root_text, vc_x_num1, eq_bar_root, cb_zero_root, additional_text,
        graph_axes, func_line_obj, hole_effect # These will be re-used, so hide then re-show
    ]

    for obj in elements_to_fade_out_final_pullback:
        if obj and obj.name in bpy.data.objects:
            animate_fade(obj, t, FADE_DURATION, fade_in=False)

    # Re-position simplified function and domain texts to their final positions for summary
    # The initial function components are still around: fx_eq_text, plus_op_text, three_const_text
    # Re-create a simplified fraction group to manage them
    simplified_frac_loc_final = Vector((-3.0, 0.1, 2.0))
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=simplified_frac_loc_final)
    frac_group_final = bpy.context.object
    frac_group_final.name = "GRP_SimplifiedFraction_Final"
    add_object_to_collection(frac_group_final, collections["_MATH_ELEMENTS"].name)
    
    # Re-parent the elements that form the simplified fraction (vc_x_num1 and a new frac line)
    vc_x_num1.parent = frac_group_final
    vc_x_num1.location = Vector((0, 0, 0.3)) # Relative to parent
    
    cb_four_final = create_constant_block("CB_Four_Final", "4", location=(0, 0, -0.3), size_x=0.8, size_y=0.4, size_z=0.2)
    cb_four_final.parent = frac_group_final
    
    initial_frac_line_final = create_fraction_line("FRAC_Initial_Final", Vector((-0.5, 0, 0)), Vector((0.5, 0, 0)))
    initial_frac_line_final.parent = frac_group_final
    
    fx_eq_text.parent = frac_group_final
    fx_eq_text.location = Vector((-1.5, 0, 0)) # Relative to parent
    plus_op_text.parent = frac_group_final
    plus_op_text.location = Vector((1.0, 0, 0)) # Relative to parent
    three_const_text.parent = frac_group_final
    three_const_text.location = Vector((1.5, 0, 0)) # Relative to parent


    simplified_form_text.location = Vector((-2.0, 0.1, 3.5)) # This one is global

    # Restore domain text objects (already created)
    domain_text_line1.location = Vector((0, 0.1, -3.0))
    domain_text_line2.location = Vector((0, 0.1, -3.5))

    # Re-create the simplified domain inequality objects (x!=0)
    vc_x_interact_final = create_variable_cube("VC_X_Interact_Final", "x", location=(0.0, 0.1, -1.0), size=0.6)
    ne_bar_final = create_equals_bar("NE_Bar_Final", location=(1.0, 0.1, -1.0), is_not_equal=True)
    cb_zero_final = create_constant_block("CB_Zero_Final", "0", location=(2.0, 0.1, -1.0), size_x=0.8, size_y=0.4, size_z=0.2)

    # Re-create the graph axes and function line with the hole effect.
    # We hide the old ones and show new ones if they were destroyed. If not, just re-show.
    # For simplicity, let's re-show the ones created earlier and hidden.
    for obj in [graph_axes, func_line_obj, hole_effect]:
        if obj and obj.name in bpy.data.objects:
            animate_fade(obj, t + FADE_DURATION, FADE_DURATION, fade_in=True) # Fade in again
            if obj.name == func_line_obj.name: # Ensure line is fully drawn if not already
                mod = obj.modifiers.get("Trim_Curve")
                if mod: mod.end = 1.0; mod.keyframe_insert(data_path='end', frame=t + FADE_DURATION)


    # Re-show all relevant elements
    for obj in [frac_group_final, simplified_form_text, domain_text_line1, domain_text_line2,
                vc_x_interact_final, ne_bar_final, cb_zero_final]:
        animate_fade(obj, t + FADE_DURATION, FADE_DURATION, fade_in=True)
        # Also ensure their children fade in if they are parented empties
        if obj.type == 'EMPTY':
            for child in obj.children:
                animate_fade(child, t + FADE_DURATION, FADE_DURATION, fade_in=True)
    
    # Animate camera pull back
    animate_camera_motion(camera_obj, t, 5*F, Vector((0, -20, 10)), Euler((math.radians(70), 0, 0), 'XYZ'), target_focal_length=20)
    
    solved_text = create_text_display("TXT_Solved", "Solved!", location=(0, 0.1, 0), size=2.0, extrusion=0.1, material=MAT_SOLVED_TEXT)
    animate_fade(solved_text, t + 3*F, FADE_DURATION, fade_in=True)

    t = 95 * F

    # 1:35-1:38: Fade to black. "Blender Math Animation" card.
    # Fade out all current content
    for obj in bpy.data.objects:
        if obj.name not in [camera_obj.name, light_obj1.name, light_obj2.name, whiteboard_bg.name]: # Keep camera, lights, whiteboard
            animate_fade(obj, t, 2*F, fade_in=False) # Faster fade out everything

    # Create end card
    end_card_text = create_text_display("TXT_EndCard", "Blender Math Animation", location=(0, -1, 0), size=1.5, extrusion=0.05, material=MAT_END_CARD)
    end_card_text.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ') # Lay flat to be seen by camera
    animate_fade(end_card_text, t + 2*F, FADE_DURATION, fade_in=True)
    
    # Fade whiteboard to black (by dimming its color)
    whiteboard_mat = bpy.data.materials.get("MAT_Whiteboard")
    if whiteboard_mat and whiteboard_mat.use_nodes:
        principled_node = whiteboard_mat.node_tree.nodes.get('Principled BSDF')
        if principled_node:
            animate_property(principled_node.inputs['Base Color'], 'default_value', t + 2*F, TOTAL_FRAMES, (0.95, 0.95, 0.95, 1), (0.0, 0.0, 0.0, 1), LINE)

    # Fade world background to black
    bpy.context.scene.world.use_nodes = True
    world_nodes = bpy.context.scene.world.node_tree.nodes
    bg_node = world_nodes.get('Background')
    if bg_node:
        bg_node.inputs['Color'].default_value = (0, 0, 0, 1) # Black
        bg_node.inputs['Color'].keyframe_insert(data_path='default_value', frame=t + 2*F)
        bg_node.inputs['Color'].default_value = (0, 0, 0, 1) # Still black
        bg_node.inputs['Color'].keyframe_insert(data_path='default_value', frame=TOTAL_FRAMES)
        
    bpy.context.scene.frame_current = 0 # Reset timeline to start

# Run the script
if __name__ == "__main__":
    main()