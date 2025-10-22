```python
import bpy
import bmesh
import math
from mathutils import Vector, Euler, Color

# --- 0. Scene Setup and Clear Previous Data ---
def clean_scene():
    """Cleans up the scene by deleting all objects, materials, collections."""
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Delete all objects
    bpy.ops.object.select_all(action='SELECT')
    if bpy.context.selected_objects:
        bpy.ops.object.delete()

    # Delete all materials
    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material)

    # Delete all collections except the default "Scene Collection"
    for collection in list(bpy.data.collections):
        if collection.name != "Scene Collection":
            bpy.data.collections.remove(collection)

    # Recreate default collection if somehow deleted or ensure it's there
    if "Scene Collection" not in bpy.data.collections:
        bpy.context.scene.collection.children.link(bpy.data.collections.new("Scene Collection"))

clean_scene()

# --- 1. Global Animation Settings ---
FPS = 30
bpy.context.scene.render.fps = FPS
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.film_transparent = True # For whiteboard background to be alpha
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = 4 * 60 * FPS # Initial estimate for 4 minutes

# Set up EEVEE for glow effects
bpy.context.scene.eevee.use_bloom = True
bpy.context.scene.eevee.bloom_threshold = 0.5
bpy.context.scene.eevee.bloom_intensity = 0.05
bpy.context.scene.eevee.bloom_radius = 6.0
bpy.context.scene.eevee.bloom_clamp = 0.0
bpy.context.scene.eevee.bloom_color = (0.5, 0.7, 1.0) # Slight blue tint to bloom

# --- 2. Materials Definition ---
materials = {}

def create_material(name, base_color=(1,1,1,1), emission_color=(0,0,0,1), emission_strength=0.0, alpha=1.0, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    
    # Set transparency
    mat.blend_method = 'BLEND'
    bsdf.inputs["Alpha"].default_value = alpha

    if emission_strength > 0:
        emission = mat.node_tree.nodes.new(type='ShaderNodeEmission')
        emission.inputs["Color"].default_value = emission_color
        emission.inputs["Strength"].default_value = emission_strength
        
        mat_output = mat.node_tree.nodes["Material Output"]
        
        # Connect Principled BSDF through Add Shader if needed for base color + emission
        add_shader = mat.node_tree.nodes.new(type='ShaderNodeAddShader')
        mat.node_tree.links.new(bsdf.outputs["BSDF"], add_shader.inputs[0])
        mat.node_tree.links.new(emission.outputs["Emission"], add_shader.inputs[1])
        mat.node_tree.links.new(add_shader.outputs[0], mat_output.inputs["Surface"])
    
    materials[name] = mat
    return mat

# Base colors
COLOR_WHITE = (1, 1, 1, 1)
COLOR_BLACK = (0, 0, 0, 1)
COLOR_BLUE = (0.1, 0.4, 0.8, 1)
COLOR_RED = (0.8, 0.2, 0.1, 1)
COLOR_GREEN = (0.2, 0.7, 0.3, 1)
COLOR_ORANGE = (0.9, 0.5, 0.1, 1)
COLOR_CYAN = (0.1, 0.8, 0.9, 1)
COLOR_YELLOW = (0.9, 0.9, 0.1, 1)
COLOR_LIGHT_GRAY = (0.7, 0.7, 0.7, 1)
COLOR_DARK_GRAY = (0.2, 0.2, 0.2, 1)

# Materials
create_material("MatWhiteboard", base_color=(0.95, 0.95, 0.95, 1), roughness=0.7)
create_material("MatProblemTitle", base_color=COLOR_BLUE, emission_color=COLOR_BLUE, emission_strength=0.1)
create_material("MatFunctionBox", base_color=COLOR_BLUE, metallic=0.2, roughness=0.3)
create_material("MatXVariable", base_color=COLOR_RED, metallic=0.1, roughness=0.4)
create_material("MatXSquared", base_color=(0.6, 0.1, 0.1, 1), metallic=0.1, roughness=0.4) # Darker Red
create_material("MatConstantDefault", base_color=COLOR_LIGHT_GRAY, roughness=0.5)
create_material("MatConstantBlue", base_color=COLOR_BLUE, roughness=0.5)
create_material("MatConstantRed", base_color=COLOR_RED, roughness=0.5)
create_material("MatConstantGreen", base_color=COLOR_GREEN, roughness=0.5)
create_material("MatConstantOrange", base_color=COLOR_ORANGE, roughness=0.5)
create_material("MatOperationSymbol", base_color=COLOR_WHITE, emission_color=COLOR_WHITE, emission_strength=2.0)
create_material("MatEqualsBar", base_color=COLOR_CYAN, emission_color=COLOR_CYAN, emission_strength=5.0)
create_material("MatQuestionMark", base_color=COLOR_YELLOW, emission_color=COLOR_YELLOW, emission_strength=1.0)
create_material("MatThoughtBubble", base_color=(0.9, 0.9, 1.0, 0.6), alpha=0.6) # Translucent
create_material("MatGraphPlane", base_color=(0.1, 0.1, 0.15, 1), metallic=0.1, roughness=0.2)
create_material("MatGraphAxis", base_color=COLOR_LIGHT_GRAY, emission_color=COLOR_LIGHT_GRAY, emission_strength=1.0)
create_material("MatParabolaArc", base_color=COLOR_CYAN, emission_color=COLOR_CYAN, emission_strength=5.0)
create_material("MatPointMarker", base_color=COLOR_GREEN, emission_color=COLOR_GREEN, emission_strength=10.0)
create_material("MatDiscriminantShield", base_color=(0.3, 0.3, 0.4, 1), metallic=0.8, roughness=0.2, emission_color=(0.1, 0.2, 0.8, 1), emission_strength=0.5)
create_material("MatQuadraticFormulaSheet", base_color=(0.1, 0.1, 0.1, 1), emission_color=(0.2, 0.8, 0.2, 1), emission_strength=1.0) # Green text on black
create_material("MatHighlightText", base_color=COLOR_YELLOW, emission_color=COLOR_YELLOW, emission_strength=2.0)
create_material("MatErrorText", base_color=COLOR_RED, emission_color=COLOR_RED, emission_strength=3.0)
create_material("MatSolutionText", base_color=COLOR_GREEN, emission_color=COLOR_GREEN, emission_strength=2.0)
create_material("MatAxisHighlight", base_color=COLOR_YELLOW, emission_color=COLOR_YELLOW, emission_strength=5.0) # For domain/range axis highlights


# --- 3. Helper Functions for Object Creation ---

def add_to_collection(obj, collection_name):
    """Adds an object to a collection, creating it if it doesn't exist."""
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    
    # Link object to the new collection and unlink from default 'Collection'
    if obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)
    collection.objects.link(obj)
    return collection

def create_text_object(name, text_content, font_size, location, material_name, collection_name="Objects", align_x='CENTER', align_y='CENTER'):
    font_curve = bpy.data.curves.new(type="FONT", name=f"FontCurve_{name}")
    font_curve.body = str(text_content)
    font_curve.align_x = align_x
    font_curve.align_y = align_y
    font_curve.size = font_size
    font_curve.extrude = 0.05 # Add some depth
    
    obj = bpy.data.objects.new(name, font_curve)
    obj.location = location
    
    if material_name in materials:
        obj.data.materials.append(materials[material_name])
    
    add_to_collection(obj, collection_name)
    return obj

def create_cube_object(name, size, location, material_name, collection_name="Objects"):
    mesh = bpy.data.meshes.new(f"Mesh_{name}")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    
    if material_name in materials:
        obj.data.materials.append(materials[material_name])
    
    add_to_collection(obj, collection_name)
    return obj

def create_plane_object(name, size, location, material_name, collection_name="Objects"):
    mesh = bpy.data.meshes.new(f"Mesh_{name}")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size/2)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    
    if material_name in materials:
        obj.data.materials.append(materials[material_name])
    
    add_to_collection(obj, collection_name)
    return obj

def create_sphere_object(name, radius, location, material_name, collection_name="Objects"):
    mesh = bpy.data.meshes.new(f"Mesh_{name}")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, segments=32, ring_count=16, radius=radius)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    
    if material_name in materials:
        obj.data.materials.append(materials[material_name])
    
    add_to_collection(obj, collection_name)
    return obj

def create_cylinder_object(name, radius, depth, location, material_name, collection_name="Objects"):
    mesh = bpy.data.meshes.new(f"Mesh_{name}")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, segments=32, radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    
    if material_name in materials:
        obj.data.materials.append(materials[material_name])
    
    add_to_collection(obj, collection_name)
    return obj

def create_grid_plane(name, size, segments, location, material_name, collection_name="Objects"):
    # Create mesh data
    mesh_data = bpy.data.meshes.new(name)
    bm = bmesh.new()

    # Create vertices for a quad with specified segments
    bmesh.ops.create_grid(bm, x_segments=segments, y_segments=segments, size=size/2)
    
    bm.to_mesh(mesh_data)
    bm.free()

    obj = bpy.data.objects.new(name, mesh_data)
    obj.location = location

    if material_name in materials:
        obj.data.materials.append(materials[material_name])

    # Add a Wireframe modifier for grid lines
    mod_wireframe = obj.modifiers.new(name="Wireframe", type='WIREFRAME')
    mod_wireframe.thickness = 0.02 # Thickness of grid lines
    mod_wireframe.material_offset = 1 # Use second material slot for wireframe
    mod_wireframe.boundary_edges = True

    add_to_collection(obj, collection_name)

    # Assign a second material for the grid lines
    if "MatGraphAxis" in materials:
        obj.data.materials.append(materials["MatGraphAxis"])
    
    return obj

def create_parabola_curve(name, material_name, collection_name="Objects", num_points=100, x_range=(-5, 5)):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2 # Resolution of the curve between points

    spline = curve_data.splines.new('BEZIER')
    
    points = []
    # g(x) = 2x^2 + 3x + 5
    for i in range(num_points):
        x = x_range[0] + (x_range[1] - x_range[0]) * i / (num_points - 1)
        y = 2 * x**2 + 3 * x + 5
        points.append(Vector((x, y, 0)))

    spline.bezier_points.add(len(points) - 1)
    for i, p in enumerate(points):
        spline.bezier_points[i].co = p
        spline.bezier_points[i].handle_left_type = 'AUTO'
        spline.bezier_points[i].handle_right_type = 'AUTO'

    obj = bpy.data.objects.new(name, curve_data)
    
    # Add bevel for visibility
    obj.data.bevel_depth = 0.05
    obj.data.bevel_resolution = 4

    if material_name in materials:
        obj.data.materials.append(materials[material_name])
    
    add_to_collection(obj, collection_name)
    return obj

# --- 4. Helper Functions for Animation ---

def set_visibility(obj, frame, visible):
    """Sets object visibility in viewport and render at a specific frame."""
    obj.hide_set(not visible)
    obj.hide_render = not visible
    obj.keyframe_insert(data_path='hide_set', frame=frame)
    obj.keyframe_insert(data_path='hide_render', frame=frame)

def animate_fade_in(obj, start_frame, duration_frames, initial_alpha=0.0):
    if not obj.data.materials: return
    mat = obj.data.materials[0]
    mat.use_nodes = True
    principled_bsdf = mat.node_tree.nodes.get("Principled BSDF")
    
    # Ensure blend method is set for transparency
    mat.blend_method = 'BLEND'
    mat.shadow_method = 'HASHED' # For better transparency shadows

    if principled_bsdf:
        principled_bsdf.inputs["Alpha"].default_value = initial_alpha
        principled_bsdf.inputs["Alpha"].keyframe_insert(data_path='default_value', frame=start_frame)
        principled_bsdf.inputs["Alpha"].default_value = 1.0
        principled_bsdf.inputs["Alpha"].keyframe_insert(data_path='default_value', frame=start_frame + duration_frames)
    
    # Animate emission strength
    emission_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    
    if emission_node:
        final_emission = emission_node.inputs["Strength"].default_value # Store actual final strength
        emission_node.inputs["Strength"].default_value = 0.0
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame)
        emission_node.inputs["Strength"].default_value = final_emission
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame + duration_frames)

def animate_fade_out(obj, start_frame, duration_frames, final_alpha=0.0):
    if not obj.data.materials: return
    mat = obj.data.materials[0]
    mat.use_nodes = True
    principled_bsdf = mat.node_tree.nodes.get("Principled BSDF")
    
    mat.blend_method = 'BLEND'
    mat.shadow_method = 'HASHED'

    if principled_bsdf:
        principled_bsdf.inputs["Alpha"].default_value = 1.0
        principled_bsdf.inputs["Alpha"].keyframe_insert(data_path='default_value', frame=start_frame)
        principled_bsdf.inputs["Alpha"].default_value = final_alpha
        principled_bsdf.inputs["Alpha"].keyframe_insert(data_path='default_value', frame=start_frame + duration_frames)
    
    emission_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    
    if emission_node:
        start_emission = emission_node.inputs["Strength"].default_value # Store actual start strength
        emission_node.inputs["Strength"].default_value = start_emission
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame)
        emission_node.inputs["Strength"].default_value = 0.0
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame + duration_frames)

def animate_slide(obj, start_frame, duration_frames, start_loc, end_loc, interp='BEZIER'):
    obj.location = start_loc
    obj.keyframe_insert(data_path='location', frame=start_frame)
    obj.location = end_loc
    obj.keyframe_insert(data_path='location', frame=start_frame + duration_frames)
    
    if obj.animation_data and obj.animation_data.action:
        fcurves = obj.animation_data.action.fcurves
        for fcurve in fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = interp

def animate_scale(obj, start_frame, duration_frames, start_scale_val, end_scale_val, interp='BEZIER'):
    obj.scale = Vector((start_scale_val, start_scale_val, start_scale_val))
    obj.keyframe_insert(data_path='scale', frame=start_frame)
    obj.scale = Vector((end_scale_val, end_scale_val, end_scale_val))
    obj.keyframe_insert(data_path='scale', frame=start_frame + duration_frames)
    
    if obj.animation_data and obj.animation_data.action:
        fcurves = obj.animation_data.action.fcurves
        for fcurve in fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = interp

def animate_glow(obj, start_frame, duration_frames, final_strength=5.0, start_strength=0.0):
    if not obj.data.materials: return
    mat = obj.data.materials[0]
    emission_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    
    if emission_node:
        emission_node.inputs["Strength"].default_value = start_strength
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame)
        emission_node.inputs["Strength"].default_value = final_strength
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame + duration_frames)

def animate_unglow(obj, start_frame, duration_frames, final_strength=0.0):
    if not obj.data.materials: return
    mat = obj.data.materials[0]
    emission_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    
    if emission_node:
        start_strength = emission_node.inputs["Strength"].default_value 
        emission_node.inputs["Strength"].default_value = start_strength
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame)
        emission_node.inputs["Strength"].default_value = final_strength
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame + duration_frames)

def animate_text_content_change(obj, start_frame, new_text):
    """Changes the text content of a text object at a specific frame."""
    # Ensure animation data exists
    if not obj.data.animation_data:
        obj.data.animation_data_create()
    
    obj.data.body = obj.data.body # Insert initial keyframe to prevent unwanted interpolation
    obj.data.keyframe_insert(data_path='body', frame=start_frame - 1) 
    obj.data.body = new_text
    obj.data.keyframe_insert(data_path='body', frame=start_frame)


# --- 5. Scene Setup: Camera and Light ---
def setup_camera_light():
    # Camera
    cam_data = bpy.data.cameras.new("MainCamera")
    cam = bpy.data.objects.new("MainCamera", cam_data)
    cam.location = (0, -15, 5) # Pull back slightly, raise
    cam.rotation_euler = Euler((math.radians(70), math.radians(0), math.radians(0))) # Look down at the board
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 18 # Adjust to fit the board
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    # Light (Sun Lamp for uniform lighting)
    light_data = bpy.data.lights.new("SunLamp", type='SUN')
    light_data.energy = 5
    light_data.angle = math.radians(20) # Softer shadows
    sun = bpy.data.objects.new("SunLamp", light_data)
    sun.location = (0, -10, 10)
    sun.rotation_euler = Euler((math.radians(45), math.radians(-30), math.radians(0)))
    bpy.context.scene.collection.objects.link(sun)

setup_camera_light()

# --- 6. Main Animation Logic ---

current_frame = 0

# --- Scene 1: Introduction - What Does "Solve" Mean? (0:00 - 0:15) ---
print(f"--- Scene 1: Introduction (0:00 - 0:15) --- Start Frame: {current_frame}")

# Background
whiteboard_bg = create_plane_object("WhiteboardBackground", size=20, location=(0, 0, -0.1), material_name="MatWhiteboard", collection_name="Scene1_Intro")
set_visibility(whiteboard_bg, current_frame, True)

# 0:00 - 0:03: Fade in WhiteboardBackground. ProblemTitleCard slides in.
title_card = create_text_object("ProblemTitleCard", "Solve g(x) = 2x² + 3x + 5", 1.2, (0, 10, 0.5), "MatProblemTitle", collection_name="Scene1_Intro")
set_visibility(title_card, current_frame, True) # Visible from start
animate_slide(title_card, current_frame, 3*FPS, (0, 10, 0.5), (0, 7, 0.5))
current_frame += 3*FPS

# 0:03 - 0:08: Function and expression build
# g(x)
fx_box = create_cube_object("FunctionBox_g_x", 1.5, (-6, 0, 0.5), "MatFunctionBox", collection_name="Scene1_Intro")
fx_text = create_text_object("FunctionText_g_x", "g(x)", 0.7, (-6, 0, 0.6), "MatProblemTitle", collection_name="Scene1_Intro")
fx_text.parent = fx_box # Parent text to box for easier movement
set_visibility(fx_box, current_frame, False)
set_visibility(fx_text, current_frame, False)
animate_fade_in(fx_box, current_frame, 15)
animate_fade_in(fx_text, current_frame, 15)

# Expression components
# g(x) = 2x^2 + 3x + 5
# X positions for expression components
x_pos_start = -2
x_step = 1.5
y_offset = 0 # Baseline for equation

expr_objs = []
# 2x^2
c2 = create_cube_object("ConstantBlock_2", 0.8, (x_pos_start, y_offset, 0.5), "MatConstantBlue", collection_name="Scene1_Intro")
c2_txt = create_text_object("ConstantText_2", "2", 0.5, (x_pos_start, y_offset, 0.6), "MatProblemTitle", collection_name="Scene1_Intro")
c2_txt.parent = c2
expr_objs.extend([c2, c2_txt])

xsq_box = create_cube_object("X_Squared_Box", 0.8, (x_pos_start + 0.8, y_offset, 0.5), "MatXSquared", collection_name="Scene1_Intro")
xsq_txt = create_text_object("X_Squared_Text", "x²", 0.5, (x_pos_start + 0.8, y_offset, 0.6), "MatProblemTitle", collection_name="Scene1_Intro")
xsq_txt.parent = xsq_box
expr_objs.extend([xsq_box, xsq_txt])

op_plus1 = create_text_object("OperationSymbol_Plus1", "+", 0.8, (x_pos_start + x_step * 1.5, y_offset, 0.6), "MatOperationSymbol", collection_name="Scene1_Intro")
expr_objs.append(op_plus1)

# 3x
c3 = create_cube_object("ConstantBlock_3", 0.8, (x_pos_start + x_step * 2, y_offset, 0.5), "MatConstantOrange", collection_name="Scene1_Intro")
c3_txt = create_text_object("ConstantText_3", "3", 0.5, (x_pos_start + x_step * 2, y_offset, 0.6), "MatProblemTitle", collection_name="Scene1_Intro")
c3_txt.parent = c3
expr_objs.extend([c3, c3_txt])

x_var_box = create_cube_object("X_VariableBox_1", 0.8, (x_pos_start + x_step * 2 + 0.8, y_offset, 0.5), "MatXVariable", collection_name="Scene1_Intro")
x_var_txt = create_text_object("X_VariableText_1", "x", 0.5, (x_pos_start + x_step * 2 + 0.8, y_offset, 0.6), "MatProblemTitle", collection_name="Scene1_Intro")
x_var_txt.parent = x_var_box
expr_objs.extend([x_var_box, x_var_txt])

op_plus2 = create_text_object("OperationSymbol_Plus2", "+", 0.8, (x_pos_start + x_step * 3.5, y_offset, 0.6), "MatOperationSymbol", collection_name="Scene1_Intro")
expr_objs.append(op_plus2)

# 5
c5 = create_cube_object("ConstantBlock_5", 0.8, (x_pos_start + x_step * 4, y_offset, 0.5), "MatConstantGreen", collection_name="Scene1_Intro")
c5_txt = create_text_object("ConstantText_5", "5", 0.5, (x_pos_start + x_step * 4, y_offset, 0.6), "MatProblemTitle", collection_name="Scene1_Intro")
c5_txt.parent = c5
expr_objs.extend([c5, c5_txt])

# Set initial visibility and animate fade in for expression
for i, obj in enumerate(expr_objs):
    set_visibility(obj, current_frame, False)
    animate_fade_in(obj, current_frame + i * 5, 15) # Sequential fade in
    
current_frame += 5*FPS # Allow time for sequential fade-in to complete

# Equals bar
equals_bar = create_cube_object("EqualsBar", 0.2, (-4.5, y_offset, 0.5), "MatEqualsBar", collection_name="Scene1_Intro")
equals_bar.scale = (0.2, 0.2, 0.2) # Initial small scale
set_visibility(equals_bar, current_frame, False)
animate_fade_in(equals_bar, current_frame, 15)
animate_scale(equals_bar, current_frame, 15, 0.2, 1.0) # Grow to full size (1.0 default)
current_frame += 15 # Frame to finish

# 0:08 - 0:15: Question marks, "What does 'solve' mean?", thought bubbles
question_marks = []
qm_locations = [(-8, 3, 0.5), (8, 3, 0.5), (-8, -3, 0.5), (8, -3, 0.5)]
for i, loc in enumerate(qm_locations):
    qm = create_text_object(f"QuestionMark_{i}", "?", 1.0, loc, "MatQuestionMark", collection_name="Scene1_Intro")
    set_visibility(qm, current_frame, True)
    # Animate expanding and contracting
    animate_scale(qm, current_frame + i*5, 10, 1.0, 1.2)
    animate_scale(qm, current_frame + i*5 + 10, 10, 1.2, 1.0)
    question_marks.append(qm)
    
text_solve_mean = create_text_object("Text_WhatSolveMean", "What does 'solve' mean?", 0.8, (0, -4, 0.5), "MatProblemTitle", collection_name="Scene1_Intro")
set_visibility(text_solve_mean, current_frame, False)
animate_fade_in(text_solve_mean, current_frame, 20)
current_frame += 20

thought_bubbles_data = [
    ("Find Roots?", (-4, -7, 0.5)),
    ("Evaluate?", (4, -7, 0.5)),
    ("Find Vertex?", (-4, -9, 0.5)),
    ("Analyze?", (4, -9, 0.5))
]
thought_bubble_objs = []
for i, (text, loc) in enumerate(thought_bubbles_data):
    tb = create_text_object(f"ThoughtBubble_{i}", text, 0.6, loc, "MatThoughtBubble", collection_name="Scene1_Intro")
    set_visibility(tb, current_frame, False)
    # Pop up (scale and fade in)
    animate_scale(tb, current_frame + i*10, 15, 0.1, 1.0) 
    animate_fade_in(tb, current_frame + i*10, 15, initial_alpha=0.0)
    # Retract (scale down and fade out)
    animate_scale(tb, current_frame + i*10 + 20, 15, 1.0, 0.1) 
    animate_fade_out(tb, current_frame + i*10 + 20, 15, final_alpha=0.0)
    thought_bubble_objs.append(tb)

current_frame += 7*FPS # Total for Scene 1 (0:15)
print(f"--- Scene 1 End. Current Frame: {current_frame} ---")

# --- Scene 2: Interpretation 1 - Finding the Roots (g(x) = 0) (0:15 - 1:30) ---
print(f"--- Scene 2: Finding Roots (0:15 - 1:30) --- Start Frame: {current_frame}")
# Hide Scene 1 elements not needed
for obj in question_marks + thought_bubble_objs + [text_solve_mean, title_card]:
    set_visibility(obj, current_frame, False)

# 0:15 - 0:20: ThoughtBubble(1) expands and moves. Equation slides to top center.
roots_bubble = thought_bubble_objs[0] # "Find Roots?"
animate_slide(roots_bubble, current_frame, 2*FPS, roots_bubble.location, (-6, 7, 0.5))
animate_scale(roots_bubble, current_frame, 2*FPS, 0.1, 1.0) # Ensure it's fully grown from previous retract
set_visibility(roots_bubble, current_frame, True)
animate_fade_in(roots_bubble, current_frame, 2*FPS, initial_alpha=0.6)
current_frame += 2*FPS

# Equation slide up (fx_box and expr_objs need to move together)
equation_group_origin = Vector((-2.5, 0, 0)) # Approximate center of the expression
equation_group_target = Vector((0, 3, 0)) # Target top center

# Create an empty parent for the equation elements
equation_parent = bpy.data.objects.new("EquationParent", None)
equation_parent.location = Vector((0,0,0)) # Set its initial location
add_to_collection(equation_parent, "Scene2_Roots")

# Parent fx_box and all expr_objs to the equation_parent
all_equation_elements = [fx_box, fx_text, equals_bar] + expr_objs
for obj in all_equation_elements:
    obj.parent = equation_parent

# Now move the parent
animate_slide(equation_parent, current_frame, 3*FPS, equation_group_origin, equation_group_target)
current_frame += 3*FPS

# 0:20 - 0:25: g(x) fades out. ConstantBlock(0) slides in. EqualsBar glows.
animate_fade_out(fx_box, current_frame, 15)
animate_fade_out(fx_text, current_frame, 15)

const_0 = create_cube_object("ConstantBlock_0", 0.8, fx_box.location, "MatConstantRed", collection_name="Scene2_Roots")
const_0_txt = create_text_object("ConstantText_0", "0", 0.5, fx_text.location, "MatProblemTitle", collection_name="Scene2_Roots")
const_0_txt.parent = const_0
set_visibility(const_0, current_frame, False)
set_visibility(const_0_txt, current_frame, False)
const_0.parent = equation_parent # Parent to equation group
const_0_txt.parent = equation_parent

animate_fade_in(const_0, current_frame, 15)
animate_fade_in(const_0_txt, current_frame, 15)

animate_glow(equals_bar, current_frame, 15, final_strength=10.0) # Brighter glow
current_frame += 15

# 0:25 - 0:30: "This is a Quadratic Equation"
quadratic_text = create_text_object("Text_QuadraticEquation", "This is a Quadratic Equation", 0.7, (0, -0.5, 0.5), "MatHighlightText", collection_name="Scene2_Roots")
set_visibility(quadratic_text, current_frame, False)
animate_fade_in(quadratic_text, current_frame, 15)
current_frame += 15

# 0:30 - 0:35: a,b,c glow. Labels appear.
animate_glow(c2, current_frame, 10, final_strength=5.0) # a=2
animate_glow(c3, current_frame, 10, final_strength=5.0) # b=3
animate_glow(c5, current_frame, 10, final_strength=5.0) # c=5
current_frame += 5

label_a = create_text_object("Label_a", "a=2", 0.4, (c2.location.x, c2.location.y + 1, c2.location.z), "MatHighlightText", collection_name="Scene2_Roots")
label_b = create_text_object("Label_b", "b=3", 0.4, (c3.location.x, c3.location.y + 1, c3.location.z), "MatHighlightText", collection_name="Scene2_Roots")
label_c = create_text_object("Label_c", "c=5", 0.4, (c5.location.x, c5.location.y + 1, c5.location.z), "MatHighlightText", collection_name="Scene2_Roots")

for label in [label_a, label_b, label_c]:
    label.parent = equation_parent # Parent to equation group
    set_visibility(label, current_frame, False)
    animate_fade_in(label, current_frame, 10)
current_frame += 10

# 0:35 - 0:40: QuadraticFormulaSheet slides in.
q_formula_sheet = create_plane_object("QuadraticFormulaSheet", 10, (15, 0, 0.5), "MatQuadraticFormulaSheet", collection_name="Scene2_Roots")
q_formula_text = create_text_object("QuadraticFormulaText", "x = [-b ± sqrt(b² - 4ac)] / 2a", 0.7, (15, 0, 0.6), "MatHighlightText", collection_name="Scene2_Roots")
q_formula_text.parent = q_formula_sheet
set_visibility(q_formula_sheet, current_frame, False)
set_visibility(q_formula_text, current_frame, False)

animate_slide(q_formula_sheet, current_frame, 15, (15, 0, 0.5), (0, 0, 0.5))
animate_slide(q_formula_text, current_frame, 15, (15, 0, 0.6), (0, 0, 0.6))
animate_fade_in(q_formula_sheet, current_frame, 15)
animate_fade_in(q_formula_text, current_frame, 15)
current_frame += 15

# 0:40 - 0:45: DiscriminantShield appears, isolating Δ = b² - 4ac.
discriminant_shield = create_plane_object("DiscriminantShield", 5, (0, 0, 0.7), "MatDiscriminantShield", collection_name="Scene2_Roots")
discriminant_text = create_text_object("DiscriminantText", "Δ = b² - 4ac", 0.6, (0, 0, 0.8), "MatHighlightText", collection_name="Scene2_Roots")
discriminant_text.parent = discriminant_shield
set_visibility(discriminant_shield, current_frame, False)
set_visibility(discriminant_text, current_frame, False)

animate_fade_in(discriminant_shield, current_frame, 10)
animate_fade_in(discriminant_text, current_frame, 10)
animate_glow(discriminant_shield, current_frame, 10, final_strength=1.0) # Subtle glow
animate_glow(discriminant_text, current_frame, 10, final_strength=3.0)
current_frame += 10

# 0:45 - 0:55: Discriminant Calculation
calc_start_x = -2
calc_y_offset = -4

# (3)^2
val_b_sq = create_text_object("Calc_b_sq", "(3)²", 0.5, (calc_start_x, calc_y_offset, 0.5), "MatConstantOrange", collection_name="Scene2_Roots_Calc")
set_visibility(val_b_sq, current_frame, False)
animate_fade_in(val_b_sq, current_frame, 10)
animate_glow(c3, current_frame, 10, final_strength=5.0) # Re-glow b

current_frame += 10
animate_fade_out(val_b_sq, current_frame, 10)
val_9 = create_text_object("Calc_9", "9", 0.5, (calc_start_x, calc_y_offset, 0.5), "MatConstantDefault", collection_name="Scene2_Roots_Calc")
set_visibility(val_9, current_frame, False)
animate_fade_in(val_9, current_frame, 10)
current_frame += 10
animate_unglow(c3, current_frame, 10, final_strength=0.0)

# 4ac
val_4ac_parts = [
    create_cube_object("Const_4_calc", 0.8, (calc_start_x + 1.5, calc_y_offset, 0.5), "MatConstantDefault", collection_name="Scene2_Roots_Calc"),
    create_text_object("Const_4_calc_txt", "4", 0.5, (calc_start_x + 1.5, calc_y_offset, 0.6), "MatProblemTitle", collection_name="Scene2_Roots_Calc"),
    create_text_object("Op_Mult1_calc", "✖", 0.5, (calc_start_x + 2.5, calc_y_offset, 0.6), "MatOperationSymbol", collection_name="Scene2_Roots_Calc"),
    create_cube_object("Const_a_calc", 0.8, (calc_start_x + 3.5, calc_y_offset, 0.5), "MatConstantBlue", collection_name="Scene2_Roots_Calc"),
    create_text_object("Const_a_calc_txt", "2", 0.5, (calc_start_x + 3.5, calc_y_offset, 0.6), "MatProblemTitle", collection_name="Scene2_Roots_Calc"),
    create_text_object("Op_Mult2_calc", "✖", 0.5, (calc_start_x + 4.5, calc_y_offset, 0.6), "MatOperationSymbol", collection_name="Scene2_Roots_Calc"),
    create_cube_object("Const_c_calc", 0.8, (calc_start_x + 5.5, calc_y_offset, 0.5), "MatConstantGreen", collection_name="Scene2_Roots_Calc"),
    create_text_object("Const_c_calc_txt", "5", 0.5, (calc_start_x + 5.5, calc_y_offset, 0.6), "MatProblemTitle", collection_name="Scene2_Roots_Calc")
]

for obj in val_4ac_parts:
    set_visibility(obj, current_frame, False)
    animate_fade_in(obj, current_frame, 10)

animate_glow(c2, current_frame, 10, final_strength=5.0) # Re-glow a
animate_glow(c5, current_frame, 10, final_strength=5.0) # Re-glow c
current_frame += 10

# Consolidate 4ac to 40
for obj in val_4ac_parts:
    animate_fade_out(obj, current_frame, 10)
    
val_40 = create_text_object("Calc_40", "40", 0.5, (calc_start_x + 4.0, calc_y_offset, 0.5), "MatConstantDefault", collection_name="Scene2_Roots_Calc")
set_visibility(val_40, current_frame, False)
animate_fade_in(val_40, current_frame, 10)
current_frame += 10
animate_unglow(c2, current_frame, 10, final_strength=0.0)
animate_unglow(c5, current_frame, 10, final_strength=0.0)

# 9 - 40 = -31
op_minus_calc = create_text_object("Op_Minus_Calc", "-", 0.8, (calc_start_x + 0.5, calc_y_offset, 0.6), "MatOperationSymbol", collection_name="Scene2_Roots_Calc")
set_visibility(op_minus_calc, current_frame, False)
animate_fade_in(op_minus_calc, current_frame, 10)
animate_glow(op_minus_calc, current_frame, 10, final_strength=5.0)

animate_slide(val_9, current_frame, 10, val_9.location, (calc_start_x - 0.5, calc_y_offset, 0.5))
animate_slide(val_40, current_frame, 10, val_40.location, (calc_start_x + 1.5, calc_y_offset, 0.5))
current_frame += 10

animate_fade_out(val_9, current_frame, 10)
animate_fade_out(op_minus_calc, current_frame, 10)
animate_fade_out(val_40, current_frame, 10)

val_neg31 = create_text_object("Calc_Neg31", "-31", 0.5, (calc_start_x + 0.5, calc_y_offset, 0.5), "MatConstantRed", collection_name="Scene2_Roots_Calc")
set_visibility(val_neg31, current_frame, False)
animate_fade_in(val_neg31, current_frame, 10)

# Discriminant shield update
animate_text_content_change(discriminant_text, current_frame, "Δ = -31")
animate_glow(discriminant_text, current_frame, 10, final_strength=5.0)
current_frame += 10

# 0:55 - 1:00: DiscriminantShield fades out. Text "Discriminant is negative" appears.
animate_fade_out(discriminant_shield, current_frame, 15)
animate_fade_out(discriminant_text, current_frame, 15)
for obj in [val_neg31] + val_4ac_parts + [val_9, op_minus_calc, val_40]: # Hide all calc elements
    set_visibility(obj, current_frame + 10, False) # Hide slightly after fade out starts
current_frame += 15

neg_discriminant_text = create_text_object("Text_NegDiscriminant", "Discriminant is negative (-31 < 0)", 0.8, (0, -2, 0.5), "MatErrorText", collection_name="Scene2_Roots")
set_visibility(neg_discriminant_text, current_frame, False)
animate_fade_in(neg_discriminant_text, current_frame, 15)
current_frame += 15

# 1:00 - 1:15: GraphPlane, ParabolaArc, NO REAL SOLUTIONS
graph_plane = create_grid_plane("GraphPlane", 12, 12, (0, 0, 0), "MatGraphPlane", collection_name="Scene2_Roots_Graph")
parabola_arc = create_parabola_curve("ParabolaArc", "MatParabolaArc", collection_name="Scene2_Roots_Graph", x_range=(-3, 3))
parabola_arc.data.bevel_factor_end = 0.0 # Initial state for build animation

set_visibility(graph_plane, current_frame, False)
animate_fade_in(graph_plane, current_frame, 20)
current_frame += 20

# Parabola builds
set_visibility(parabola_arc, current_frame, True)
parabola_arc.data.bevel_factor_end = 0.0
parabola_arc.data.keyframe_insert(data_path='bevel_factor_end', frame=current_frame)
parabola_arc.data.bevel_factor_end = 1.0
parabola_arc.data.keyframe_insert(data_path='bevel_factor_end', frame=current_frame + 30)
current_frame += 30

text_means = create_text_object("Text_ThisMeans", "This means...", 0.6, (0, -4, 0.5), "MatProblemTitle", collection_name="Scene2_Roots_Graph")
set_visibility(text_means, current_frame, False)
animate_fade_in(text_means, current_frame, 15)
current_frame += 15
animate_fade_out(text_means, current_frame, 15)
set_visibility(text_means, current_frame + 15, False)
current_frame += 15

# Animated line attempts to descend
line_attempt = create_cylinder_object("LineAttempt", 0.05, 3, (0, 7, 0.5), "MatPointMarker", collection_name="Scene2_Roots_Graph")
line_attempt.rotation_euler = Euler((math.radians(90), 0, 0)) # Point downwards along Y
set_visibility(line_attempt, current_frame, False)
animate_fade_in(line_attempt, current_frame, 5)

line_start_loc = Vector((0, 7, 0.5))
line_end_loc_hit = Vector((0, 2, 0.5)) # Just above x-axis
line_bounce_loc = Vector((0, 3, 0.5))

animate_slide(line_attempt, current_frame, 20, line_start_loc, line_end_loc_hit)
current_frame += 20
animate_slide(line_attempt, current_frame, 10, line_end_loc_hit, line_bounce_loc) # Bounce back
current_frame += 10
animate_fade_out(line_attempt, current_frame, 10)
set_visibility(line_attempt, current_frame + 10, False)
current_frame += 10

no_real_solutions_text = create_text_object("Text_NoRealSolutions", "NO REAL SOLUTIONS", 1.5, (0, 0, 0.5), "MatErrorText", collection_name="Scene2_Roots_Graph")
set_visibility(no_real_solutions_text, current_frame, False)
animate_fade_in(no_real_solutions_text, current_frame, 20)
current_frame += 20
animate_fade_out(no_real_solutions_text, current_frame, 20)
set_visibility(no_real_solutions_text, current_frame + 20, False)
current_frame += 20

# 1:15 - 1:25: GraphPlane fades out. QuadraticFormulaSheet reappears. Complex solutions.
animate_fade_out(graph_plane, current_frame, 20)
animate_fade_out(parabola_arc, current_frame, 20)
set_visibility(graph_plane, current_frame + 20, False)
set_visibility(parabola_arc, current_frame + 20, False)
current_frame += 20

# Hide old labels
for label in [label_a, label_b, label_c]:
    set_visibility(label, current_frame, False)
set_visibility(quadratic_text, current_frame, False)
set_visibility(neg_discriminant_text, current_frame, False)

# Q formula sheet reappears (from being off-screen or faded out)
q_formula_sheet.location = (0,0,0.5) # Already at center
q_formula_text.location = (0,0,0.6)
set_visibility(q_formula_sheet, current_frame, True)
set_visibility(q_formula_text, current_frame, True)
animate_fade_in(q_formula_sheet, current_frame, 10)
animate_fade_in(q_formula_text, current_frame, 10)
current_frame += 10

# Substitute values for complex roots
# x = [-b ± sqrt(b² - 4ac)] / 2a
# a=2, b=3, c=5 -> x = [-3 ± sqrt(-31)] / 4
animate_text_content_change(q_formula_text, current_frame, "x = [-3 ± sqrt(-31)] / 4")
current_frame += 15

# sqrt(-31) -> sqrt(31)i
# Need a subtle reposition of the i symbol relative to the text block
i_symbol = create_text_object("i_symbol", "i", 0.5, (q_formula_text.location.x + 4.5, q_formula_text.location.y + 0.1, q_formula_text.location.z), "MatHighlightText", collection_name="Scene2_Roots")
set_visibility(i_symbol, current_frame, False)
animate_fade_in(i_symbol, current_frame, 10)
animate_glow(i_symbol, current_frame, 10, final_strength=5.0)
animate_text_content_change(q_formula_text, current_frame + 5, "x = [-3 ± sqrt(31)i] / 4") # Update text after i appears
current_frame += 10
animate_unglow(i_symbol, current_frame, 10, final_strength=0.0)


# Highlight ±
plus_minus_highlight = create_text_object("PlusMinusHighlight", "±", 1.0, (q_formula_text.location.x + 0.1, q_formula_text.location.y, q_formula_text.location.z + 0.1), "MatHighlightText", collection_name="Scene2_Roots")
set_visibility(plus_minus_highlight, current_frame, False)
animate_fade_in(plus_minus_highlight, current_frame, 10)
animate_scale(plus_minus_highlight, current_frame, 10, 0.5, 1.2)
animate_scale(plus_minus_highlight, current_frame + 10, 10, 1.2, 1.0)
current_frame += 15

# 1:25 - 1:30: Text "Two Complex Conjugate Solutions"
complex_solution_text = create_text_object("Text_ComplexSolutions", "Two Complex Conjugate Solutions", 0.8, (0, -2, 0.5), "MatSolutionText", collection_name="Scene2_Roots")
set_visibility(complex_solution_text, current_frame, False)
animate_fade_in(complex_solution_text, current_frame, 15)
current_frame += 15
print(f"--- Scene 2 End. Current Frame: {current_frame} ---")

# --- Scene 3: Interpretation 2 - Evaluating the Function (1:30 - 2:20) ---
print(f"--- Scene 3: Evaluating (1:30 - 2:20) --- Start Frame: {current_frame}")
# Hide Scene 2 elements
for obj in [q_formula_sheet, q_formula_text, complex_solution_text, i_symbol, plus_minus_highlight]:
    set_visibility(obj, current_frame, False)
set_visibility(roots_bubble, current_frame, False)

# 1:30 - 1:35: ThoughtBubble(2) expands and moves. Original function slides back.
eval_bubble = thought_bubble_objs[1] # "Evaluate?"
animate_slide(eval_bubble, current_frame, 2*FPS, eval_bubble.location, (-6, 7, 0.5))
animate_scale(eval_bubble, current_frame, 2*FPS, 0.1, 1.0)
set_visibility(eval_bubble, current_frame, True)
animate_fade_in(eval_bubble, current_frame, 2*FPS, initial_alpha=0.6)
current_frame += 2*FPS

# Original function slides back (ensure elements are visible and in original state)
animate_slide(equation_parent, current_frame, 3*FPS, equation_parent.location, equation_group_target) # already there, just ensure visible
set_visibility(fx_box, current_frame, True) # Show g(x) again
set_visibility(fx_text, current_frame, True)
set_visibility(const_0, current_frame, False) # Hide 0
set_visibility(const_0_txt, current_frame, False)
animate_unglow(equals_bar, current_frame, 10, final_strength=5.0) # Reduce glow on equals

# Reset the equation to original state (relative to equation_parent)
# Unparent and re-parent if necessary to prevent cumulative transforms.
# This assumes global positions were stored for initial creation.
# For simplicity and given parent, just reset content/visibility of elements
animate_text_content_change(fx_text, current_frame, "g(x)") 
set_visibility(c2, current_frame, True)
set_visibility(c2_txt, current_frame, True)
set_visibility(xsq_box, current_frame, True)
set_visibility(xsq_txt, current_frame, True)
set_visibility(op_plus1, current_frame, True)
set_visibility(c3, current_frame, True)
set_visibility(c3_txt, current_frame, True)
set_visibility(x_var_box, current_frame, True)
set_visibility(x_var_txt, current_frame, True)
set_visibility(op_plus2, current_frame, True)
set_visibility(c5, current_frame, True)
set_visibility(c5_txt, current_frame, True)

# Hide any temporary calc objects from previous scene
for obj in bpy.data.collections.get("Scene2_Roots_Calc").objects:
    set_visibility(obj, current_frame, False)

current_frame += 3*FPS

# 1:35 - 1:40: "Example: Find g(0)"
find_g0_text = create_text_object("Text_FindG0", "Example: Find g(0)", 0.7, (0, -2, 0.5), "MatProblemTitle", collection_name="Scene3_Evaluate")
set_visibility(find_g0_text, current_frame, False)
animate_fade_in(find_g0_text, current_frame, 15)
current_frame += 15

# 1:40 - 1:50: g(0) = 2(0)² + 3(0) + 5 -> g(0) = 5
# Replace X with 0
# Create new 0 blocks for substitution at original x^2 and x locations
c0_sub1 = create_cube_object("ConstantBlock_0_Sub1", 0.8, xsq_box.location, "MatConstantRed", collection_name="Scene3_Evaluate_Calc")
c0_sub1_txt = create_text_object("ConstantText_0_Sub1", "0", 0.5, xsq_txt.location, "MatProblemTitle", collection_name="Scene3_Evaluate_Calc")
c0_sub1_txt.parent = c0_sub1

c0_sub2 = create_cube_object("ConstantBlock_0_Sub2", 0.8, x_var_box.location, "MatConstantRed", collection_name="Scene3_Evaluate_Calc")
c0_sub2_txt = create_text_object("ConstantText_0_Sub2", "0", 0.5, x_var_txt.location, "MatProblemTitle", collection_name="Scene3_Evaluate_Calc")
c0_sub2_txt.parent = c0_sub2

# Parent to equation_parent for relative movement
c0_sub1.parent = equation_parent
c0_sub1_txt.parent = equation_parent
c0_sub2.parent = equation_parent
c0_sub2_txt.parent = equation_parent

# Hide original X, X^2 and show 0s
set_visibility(xsq_box, current_frame, False)
set_visibility(xsq_txt, current_frame, False)
set_visibility(x_var_box, current_frame, False)
set_visibility(x_var_txt, current_frame, False)

set_visibility(c0_sub1, current_frame, True)
set_visibility(c0_sub1_txt, current_frame, True)
set_visibility(c0_sub2, current_frame, True)
set_visibility(c0_sub2_txt, current_frame, True)

# animate g(x) to g(0)
animate_text_content_change(fx_text, current_frame, "g(0)")
current_frame += 15 # Time for substitution

# Calculations: 2(0)^2 -> 0, 3(0) -> 0
# Make 2(0)^2 disappear and new 0 appear
temp_calc_loc_1 = (c2.location.x + 0.5, c2.location.y, c2.location.z) # Approx location for 2(0)^2
temp_calc_loc_2 = (c3.location.x + 0.5, c3.location.y, c3.location.z) # Approx location for 3(0)

# Combine 2 and 0s
for obj in [c2, c2_txt, c0_sub1, c0_sub1_txt]:
    animate_fade_out(obj, current_frame, 10)
    set_visibility(obj, current_frame + 10, False)
zero_res1 = create_text_object("ZeroResult1", "0", 0.5, temp_calc_loc_1, "MatConstantDefault", collection_name="Scene3_Evaluate_Calc")
zero_res1.parent = equation_parent
set_visibility(zero_res1, current_frame, False)
animate_fade_in(zero_res1, current_frame, 10)
current_frame += 10

# Combine 3 and 0s
for obj in [c3, c3_txt, c0_sub2, c0_sub2_txt]:
    animate_fade_out(obj, current_frame, 10)
    set_visibility(obj, current_frame + 10, False)
zero_res2 = create_text_object("ZeroResult2", "0", 0.5, temp_calc_loc_2, "MatConstantDefault", collection_name="Scene3_Evaluate_Calc")
zero_res2.parent = equation_parent
set_visibility(zero_res2, current_frame, False)
animate_fade_in(zero_res2, current_frame, 10)
current_frame += 10

# g(0) = 0 + 0 + 5
animate_text_content_change(fx_text, current_frame, "g(0)") # Re-set text if it shifted
# Need to adjust positions of ops and final constant
animate_slide(op_plus1, current_frame, 10, op_plus1.location, (op_plus1.location.x - 2, op_plus1.location.y, op_plus1.location.z))
animate_slide(op_plus2, current_frame, 10, op_plus2.location, (op_plus2.location.x - 2, op_plus2.location.y, op_plus2.location.z))
animate_slide(c5, current_frame, 10, c5.location, (c5.location.x - 2, c5.location.y, c5.location.z))
animate_slide(c5_txt, current_frame, 10, c5_txt.location, (c5_txt.location.x - 2, c5_txt.location.y, c5_txt.location.z))
animate_slide(zero_res2, current_frame, 10, zero_res2.location, (zero_res2.location.x - 2, zero_res2.location.y, zero_res2.location.z))
current_frame += 10

# g(0) = 5
animate_fade_out(zero_res1, current_frame, 10)
animate_fade_out(op_plus1, current_frame, 10)
animate_fade_out(zero_res2, current_frame, 10)
animate_fade_out(op_plus2, current_frame, 10)

set_visibility(zero_res1, current_frame + 10, False)
set_visibility(op_plus1, current_frame + 10, False)
set_visibility(zero_res2, current_frame + 10, False)
set_visibility(op_plus2, current_frame + 10, False)

animate_slide(c5, current_frame, 10, c5.location, (c2.location.x, c2.location.y, c2.location.z)) # Move 5 to start of expression
animate_slide(c5_txt, current_frame, 10, c5_txt.location, (c2_txt.location.x, c2_txt.location.y, c2_txt.location.z))
animate_text_content_change(fx_text, current_frame, "g(0) = 5") # Update full equation string
set_visibility(c5, current_frame, True) # Keep 5 visible
set_visibility(c5_txt, current_frame, True)
current_frame += 10

# 1:50 - 1:55: GraphPlane (simple grid), PointMarker(0,5). "Y-intercept: (0, 5)"
graph_plane_eval = create_grid_plane("GraphPlane_Eval", 12, 12, (0, 0, 0), "MatGraphPlane", collection_name="Scene3_Evaluate_Graph")
set_visibility(graph_plane_eval, current_frame, False)
animate_fade_in(graph_plane_eval, current_frame, 15)
current_frame += 15

point_0_5 = create_sphere_object("PointMarker_0_5", 0.2, (0, 5, 0.1), "MatPointMarker", collection_name="Scene3_Evaluate_Graph")
set_visibility(point_0_5, current_frame, False)
animate_fade_in(point_0_5, current_frame, 5)
animate_glow(point_0_5, current_frame, 5, final_strength=15.0) # Flash
animate_unglow(point_0_5, current_frame + 5, 5, final_strength=5.0) # Settle glow
current_frame += 5

y_intercept_text = create_text_object("Text_YIntercept", "Y-intercept: (0, 5)", 0.6, (point_0_5.location.x + 1.5, point_0_5.location.y, point_0_5.location.z), "MatSolutionText", collection_name="Scene3_Evaluate_Graph")
set_visibility(y_intercept_text, current_frame, False)
animate_fade_in(y_intercept_text, current_frame, 10)
current_frame += 10

# 1:55 - 2:00: "Example: Find g(1)"
animate_fade_out(find_g0_text, current_frame, 10)
animate_fade_out(y_intercept_text, current_frame, 10)
set_visibility(find_g0_text, current_frame + 10, False)
set_visibility(y_intercept_text, current_frame + 10, False)

# Hide the g(0) = 5 result and bring back full expression for g(1)
animate_fade_out(c5, current_frame, 10)
animate_fade_out(c5_txt, current_frame, 10)
set_visibility(c5, current_frame + 10, False)
set_visibility(c5_txt, current_frame + 10, False)
current_frame += 10

# Reset the equation to original state (relative to equation_parent)
set_visibility(xsq_box, current_frame, True)
set_visibility(xsq_txt, current_frame, True)
set_visibility(x_var_box, current_frame, True)
set_visibility(x_var_txt, current_frame, True)
set_visibility(c2, current_frame, True)
set_visibility(c2_txt, current_frame, True)
set_visibility(op_plus1, current_frame, True)
set_visibility(c3, current_frame, True)
set_visibility(c3_txt, current_frame, True)
set_visibility(op_plus2, current_frame, True)
set_visibility(c5, current_frame, True) # Bring back original c5 block
set_visibility(c5_txt, current_frame, True)

# Reset their locations (needed if animations changed them for intermediate calc)
c2.location = (x_pos_start, y_offset, 0.5)
c2_txt.location = (x_pos_start, y_offset, 0.6)
xsq_box.location = (x_pos_start + 0.8, y_offset, 0.5)
xsq_txt.location = (x_pos_start + 0.8, y_offset, 0.6)
op_plus1.location = (x_pos_start + x_step * 1.5, y_offset, 0.6)
c3.location = (x_pos_start + x_step * 2, y_offset, 0.5)
c3_txt.location = (x_pos_start + x_step * 2, y_offset, 0.6)
x_var_box.location = (x_pos_start + x_step * 2 + 0.8, y_offset, 0.5)
x_var_txt.location = (x_pos_start + x_step * 2 + 0.8, y_offset, 0.6)
op_plus2.location = (x_pos_start + x_step * 3.5, y_offset, 0.6)
c5.location = (x_pos_start + x_step * 4, y_offset, 0.5)
c5_txt.location = (x_pos_start + x_step * 4, y_offset, 0.6)
animate_text_content_change(fx_text, current_frame, "g(x)") # Reset g(x)

# Hide old substitution objects
for obj in [c0_sub1, c0_sub1_txt, c0_sub2, c0_sub2_txt, zero_res1, zero_res2]:
    set_visibility(obj, current_frame, False)


find_g1_text = create_text_object("Text_FindG1", "Example: Find g(1)", 0.7, (0, -2, 0.5), "MatProblemTitle", collection_name="Scene3_Evaluate")
set_visibility(find_g1_text, current_frame, False)
animate_fade_in(find_g1_text, current_frame, 15)
current_frame += 15

# 2:00 - 2:15: g(1) = 2(1)² + 3(1) + 5 -> g(1) = 10
# Replace X with 1
c1_sub1 = create_cube_object("ConstantBlock_1_Sub1", 0.8, xsq_box.location, "MatConstantBlue", collection_name="Scene3_Evaluate_Calc")
c1_sub1_txt = create_text_object("ConstantText_1_Sub1", "1", 0.5, xsq_txt.location, "MatProblemTitle", collection_name="Scene3_Evaluate_Calc")
c1_sub1_txt.parent = c1_sub1

c1_sub2 = create_cube_object("ConstantBlock_1_Sub2", 0.8, x_var_box.location, "MatConstantBlue", collection_name="Scene3_Evaluate_Calc")
c1_sub2_txt = create_text_object("ConstantText_1_Sub2", "1", 0.5, x_var_txt.location, "MatProblemTitle", collection_name="Scene3_Evaluate_Calc")
c1_sub2_txt.parent = c1_sub2

# Parent to equation_parent for relative movement
c1_sub1.parent = equation_parent
c1_sub1_txt.parent = equation_parent
c1_sub2.parent = equation_parent
c1_sub2_txt.parent = equation_parent

# Hide original X, X^2 and show 1s
set_visibility(xsq_box, current_frame, False)
set_visibility(xsq_txt, current_frame, False)
set_visibility(x_var_box, current_frame, False)
set_visibility(x_var_txt, current_frame, False)

set_visibility(c1_sub1, current_frame, True)
set_visibility(c1_sub1_txt, current_frame, True)
set_visibility(c1_sub2, current_frame, True)
set_visibility(c1_sub2_txt, current_frame, True)

# animate g(x) to g(1)
animate_text_content_change(fx_text, current_frame, "g(1)")
current_frame += 15 # Time for substitution

# Calculations: 2(1)^2 -> 2, 3(1) -> 3
# 2(1)^2 -> 2
for obj in [c2, c2_txt, c1_sub1, c1_sub1_txt]:
    animate_fade_out(obj, current_frame, 10)
    set_visibility(obj, current_frame + 10, False)
res_2 = create_text_object("Result_2", "2", 0.5, temp_calc_loc_1, "MatConstantDefault", collection_name="Scene3_Evaluate_Calc")
res_2.parent = equation_parent
set_visibility(res_2, current_frame, False)
animate_fade_in(res_2, current_frame, 10)
current_frame += 10

# 3(1) -> 3
for obj in [c3, c3_txt, c1_sub2, c1_sub2_txt]:
    animate_fade_out(obj, current_frame, 10)
    set_visibility(obj, current_frame + 10, False)
res_3 = create_text_object("Result_3", "3", 0.5, temp_calc_loc_2, "MatConstantDefault", collection_name="Scene3_Evaluate_Calc")
res_3.parent = equation_parent
set_visibility(res_3, current_frame, False)
animate_fade_in(res_3, current_frame, 10)
current_frame += 10

# g(1) = 2 + 3 + 5
animate_text_content_change(fx_text, current_frame, "g(1)")
animate_slide(op_plus1, current_frame, 10, op_plus1.location, (res_2.location.x + 1, op_plus1.location.y, op_plus1.location.z))
animate_slide(res_3, current_frame, 10, res_3.location, (res_2.location.x + 2, res_3.location.y, res_3.location.z))
animate_slide(op_plus2, current_frame, 10, op_plus2.location, (res_2.location.x + 3, op_plus2.location.y, op_plus2.location.z))
animate_slide(c5, current_frame, 10, c5.location, (res_2.location.x + 4, c5.location.y, c5.location.z))
animate_slide(c5_txt, current_frame, 10, c5_txt.location, (res_2.location.x + 4, c5_txt.location.y, c5_txt.location.z))
current_frame += 10

# g(1) = 10
animate_fade_out(res_2, current_frame, 10)
animate_fade_out(op_plus1, current_frame, 10)
animate_fade_out(res_3, current_frame, 10)
animate_fade_out(op_plus2, current_frame, 10)
animate_fade_out(c5, current_frame, 10)
animate_fade_out(c5_txt, current_frame, 10)

set_visibility(res_2, current_frame + 10, False)
set_visibility(op_plus1, current_frame + 10, False)
set_visibility(res_3, current_frame + 10, False)
set_visibility(op_plus2, current_frame + 10, False)
set_visibility(c5, current_frame + 10, False)
set_visibility(c5_txt, current_frame + 10, False)

res_10 = create_text_object("Result_10", "10", 0.5, (res_2.location.x + 2, res_2.location.y, res_2.location.z), "MatConstantDefault", collection_name="Scene3_Evaluate_Calc")
res_10.parent = equation_parent
set_visibility(res_10, current_frame, False)
animate_fade_in(res_10, current_frame, 10)
animate_text_content_change(fx_text, current_frame, "g(1) = 10")
current_frame += 10

# 2:15 - 2:20: PointMarker(1,10).
point_1_10 = create_sphere_object("PointMarker_1_10", 0.2, (1, 10, 0.1), "MatPointMarker", collection_name="Scene3_Evaluate_Graph")
set_visibility(point_1_10, current_frame, False)
animate_fade_in(point_1_10, current_frame, 5)
animate_glow(point_1_10, current_frame, 5, final_strength=15.0) # Flash
animate_unglow(point_1_10, current_frame + 5, 5, final_strength=5.0) # Settle glow
current_frame += 5
print(f"--- Scene 3 End. Current Frame: {current_frame} ---")

# --- Scene 4: Interpretation 3 - Finding the Vertex (2:20 - 3:20) ---
print(f"--- Scene 4: Finding Vertex (2:20 - 3:20) --- Start Frame: {current_frame}")
# Hide Scene 3 elements
set_visibility(eval_bubble, current_frame, False)
set_visibility(find_g1_text, current_frame, False)
set_visibility(res_10, current_frame, False) # Hide the 10 result
set_visibility(point_0_5, current_frame, False)
set_visibility(point_1_10, current_frame, False)
# Also hide current equation elements (temporarily)
for obj in all_equation_elements + [res_2, res_3]:
    set_visibility(obj, current_frame, False)
for obj in bpy.data.collections.get("Scene3_Evaluate_Calc").objects:
    set_visibility(obj, current_frame, False)


# 2:20 - 2:25: ThoughtBubble(3). GraphPlane with ParabolaArc. Function slides in.
vertex_bubble = thought_bubble_objs[2] # "Find Vertex?"
animate_slide(vertex_bubble, current_frame, 2*FPS, vertex_bubble.location, (-6, 7, 0.5))
animate_scale(vertex_bubble, current_frame, 2*FPS, 0.1, 1.0)
set_visibility(vertex_bubble, current_frame, True)
animate_fade_in(vertex_bubble, current_frame, 2*FPS, initial_alpha=0.6)
current_frame += 2*FPS

set_visibility(graph_plane_eval, current_frame, True)
animate_fade_in(graph_plane_eval, current_frame, 15)
set_visibility(parabola_arc, current_frame, True)
animate_fade_in(parabola_arc, current_frame, 15)
parabola_arc.data.bevel_factor_end = 1.0 # Ensure it's fully drawn
parabola_arc.data.keyframe_insert(data_path='bevel_factor_end', frame=current_frame)

animate_slide(equation_parent, current_frame, 3*FPS, equation_parent.location, equation_group_target) # Already there
set_visibility(equation_parent, current_frame, True)
# Re-enable original expression elements.
for obj in [fx_box, fx_text, equals_bar, c2, c2_txt, xsq_box, xsq_txt, op_plus1, c3, c3_txt, x_var_box, x_var_txt, op_plus2, c5, c5_txt]:
    set_visibility(obj, current_frame, True)
animate_text_content_change(fx_text, current_frame, "g(x)") # Reset to g(x)
current_frame += 3*FPS

# 2:25 - 2:30: "Parabola opens UPWARDS (a=2 is positive)."
parabola_up_text = create_text_object("Text_ParabolaUp", "Parabola opens UPWARDS (a=2 is positive).", 0.6, (0, -2, 0.5), "MatProblemTitle", collection_name="Scene4_Vertex")
set_visibility(parabola_up_text, current_frame, False)
animate_fade_in(parabola_up_text, current_frame, 15)

# Animated arrow points upwards
arrow_up = create_cylinder_object("ArrowUp", 0.05, 1.0, (0, 6, 0.5), "MatHighlightText", collection_name="Scene4_Vertex")
arrow_up.rotation_euler = Euler((0, math.radians(90), 0))
set_visibility(arrow_up, current_frame, False)
animate_fade_in(arrow_up, current_frame, 10)
animate_slide(arrow_up, current_frame, 20, (0, 6, 0.5), (0, 8, 0.5)) # Animate slight movement up
current_frame += 20
animate_fade_out(arrow_up, current_frame, 10)
set_visibility(arrow_up, current_frame + 10, False)
current_frame += 10


# 2:30 - 2:35: X-coordinate of Vertex: x_v = -b / 2a
animate_fade_out(parabola_up_text, current_frame, 10)
set_visibility(parabola_up_text, current_frame + 10, False)
current_frame += 10

vertex_formula_text = create_text_object("Text_VertexFormula", "X-coordinate of Vertex: x_v = -b / 2a", 0.7, (0, -2, 0.5), "MatProblemTitle", collection_name="Scene4_Vertex")
set_visibility(vertex_formula_text, current_frame, False)
animate_fade_in(vertex_formula_text, current_frame, 15)
animate_glow(c2, current_frame, 10, final_strength=5.0) # Glow 'a'
animate_glow(c3, current_frame, 10, final_strength=5.0) # Glow 'b'
current_frame += 15

# 2:35 - 2:45: Calculation of x_v: x_v = -3 / (2 * 2) -> x_v = -3 / 4
calc_xv_start_x = -2
calc_xv_y_offset = -4

xv_b = create_text_object("XV_b", "-3", 0.5, (calc_xv_start_x, calc_xv_y_offset, 0.5), "MatConstantRed", collection_name="Scene4_Vertex_Calc")
xv_div = create_text_object("XV_Div", "/", 0.8, (calc_xv_start_x + 0.5, calc_xv_y_offset, 0.5), "MatOperationSymbol", collection_name="Scene4_Vertex_Calc")
xv_2a = create_text_object("XV_2a", "(2 * 2)", 0.5, (calc_xv_start_x + 1.5, calc_xv_y_offset, 0.5), "MatConstantBlue", collection_name="Scene4_Vertex_Calc")

for obj in [xv_b, xv_div, xv_2a]:
    set_visibility(obj, current_frame, False)
    animate_fade_in(obj, current_frame, 10)
current_frame += 10

animate_unglow(c2, current_frame, 10, final_strength=0.0)
animate_unglow(c3, current_frame, 10, final_strength=0.0)

# Simplify 2*2 to 4
animate_fade_out(xv_2a, current_frame, 10)
set_visibility(xv_2a, current_frame + 10, False)
xv_4 = create_text_object("XV_4", "4", 0.5, (calc_xv_start_x + 1.5, calc_xv_y_offset, 0.5), "MatConstantDefault", collection_name="Scene4_Vertex_Calc")
set_visibility(xv_4, current_frame, False)
animate_fade_in(xv_4, current_frame, 10)
current_frame += 10

# Final x_v = -3/4
animate_text_content_change(vertex_formula_text, current_frame, "X-coordinate of Vertex: x_v = -3/4")
animate_fade_out(xv_b, current_frame, 10)
animate_fade_out(xv_div, current_frame, 10)
animate_fade_out(xv_4, current_frame, 10)
for obj in [xv_b, xv_div, xv_4]:
    set_visibility(obj, current_frame + 10, False)
current_frame += 10

# 2:45 - 2:50: "Now find y-coordinate: g(-3/4)"
find_yv_text = create_text_object("Text_FindYV", "Now find y-coordinate: g(-3/4)", 0.7, (0, -2, 0.5), "MatProblemTitle", collection_name="Scene4_Vertex")
set_visibility(find_yv_text, current_frame, False)
animate_fade_in(find_yv_text, current_frame, 15)
current_frame += 15

# Hide old vertex formula text
animate_fade_out(vertex_formula_text, current_frame, 10)
set_visibility(vertex_formula_text, current_frame + 10, False)
current_frame += 10

# 2:50 - 3:10: Substitute x = -3/4 into g(x) and calculate.
# Reset equation objects to original positions and visibility state
set_visibility(fx_box, current_frame, True)
set_visibility(fx_text, current_frame, True)
animate_text_content_change(fx_text, current_frame, "g(-3/4)") # Update g(x) to g(-3/4)

for obj in [c2, c2_txt, xsq_box, xsq_txt, op_plus1, c3, c3_txt, x_var_box, x_var_txt, op_plus2, c5, c5_txt]:
    set_visibility(obj, current_frame, True)

# Create -3/4 blocks for substitution
neg_3_4_sub1 = create_cube_object("ConstantBlock_Neg3_4_Sub1", 0.8, xsq_box.location, "MatConstantRed", collection_name="Scene4_Vertex_Calc")
neg_3_4_sub1_txt = create_text_object("ConstantText_Neg3_4_Sub1", "(-3/4)", 0.5, xsq_txt.location, "MatProblemTitle", collection_name="Scene4_Vertex_Calc")
neg_3_4_sub1_txt.parent = neg_3_4_sub1

neg_3_4_sub2 = create_cube_object("ConstantBlock_Neg3_4_Sub2", 0.8, x_var_box.location, "MatConstantRed", collection_name="Scene4_Vertex_Calc")
neg_3_4_sub2_txt = create_text_object("ConstantText_Neg3_4_Sub2", "(-3/4)", 0.5, x_var_txt.location, "MatProblemTitle", collection_name="Scene4_Vertex_Calc")
neg_3_4_sub2_txt.parent = neg_3_4_sub2

# Parent to equation_parent for relative movement
neg_3_4_sub1.parent = equation_parent
neg_3_4_sub1_txt.parent = equation_parent
neg_3_4_sub2.parent = equation_parent
neg_3_4_sub2_txt.parent = equation_parent

# Hide original X, X^2 and show -3/4s
set_visibility(xsq_box, current_frame, False)
set_visibility(xsq_txt, current_frame, False)
set_visibility(x_var_box, current_frame, False)
set_visibility(x_var_txt, current_frame, False)

set_visibility(neg_3_4_sub1, current_frame, True)
set_visibility(neg_3_4_sub1_txt, current_frame, True)
set_visibility(neg_3_4_sub2, current_frame, True)
set_visibility(neg_3_4_sub2_txt, current_frame, True)
current_frame += 15 # Time for substitution

# Calculations: 2(-3/4)² -> 9/8, 3(-3/4) -> -9/4
# 2(-3/4)² -> 2(9/16) -> 18/16 -> 9/8
calc_loc_x1 = (c2.location.x + 0.5, c2.location.y, c2.location.z)
for obj in [c2, c2_txt, neg_3_4_sub1, neg_3_4_sub1_txt]:
    animate_fade_out(obj, current_frame, 10)
    set_visibility(obj, current_frame + 10, False)
res_9_8 = create_text_object("Result_9_8", "9/8", 0.5, calc_loc_x1, "MatConstantDefault", collection_name="Scene4_Vertex_Calc")
res_9_8.parent = equation_parent
set_visibility(res_9_8, current_frame, False)
animate_fade_in(res_9_8, current_frame, 10)
current_frame += 10

# 3(-3/4) -> -9/4
calc_loc_x2 = (c3.location.x + 0.5, c3.location.y, c3.location.z)
for obj in [c3, c3_txt, neg_3_4_sub2, neg_3_4_sub2_txt]:
    animate_fade_out(obj, current_frame, 10)
    set_visibility(obj, current_frame + 10, False)
res_neg_9_4 = create_text_object("Result_Neg9_4", "-9/4", 0.5, calc_loc_x2, "MatConstantRed", collection_name="Scene4_Vertex_Calc")
res_neg_9_4.parent = equation_parent
set_visibility(res_neg_9_4, current_frame, False)
animate_fade_in(res_neg_9_4, current_frame, 10)
current_frame += 10

# g(-3/4) = 9/8 - 9/4 + 5
animate_text_content_change(fx_text, current_frame, "g(-3/4)")
animate_slide(op_plus1, current_frame, 10, op_plus1.location, (res_9_8.location.x + 1, op_plus1.location.y, op_plus1.location.z))
op_minus_new = create_text_object("Op_Minus_New", "-", 0.8, op_plus1.location, "MatOperationSymbol", collection_name="Scene4_Vertex_Calc")
op_minus_new.parent = equation_parent
set_visibility(op_minus_new, current_frame, False)
animate_fade_in(op_minus_new, current_frame, 10)
animate_fade_out(op_plus1, current_frame, 10) # Replace + with -
set_visibility(op_plus1, current_frame + 10, False) # Hide original +

animate_slide(res_neg_9_4, current_frame, 10, res_neg_9_4.location, (res_9_8.location.x + 2, res_neg_9_4.location.y, res_neg_9_4.location.z))
animate_slide(op_plus2, current_frame, 10, op_plus2.location, (res_9_8.location.x + 3, op_plus2.location.y, op_plus2.location.z))
animate_slide(c5, current_frame, 10, c5.location, (res_9_8.location.x + 4, c5.location.y, c5.location.z))
animate_slide(c5_txt, current_frame, 10, c5_txt.location, (res_9_8.location.x + 4, c5_txt.location.y, c5_txt.location.z))
current_frame += 10

# Find common denominator: 9/8 - 18/8 + 40/8
res_18_8 = create_text_object("Result_18_8", "18/8", 0.5, res_neg_9_4.location, "MatConstantRed", collection_name="Scene4_Vertex_Calc")
res_18_8.parent = equation_parent
set_visibility(res_18_8, current_frame, False)
animate_fade_in(res_18_8, current_frame, 10)
animate_fade_out(res_neg_9_4, current_frame, 10)
set_visibility(res_neg_9_4, current_frame + 10, False)

res_40_8 = create_text_object("Result_40_8", "40/8", 0.5, c5.location, "MatConstantGreen", collection_name="Scene4_Vertex_Calc")
res_40_8.parent = equation_parent
set_visibility(res_40_8, current_frame, False)
animate_fade_in(res_40_8, current_frame, 10)
animate_fade_out(c5, current_frame, 10)
animate_fade_out(c5_txt, current_frame, 10)
set_visibility(c5, current_frame + 10, False)
set_visibility(c5_txt, current_frame + 10, False)
current_frame += 10

# Combine (9 - 18 + 40) / 8 -> 31/8
animate_fade_out(res_9_8, current_frame, 10)
animate_fade_out(op_minus_new, current_frame, 10)
animate_fade_out(res_18_8, current_frame, 10)
animate_fade_out(op_plus2, current_frame, 10)
animate_fade_out(res_40_8, current_frame, 10)

for obj in [res_9_8, op_minus_new, res_18_8, op_plus2, res_40_8]:
    set_visibility(obj, current_frame + 10, False)

res_31_8 = create_text_object("Result_31_8", "31/8", 0.8, (equation_group_target.x + 2, equation_group_target.y, equation_group_target.z + 0.5), "MatSolutionText", collection_name="Scene4_Vertex_Calc")
res_31_8.parent = equation_parent # Parent to move with equation group
set_visibility(res_31_8, current_frame, False)
animate_fade_in(res_31_8, current_frame, 10)
animate_text_content_change(fx_text, current_frame, "g(-3/4) = 31/8")
current_frame += 10

# 3:10 - 3:20: PointMarker(-3/4, 31/8) snaps to lowest point. Text "Vertex: (-3/4, 31/8)"
# Note: Parabola is at (0,0,0) with vertex roughly at (-0.75, 3.875, 0)
vertex_x_coord = -3/4
vertex_y_coord = 31/8 # 3.875

vertex_point = create_sphere_object("PointMarker_Vertex", 0.2, (vertex_x_coord, vertex_y_coord, 0.1), "MatPointMarker", collection_name="Scene4_Vertex_Graph")
set_visibility(vertex_point, current_frame, False)
animate_fade_in(vertex_point, current_frame, 5)
animate_glow(vertex_point, current_frame, 5, final_strength=15.0) # Flash
animate_unglow(vertex_point, current_frame + 5, 5, final_strength=5.0) # Settle glow
current_frame += 5

vertex_coords_text = create_text_object("Text_VertexCoords", "Vertex: (-3/4, 31/8)", 0.6, (vertex_x_coord + 1.5, vertex_y_coord, 0.5), "MatSolutionText", collection_name="Scene4_Vertex_Graph")
set_visibility(vertex_coords_text, current_frame, False)
animate_fade_in(vertex_coords_text, current_frame, 10)
current_frame += 10
print(f"--- Scene 4 End. Current Frame: {current_frame} ---")


# --- Scene 5: Interpretation 4 - Domain and Range (3:20 - 3:50) ---
print(f"--- Scene 5: Domain & Range (3:20 - 3:50) --- Start Frame: {current_frame}")
# Hide Scene 4 elements not needed
set_visibility(vertex_bubble, current_frame, False)
set_visibility(find_yv_text, current_frame, False)
set_visibility(res_31_8, current_frame, False)
# Also hide equation elements (temporarily)
for obj in all_equation_elements:
    set_visibility(obj, current_frame, False)
set_visibility(equation_parent, current_frame, False)
for obj in bpy.data.collections.get("Scene4_Vertex_Calc").objects:
    set_visibility(obj, current_frame, False)


# 3:20 - 3:25: ThoughtBubble(4). GraphPlane with ParabolaArc and VertexPoint.
domain_range_bubble = thought_bubble_objs[3] # "Analyze?" (actually "Domain & Range")
animate_slide(domain_range_bubble, current_frame, 2*FPS, domain_range_bubble.location, (-6, 7, 0.5))
animate_scale(domain_range_bubble, current_frame, 2*FPS, 0.1, 1.0)
set_visibility(domain_range_bubble, current_frame, True)
animate_fade_in(domain_range_bubble, current_frame, 2*FPS, initial_alpha=0.6)
current_frame += 2*FPS

set_visibility(graph_plane_eval, current_frame, True) # Re-use graph plane
animate_fade_in(graph_plane_eval, current_frame, 15)
set_visibility(parabola_arc, current_frame, True)
animate_fade_in(parabola_arc, current_frame, 15)
set_visibility(vertex_point, current_frame, True)
animate_fade_in(vertex_point, current_frame, 15)
set_visibility(vertex_coords_text, current_frame, True)
animate_fade_in(vertex_coords_text, current_frame, 15)
current_frame += 15

# 3:25 - 3:35: Domain
domain_text_title = create_text_object("Text_DomainTitle", "Domain: All Real Numbers", 0.7, (0, -2, 0.5), "MatProblemTitle", collection_name="Scene5_DomainRange")
set_visibility(domain_text_title, current_frame, False)
animate_fade_in(domain_text_title, current_frame, 15)
current_frame += 15

# X-axis highlights and stretches
# For X-axis highlight, duplicate the axis line, make it emissive, and scale it
x_axis_highlight = create_cylinder_object("X_Axis_Highlight", 0.08, 12, (0, 0, 0.05), "MatAxisHighlight", collection_name="Scene5_DomainRange")
x_axis_highlight.rotation_euler = Euler((0, math.radians(90), 0))
x_axis_highlight.scale = (1, 1, 1) # Initial scale
set_visibility(x_axis_highlight, current_frame, False)
animate_fade_in(x_axis_highlight, current_frame, 10)
animate_scale(x_axis_highlight, current_frame, 30, 1.0, 1.5) # Stretch
current_frame += 30

domain_notation = create_text_object("DomainNotation", "(-∞, ∞)", 0.7, (0, -4, 0.5), "MatSolutionText", collection_name="Scene5_DomainRange")
set_visibility(domain_notation, current_frame, False)
animate_fade_in(domain_notation, current_frame, 15)
current_frame += 15

# 3:35 - 3:45: Range
animate_fade_out(domain_text_title, current_frame, 10)
animate_fade_out(domain_notation, current_frame, 10)
animate_fade_out(x_axis_highlight, current_frame, 10) # Fade out x-axis highlight
set_visibility(domain_text_title, current_frame + 10, False)
set_visibility(domain_notation, current_frame + 10, False)
set_visibility(x_axis_highlight, current_frame + 10, False)
current_frame += 10

range_text_title = create_text_object("Text_RangeTitle", "Range: y ≥ 31/8", 0.7, (0, -2, 0.5), "MatProblemTitle", collection_name="Scene5_DomainRange")
set_visibility(range_text_title, current_frame, False)
animate_fade_in(range_text_title, current_frame, 15)
current_frame += 15

# Y-axis highlights and stretches upwards from vertex
y_axis_highlight = create_cylinder_object("Y_Axis_Highlight", 0.08, 12, (0, 0, 0.05), "MatAxisHighlight", collection_name="Scene5_DomainRange")
y_axis_highlight.rotation_euler = Euler((math.radians(90), 0, 0)) # Rotate to be vertical
y_axis_highlight.location = (vertex_x_coord, vertex_y_coord + (12/2), 0.05) # Center top of y-axis segment
y_axis_highlight.scale = (1, 1, 0.01) # Initial scale (very short)
set_visibility(y_axis_highlight, current_frame, False)
animate_fade_in(y_axis_highlight, current_frame, 10)
animate_scale(y_axis_highlight, current_frame, 30, 0.01, 1.0) # Grow vertically (Y-scale becomes Z-scale due to rotation)
current_frame += 30

range_notation = create_text_object("RangeNotation", "[31/8, ∞)", 0.7, (0, -4, 0.5), "MatSolutionText", collection_name="Scene5_DomainRange")
set_visibility(range_notation, current_frame, False)
animate_fade_in(range_notation, current_frame, 15)
current_frame += 15

# 3:45 - 3:50: GraphPlane and ParabolaArc smoothly fade out.
animate_fade_out(graph_plane_eval, current_frame, 15)
animate_fade_out(parabola_arc, current_frame, 15)
animate_fade_out(vertex_point, current_frame, 15)
animate_fade_out(vertex_coords_text, current_frame, 15)
animate_fade_out(range_text_title, current_frame, 15)
animate_fade_out(range_notation, current_frame, 15)
animate_fade_out(y_axis_highlight, current_frame, 15)

set_visibility(graph_plane_eval, current_frame + 15, False)
set_visibility(parabola_arc, current_frame + 15, False)
set_visibility(vertex_point, current_frame + 15, False)
set_visibility(vertex_coords_text, current_frame + 15, False)
set_visibility(range_text_title, current_frame + 15, False)
set_visibility(range_notation, current_frame + 15, False)
set_visibility(y_axis_highlight, current_frame + 15, False)
current_frame += 15
print(f"--- Scene 5 End. Current Frame: {current_frame} ---")

# --- Scene 6: Summary and Conclusion (3:50 - 4:00) ---
print(f"--- Scene 6: Summary (3:50 - 4:00) --- Start Frame: {current_frame} ---")
# Hide domain range bubble
set_visibility(domain_range_bubble, current_frame, False)

# 3:50 - 3:55: Summary Title Card
summary_title = create_text_object("SummaryTitleCard", "Summary", 1.2, (0, 7, 0.5), "MatProblemTitle", collection_name="Scene6_Summary")
set_visibility(summary_title, current_frame, False)
animate_fade_in(summary_title, current_frame, 15)
current_frame += 15

# 3:55 - 4:00: Key findings as bullet points
flash_duration = 10

# Note: We will re-show/re-hide existing objects for flash effect.
# Ensure they are currently hidden.
# Also ensure they are in a collection that is not set to permanently hidden.
# Let's ensure these objects are initially created in a general "FlashAssets" collection
# so they can be re-used, and then hide them after each scene's use.
flash_assets_collection = add_to_collection(bpy.data.objects.new("FlashAssetPlaceholder",None), "FlashAssets")
bpy.context.scene.collection.objects.unlink(flash_assets_collection.objects[0]) # Remove the placeholder

# Move key assets to FlashAssets collection if they aren't already there
# This is crucial for their visibility management later
for obj in [q_formula_sheet, parabola_arc, vertex_point, point_0_5, graph_plane_eval, x_axis_highlight, y_axis_highlight]:
    # Unlink from its original scene collection
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    # Link to the FlashAssets collection
    flash_assets_collection.objects.link(obj)

bullet_points_data = [
    ("If g(x)=0: No Real Solutions (Complex roots)", (0, 4, 0.5), q_formula_sheet), 
    ("Vertex: (-3/4, 31/8)", (0, 2, 0.5), vertex_point),
    ("Y-intercept: (0, 5)", (0, 0, 0.5), point_0_5),
    ("Domain: (-∞, ∞)", (0, -2, 0.5), x_axis_highlight),
    ("Range: [31/8, ∞)", (0, -4, 0.5), y_axis_highlight)
]

for i, (text, loc, flash_obj_ref) in enumerate(bullet_points_data):
    bp_text = create_text_object(f"SummaryBullet_{i}", text, 0.6, loc, "MatSolutionText", collection_name="Scene6_Summary")
    set_visibility(bp_text, current_frame, False)
    animate_fade_in(bp_text, current_frame, 15)
    
    # Brief flash of corresponding visual asset
    if flash_obj_ref:
        set_visibility(flash_obj_ref, current_frame + 15, True)
        animate_glow(flash_obj_ref, current_frame + 15, flash_duration, final_strength=10.0)
        animate_fade_in(flash_obj_ref, current_frame + 15, 1) # Ensure visible (in case it was hidden)
        
        # Ensure the underlying visuals for the flash are reset to their visible state before glowing
        if flash_obj_ref == q_formula_sheet:
            set_visibility(q_formula_text, current_frame + 15, True) # Show text on sheet
            set_visibility(i_symbol, current_frame + 15, True)
            set_visibility(plus_minus_highlight, current_frame + 15, True)

        if flash_obj_ref == x_axis_highlight:
            # Need to ensure the graph plane is visible for x-axis highlight
            set_visibility(graph_plane_eval, current_frame + 15, True)
            animate_fade_in(graph_plane_eval, current_frame + 15, 1)

        if flash_obj_ref == y_axis_highlight:
            # Need to ensure the graph plane is visible for y-axis highlight
            set_visibility(graph_plane_eval, current_frame + 15, True)
            animate_fade_in(graph_plane_eval, current_frame + 15, 1)
            set_visibility(parabola_arc, current_frame + 15, True)
            set_visibility(vertex_point, current_frame + 15, True)
            set_visibility(vertex_coords_text, current_frame + 15, True)


        # Hide after flash
        animate_unglow(flash_obj_ref, current_frame + 15 + flash_duration, 1)
        set_visibility(flash_obj_ref, current_frame + 15 + flash_duration + 1, False)

        # Hide associated elements as well
        if flash_obj_ref == q_formula_sheet:
            set_visibility(q_formula_text, current_frame + 15 + flash_duration + 1, False)
            set_visibility(i_symbol, current_frame + 15 + flash_duration + 1, False)
            set_visibility(plus_minus_highlight, current_frame + 15 + flash_duration + 1, False)
        if flash_obj_ref == x_axis_highlight or flash_obj_ref == y_axis_highlight:
            set_visibility(graph_plane_eval, current_frame + 15 + flash_duration + 1, False)
        if flash_obj_ref == y_axis_highlight:
            set_visibility(parabola_arc, current_frame + 15 + flash_duration + 1, False)
            set_visibility(vertex_point, current_frame + 15 + flash_duration + 1, False)
            set_visibility(vertex_coords_text, current_frame + 15 + flash_duration + 1, False)

    current_frame += 20 # Spacing between bullets

current_frame += 20 # Final pause after last bullet

# 4:00: Fade to black
bpy.context.scene.frame_end = current_frame

# Ensure objects start hidden if they are meant to fade in
# Go through all collections and set initial visibility for the first frame
for collection in bpy.data.collections:
    if collection.name.startswith("Scene"): 
        for obj in collection.objects:
            # Check if the object is *not* meant to be visible from frame 0
            # If an object is not already explicitly keyframed as visible at frame 0,
            # then ensure it is hidden at frame 0.
            if not obj.animation_data or not any(kp.co[0] == 0 and kp.data_path.startswith('hide_') for fc in obj.animation_data.action.fcurves for kp in fc.keyframe_points):
                 set_visibility(obj, 0, False)

print(f"--- Animation Script Complete --- Final Frame: {current_frame}")
```