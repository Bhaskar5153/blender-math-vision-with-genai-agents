import bpy
import math

# --- Scene Setup ---
def setup_scene():
    """Clears the scene, sets render settings, and creates a camera and light."""
    # Clear existing objects
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Set render engine to Cycles for better materials/emission
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128 # Lower for faster previews, increase for final render
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.fps = 25
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 3500 # Approx 2:35 * 25 fps

    # Camera setup
    cam_data = bpy.data.cameras.new('MainCamera')
    camera = bpy.data.objects.new('MainCamera', cam_data)
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    camera.location = (0, -10, 5)
    camera.rotation_euler = (math.radians(60), 0, 0) # Look down slightly

    # Lighting: Sun Lamp
    light_data = bpy.data.lights.new(name="SunLight", type='SUN')
    sun_light = bpy.data.objects.new(name="SunLight", object_data=light_data)
    bpy.context.collection.objects.link(sun_light)
    sun_light.location = (5, -5, 10)
    sun_light.rotation_euler = (math.radians(-45), math.radians(45), math.radians(-10))
    light_data.energy = 5 # Adjust as needed
    
    # Create main collections for better organization
    if "EquationElements" not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(bpy.data.collections.new("EquationElements"))
    if "Backgrounds" not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(bpy.data.collections.new("Backgrounds"))
    if "Graphs" not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(bpy.data.collections.new("Graphs"))

    return camera

# --- Material Functions ---
def get_material(name, color=(0.8, 0.8, 0.8, 1), emission_color=(0,0,0,0), emission_strength=0.0, transparency=0.0, metallic=0.0, roughness=0.5):
    """Gets an existing material or creates a new one with specified properties."""
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        
        # Emission
        if emission_strength > 0:
            bsdf.inputs['Emission'].default_value = emission_color
            bsdf.inputs['Emission Strength'].default_value = emission_strength

        # Transparency (Alpha)
        if transparency > 0:
            mat.blend_method = 'BLEND'
            bsdf.inputs['Alpha'].default_value = 1.0 - transparency
            
    return mat

# --- Asset Creation Functions ---
def create_text_mesh(name, text_content, font_size=1.0, extrusion=0.05):
    """Creates a Blender Text object and converts it to mesh (optional but simplifies material/animation)."""
    font_curve = bpy.data.curves.new(type="FONT", name=f"{name}_Curve")
    font_curve.body = str(text_content)
    font_curve.size = font_size
    font_curve.extrude = extrusion
    font_curve.resolution_u = 2 

    text_obj = bpy.data.objects.new(name, font_curve)
    bpy.context.collection.objects.link(text_obj)
    
    # For animation, keeping as FONT is better if text content changes.
    # If text content is static, converting to mesh can reduce overhead.
    # For this script, content changes on temp objects, so FONT is okay.
    
    return text_obj

def create_variable_cube(name, symbol, color, emission_strength=0.0):
    """Creates a cube with a text symbol on its face."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, align='WORLD', location=(0,0,0))
    cube = bpy.context.active_object
    cube.name = name
    
    text_obj = create_text_mesh(f"{name}_Text", symbol, font_size=0.8, extrusion=0.1)
    text_obj.parent = cube
    # Position and rotate text to be centered on the front face
    text_obj.location = (0, -0.51, 0) # Slightly in front of the cube's face
    text_obj.rotation_euler = (math.radians(90), math.radians(0), math.radians(0)) # Face towards +Y, then rotate to face cam
    
    # Material
    mat = get_material(f"{name}_Mat", color=(*color[:3], 0.6), transparency=0.4, metallic=0.1, roughness=0.3,
                       emission_color=(*color[:3], 1), emission_strength=emission_strength)
    cube.data.materials.append(mat)
    text_obj.data.materials.append(mat)
    
    # Set parent inverse for proper local transformation
    text_obj.matrix_parent_inverse = cube.matrix_world.inverted()
    
    return cube, text_obj

def create_constant_block(name, value, color, emission_strength=0.0):
    """Creates a solid block with a number on its face."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, align='WORLD', location=(0,0,0))
    block = bpy.context.active_object
    block.name = name

    text_obj = create_text_mesh(f"{name}_Text", str(value), font_size=0.8, extrusion=0.1)
    text_obj.parent = block
    text_obj.location = (0, -0.51, 0) # Slightly in front of the block's face
    text_obj.rotation_euler = (math.radians(90), math.radians(0), math.radians(0)) # Face towards +Y, then rotate to face cam

    mat = get_material(f"{name}_Mat", color=(*color[:3], 1), metallic=0.7, roughness=0.2,
                       emission_color=(*color[:3], 1), emission_strength=emission_strength)
    block.data.materials.append(mat)
    text_obj.data.materials.append(mat)
    
    text_obj.matrix_parent_inverse = block.matrix_world.inverted()

    return block, text_obj

def create_operation_arrow(name, op_type, size=0.5):
    """Creates an arrow mesh with an operation symbol and color."""
    # Create simple arrow mesh: cone for head, cylinder for body
    bpy.ops.mesh.primitive_cone_add(radius1=0.15*size, radius2=0, depth=0.4*size, enter_editmode=False, align='WORLD', location=(0,0,0.2*size))
    head = bpy.context.active_object
    head.name = f"{name}_Head"
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05*size, depth=0.6*size, enter_editmode=False, align='WORLD', location=(0,0,-0.1*size))
    body = bpy.context.active_object
    body.name = f"{name}_Body"

    # Join them
    bpy.ops.object.select_all(action='DESELECT')
    head.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.join()
    arrow = bpy.context.active_object
    arrow.name = name
    arrow.rotation_euler = (math.radians(90), 0, 0) # Orient arrow to point along Y-axis for initial setup

    # Create symbol text
    symbol_map = {
        'plus': '+', 'minus': '-', 'multiply': '�', 'divide': '�'
    }
    color_map = {
        'plus': (1, 1, 0, 1),       # Bright yellow
        'minus': (0.5, 0, 0.5, 1),  # Deep purple
        'multiply': (1, 0.5, 0, 1), # Orange
        'divide': (0, 1, 1, 1)      # Cyan
    }
    
    symbol_text_obj = create_text_mesh(f"{name}_Symbol", symbol_map.get(op_type, '?'), font_size=0.5*size, extrusion=0.05)
    symbol_text_obj.parent = arrow
    symbol_text_obj.location = (0, 0.0, 0.0) # Centered on arrow
    symbol_text_obj.rotation_euler = (-math.radians(90), 0, 0) # Rotate to face camera relative to parent
    symbol_text_obj.matrix_parent_inverse = arrow.matrix_world.inverted()

    mat_color = color_map.get(op_type, (0.8, 0.8, 0.8, 1))
    mat = get_material(f"{name}_Mat", color=(0,0,0,1), emission_color=(*mat_color[:3], 1), emission_strength=5.0, metallic=0.0, roughness=0.5)
    arrow.data.materials.append(mat)
    symbol_text_obj.data.materials.append(mat)
    
    return arrow, symbol_text_obj

def create_equals_bar(name, length=2.0, thickness=0.1):
    """Creates two horizontal bars representing an equals sign."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, enter_editmode=False, align='WORLD')
    bar1 = bpy.context.active_object
    bar1.name = f"{name}_Bar1"
    bar1.scale = (length, thickness, thickness)
    bar1.location = (0, 0, 0.5 * thickness)

    bpy.ops.mesh.primitive_plane_add(size=1.0, enter_editmode=False, align='WORLD')
    bar2 = bpy.context.active_object
    bar2.name = f"{name}_Bar2"
    bar2.scale = (length, thickness, thickness)
    bar2.location = (0, 0, -0.5 * thickness)

    # Join them
    bpy.ops.object.select_all(action='DESELECT')
    bar1.select_set(True)
    bar2.select_set(True)
    bpy.context.view_layer.objects.active = bar1
    bpy.ops.object.join()
    equals_bar = bpy.context.active_object
    equals_bar.name = name

    mat = get_material(f"{name}_Mat", color=(1,1,1,1), emission_color=(1,1,1,1), emission_strength=5.0, metallic=0.0, roughness=0.1)
    equals_bar.data.materials.append(mat)
    return equals_bar

def create_fraction_line(name, length=1.0, thickness=0.05):
    """Creates a thin horizontal line for fractions."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, enter_editmode=False, align='WORLD')
    line = bpy.context.active_object
    line.name = name
    line.scale = (length, thickness, thickness)
    mat = get_material(f"{name}_Mat", color=(0.2,0.2,0.2,1))
    line.data.materials.append(mat)
    return line

def create_whiteboard_grid(name="WhiteboardGrid", size=20):
    """Creates a large plane with a grid texture material."""
    bpy.ops.mesh.primitive_plane_add(size=size, enter_editmode=False, align='WORLD', location=(0,0,-0.01))
    whiteboard = bpy.context.active_object
    whiteboard.name = name

    mat = get_material(f"{name}_Mat", color=(0.95,0.95,0.95,1))
    whiteboard.data.materials.append(mat)
    
    # Add grid texture nodes
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    if "Grid Texture" not in nodes:
        grid_tex = nodes.new(type='ShaderNodeTexChecker')
        grid_tex.location = (-400, 300)
        grid_tex.inputs['Scale'].default_value = 10 
        
        mix_rgb = nodes.new(type='ShaderNodeMixRGB')
        mix_rgb.location = (-200, 300)
        mix_rgb.inputs['Fac'].default_value = 0.9 
        mix_rgb.inputs['Color1'].default_value = (0.95, 0.95, 0.95, 1) 
        mix_rgb.inputs['Color2'].default_value = (0.8, 0.8, 0.8, 1) 
        
        links.new(grid_tex.outputs['Color'], mix_rgb.inputs['Fac'])
        links.new(mix_rgb.outputs['Color'], nodes["Principled BSDF"].inputs['Base Color'])
        
    whiteboard.hide_render = True 
    whiteboard.hide_set(True)

    return whiteboard

def create_coordinate_plane(name="CoordinatePlane", size=10, grid_spacing=1.0):
    """Creates a 2D coordinate plane with glowing X and Y axes."""
    # Main plane
    bpy.ops.mesh.primitive_plane_add(size=size*2, enter_editmode=False, align='WORLD', location=(0,0,-0.01))
    plane = bpy.context.active_object
    plane.name = f"{name}_Base"
    
    # Material for the plane (subtle grid)
    mat = get_material(f"{name}_Mat", color=(0.1,0.1,0.1,1), metallic=0.0, roughness=0.8)
    plane.data.materials.append(mat)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    if "Grid Texture" not in nodes: 
        grid_tex = nodes.new(type='ShaderNodeTexGrid')
        grid_tex.location = (-400, 300)
        grid_tex.inputs['Scale'].default_value = 1 / grid_spacing
        grid_tex.inputs['Lines'].default_value = 0.01 
        
        mix_rgb = nodes.new(type='ShaderNodeMixRGB')
        mix_rgb.location = (-200, 300)
        mix_rgb.inputs['Fac'].default_value = 0.95 
        mix_rgb.inputs['Color1'].default_value = (0.1, 0.1, 0.1, 1) 
        mix_rgb.inputs['Color2'].default_value = (0.2, 0.2, 0.2, 1) 
        
        links.new(grid_tex.outputs['Color'], mix_rgb.inputs['Fac'])
        links.new(mix_rgb.outputs['Color'], nodes["Principled BSDF"].inputs['Base Color'])
    
    # Axes material
    axis_mat = get_material("AxisMat", color=(0,0,1,1), emission_color=(0,0,1,1), emission_strength=5)
    
    # X-Axis
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=size*2, enter_editmode=False, align='WORLD', location=(0,0,0))
    x_axis = bpy.context.active_object
    x_axis.name = "X_Axis"
    x_axis.rotation_euler = (0, math.radians(90), 0)
    x_axis.data.materials.append(axis_mat)
    
    # Y-Axis
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=size*2, enter_editmode=False, align='WORLD', location=(0,0,0))
    y_axis = bpy.context.active_object
    y_axis.name = "Y_Axis"
    y_axis.data.materials.append(axis_mat)
    
    # Labels for axes
    x_label = create_text_mesh("X_Label", "X", font_size=0.5, extrusion=0.05)
    x_label.location = (size + 0.5, 0, 0.05)
    x_label.rotation_euler = (math.radians(90), 0, 0)
    x_label.data.materials.append(axis_mat)

    y_label = create_text_mesh("Y_Label", "Y", font_size=0.5, extrusion=0.05)
    y_label.location = (0, size + 0.5, 0.05)
    y_label.rotation_euler = (math.radians(90), 0, 0)
    y_label.data.materials.append(axis_mat)

    # Group into an empty for easy manipulation
    coord_plane_empty = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(coord_plane_empty)
    for obj in [plane, x_axis, y_axis, x_label, y_label]:
        obj.parent = coord_plane_empty
        
    coord_plane_empty.hide_render = True 
    coord_plane_empty.hide_set(True)

    return coord_plane_empty, plane, x_axis, y_axis, x_label, y_label

def create_point_sphere(name, radius=0.1, color=(1,0,0,1), emission_strength=10):
    """Creates a small glowing sphere to mark points on the graph."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, enter_editmode=False, align='WORLD', location=(0,0,0))
    sphere = bpy.context.active_object
    sphere.name = name
    mat = get_material(f"{name}_Mat", color=(*color[:3], 1), emission_color=(*color[:3], 1), emission_strength=emission_strength)
    sphere.data.materials.append(mat)
    sphere.hide_render = True 
    sphere.hide_set(True)
    return sphere

def create_solution_line(name="SolutionLine", color=(0,1,0,1), emission_strength=5, thickness=0.05):
    """Creates a Bezier Curve object to represent the solution line."""
    curve_data = bpy.data.curves.new(name=f"{name}_Curve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = thickness / 2
    curve_data.bevel_resolution = 6
    curve_data.fill_mode = 'FULL'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)

    mat = get_material(f"{name}_Mat", color=(*color[:3], 1), emission_color=(*color[:3], 1), emission_strength=emission_strength)
    obj.data.materials.append(mat)
    
    # Set up start/end keyframes for line drawing animation
    curve_data.path_properties.eval_time = 0 
    obj.hide_render = True
    obj.hide_set(True)
    return obj

# --- Animation Helper Functions ---

def animate_property(obj, property_name, value_start, value_end, frame_start, duration_frames, ease_func='BEZIER'):
    """Animates a property of an object (location, rotation, scale, material input)."""
    frame_end = frame_start + duration_frames
    
    obj.hide_render = False # Ensure visible during animation
    obj.hide_set(False) 
    
    if hasattr(obj, property_name):
        setattr(obj, property_name, value_start)
        obj.keyframe_insert(data_path=property_name, frame=frame_start)
        setattr(obj, property_name, value_end)
        obj.keyframe_insert(data_path=property_name, frame=frame_end)
    elif isinstance(obj, bpy.types.Material) and "nodes" in property_name:
        # For material node properties like Emission Strength
        node_path = property_name.split(".nodes[")[1].split("].inputs[")
        node_name = node_path[0].strip('"')
        input_name = node_path[1].split("].default_value")[0].strip('"')
        
        bsdf_node = obj.node_tree.nodes.get(node_name)
        if bsdf_node and input_name in bsdf_node.inputs:
            bsdf_node.inputs[input_name].default_value = value_start
            bsdf_node.inputs[input_name].keyframe_insert(data_path=f'nodes["{node_name}"].inputs["{input_name}"].default_value', frame=frame_start)
            bsdf_node.inputs[input_name].default_value = value_end
            bsdf_node.inputs[input_name].keyframe_insert(data_path=f'nodes["{node_name}"].inputs["{input_name}"].default_value', frame=frame_end)
            
    # Set interpolation
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path == property_name or fcurve.data_path.startswith(property_name):
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'BEZIER' if ease_func == 'BEZIER' else 'LINEAR'

def animate_location(obj, loc_start, loc_end, frame_start, duration_frames, ease_func='BEZIER'):
    obj.location = loc_start
    animate_property(obj, "location", loc_start, loc_end, frame_start, duration_frames, ease_func)

def animate_rotation(obj, rot_start, rot_end, frame_start, duration_frames, ease_func='BEZIER'):
    obj.rotation_euler = rot_start
    animate_property(obj, "rotation_euler", rot_start, rot_end, frame_start, duration_frames, ease_func)

def animate_scale(obj, scale_start, scale_end, frame_start, duration_frames, ease_func='BEZIER'):
    obj.scale = scale_start
    animate_property(obj, "scale", scale_start, scale_end, frame_start, duration_frames, ease_func)

def animate_emission_strength(obj, strength_start, strength_end, frame_start, duration_frames, ease_func='BEZIER'):
    """Animates the emission strength of an object's first material (Principled BSDF)."""
    if obj.data.materials and obj.data.materials[0].use_nodes:
        mat = obj.data.materials[0]
        animate_property(mat, 'nodes["Principled BSDF"].inputs["Emission Strength"].default_value', strength_start, strength_end, frame_start, duration_frames, ease_func)
    
    obj.hide_render = False
    obj.hide_set(False)

def animate_glow(obj, frame_start, duration_frames, strength=10, pulse_duration_frames=10):
    """Applies a pulse glow effect to an object."""
    start_frame = frame_start
    end_frame = frame_start + duration_frames
    
    obj.hide_render = False
    obj.hide_set(False)

    animate_emission_strength(obj, 0, strength, start_frame, pulse_duration_frames, 'BEZIER')
    animate_emission_strength(obj, strength, strength, start_frame + pulse_duration_frames, duration_frames - pulse_duration_frames * 2, 'LINEAR')
    animate_emission_strength(obj, strength, 0, end_frame - pulse_duration_frames, pulse_duration_frames, 'BEZIER')

def animate_fade_out(obj, frame_start, duration_frames):
    """Fades out an object by scaling it down and then hiding it."""
    animate_scale(obj, obj.scale.copy(), (0.01, 0.01, 0.01), frame_start, duration_frames, 'BEZIER')
    
    # Hide after fade out
    obj.hide_render = False
    obj.hide_set(False)
    obj.keyframe_insert(data_path='hide_render', frame=frame_start)
    obj.hide_render = True
    obj.hide_set(True)
    obj.keyframe_insert(data_path='hide_render', frame=frame_start + duration_frames + 1) 
    obj.keyframe_insert(data_path='hide_set', frame=frame_start + duration_frames + 1) 

def animate_visibility(obj, frame_start, duration_frames, hide_render_start=True, hide_render_end=False):
    """Animates the visibility (hide_render and hide_set) of an object."""
    obj.hide_render = hide_render_start
    obj.hide_set(hide_render_start)
    obj.keyframe_insert(data_path='hide_render', frame=frame_start)
    obj.keyframe_insert(data_path='hide_set', frame=frame_start)
    
    obj.hide_render = hide_render_end
    obj.hide_set(hide_render_end)
    obj.keyframe_insert(data_path='hide_render', frame=frame_start + duration_frames)
    obj.keyframe_insert(data_path='hide_set', frame=frame_start + duration_frames)

def animate_line_draw(curve_obj, frame_start, duration_frames):
    """Animates a curve object drawing itself by controlling its eval_time."""
    curve_obj.hide_render = False
    curve_obj.hide_set(False)
    
    curve_obj.data.path_properties.eval_time = 0
    curve_obj.data.keyframe_insert(data_path='path_properties.eval_time', frame=frame_start)
    
    # Max eval_time is the total length of the curve's path. Typically, it's (number of points - 1) * 100
    # For a simple polyline, num_points * 100 or higher ensures it draws fully.
    # We'll set it to a high enough value based on segment count
    max_eval_time = curve_obj.data.splines[0].points.count_points() * 100 
    
    curve_obj.data.path_properties.eval_time = max_eval_time
    curve_obj.data.keyframe_insert(data_path='path_properties.eval_time', frame=frame_start + duration_frames)

def animate_camera_move(camera, start_loc, end_loc, start_rot, end_rot, frame_start, duration_frames, ease_func='BEZIER'):
    """Animates camera location and rotation."""
    animate_location(camera, start_loc, end_loc, frame_start, duration_frames, ease_func)
    animate_rotation(camera, start_rot, end_rot, frame_start, duration_frames, ease_func)

# --- Main Animation Logic ---

def create_equation_elements(elements_data):
    """Creates all core equation elements and their text objects, linking to collection."""
    objs = {}
    text_objs = {}
    for data in elements_data:
        name, type, value, color = data['name'], data['type'], data['value'], data['color']
        if type == 'variable':
            obj, text_obj = create_variable_cube(name, value, color)
        elif type == 'constant':
            obj, text_obj = create_constant_block(name, value, color)
        elif type == 'operation':
            obj, text_obj = create_operation_arrow(name, value)
        elif type == 'equals':
            obj = create_equals_bar(name)
            text_obj = None # Equals bar has no text object
        elif type == 'fraction_line':
            obj = create_fraction_line(name)
            text_obj = None

        objs[name] = obj
        text_objs[name] = text_obj
        
        # Parent to EquationElements collection
        if obj.name in bpy.context.collection.objects:
            bpy.context.collection.objects.unlink(obj)
        bpy.data.collections["EquationElements"].objects.link(obj)
        if text_obj and text_obj.name in bpy.context.collection.objects:
            bpy.context.collection.objects.unlink(text_obj)
        if text_obj:
            bpy.data.collections["EquationElements"].objects.link(text_obj)
        
        obj.hide_render = True # Start all hidden
        obj.hide_set(True)

    return objs, text_objs

def animate_solution_plan():
    """Main function to orchestrate the entire animation sequence."""
    camera = setup_scene()
    
    # --- Define Elements for Equation ---
    # These are definitions, not actual objects yet. Objects will be created from these.
    elements_data = [
        {'name': 'num3x', 'type': 'variable', 'value': '3x', 'color': (0.1, 0.4, 0.8, 1)}, # Blue
        {'name': 'plus1', 'type': 'operation', 'value': 'plus', 'color': (1, 1, 0, 1)},
        {'name': 'num4y', 'type': 'variable', 'value': '4y', 'color': (0.1, 0.8, 0.4, 1)}, # Green
        {'name': 'plus2', 'type': 'operation', 'value': 'plus', 'color': (1, 1, 0, 1)},
        {'name': 'num9', 'type': 'constant', 'value': '9', 'color': (0.9, 0.5, 0.1, 1)}, # Orange
        {'name': 'equals', 'type': 'equals', 'value': '=', 'color': (1, 1, 1, 1)},
        {'name': 'num0', 'type': 'constant', 'value': '0', 'color': (0.7, 0.7, 0.7, 1)}, # Grey
        
        # Temporary/duplicable elements for operations (reused)
        {'name': 'minus_3x_temp', 'type': 'variable', 'value': '-3x', 'color': (0.1, 0.4, 0.8, 1)},
        {'name': 'minus_9_temp', 'type': 'constant', 'value': '-9', 'color': (0.9, 0.5, 0.1, 1)},
        {'name': 'minus_4y_temp', 'type': 'variable', 'value': '-4y', 'color': (0.1, 0.8, 0.4, 1)},
        
        # Division specific terms for y = mx + b
        {'name': 'y_term', 'type': 'variable', 'value': 'y', 'color': (0.1, 0.8, 0.4, 1)},
        {'name': 'minus_3_div_4', 'type': 'constant', 'value': '-3/4', 'color': (0.1, 0.4, 0.8, 1)},
        {'name': 'x_alone', 'type': 'variable', 'value': 'x', 'color': (0.1, 0.4, 0.8, 1)},
        {'name': 'minus_9_div_4', 'type': 'constant', 'value': '-9/4', 'color': (0.9, 0.5, 0.1, 1)},
        
        # Division specific terms for x = my + c
        {'name': 'x_term', 'type': 'variable', 'value': 'x', 'color': (0.1, 0.4, 0.8, 1)},
        {'name': 'minus_4_div_3', 'type': 'constant', 'value': '-4/3', 'color': (0.1, 0.8, 0.4, 1)},
        {'name': 'y_alone', 'type': 'variable', 'value': 'y', 'color': (0.1, 0.8, 0.4, 1)},
        {'name': 'minus_3_const', 'type': 'constant', 'value': '-3', 'color': (0.9, 0.5, 0.1, 1)},
        
        # For graph points
        {'name': 'zero_for_x_val', 'type': 'constant', 'value': '0', 'color': (0.7, 0.7, 0.7, 1)},
        {'name': 'zero_for_y_val', 'type': 'constant', 'value': '0', 'color': (0.7, 0.7, 0.7, 1)},
    ]
    
    # Store objects in dictionaries for easy access
    equation_objs, equation_text_objs = create_equation_elements(elements_data)
    
    # Special objects not in the generic element list (backgrounds, graph elements, etc.)
    whiteboard = create_whiteboard_grid()
    coord_plane_group, coord_plane_base, x_axis, y_axis, x_label, y_label = create_coordinate_plane()
    
    # Graph points
    point_y_intercept = create_point_sphere("Y_Intercept_Point", color=(1,0.5,0,1)) # Orange
    point_x_intercept = create_point_sphere("X_Intercept_Point", color=(0.5,0,1,1)) # Purple
    point_on_line_1 = create_point_sphere("Point_On_Line_1", color=(0,1,0.5,1)) # Cyan-Green
    point_on_line_2 = create_point_sphere("Point_On_Line_2", color=(0,1,0.5,1))
    point_on_line_3 = create_point_sphere("Point_On_Line_3", color=(0,1,0.5,1))
    solution_line_obj = create_solution_line()

    # Operations for division steps (need to create them explicitly as they are 'new' elements)
    divide_arrow_y, _ = create_operation_arrow("divide_arrow_y", "divide", size=0.8)
    divide_arrow_x, _ = create_operation_arrow("divide_arrow_x", "divide", size=0.8)
    
    # Operation symbols for final equations (minus signs)
    minus_op_y_eq, text_minus_op_y_eq = create_operation_arrow("minus_op_y_eq", "minus", size=0.5)
    minus_op_x_eq, text_minus_op_x_eq = create_operation_arrow("minus_op_x_eq", "minus", size=0.5)

    # Clone equals bar for the second final equation display
    equals_clone_2 = create_equals_bar("equals_clone_2")
    bpy.context.collection.objects.unlink(equals_clone_2)
    bpy.data.collections["EquationElements"].objects.link(equals_clone_2)
    equals_clone_2.hide_render = True
    equals_clone_2.hide_set(True)

    # --- Initial Positions (relative to center) ---
    eq_pos = {
        'num3x': (-3.0, 0, 0), 'plus1': (-1.5, 0, 0), 'num4y': (0.0, 0, 0),
        'plus2': (1.5, 0, 0), 'num9': (3.0, 0, 0), 'equals': (4.5, 0, 0),
        'num0': (6.0, 0, 0),
        
        # Initial positions for temporary elements (off-screen or as templates)
        'minus_3x_temp': (8.0, 0, 0), 
        'minus_9_temp': (8.0, 0, 0),
        'minus_4y_temp': (8.0, 0, 0),
        
        # Positions for simplified terms (relative to equation center)
        'y_term': (-2.5, 0, 0), # y = ...
        'minus_3_div_4': (0.5, 0, 0),
        'x_alone': (1.5, 0, 0),
        'minus_9_div_4': (3.5, 0, 0),
        
        'x_term': (-2.5, 0, 0), # x = ...
        'minus_4_div_3': (0.5, 0, 0),
        'y_alone': (1.5, 0, 0),
        'minus_3_const': (3.0, 0, 0),
    }

    # Set initial positions for main elements (off-screen)
    for name, obj in equation_objs.items():
        if name in eq_pos:
            obj.location = (eq_pos[name][0], eq_pos[name][1] + 5, eq_pos[name][2]) # Start slightly off-screen +Y
        else:
            obj.location = (0,0,0) # For non-initial equation elements
        
        # Hide all elements initially
        obj.hide_render = True
        obj.hide_set(True)
        if equation_text_objs[name]:
            equation_text_objs[name].hide_render = True
            equation_text_objs[name].hide_set(True)
    
    # Hide new operation arrows initially
    divide_arrow_y.hide_render = True; divide_arrow_y.hide_set(True)
    divide_arrow_x.hide_render = True; divide_arrow_x.hide_set(True)
    minus_op_y_eq.hide_render = True; minus_op_y_eq.hide_set(True)
    minus_op_x_eq.hide_render = True; minus_op_x_eq.hide_set(True)
    if text_minus_op_y_eq: text_minus_op_y_eq.hide_render = True; text_minus_op_y_eq.hide_set(True)
    if text_minus_op_x_eq: text_minus_op_x_eq.hide_render = True; text_minus_op_x_eq.hide_set(True)


    # --- Animation Timing (Frames) ---
    fps = bpy.context.scene.render.fps
    
    # Helper to convert seconds to frames
    def s_to_f(seconds):
        return int(seconds * fps)

    # Store initial camera position and rotation
    cam_start_loc = camera.location.copy()
    cam_start_rot = camera.rotation_euler.copy()

    # --- Scene 1: Introduction - The Problem (0:00 - 0:10) ---
    frame = s_to_f(0)
    duration_intro = s_to_f(10)
    slide_in_duration = s_to_f(1)
    
    whiteboard.hide_render = False
    whiteboard.hide_set(False)

    for i, name in enumerate(['num3x', 'plus1', 'num4y', 'plus2', 'num9', 'equals', 'num0']):
        obj = equation_objs[name]
        text_obj = equation_text_objs[name] # Could be None for equals bar
        start_frame_current = frame + i * s_to_f(0.5)
        
        animate_visibility(obj, start_frame_current, 1, hide_render_start=True, hide_render_end=False)
        animate_location(obj, obj.location, eq_pos[name], start_frame_current, slide_in_duration)
        animate_glow(obj, start_frame_current + slide_in_duration, s_to_f(0.5), strength=5)
        
        if text_obj: 
            animate_visibility(text_obj, start_frame_current, 1, hide_render_start=True, hide_render_end=False)
            
    frame += duration_intro

    # --- Scene 2: Understanding the Problem (0:10 - 0:25) ---
    duration_understanding = s_to_f(15)
    
    # X and Y cubes detach and float
    animate_location(equation_objs['num3x'], eq_pos['num3x'], (eq_pos['num3x'][0]-0.5, eq_pos['num3x'][1]+0.5, eq_pos['num3x'][2]+0.5), frame, s_to_f(2))
    animate_location(equation_objs['num4y'], eq_pos['num4y'], (eq_pos['num4y'][0]+0.5, eq_pos['num4y'][1]+0.5, eq_pos['num4y'][2]+0.5), frame, s_to_f(2))
    animate_rotation(equation_objs['num3x'], (0,0,0), (0, math.radians(360), math.radians(360)), frame, s_to_f(2))
    animate_rotation(equation_objs['num4y'], (0,0,0), (0, math.radians(360), math.radians(360)), frame, s_to_f(2))
    
    # Equals bar pulses (scale slightly)
    animate_scale(equation_objs['equals'], (1,1,1), (1.1,1.1,1.1), frame, s_to_f(0.5))
    animate_scale(equation_objs['equals'], (1.1,1.1,1.1), (1,1,1), frame + s_to_f(0.5), s_to_f(0.5))
    animate_scale(equation_objs['equals'], (1,1,1), (1.1,1.1,1.1), frame + s_to_f(1), s_to_f(0.5))
    animate_scale(equation_objs['equals'], (1.1,1.1,1.1), (1,1,1), frame + s_to_f(1.5), s_to_f(0.5))
    
    # Camera transition to blurred coordinate plane
    transition_start_f = frame + s_to_f(6)
    transition_duration_f = s_to_f(2)
    
    animate_visibility(whiteboard, transition_start_f, transition_duration_f, hide_render_start=False, hide_render_end=True)
    animate_visibility(coord_plane_group, transition_start_f, transition_duration_f, hide_render_start=True, hide_render_end=False)
    
    animate_camera_move(camera, cam_start_loc, (0, -2, 10), cam_start_rot, (math.radians(90), 0, 0), transition_start_f, transition_duration_f)

    # Transition back to whiteboard
    transition_back_start_f = transition_start_f + transition_duration_f + s_to_f(3) 
    
    animate_visibility(whiteboard, transition_back_start_f, transition_duration_f, hide_render_start=True, hide_render_end=False)
    animate_visibility(coord_plane_group, transition_back_start_f, transition_duration_f, hide_render_start=False, hide_render_end=True)
    
    animate_camera_move(camera, (0, -2, 10), cam_start_loc, (math.radians(90), 0, 0), cam_start_rot, transition_back_start_f, transition_duration_f)

    # Re-align elements after floating
    animate_location(equation_objs['num3x'], equation_objs['num3x'].location, eq_pos['num3x'], frame + duration_understanding - s_to_f(2), s_to_f(2))
    animate_location(equation_objs['num4y'], equation_objs['num4y'].location, eq_pos['num4y'], frame + duration_understanding - s_to_f(2), s_to_f(2))
    animate_rotation(equation_objs['num3x'], equation_objs['num3x'].rotation_euler, (0,0,0), frame + duration_understanding - s_to_f(2), s_to_f(2))
    animate_rotation(equation_objs['num4y'], equation_objs['num4y'].rotation_euler, (0,0,0), frame + duration_understanding - s_to_f(2), s_to_f(2))
    
    frame += duration_understanding

    # --- Scene 3: Method 1A - Expressing Y in terms of X (0:25 - 1:15) ---
    # Equation: 3x + 4y + 9 = 0
    
    # Step 3.1: Subtract 3x from both sides (0:25 - 0:40) (15s)
    step_duration_slow = s_to_f(15)
    
    animate_glow(equation_objs['num3x'], frame, s_to_f(1), strength=5)

    minus_3x_temp = equation_objs['minus_3x_temp']
    text_minus_3x_temp = equation_text_objs['minus_3x_temp']
    minus_3x_temp_start_loc = (eq_pos['num0'][0] + 2, eq_pos['num0'][1], eq_pos['num0'][2])
    minus_3x_temp.location = minus_3x_temp_start_loc
    animate_visibility(minus_3x_temp, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_3x_temp, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    animate_location(minus_3x_temp, minus_3x_temp_start_loc, eq_pos['num0'], frame + s_to_f(1), s_to_f(3))
    
    animate_fade_out(equation_objs['num3x'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['num3x'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_objs['plus1'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['plus1'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_objs['num0'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['num0'], frame + s_to_f(4), s_to_f(2))
    
    # After 0 is gone, -3x_temp repositions slightly if needed
    animate_location(minus_3x_temp, minus_3x_temp.location, eq_pos['num0'], frame + s_to_f(6), s_to_f(1)) # Recenter
    
    # Shift remaining elements on left (4y + 9)
    shift_duration = s_to_f(1)
    animate_location(equation_objs['num4y'], eq_pos['num4y'], (eq_pos['num4y'][0] - 1.5, eq_pos['num4y'][1], eq_pos['num4y'][2]), frame + s_to_f(6), shift_duration)
    animate_location(equation_objs['plus2'], eq_pos['plus2'], (eq_pos['plus2'][0] - 1.5, eq_pos['plus2'][1], eq_pos['plus2'][2]), frame + s_to_f(6), shift_duration)
    animate_location(equation_objs['num9'], eq_pos['num9'], (eq_pos['num9'][0] - 1.5, eq_pos['num9'][1], eq_pos['num9'][2]), frame + s_to_f(6), shift_duration)
    
    current_eq_pos = {
        'num4y': (eq_pos['num4y'][0] - 1.5, eq_pos['num4y'][1], eq_pos['num4y'][2]),
        'plus2': (eq_pos['plus2'][0] - 1.5, eq_pos['plus2'][1], eq_pos['plus2'][2]),
        'num9': (eq_pos['num9'][0] - 1.5, eq_pos['num9'][1], eq_pos['num9'][2]),
        'equals': eq_pos['equals'],
        'minus_3x_temp': eq_pos['num0'] # Current pos of -3x
    }
    
    frame += step_duration_slow

    # Step 3.2: Subtract 9 from both sides (0:40 - 0:55) (15s)
    # Equation: 4y + 9 = -3x
    
    animate_glow(equation_objs['num9'], frame, s_to_f(1), strength=5)
    
    minus_9_temp = equation_objs['minus_9_temp']
    text_minus_9_temp = equation_text_objs['minus_9_temp']
    
    minus_9_temp_start_loc = (current_eq_pos['minus_3x_temp'][0] + 2, current_eq_pos['minus_3x_temp'][1], current_eq_pos['minus_3x_temp'][2])
    minus_9_temp.location = minus_9_temp_start_loc
    animate_visibility(minus_9_temp, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_9_temp, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    animate_location(minus_9_temp, minus_9_temp_start_loc, (current_eq_pos['minus_3x_temp'][0] + 1.5, current_eq_pos['minus_3x_temp'][1], current_eq_pos['minus_3x_temp'][2]), frame + s_to_f(1), s_to_f(3))
    
    animate_fade_out(equation_objs['num9'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['num9'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_objs['plus2'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['plus2'], frame + s_to_f(4), s_to_f(2))

    # Shift 4y left
    animate_location(equation_objs['num4y'], equation_objs['num4y'].location, (equation_objs['num4y'].location[0] - 1.5, equation_objs['num4y'].location[1], equation_objs['num4y'].location[2]), frame + s_to_f(6), s_to_f(1))
    
    current_eq_pos['num4y'] = (equation_objs['num4y'].location[0] - 1.5, equation_objs['num4y'].location[1], equation_objs['num4y'].location[2]) # Update pos
    current_eq_pos['minus_9_temp'] = (current_eq_pos['minus_3x_temp'][0] + 1.5, current_eq_pos['minus_3x_temp'][1], current_eq_pos['minus_3x_temp'][2]) # Update pos
    
    frame += step_duration_slow
    
    # Step 3.3: Divide by 4 (0:55 - 1:15) (20s)
    # Equation: 4y = -3x - 9
    
    animate_glow(equation_objs['num4y'], frame, s_to_f(1), strength=5)
    
    # Animate division arrow
    divide_arrow_y.location = (equation_objs['equals'].location[0] - 2.5, equation_objs['equals'].location[1], equation_objs['equals'].location[2] + 2)
    animate_visibility(divide_arrow_y, frame + s_to_f(0.5), 1, hide_render_start=True, hide_render_end=False)
    
    # Create fraction lines and denominators
    line_length = 1.5 # Extend slightly for -3x - 9
    divide4_line_l = create_fraction_line("divide4_line_l", length=1.0) 
    divide4_line_r1 = create_fraction_line("divide4_line_r1", length=1.0) 
    divide4_line_r2 = create_fraction_line("divide4_line_r2", length=1.0) 

    num4_denom_l, text_num4_denom_l = create_constant_block("num4_denom_l", "4", (0.7,0.7,0.7,1))
    num4_denom_r1, text_num4_denom_r1 = create_constant_block("num4_denom_r1", "4", (0.7,0.7,0.7,1))
    num4_denom_r2, text_num4_denom_r2 = create_constant_block("num4_denom_r2", "4", (0.7,0.7,0.7,1))
    
    divide4_line_l.location = (current_eq_pos['num4y'][0], current_eq_pos['num4y'][1], current_eq_pos['num4y'][2] - 0.7)
    num4_denom_l.location = (current_eq_pos['num4y'][0], current_eq_pos['num4y'][1], current_eq_pos['num4y'][2] - 1.2)

    divide4_line_r1.location = (current_eq_pos['minus_3x_temp'][0], current_eq_pos['minus_3x_temp'][1], current_eq_pos['minus_3x_temp'][2] - 0.7)
    num4_denom_r1.location = (current_eq_pos['minus_3x_temp'][0], current_eq_pos['minus_3x_temp'][1], current_eq_pos['minus_3x_temp'][2] - 1.2)

    divide4_line_r2.location = (current_eq_pos['minus_9_temp'][0], current_eq_pos['minus_9_temp'][1], current_eq_pos['minus_9_temp'][2] - 0.7)
    num4_denom_r2.location = (current_eq_pos['minus_9_temp'][0], current_eq_pos['minus_9_temp'][1], current_eq_pos['minus_9_temp'][2] - 1.2)
    
    for obj in [divide4_line_l, divide4_line_r1, divide4_line_r2, num4_denom_l, num4_denom_r1, num4_denom_r2, text_num4_denom_l, text_num4_denom_r1, text_num4_denom_r2]:
        animate_visibility(obj, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    
    # Animate 4y/4 to y
    fade_duration_div = s_to_f(1.5)
    animate_fade_out(equation_objs['num4y'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(equation_text_objs['num4y'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(num4_denom_l, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(text_num4_denom_l, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(divide4_line_l, frame + s_to_f(3), fade_duration_div)

    y_term = equation_objs['y_term']
    text_y_term = equation_text_objs['y_term']
    y_term.location = (current_eq_pos['num4y'][0], current_eq_pos['num4y'][1], current_eq_pos['num4y'][2])
    animate_visibility(y_term, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_y_term, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    
    # Animate -3x/4 to -3/4 x
    animate_fade_out(equation_objs['minus_3x_temp'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(equation_text_objs['minus_3x_temp'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(num4_denom_r1, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(text_num4_denom_r1, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(divide4_line_r1, frame + s_to_f(3), fade_duration_div)

    minus_3_div_4 = equation_objs['minus_3_div_4']
    text_minus_3_div_4 = equation_text_objs['minus_3_div_4']
    x_alone = equation_objs['x_alone']
    text_x_alone = equation_text_objs['x_alone']
    
    minus_3_div_4.location = (current_eq_pos['minus_3x_temp'][0] - 0.5, current_eq_pos['minus_3x_temp'][1], current_eq_pos['minus_3x_temp'][2])
    x_alone.location = (current_eq_pos['minus_3x_temp'][0] + 0.5, current_eq_pos['minus_3x_temp'][1], current_eq_pos['minus_3x_temp'][2])
    
    animate_visibility(minus_3_div_4, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_3_div_4, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(x_alone, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_x_alone, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)

    # Animate -9/4 to -9/4
    animate_fade_out(equation_objs['minus_9_temp'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(equation_text_objs['minus_9_temp'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(num4_denom_r2, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(text_num4_denom_r2, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(divide4_line_r2, frame + s_to_f(3), fade_duration_div)

    minus_9_div_4 = equation_objs['minus_9_div_4']
    text_minus_9_div_4 = equation_text_objs['minus_9_div_4']
    
    minus_9_div_4.location = (current_eq_pos['minus_9_temp'][0], current_eq_pos['minus_9_temp'][1], current_eq_pos['minus_9_temp'][2])
    animate_visibility(minus_9_div_4, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_9_div_4, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)

    # Fade out division arrow
    animate_fade_out(divide_arrow_y, frame + s_to_f(4.5), 1)

    # Re-align final equation y = -3/4 x - 9/4
    final_y_eq_start_frame = frame + s_to_f(6)
    animate_location(y_term, y_term.location, eq_pos['y_term'], final_y_eq_start_frame, s_to_f(1))
    animate_location(equation_objs['equals'], equation_objs['equals'].location, (-1.0,0,0), final_y_eq_start_frame, s_to_f(1))
    animate_location(minus_3_div_4, minus_3_div_4.location, eq_pos['minus_3_div_4'], final_y_eq_start_frame, s_to_f(1))
    animate_location(x_alone, x_alone.location, eq_pos['x_alone'], final_y_eq_start_frame, s_to_f(1))
    animate_location(minus_9_div_4, minus_9_div_4.location, eq_pos['minus_9_div_4'], final_y_eq_start_frame, s_to_f(1)) 
    
    # Introduce "minus" operation for the -9/4 term
    minus_op_y_eq.location = (eq_pos['minus_9_div_4'][0] - 1.0, eq_pos['minus_9_div_4'][1], eq_pos['minus_9_div_4'][2])
    animate_visibility(minus_op_y_eq, final_y_eq_start_frame, 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_op_y_eq, final_y_eq_start_frame, 1, hide_render_start=True, hide_render_end=False)
    
    animate_glow(y_term, final_y_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(equation_objs['equals'], final_y_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(minus_3_div_4, final_y_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(x_alone, final_y_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(minus_9_div_4, final_y_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(minus_op_y_eq, final_y_eq_start_frame, s_to_f(3), strength=5)
    
    frame += step_duration_slow + s_to_f(5) 

    # --- Scene 4: Method 1B - Expressing X in terms of Y (1:15 - 1:45) ---
    # Reset equation to original for next method.
    reset_duration = s_to_f(1)
    
    # Hide all previous intermediate objects and solution
    elements_to_hide_prev_method = [
        y_term, text_y_term, minus_op_y_eq, text_minus_op_y_eq,
        minus_3_div_4, text_minus_3_div_4, x_alone, text_x_alone,
        minus_9_div_4, text_minus_9_div_4
    ]
    for obj in elements_to_hide_prev_method:
        if obj and not obj.hide_render: 
            animate_visibility(obj, frame, reset_duration, hide_render_start=False, hide_render_end=True)
    
    # Show original equation, ensure they are at original locations
    for name in ['num3x', 'plus1', 'num4y', 'plus2', 'num9', 'equals', 'num0']:
        obj = equation_objs[name]
        text_obj = equation_text_objs[name]
        obj.location = eq_pos[name]
        animate_visibility(obj, frame, reset_duration, hide_render_start=True, hide_render_end=False)
        if text_obj: animate_visibility(text_obj, frame, reset_duration, hide_render_start=True, hide_render_end=False)
    
    # Hide temp elements if they were lingering from prev steps
    for name in ['minus_3x_temp', 'minus_9_temp', 'minus_4y_temp']:
        if equation_objs[name]: equation_objs[name].hide_render = True; equation_objs[name].hide_set(True)
        if equation_text_objs[name]: equation_text_objs[name].hide_render = True; equation_text_objs[name].hide_set(True)
    
    frame += reset_duration
    
    # Step 4.1: Subtract 4y from both sides (1:20 - 1:30) (10s)
    step_duration_fast = s_to_f(10)
    
    animate_glow(equation_objs['num4y'], frame, s_to_f(1), strength=5)
    
    minus_4y_temp = equation_objs['minus_4y_temp']
    text_minus_4y_temp = equation_text_objs['minus_4y_temp']
    minus_4y_temp_start_loc = (eq_pos['num0'][0] + 2, eq_pos['num0'][1], eq_pos['num0'][2])
    minus_4y_temp.location = minus_4y_temp_start_loc
    animate_visibility(minus_4y_temp, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_4y_temp, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    animate_location(minus_4y_temp, minus_4y_temp_start_loc, eq_pos['num0'], frame + s_to_f(1), s_to_f(3))
    
    animate_fade_out(equation_objs['num4y'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['num4y'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_objs['plus2'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['plus2'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_objs['num0'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['num0'], frame + s_to_f(4), s_to_f(2))

    animate_location(minus_4y_temp, minus_4y_temp.location, eq_pos['num0'], frame + s_to_f(6), s_to_f(1)) # Recenter
    
    # Shift remaining elements on left
    animate_location(equation_objs['plus1'], eq_pos['plus1'], (eq_pos['plus1'][0]+1.5, eq_pos['plus1'][1], eq_pos['plus1'][2]), frame + s_to_f(6), s_to_f(1))
    animate_location(equation_objs['num9'], eq_pos['num9'], (eq_pos['num9'][0]-1.5, eq_pos['num9'][1], eq_pos['num9'][2]), frame + s_to_f(6), s_to_f(1))
    
    current_eq_pos['num3x'] = eq_pos['num3x']
    current_eq_pos['plus1'] = (eq_pos['plus1'][0]+1.5, eq_pos['plus1'][1], eq_pos['plus1'][2])
    current_eq_pos['num9'] = (eq_pos['num9'][0]-1.5, eq_pos['num9'][1], eq_pos['num9'][2])
    current_eq_pos['minus_4y_temp'] = eq_pos['num0'] # Current pos of -4y

    frame += step_duration_fast
    
    # Step 4.2: Subtract 9 from both sides (1:30 - 1:40) (10s)
    # Equation: 3x + 9 = -4y
    animate_glow(equation_objs['num9'], frame, s_to_f(1), strength=5)
    
    minus_9_temp = equation_objs['minus_9_temp']
    text_minus_9_temp = equation_text_objs['minus_9_temp']
    minus_9_temp_start_loc = (current_eq_pos['minus_4y_temp'][0] + 2, current_eq_pos['minus_4y_temp'][1], current_eq_pos['minus_4y_temp'][2])
    minus_9_temp.location = minus_9_temp_start_loc
    animate_visibility(minus_9_temp, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_9_temp, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    animate_location(minus_9_temp, minus_9_temp_start_loc, (current_eq_pos['minus_4y_temp'][0] + 1.5, current_eq_pos['minus_4y_temp'][1], current_eq_pos['minus_4y_temp'][2]), frame + s_to_f(1), s_to_f(3))
    
    animate_fade_out(equation_objs['num9'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['num9'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_objs['plus1'], frame + s_to_f(4), s_to_f(2))
    animate_fade_out(equation_text_objs['plus1'], frame + s_to_f(4), s_to_f(2))
    
    animate_location(equation_objs['num3x'], equation_objs['num3x'].location, (equation_objs['num3x'].location[0] + 1.5, equation_objs['num3x'].location[1], equation_objs['num3x'].location[2]), frame + s_to_f(6), s_to_f(1))
    
    current_eq_pos['num3x'] = (equation_objs['num3x'].location[0] + 1.5, equation_objs['num3x'].location[1], equation_objs['num3x'].location[2]) # Update pos
    current_eq_pos['minus_9_temp'] = (current_eq_pos['minus_4y_temp'][0] + 1.5, current_eq_pos['minus_4y_temp'][1], current_eq_pos['minus_4y_temp'][2]) # Update pos

    frame += step_duration_fast
    
    # Step 4.3: Divide by 3 (1:40 - 1:55) (15s)
    # Equation: 3x = -4y - 9
    
    animate_glow(equation_objs['num3x'], frame, s_to_f(1), strength=5)
    
    divide_arrow_x.location = (equation_objs['equals'].location[0] - 2.5, equation_objs['equals'].location[1], equation_objs['equals'].location[2] + 2)
    animate_visibility(divide_arrow_x, frame + s_to_f(0.5), 1, hide_render_start=True, hide_render_end=False)
    
    divide3_line_l = create_fraction_line("divide3_line_l", length=1.0) 
    divide3_line_r1 = create_fraction_line("divide3_line_r1", length=1.0) 
    divide3_line_r2 = create_fraction_line("divide3_line_r2", length=1.0) 

    num3_denom_l, text_num3_denom_l = create_constant_block("num3_denom_l", "3", (0.7,0.7,0.7,1))
    num3_denom_r1, text_num3_denom_r1 = create_constant_block("num3_denom_r1", "3", (0.7,0.7,0.7,1))
    num3_denom_r2, text_num3_denom_r2 = create_constant_block("num3_denom_r2", "3", (0.7,0.7,0.7,1))
    
    divide3_line_l.location = (current_eq_pos['num3x'][0], current_eq_pos['num3x'][1], current_eq_pos['num3x'][2] - 0.7)
    num3_denom_l.location = (current_eq_pos['num3x'][0], current_eq_pos['num3x'][1], current_eq_pos['num3x'][2] - 1.2)

    divide3_line_r1.location = (current_eq_pos['minus_4y_temp'][0], current_eq_pos['minus_4y_temp'][1], current_eq_pos['minus_4y_temp'][2] - 0.7)
    num3_denom_r1.location = (current_eq_pos['minus_4y_temp'][0], current_eq_pos['minus_4y_temp'][1], current_eq_pos['minus_4y_temp'][2] - 1.2)

    divide3_line_r2.location = (current_eq_pos['minus_9_temp'][0], current_eq_pos['minus_9_temp'][1], current_eq_pos['minus_9_temp'][2] - 0.7)
    num3_denom_r2.location = (current_eq_pos['minus_9_temp'][0], current_eq_pos['minus_9_temp'][1], current_eq_pos['minus_9_temp'][2] - 1.2)
    
    for obj in [divide3_line_l, divide3_line_r1, divide3_line_r2, num3_denom_l, num3_denom_r1, num3_denom_r2, text_num3_denom_l, text_num3_denom_r1, text_num3_denom_r2]:
        animate_visibility(obj, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    
    # Animate 3x/3 to x
    animate_fade_out(equation_objs['num3x'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(equation_text_objs['num3x'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(num3_denom_l, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(text_num3_denom_l, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(divide3_line_l, frame + s_to_f(3), fade_duration_div)
    
    x_term = equation_objs['x_term']
    text_x_term = equation_text_objs['x_term']
    x_term.location = (current_eq_pos['num3x'][0], current_eq_pos['num3x'][1], current_eq_pos['num3x'][2])
    animate_visibility(x_term, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_x_term, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    
    # Animate -4y/3 to -4/3 y
    animate_fade_out(equation_objs['minus_4y_temp'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(equation_text_objs['minus_4y_temp'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(num3_denom_r1, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(text_num3_denom_r1, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(divide3_line_r1, frame + s_to_f(3), fade_duration_div)

    minus_4_div_3 = equation_objs['minus_4_div_3']
    text_minus_4_div_3 = equation_text_objs['minus_4_div_3']
    y_alone = equation_objs['y_alone']
    text_y_alone = equation_text_objs['y_alone']
    
    minus_4_div_3.location = (current_eq_pos['minus_4y_temp'][0] - 0.5, current_eq_pos['minus_4y_temp'][1], current_eq_pos['minus_4y_temp'][2])
    y_alone.location = (current_eq_pos['minus_4y_temp'][0] + 0.5, current_eq_pos['minus_4y_temp'][1], current_eq_pos['minus_4y_temp'][2])
    
    animate_visibility(minus_4_div_3, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_4_div_3, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(y_alone, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_y_alone, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    
    # Animate -9/3 to -3
    animate_fade_out(equation_objs['minus_9_temp'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(equation_text_objs['minus_9_temp'], frame + s_to_f(3), fade_duration_div)
    animate_fade_out(num3_denom_r2, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(text_num3_denom_r2, frame + s_to_f(3), fade_duration_div)
    animate_fade_out(divide3_line_r2, frame + s_to_f(3), fade_duration_div)
    
    minus_3_const = equation_objs['minus_3_const']
    text_minus_3_const = equation_text_objs['minus_3_const']
    minus_3_const.location = (current_eq_pos['minus_9_temp'][0], current_eq_pos['minus_9_temp'][1], current_eq_pos['minus_9_temp'][2])
    animate_visibility(minus_3_const, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_3_const, frame + s_to_f(4.5), 1, hide_render_start=True, hide_render_end=False)

    # Fade out division arrow
    animate_fade_out(divide_arrow_x, frame + s_to_f(4.5), 1)

    # Re-align final equation x = -4/3 y - 3
    final_x_eq_start_frame = frame + s_to_f(6)
    animate_location(x_term, x_term.location, eq_pos['x_term'], final_x_eq_start_frame, s_to_f(1))
    animate_location(equation_objs['equals'], equation_objs['equals'].location, (-1.0,0,0), final_x_eq_start_frame, s_to_f(1)) # Reuse equals bar
    animate_location(minus_4_div_3, minus_4_div_3.location, eq_pos['minus_4_div_3'], final_x_eq_start_frame, s_to_f(1))
    animate_location(y_alone, y_alone.location, eq_pos['y_alone'], final_x_eq_start_frame, s_to_f(1))
    animate_location(minus_3_const, minus_3_const.location, eq_pos['minus_3_const'], final_x_eq_start_frame, s_to_f(1))
    
    minus_op_x_eq.location = (eq_pos['minus_3_const'][0] - 1.0, eq_pos['minus_3_const'][1], eq_pos['minus_3_const'][2])
    animate_visibility(minus_op_x_eq, final_x_eq_start_frame, 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_op_x_eq, final_x_eq_start_frame, 1, hide_render_start=True, hide_render_end=False)
    
    animate_glow(x_term, final_x_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(equation_objs['equals'], final_x_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(minus_4_div_3, final_x_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(y_alone, final_x_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(minus_3_const, final_x_eq_start_frame, s_to_f(3), strength=5)
    animate_glow(minus_op_x_eq, final_x_eq_start_frame, s_to_f(3), strength=5)
    
    frame += step_duration_fast + s_to_f(5)

    # --- Scene 5: Graphical Representation & Conclusion (1:55 - 2:30) ---
    # Hide all equation elements
    all_eq_elements_for_graph_hide = [
        obj for name, obj in equation_objs.items() if name not in ['y_term', 'equals', 'minus_3_div_4', 'x_alone', 'minus_9_div_4', 'x_term', 'minus_4_div_3', 'y_alone', 'minus_3_const']
    ] + [
        obj for name, obj in equation_text_objs.items() if obj is not None and name not in ['y_term', 'equals', 'minus_3_div_4', 'x_alone', 'minus_9_div_4', 'x_term', 'minus_4_div_3', 'y_alone', 'minus_3_const']
    ] + [
        minus_op_y_eq, text_minus_op_y_eq, minus_op_x_eq, text_minus_op_x_eq,
        divide_arrow_y, divide_arrow_x,
        divide4_line_l, divide4_line_r1, divide4_line_r2, 
        num4_denom_l, text_num4_denom_l, num4_denom_r1, text_num4_denom_r1, num4_denom_r2, text_num4_denom_r2,
        divide3_line_l, divide3_line_r1, divide3_line_r2, 
        num3_denom_l, text_num3_denom_l, num3_denom_r1, text_num3_denom_r1, num3_denom_r2, text_num3_denom_r2
    ]
                      
    for obj in all_eq_elements_for_graph_hide:
        if obj and not obj.hide_render: 
            animate_visibility(obj, frame, s_to_f(1), hide_render_start=False, hide_render_end=True)

    # Transition from Whiteboard to CoordinatePlane
    transition_duration_graph = s_to_f(2)
    animate_visibility(whiteboard, frame, transition_duration_graph, hide_render_start=False, hide_render_end=True)
    animate_visibility(coord_plane_group, frame, transition_duration_graph, hide_render_start=True, hide_render_end=False)
    
    # Move camera to top-down view for graph
    cam_graph_loc = (0, -2, 10)
    cam_graph_rot = (math.radians(90), 0, 0)
    animate_camera_move(camera, camera.location.copy(), cam_graph_loc, camera.rotation_euler.copy(), cam_graph_rot, frame, transition_duration_graph)
    
    frame += transition_duration_graph + s_to_f(1) 

    # Float final equation (y = -3/4 x - 9/4) above graph
    final_eq_y_pos = (-2, 0, 5) # Y-equation (top)
    
    animate_location(y_term, y_term.location, (final_eq_y_pos[0]-2, final_eq_y_pos[1], final_eq_y_pos[2]), frame, s_to_f(1))
    animate_visibility(y_term, frame, 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_y_term, frame, 1, hide_render_start=True, hide_render_end=False)
    
    animate_location(equation_objs['equals'], equation_objs['equals'].location, (final_eq_y_pos[0]-1, final_eq_y_pos[1], final_eq_y_pos[2]), frame, s_to_f(1))
    animate_visibility(equation_objs['equals'], frame, 1, hide_render_start=True, hide_render_end=False)
    
    animate_location(minus_3_div_4, minus_3_div_4.location, (final_eq_y_pos[0], final_eq_y_pos[1], final_eq_y_pos[2]), frame, s_to_f(1))
    animate_visibility(minus_3_div_4, frame, 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_3_div_4, frame, 1, hide_render_start=True, hide_render_end=False)
    
    animate_location(x_alone, x_alone.location, (final_eq_y_pos[0]+1, final_eq_y_pos[1], final_eq_y_pos[2]), frame, s_to_f(1))
    animate_visibility(x_alone, frame, 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_x_alone, frame, 1, hide_render_start=True, hide_render_end=False)
    
    animate_location(minus_op_y_eq, minus_op_y_eq.location, (final_eq_y_pos[0]+2, final_eq_y_pos[1], final_eq_y_pos[2]), frame, s_to_f(1))
    animate_visibility(minus_op_y_eq, frame, 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_op_y_eq, frame, 1, hide_render_start=True, hide_render_end=False)

    animate_location(minus_9_div_4, minus_9_div_4.location, (final_eq_y_pos[0]+3, final_eq_y_pos[1], final_eq_y_pos[2]), frame, s_to_f(1))
    animate_visibility(minus_9_div_4, frame, 1, hide_render_start=True, hide_render_end=False)
    animate_visibility(text_minus_9_div_4, frame, 1, hide_render_start=True, hide_render_end=False)
    
    frame += s_to_f(2) 

    # Y-intercept: (0, -9/4) = (0, -2.25)
    point_y_intercept_loc = (0, -2.25, 0.05)
    animate_location(point_y_intercept, (0,0,5), point_y_intercept_loc, frame, s_to_f(1))
    animate_visibility(point_y_intercept, frame, 1, hide_render_start=True, hide_render_end=False)
    animate_glow(point_y_intercept, frame, s_to_f(2), strength=10)
    
    y_intercept_label = create_text_mesh("Y_Intercept_Label", "(0, -2.25)", font_size=0.4, extrusion=0.03)
    y_intercept_label.location = (point_y_intercept_loc[0] + 0.5, point_y_intercept_loc[1], point_y_intercept_loc[2] + 0.5)
    y_intercept_label.rotation_euler = (math.radians(90), 0, 0)
    y_intercept_label.data.materials.append(get_material("YInterceptLabelMat", color=(1,0.5,0,1), emission_color=(1,0.5,0,1), emission_strength=5))
    animate_visibility(y_intercept_label, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    
    frame += s_to_f(3)

    # X-intercept: (-3, 0)
    point_x_intercept_loc = (-3, 0, 0.05)
    animate_location(point_x_intercept, (0,0,5), point_x_intercept_loc, frame, s_to_f(1))
    animate_visibility(point_x_intercept, frame, 1, hide_render_start=True, hide_render_end=False)
    animate_glow(point_x_intercept, frame, s_to_f(2), strength=10)

    x_intercept_label = create_text_mesh("X_Intercept_Label", "(-3, 0)", font_size=0.4, extrusion=0.03)
    x_intercept_label.location = (point_x_intercept_loc[0] + 0.5, point_x_intercept_loc[1], point_x_intercept_loc[2] + 0.5)
    x_intercept_label.rotation_euler = (math.radians(90), 0, 0)
    x_intercept_label.data.materials.append(get_material("XInterceptLabelMat", color=(0.5,0,1,1), emission_color=(0.5,0,1,1), emission_strength=5))
    animate_visibility(x_intercept_label, frame + s_to_f(1), 1, hide_render_start=True, hide_render_end=False)
    
    frame += s_to_f(3)

    # Solution Line draws itself
    line_points = [
        (-6.0, 2.25), 
        (-3.0, 0.0), 
        (0.0, -2.25), 
        (4.0, -5.25)  
    ]
    
    polyline = solution_line_obj.data.splines.new('POLY')
    polyline.points.add(len(line_points) - 1)
    for i, (x, y) in enumerate(line_points):
        polyline.points[i].co = (x, y, 0.05, 1) # z slightly above plane
    
    animate_line_draw(solution_line_obj, frame, s_to_f(3))
    frame += s_to_f(4)

    # Three PointSpheres land on the line
    dynamic_points = [
        point_on_line_1, point_on_line_2, point_on_line_3
    ]
    dynamic_point_locs = [
        (-4.0, 0.75, 0.05), # y = -3/4(-4) - 9/4 = 3 - 2.25 = 0.75
        (2.0, -3.75, 0.05), # y = -3/4(2) - 9/4 = -1.5 - 2.25 = -3.75
        (5.0, -6.75, 0.05) # y = -3/4(5) - 9/4 = -3.75 - 2.25 = -6 (Oops, recalculate: -15/4 - 9/4 = -24/4 = -6) Let's use (5, -6)
    ]
    dynamic_point_locs[2] = (5.0, -6.0, 0.05)
    
    for i, pt_obj in enumerate(dynamic_points):
        start_loc = (dynamic_point_locs[i][0], dynamic_point_locs[i][1], dynamic_point_locs[i][2] + 3)
        end_loc = dynamic_point_locs[i]
        
        animate_visibility(pt_obj, frame + i * s_to_f(0.5), 1, hide_render_start=True, hide_render_end=False)
        animate_location(pt_obj, start_loc, end_loc, frame + i * s_to_f(0.5), s_to_f(1))
        animate_glow(pt_obj, frame + i * s_to_f(0.5), s_to_f(1.5), strength=10, pulse_duration_frames=5)
    
    frame += s_to_f(4)

    # Both final equations appear side-by-side, glowing brightly.
    final_eq_display_frame = frame
    
    # Reposition y = -3/4 x - 9/4
    y_eq_display_x_offset = -3.0
    animate_location(y_term, y_term.location, (y_eq_display_x_offset - 2.0, 0, 5), final_eq_display_frame, s_to_f(1))
    animate_location(equation_objs['equals'], equation_objs['equals'].location, (y_eq_display_x_offset - 1.0, 0, 5), final_eq_display_frame, s_to_f(1))
    animate_location(minus_3_div_4, minus_3_div_4.location, (y_eq_display_x_offset + 0.0, 0, 5), final_eq_display_frame, s_to_f(1))
    animate_location(x_alone, x_alone.location, (y_eq_display_x_offset + 1.0, 0, 5), final_eq_display_frame, s_to_f(1))
    animate_location(minus_op_y_eq, minus_op_y_eq.location, (y_eq_display_x_offset + 2.0, 0, 5), final_eq_display_frame, s_to_f(1))
    animate_location(minus_9_div_4, minus_9_div_4.location, (y_eq_display_x_offset + 3.0, 0, 5), final_eq_display_frame, s_to_f(1))
    
    # Reposition x = -4/3 y - 3
    x_eq_display_x_offset = 3.0
    animate_location(x_term, x_term.location, (x_eq_display_x_offset - 2.0, 0, 5), final_eq_display_frame, s_to_f(1))
    
    equals_clone_2.location = (x_eq_display_x_offset - 1.0, 0, 5) # Set explicit location
    animate_visibility(equals_clone_2, final_eq_display_frame, 1, hide_render_start=True, hide_render_end=False)
    
    animate_location(minus_4_div_3, minus_4_div_3.location, (x_eq_display_x_offset + 0.0, 0, 5), final_eq_display_frame, s_to_f(1))
    animate_location(y_alone, y_alone.location, (x_eq_display_x_offset + 1.0, 0, 5), final_eq_display_frame, s_to_f(1))
    animate_location(minus_op_x_eq, minus_op_x_eq.location, (x_eq_display_x_offset + 2.0, 0, 5), final_eq_display_frame, s_to_f(1))
    animate_location(minus_3_const, minus_3_const.location, (x_eq_display_x_offset + 3.0, 0, 5), final_eq_display_frame, s_to_f(1))
    
    # Make sure all are visible (already animated from hidden in previous steps, but re-show)
    for obj in [y_term, text_y_term, equation_objs['equals'], minus_3_div_4, text_minus_3_div_4, x_alone, text_x_alone, minus_op_y_eq, text_minus_op_y_eq, minus_9_div_4, text_minus_9_div_4,
                x_term, text_x_term, equals_clone_2, minus_4_div_3, text_minus_4_div_3, y_alone, text_y_alone, minus_op_x_eq, text_minus_op_x_eq, minus_3_const, text_minus_3_const]:
        if obj: animate_visibility(obj, final_eq_display_frame, 1, hide_render_start=True, hide_render_end=False)

    # Glow final equations
    glow_duration_final = s_to_f(5)
    animate_glow(y_term, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(equation_objs['equals'], final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(minus_3_div_4, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(x_alone, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(minus_op_y_eq, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(minus_9_div_4, final_eq_display_frame, glow_duration_final, strength=10)
    
    animate_glow(x_term, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(equals_clone_2, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(minus_4_div_3, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(y_alone, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(minus_op_x_eq, final_eq_display_frame, glow_duration_final, strength=10)
    animate_glow(minus_3_const, final_eq_display_frame, glow_duration_final, strength=10)

    frame += glow_duration_final

    # --- Scene 6: Outro (2:30 - 2:35) ---
    transition_outro_duration = s_to_f(2)
    
    # Hide graph elements
    for obj in [coord_plane_group, point_y_intercept, point_x_intercept, y_intercept_label, x_intercept_label, solution_line_obj, point_on_line_1, point_on_line_2, point_on_line_3]:
        if obj and not obj.hide_render: 
            animate_visibility(obj, frame, transition_outro_duration, hide_render_start=False, hide_render_end=True)

    # Show whiteboard
    animate_visibility(whiteboard, frame, transition_outro_duration, hide_render_start=True, hide_render_end=False)
    
    # Move camera back to initial pose
    animate_camera_move(camera, camera.location.copy(), cam_start_loc, camera.rotation_euler.copy(), cam_start_rot, frame, transition_outro_duration)
    
    frame += transition_outro_duration + s_to_f(3) # Hold final screen for 3 seconds

    # Set final frame
    bpy.context.scene.frame_end = frame
    
    # Set current frame to start for preview
    bpy.context.scene.frame_set(0)

# Run the animation script
if __name__ == "__main__":
    animate_solution_plan()
