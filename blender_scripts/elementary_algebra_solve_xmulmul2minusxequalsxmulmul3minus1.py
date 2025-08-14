import bpy
import math
import mathutils

# --- Global Settings ---
FPS = 24
DURATION_SECONDS = 60
TOTAL_FRAMES = DURATION_SECONDS * FPS
bpy.context.scene.frame_end = TOTAL_FRAMES
bpy.context.scene.render.fps = FPS

# Set Render Engine
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.film_transparent = False # Keep background for classroom elements

# Eevee specific settings for better glow
bpy.context.scene.eevee.use_bloom = True
bpy.context.scene.eevee.bloom_threshold = 0.5
bpy.context.scene.eevee.bloom_intensity = 0.05
bpy.context.scene.eevee.bloom_radius = 6.0

# --- Helper Functions for Scene Management ---
def clear_scene():
    """Clears all objects, collections, materials, meshes, and lights."""
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Delete all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Delete all collections except the master scene collection
    for collection in bpy.data.collections:
        if collection.name != "Scene Collection": # Don't delete the root
            bpy.data.collections.remove(collection)

    # Delete all materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)

    # Delete all meshes
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    # Delete all curves (for text)
    for curve in bpy.data.curves:
        bpy.data.curves.remove(curve)

    # Delete all lights
    for light in bpy.data.lights:
        bpy.data.lights.remove(light)

def get_or_create_collection(name, parent_collection=None):
    """Gets an existing collection or creates a new one."""
    if name not in bpy.data.collections:
        new_collection = bpy.data.collections.new(name)
        if parent_collection:
            parent_collection.children.link(new_collection)
        else:
            bpy.context.scene.collection.children.link(new_collection)
    return bpy.data.collections[name]

def add_object_to_collection(obj, collection):
    """Adds an object to a specified collection and removes it from the default."""
    # Ensure the object is not linked to the scene's default collection
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    collection.objects.link(obj)

# --- Material Definitions ---
materials = {}

def create_material(name, color, emission_color=(0,0,0,1), emission_strength=0, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.4
    bsdf.inputs["Metallic"].default_value = 0.1

    if emission_strength > 0:
        bsdf.inputs["Emission"].default_value = emission_color
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    if alpha < 1.0:
        mat.blend_method = 'BLEND'
        bsdf.inputs["Alpha"].default_value = alpha

    materials[name] = mat
    return mat

def setup_materials():
    create_material("WhiteboardMat", (0.95, 0.95, 0.95, 1.0), emission_strength=0) # Base whiteboard material
    create_material("WhiteboardGridMat", (0.8, 0.8, 0.8, 1.0), emission_strength=0) # For grid lines
    create_material("VariableX2Mat", (0.9, 0.1, 0.1, 1.0), emission_strength=0) # Red
    create_material("VariableXMat", (0.1, 0.1, 0.9, 1.0), emission_strength=0) # Blue
    create_material("VariableX3Mat", (0.1, 0.9, 0.1, 0.7), emission_strength=0, alpha=0.7) # Translucent Green
    create_material("ConstantMat", (0.9, 0.9, 0.9, 1.0), emission_strength=0) # White
    create_material("ZeroMat", (0.6, 0.6, 0.6, 0.5), emission_strength=0, alpha=0.5) # Transparent Grey
    create_material("EqBarMat", (1.0, 1.0, 1.0, 1.0), emission_color=(1,1,1,1), emission_strength=1.0) # Glowing White
    create_material("ParenthesesMat", (0.5, 0.5, 0.5, 0.7), emission_strength=0, alpha=0.7) # Semi-transparent Grey
    create_material("ImaginaryUnitMat", (0.6, 0.1, 0.9, 1.0), emission_color=(0.6, 0.1, 0.9, 1.0), emission_strength=0.5) # Purple Aura
    create_material("PlusMinusMat", (1.0, 1.0, 1.0, 1.0), emission_color=(1,1,1,1), emission_strength=1.0) # Glowing White
    create_material("SquareRootMat", (0.1, 0.9, 0.1, 1.0), emission_color=(0.1, 0.9, 0.1, 1.0), emission_strength=1.0) # Lime Green
    create_material("TextMat", (0.9, 0.9, 0.9, 1.0), emission_strength=0) # White Text
    create_material("TitleTextMat", (0.9, 0.9, 0.9, 1.0), emission_strength=0) # White Text
    create_material("OpArrowPlusMat", (0.0, 0.8, 0.8, 1.0), emission_color=(0.0, 0.8, 0.8, 1.0), emission_strength=1.0) # Cyan
    create_material("OpArrowMinusMat", (0.8, 0.0, 0.8, 1.0), emission_color=(0.8, 0.0, 0.8, 1.0), emission_strength=1.0) # Magenta
    create_material("OpArrowFactorMat", (0.1, 0.9, 0.1, 1.0), emission_color=(0.1, 0.9, 0.1, 1.0), emission_strength=1.0) # Pulsing Green
    create_material("BackgroundMat", (0.1, 0.1, 0.2, 1.0), emission_strength=0) # Dark blue for classroom blur
    create_material("BlackFadeMat", (0.0, 0.0, 0.0, 1.0), alpha=0.0) # For fading to black

    # Create glowing versions of materials for pulsing effect
    for name, mat in list(materials.items()):
        if "Mat" in name and "Arrow" not in name and "Bar" not in name and "PlusMinus" not in name and "Root" not in name and "Fade" not in name:
            glow_mat_name = name.replace("Mat", "GlowMat")
            base_color = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
            glow_mat = create_material(glow_mat_name, base_color,
                                        emission_color=base_color,
                                        emission_strength=3.0, alpha=mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value)
            materials[glow_mat_name] = glow_mat

# --- Object Creation Functions ---

def create_text_object(text_string, name, location=(0,0,0), size=0.5, depth=0.02, parent_to=None, material=None, align_x='CENTER', align_y='CENTER'):
    font_curve = bpy.data.curves.new(type="FONT", name=f"{name}_Curve")
    font_curve.body = text_string
    font_curve.size = size
    font_curve.extrude = depth
    font_curve.align_x = align_x
    font_curve.align_y = align_y

    obj = bpy.data.objects.new(name, font_curve)
    obj.location = location
    if material:
        obj.data.materials.append(material)

    if parent_to:
        obj.parent = parent_to
        obj.matrix_parent_inverse = parent_to.matrix_world.inverted()

    bpy.context.collection.objects.link(obj)
    return obj

def create_cube(name, size, location, material):
    bpy.ops.mesh.primitive_cube_add(size=size, enter_editmode=False, align='WORLD', location=location)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj

def create_plane(name, size, location, material):
    bpy.ops.mesh.primitive_plane_add(size=size, enter_editmode=False, align='WORLD', location=location)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj

def create_variable_box(name, char, exponent=None, box_type='cube', size=1.0, location=(0,0,0), material=None, text_material=None):
    if box_type == 'cube':
        main_obj = create_cube(f"{name}_Box", size=size, location=location, material=material)
    elif box_type == 'plane':
        main_obj = create_plane(f"{name}_Box", size=size, location=location, material=material)
    else: # Default to cube if unknown type
        main_obj = create_cube(f"{name}_Box", size=size, location=location, material=material)

    # Position text slightly in front for better visibility from angle
    text_loc = (0, 0.01, 0) 
    char_obj = create_text_object(char, f"{name}_Char", location=text_loc, size=size*0.7, depth=0.01, parent_to=main_obj, material=text_material)

    if exponent:
        exp_obj = create_text_object(f"^{exponent}", f"{name}_Exp", location=(text_loc[0] + size*0.3, text_loc[1] + 0.01, text_loc[2] + size*0.3),
                                     size=size*0.3, depth=0.01, parent_to=main_obj, material=text_material)
        return main_obj, char_obj, exp_obj
    return main_obj, char_obj

def create_constant_block(name, value, size=1.0, location=(0,0,0), material=None, text_material=None):
    main_obj = create_cube(f"{name}_Block", size=size, location=location, material=material)
    text_loc = (0, 0.01, 0)
    text_obj = create_text_object(str(value), f"{name}_Text", location=text_loc, size=size*0.7, depth=0.01, parent_to=main_obj, material=text_material)
    return main_obj, text_obj

def create_zero_block(name, size=1.0, location=(0,0,0), material=None, text_material=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size/2, enter_editmode=False, align='WORLD', location=location)
    main_obj = bpy.context.active_object
    main_obj.name = name
    if material:
        main_obj.data.materials.append(material)
    text_loc = (0, 0.01, 0)
    text_obj = create_text_object("0", f"{name}_Text", location=text_loc, size=size*0.7, depth=0.01, parent_to=main_obj, material=text_material)
    return main_obj, text_obj

def create_equals_bar(name, length=2.0, thickness=0.1, location=(0,0,0), material=None):
    # Parent to an empty to control as one unit
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    empty_obj = bpy.context.active_object
    empty_obj.name = name

    eq_bar1 = create_cube(f"{name}_Top", size=1, location=(0, thickness*2, 0), material=material)
    eq_bar1.scale = (length/2, thickness/2, thickness/2) # Scale of a 1x1x1 cube
    eq_bar1.parent = empty_obj
    eq_bar1.matrix_parent_inverse = empty_obj.matrix_world.inverted()

    eq_bar2 = create_cube(f"{name}_Bottom", size=1, location=(0, -thickness*2, 0), material=material)
    eq_bar2.scale = (length/2, thickness/2, thickness/2)
    eq_bar2.parent = empty_obj
    eq_bar2.matrix_parent_inverse = empty_obj.matrix_world.inverted()
    
    return empty_obj, eq_bar1, eq_bar2

def create_operation_arrow(name, symbol, material, location, rotation_euler=(0,0,0), scale=(1,1,1)):
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=0.4, location=(0,0,0.2))
    cone = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0,0,-0.3))
    cyl = bpy.context.active_object

    bpy.ops.object.select_all(action='DESELECT')
    cyl.select_set(True)
    cone.select_set(True)
    bpy.context.view_layer.objects.active = cone
    bpy.ops.object.join()

    arrow_obj = bpy.context.active_object
    arrow_obj.name = name + "_Arrow"
    arrow_obj.location = location
    arrow_obj.rotation_euler = rotation_euler
    arrow_obj.scale = scale
    arrow_obj.data.materials.append(material)

    symbol_obj = create_text_object(symbol, f"{name}_Symbol", location=(0,0.01,0), size=0.3, depth=0.01, parent_to=arrow_obj, material=materials["TextMat"])
    return arrow_obj, symbol_obj

def create_parentheses(name, height=2.0, thickness=0.1, location=(0,0,0), material=None):
    # Create left parenthesis (approximated with a Bezier curve)
    curve_data = bpy.data.curves.new(name=f"{name}_LeftCurve", type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(2) # 3 points: top, middle, bottom

    spline.bezier_points[0].co = (0, 0, height/2)
    spline.bezier_points[0].handle_left_type = 'VECTOR'
    spline.bezier_points[0].handle_right = (-thickness*2, 0, height/2)
    spline.bezier_points[0].handle_right_type = 'FREE'

    spline.bezier_points[1].co = (-thickness, 0, 0)
    spline.bezier_points[1].handle_left = (-thickness, 0, 0.5 * height)
    spline.bezier_points[1].handle_left_type = 'FREE'
    spline.bezier_points[1].handle_right = (-thickness, 0, -0.5 * height)
    spline.bezier_points[1].handle_right_type = 'FREE'

    spline.bezier_points[2].co = (0, 0, -height/2)
    spline.bezier_points[2].handle_left_type = 'VECTOR'
    spline.bezier_points[2].handle_left = (-thickness*2, 0, -height/2)
    spline.bezier_points[2].handle_left_type = 'FREE'

    curve_data.resolution_u = 10
    curve_data.fill_mode = 'FULL'
    curve_data.extrude = thickness * 0.5 # Make it a 3D object

    obj_left = bpy.data.objects.new(f"{name}_Left", curve_data)
    bpy.context.collection.objects.link(obj_left)
    obj_left.data.materials.append(material)
    obj_left.location = location

    # Create right parenthesis by duplicating and mirroring
    obj_right = obj_left.copy()
    obj_right.data = obj_left.data.copy()
    obj_right.name = f"{name}_Right"
    bpy.context.collection.objects.link(obj_right)
    obj_right.location = (location[0] + 0.1, location[1], location[2]) # Initial position, will be adjusted
    obj_right.scale.x = -1 # Mirror

    return obj_left, obj_right

def create_square_root_symbol(name, length=2.0, height=1.0, thickness=0.1, location=(0,0,0), material=None):
    curve_data = bpy.data.curves.new(name=f"{name}_Curve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.fill_mode = 'FULL'
    curve_data.extrude = thickness / 2

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(3) # 4 points total

    # Points for a radical symbol shape
    spline.bezier_points[0].co = (0, 0, -height/2)
    spline.bezier_points[0].handle_left_type = 'VECTOR'
    spline.bezier_points[0].handle_right_type = 'VECTOR'

    spline.bezier_points[1].co = (0.2 * length, 0, -height/2)
    spline.bezier_points[1].handle_left_type = 'VECTOR'
    spline.bezier_points[1].handle_right_type = 'VECTOR'

    spline.bezier_points[2].co = (0.3 * length, 0, height/2)
    spline.bezier_points[2].handle_left_type = 'VECTOR'
    spline.bezier_points[2].handle_right_type = 'VECTOR'

    spline.bezier_points[3].co = (length, 0, height/2)
    spline.bezier_points[3].handle_left_type = 'VECTOR'
    spline.bezier_points[3].handle_right_type = 'VECTOR'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj.location = location
    
    return obj

# --- Animation Helpers ---
def animate_visibility(obj, start_frame, end_frame, hide_at_start=True, hide_at_end=False):
    # Set current hide state and keyframe
    obj.hide_render = hide_at_start
    obj.hide_viewport = hide_at_start
    obj.keyframe_insert(data_path="hide_render", frame=start_frame)
    obj.keyframe_insert(data_path="hide_viewport", frame=start_frame)

    # Set opposite hide state for next frame to create instant switch (show/hide)
    obj.hide_render = not hide_at_start
    obj.hide_viewport = not hide_at_start
    obj.keyframe_insert(data_path="hide_render", frame=start_frame + 1)
    obj.keyframe_insert(data_path="hide_viewport", frame=start_frame + 1)

    # Set final hide state at end_frame
    obj.hide_render = hide_at_end
    obj.hide_viewport = hide_at_end
    obj.keyframe_insert(data_path="hide_render", frame=end_frame)
    obj.keyframe_insert(data_path="hide_viewport", frame=end_frame)

def animate_fade(obj, start_frame, end_frame, start_alpha, end_alpha):
    # Assumes Principled BSDF with Alpha input
    if not obj.data.materials:
        print(f"Warning: Object {obj.name} has no materials for fade animation.")
        return

    mat = obj.data.materials[0]
    if mat and mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            mat.blend_method = 'BLEND' # Ensure transparency is enabled
            bsdf.inputs["Alpha"].default_value = start_alpha
            bsdf.inputs["Alpha"].keyframe_insert(data_path="default_value", frame=start_frame)

            bsdf.inputs["Alpha"].default_value = end_alpha
            bsdf.inputs["Alpha"].keyframe_insert(data_path="default_value", frame=end_frame)
            
            # Use hide_render for actual visibility toggle if fading to/from full transparency
            if end_alpha == 0.0:
                animate_visibility(obj, end_frame, end_frame + 1, hide_at_start=False, hide_at_end=True)
            elif start_alpha == 0.0:
                animate_visibility(obj, start_frame, start_frame + 1, hide_at_start=True, hide_at_end=False)


def animate_glow(obj, start_frame, peak_frame, end_frame, peak_strength=3.0, base_strength=0.0):
    if not obj.data.materials:
        print(f"Warning: Object {obj.name} has no materials for glow animation.")
        return

    mat = obj.data.materials[0]
    if mat and mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Start
            bsdf.inputs["Emission Strength"].default_value = base_strength
            bsdf.inputs["Emission Strength"].keyframe_insert(data_path="default_value", frame=start_frame)
            # Peak
            bsdf.inputs["Emission Strength"].default_value = peak_strength
            bsdf.inputs["Emission Strength"].keyframe_insert(data_path="default_value", frame=peak_frame)
            # End
            bsdf.inputs["Emission Strength"].default_value = base_strength
            bsdf.inputs["Emission Strength"].keyframe_insert(data_path="default_value", frame=end_frame)

def animate_slide(obj, start_frame, end_frame, start_loc, end_loc):
    obj.location = start_loc
    obj.keyframe_insert(data_path="location", frame=start_frame)
    obj.location = end_loc
    obj.keyframe_insert(data_path="location", frame=end_frame)

def animate_scale(obj, start_frame, end_frame, start_scale, end_scale):
    obj.scale = start_scale
    obj.keyframe_insert(data_path="scale", frame=start_frame)
    obj.scale = end_scale
    obj.keyframe_insert(data_path="scale", frame=end_frame)

# --- Main Scene Setup Function ---
def setup_scene():
    clear_scene()
    setup_materials()

    # Collections
    main_collection = get_or_create_collection("Animation_Elements")
    background_collection = get_or_create_collection("Background_Scene")
    camera_light_collection = get_or_create_collection("Camera_Lights")

    # --- Lighting ---
    # Sun light (directional for overall scene)
    sun_light_data = bpy.data.lights.new(name="Sun", type='SUN')
    sun_light_data.energy = 2.0
    sun_light_obj = bpy.data.objects.new(name="Sun", object_data=sun_light_data)
    add_object_to_collection(sun_light_obj, camera_light_collection)
    sun_light_obj.rotation_euler = (math.radians(-45), math.radians(-30), math.radians(60))

    # Area light for soft fill
    area_light_data = bpy.data.lights.new(name="AreaLight", type='AREA')
    area_light_data.energy = 200
    area_light_data.size = 5
    area_light_obj = bpy.data.objects.new(name="AreaLight", object_data=area_light_data)
    add_object_to_collection(area_light_obj, camera_light_collection)
    area_light_obj.location = (0, -10, 5)
    area_light_obj.rotation_euler = (math.radians(60), 0, 0)

    # --- Camera ---
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_obj = bpy.data.objects.new("MainCamera", cam_data)
    add_object_to_collection(cam_obj, camera_light_collection)
    bpy.context.scene.camera = cam_obj

    # Initial camera position (will be animated)
    cam_obj.location = (0, -20, 10)
    cam_obj.rotation_euler = (math.radians(50), 0, 0) # Look at origin

    # --- Whiteboard ---
    whiteboard_width = 15
    whiteboard_height = 8
    whiteboard_thickness = 0.2
    whiteboard_loc = (0, 0, 3) # Z to match camera angle

    # Whiteboard Plane
    whiteboard = create_plane("Whiteboard", size=1, location=whiteboard_loc, material=materials["WhiteboardMat"])
    whiteboard.scale = (whiteboard_width/2, whiteboard_height/2, 1) # Plane size is radius, so scale
    add_object_to_collection(whiteboard, main_collection)

    # Simple frame for whiteboard
    frame_thickness = 0.1
    frame_material = create_material("WhiteboardFrameMat", (0.2,0.2,0.2,1))
    frame_left = create_cube("WhiteboardFrameLeft", 1, (whiteboard_loc[0] - whiteboard_width/2 - frame_thickness/2, whiteboard_loc[1], whiteboard_loc[2]), frame_material)
    frame_left.scale = (frame_thickness, whiteboard_height + frame_thickness*2, whiteboard_thickness)
    frame_right = create_cube("WhiteboardFrameRight", 1, (whiteboard_loc[0] + whiteboard_width/2 + frame_thickness/2, whiteboard_loc[1], whiteboard_loc[2]), frame_material)
    frame_right.scale = (frame_thickness, whiteboard_height + frame_thickness*2, whiteboard_thickness)
    frame_top = create_cube("WhiteboardFrameTop", 1, (whiteboard_loc[0], whiteboard_loc[1] + whiteboard_height/2 + frame_thickness/2, whiteboard_loc[2]), frame_material)
    frame_top.scale = (whiteboard_width + frame_thickness*2, frame_thickness, whiteboard_thickness)
    frame_bottom = create_cube("WhiteboardFrameBottom", 1, (whiteboard_loc[0], whiteboard_loc[1] - whiteboard_height/2 - frame_thickness/2, whiteboard_loc[2]), frame_material)
    frame_bottom.scale = (whiteboard_width + frame_thickness*2, frame_thickness, whiteboard_thickness)
    add_object_to_collection(frame_left, main_collection)
    add_object_to_collection(frame_right, main_collection)
    add_object_to_collection(frame_top, main_collection)
    add_object_to_collection(frame_bottom, main_collection)

    # --- Classroom Scene (Minimalist & Blurred) ---
    desk_plane = create_plane("Desk", size=1, location=(0, -2, 0), material=materials["BackgroundMat"])
    desk_plane.scale = (10, 5, 1)
    add_object_to_collection(desk_plane, background_collection)

    back_wall = create_plane("BackWall", size=1, location=(0, 5, 5), material=materials["BackgroundMat"])
    back_wall.scale = (15, 8, 1)
    back_wall.rotation_euler = (math.radians(90), 0, 0)
    add_object_to_collection(back_wall, background_collection)

    # Set up depth of field for background blurring
    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = whiteboard # Focus on the whiteboard
    cam_data.dof.aperture_fstop = 2.8 # Adjust for desired blur

    return cam_obj, whiteboard, main_collection, background_collection, camera_light_collection

# --- Animation Sequences ---
def run_animation():
    current_frame = 0
    cam, wb, main_coll, bg_coll, cam_light_coll = setup_scene()

    # Set all objects in main_collection to hidden by default for controlled appearance
    for obj in main_coll.objects:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert(data_path="hide_render", frame=0)
        obj.keyframe_insert(data_path="hide_viewport", frame=0)

    # Make background elements, lights, and camera visible from start
    for obj in bg_coll.objects:
        obj.hide_render = False
        obj.hide_viewport = False
    for obj in cam_light_coll.objects:
        obj.hide_render = False
        obj.hide_viewport = False
    wb.hide_render = False
    wb.hide_viewport = False
    for obj in [wb] + list(wb.children): # Ensure frame is visible too
        obj.hide_render = False
        obj.hide_viewport = False


    # --- Scene 1: Introduction - Presenting the Problem (0-5 seconds) ---
    # Frames: 0 - 120
    start_frame = current_frame
    end_frame = start_frame + 120

    # Camera smoothly pans in
    cam_start_loc = cam.location
    cam_start_rot = cam.rotation_euler
    cam_end_loc = (0, -15, 7)
    cam_end_rot = (math.radians(45), 0, 0)

    animate_slide(cam, start_frame, start_frame + 60, cam_start_loc, cam_end_loc)
    cam.rotation_euler = cam_start_rot
    cam.keyframe_insert(data_path="rotation_euler", frame=start_frame)
    cam.rotation_euler = cam_end_rot
    cam.keyframe_insert(data_path="rotation_euler", frame=start_frame + 60)

    # Title "Solving Algebraic Equations"
    title_text = create_text_object("Solving Algebraic Equations", "Title",
                                    location=(0, 0.1, wb.location.z + wb.scale.y * 0.8),
                                    size=0.7, depth=0.05, material=materials["TitleTextMat"])
    add_object_to_collection(title_text, main_coll)
    animate_fade(title_text, start_frame + 30, start_frame + 60, 0.0, 1.0)
    
    # Equation elements
    # (x^2 - x) = (x^3 - 1)
    eq_start_z = wb.location.z + wb.scale.y * 0.4
    eq_y = 0.1 # Slight offset from board for depth
    obj_dist = 1.5 # Distance between objects

    # x^2
    x2_obj, _ = create_variable_box("X2", "x", "2", box_type='plane', size=1.0, location=(-obj_dist * 3, eq_y, eq_start_z), material=materials["VariableX2Mat"], text_material=materials["TextMat"])
    add_object_to_collection(x2_obj, main_coll)
    animate_slide(x2_obj, start_frame + 60, start_frame + 70, (x2_obj.location.x, eq_y, eq_start_z + 3), x2_obj.location)
    animate_fade(x2_obj, start_frame + 60, start_frame + 70, 0.0, 1.0)

    # - (minus)
    minus1_arrow, minus1_symbol = create_operation_arrow("Minus1", "-", materials["OpArrowMinusMat"], location=(-obj_dist * 2, eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    add_object_to_collection(minus1_arrow, main_coll)
    animate_fade(minus1_arrow, start_frame + 70, start_frame + 80, 0.0, 1.0)

    # x
    x1_obj, _ = create_variable_box("X1", "x", None, box_type='cube', size=0.8, location=(-obj_dist * 1, eq_y, eq_start_z), material=materials["VariableXMat"], text_material=materials["TextMat"])
    add_object_to_collection(x1_obj, main_coll)
    animate_slide(x1_obj, start_frame + 80, start_frame + 90, (x1_obj.location.x, eq_y, eq_start_z + 3), x1_obj.location)
    animate_fade(x1_obj, start_frame + 80, start_frame + 90, 0.0, 1.0)

    # = (equals)
    equals_obj, _, _ = create_equals_bar("Equals", length=1.5, location=(0, eq_y, eq_start_z), material=materials["EqBarMat"])
    add_object_to_collection(equals_obj, main_coll)
    animate_fade(equals_obj, start_frame + 90, start_frame + 100, 0.0, 1.0)

    # x^3
    x3_obj, _ = create_variable_box("X3", "x", "3", box_type='cube', size=1.2, location=(obj_dist * 1, eq_y, eq_start_z), material=materials["VariableX3Mat"], text_material=materials["TextMat"])
    add_object_to_collection(x3_obj, main_coll)
    animate_slide(x3_obj, start_frame + 100, start_frame + 110, (x3_obj.location.x, eq_y, eq_start_z + 3), x3_obj.location)
    animate_fade(x3_obj, start_frame + 100, start_frame + 110, 0.0, 1.0)

    # - (minus)
    minus2_arrow, minus2_symbol = create_operation_arrow("Minus2", "-", materials["OpArrowMinusMat"], location=(obj_dist * 2, eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    add_object_to_collection(minus2_arrow, main_coll)
    animate_fade(minus2_arrow, start_frame + 110, start_frame + 120, 0.0, 1.0)

    # 1 (constant)
    const1_obj, _ = create_constant_block("Const1", 1, size=0.7, location=(obj_dist * 3, eq_y, eq_start_z), material=materials["ConstantMat"], text_material=materials["TextMat"])
    add_object_to_collection(const1_obj, main_coll)
    animate_slide(const1_obj, start_frame + 110, start_frame + 120, (const1_obj.location.x, eq_y, eq_start_z + 3), const1_obj.location)
    animate_fade(const1_obj, start_frame + 110, start_frame + 120, 0.0, 1.0)

    current_frame = end_frame
    bpy.context.scene.frame_current = current_frame

    # --- Scene 2: Rearranging Terms to Zero (5-15 seconds) ---
    # Frames: 120 - 360
    start_frame = current_frame
    end_frame = start_frame + 240

    # Text "Step 1: Move all terms to one side."
    step1_text = create_text_object("Step 1: Move all terms to one side.", "Step1Text",
                                    location=(0, eq_y, eq_start_z - 1.5), size=0.5, depth=0.03, material=materials["TextMat"])
    add_object_to_collection(step1_text, main_coll)
    animate_fade(step1_text, start_frame + 10, start_frame + 20, 0.0, 1.0)

    # Highlight (x^2 - x)
    animate_glow(x2_obj, start_frame + 30, start_frame + 40, start_frame + 50, peak_strength=3.0)
    animate_glow(minus1_arrow, start_frame + 30, start_frame + 40, start_frame + 50, peak_strength=3.0)
    animate_glow(x1_obj, start_frame + 30, start_frame + 40, start_frame + 50, peak_strength=3.0)

    # Operation Arrow (-) representing "subtracting (x^2 - x)"
    op_minus_group_arrow, _ = create_operation_arrow("OpMinusGroupArrow", "-(x^2-x)", materials["OpArrowMinusMat"],
                                                    location=(-obj_dist * 2.5, eq_y, eq_start_z + 0.5), rotation_euler=(math.radians(90),math.radians(0),math.radians(90)), scale=(0.5,0.5,0.5))
    add_object_to_collection(op_minus_group_arrow, main_coll)
    animate_slide(op_minus_group_arrow, start_frame + 50, start_frame + 80,
                  op_minus_group_arrow.location, (obj_dist * 2.5, eq_y, eq_start_z + 0.5))
    animate_fade(op_minus_group_arrow, start_frame + 50, start_frame + 80, 0.0, 1.0)
    animate_fade(op_minus_group_arrow, start_frame + 80, start_frame + 90, 1.0, 0.0) # Fade out after arriving

    # Fade out left side, slide in new terms on right
    # -x^2
    animate_fade(x2_obj, start_frame + 80, start_frame + 90, 1.0, 0.0)
    new_minus_x2_obj, _ = create_variable_box("NewMinusX2", "-x", "2", box_type='plane', size=1.0,
                                              location=(x3_obj.location.x + obj_dist, eq_y, eq_start_z), # Position after x3
                                              material=materials["VariableX2Mat"], text_material=materials["TextMat"])
    add_object_to_collection(new_minus_x2_obj, main_coll)
    animate_slide(new_minus_x2_obj, start_frame + 85, start_frame + 95, (x3_obj.location.x + obj_dist, eq_y, eq_start_z + 3), new_minus_x2_obj.location)
    animate_fade(new_minus_x2_obj, start_frame + 85, start_frame + 95, 0.0, 1.0)

    # +x
    animate_fade(minus1_arrow, start_frame + 90, start_frame + 100, 1.0, 0.0)
    animate_fade(x1_obj, start_frame + 90, start_frame + 100, 1.0, 0.0)
    new_plus_x_obj, _ = create_variable_box("NewPlusX", "+x", None, box_type='cube', size=0.8,
                                            location=(x3_obj.location.x + obj_dist * 2, eq_y, eq_start_z), # Position after -x2
                                            material=materials["VariableXMat"], text_material=materials["TextMat"])
    add_object_to_collection(new_plus_x_obj, main_coll)
    animate_slide(new_plus_x_obj, start_frame + 95, start_frame + 105, (x3_obj.location.x + obj_dist * 2, eq_y, eq_start_z + 3), new_plus_x_obj.location)
    animate_fade(new_plus_x_obj, start_frame + 95, start_frame + 105, 0.0, 1.0)


    # EqualsBar shrinks, ZeroBlock appears on left
    animate_scale(equals_obj, start_frame + 110, start_frame + 120, equals_obj.scale, (0.5, equals_obj.scale.y, equals_obj.scale.z))
    zero_obj, _ = create_zero_block("Zero", size=0.7, location=(-obj_dist * 3, eq_y, eq_start_z), material=materials["ZeroMat"], text_material=materials["TextMat"])
    add_object_to_collection(zero_obj, main_coll)
    animate_fade(zero_obj, start_frame + 115, start_frame + 125, 0.0, 1.0)

    # Reorder terms on the right: x^3 - x^2 + x - 1
    # Current: x3_obj, minus2_arrow, const1_obj, new_minus_x2_obj, new_plus_x_obj
    # New order: x3_obj, new_minus_x2_obj, new_plus_x_obj, minus2_arrow (for -), const1_obj (for 1)

    # Re-create minus and plus signs for clarity and positioning
    # Fade out current minus2_arrow (from x^3 - 1)
    animate_fade(minus2_arrow, start_frame + 130, start_frame + 140, 1.0, 0.0)

    # Create new explicit minus and plus signs for reordered sequence
    # x^3 already there
    # -x^2
    new_minus_arrow_reorder, _ = create_operation_arrow("MinusReorder1", "-", materials["OpArrowMinusMat"], location=(x3_obj.location.x + obj_dist * 0.5, eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    add_object_to_collection(new_minus_arrow_reorder, main_coll)
    animate_fade(new_minus_arrow_reorder, start_frame + 140, start_frame + 150, 0.0, 1.0)

    # +x
    new_plus_arrow_reorder, _ = create_operation_arrow("PlusReorder1", "+", materials["OpArrowPlusMat"], location=(x3_obj.location.x + obj_dist * 1.5, eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    add_object_to_collection(new_plus_arrow_reorder, main_coll)
    animate_fade(new_plus_arrow_reorder, start_frame + 150, start_frame + 160, 0.0, 1.0)

    # -1
    new_minus_arrow_reorder2, _ = create_operation_arrow("MinusReorder2", "-", materials["OpArrowMinusMat"], location=(x3_obj.location.x + obj_dist * 2.5, eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    add_object_to_collection(new_minus_arrow_reorder2, main_coll)
    animate_fade(new_minus_arrow_reorder2, start_frame + 160, start_frame + 170, 0.0, 1.0)


    # Animate reordering of blocks
    reorder_start_frame = start_frame + 130
    reorder_end_frame = start_frame + 180

    # Define target positions for the reordered equation
    # x^3 - x^2 + x - 1 = 0
    # Pos: x^3, -x^2, +x, -1, =0
    new_x3_loc = (obj_dist * -2.5, eq_y, eq_start_z) # Move original x^3 left
    new_x2_loc = (obj_dist * -1.5, eq_y, eq_start_z)
    new_x_loc = (obj_dist * -0.5, eq_y, eq_start_z)
    new_const1_loc = (obj_dist * 0.5, eq_y, eq_start_z)
    new_minus_arrow_reorder1_loc = (obj_dist * -2.0, eq_y, eq_start_z)
    new_plus_arrow_reorder1_loc = (obj_dist * -1.0, eq_y, eq_start_z)
    new_minus_arrow_reorder2_loc = (obj_dist * 0.0, eq_y, eq_start_z)


    animate_slide(x3_obj, reorder_start_frame, reorder_end_frame, x3_obj.location, new_x3_loc)
    animate_slide(new_minus_x2_obj, reorder_start_frame, reorder_end_frame, new_minus_x2_obj.location, new_x2_loc)
    animate_slide(new_plus_x_obj, reorder_start_frame, reorder_end_frame, new_plus_x_obj.location, new_x_loc)
    animate_slide(const1_obj, reorder_start_frame, reorder_end_frame, const1_obj.location, new_const1_loc)

    # Adjust position of new arrows to align with reordered blocks
    animate_slide(new_minus_arrow_reorder, reorder_start_frame, reorder_end_frame, new_minus_arrow_reorder.location, new_minus_arrow_reorder1_loc)
    animate_slide(new_plus_arrow_reorder, reorder_start_frame, reorder_end_frame, new_plus_arrow_reorder.location, new_plus_arrow_reorder1_loc)
    animate_slide(new_minus_arrow_reorder2, reorder_start_frame, reorder_end_frame, new_minus_arrow_reorder2.location, new_minus_arrow_reorder2_loc)

    # Move equals sign and zero block to final position
    new_equals_loc = (obj_dist * 1.5, eq_y, eq_start_z)
    animate_slide(equals_obj, reorder_start_frame, reorder_end_frame, equals_obj.location, new_equals_loc)
    new_zero_loc = (obj_dist * 2.0, eq_y, eq_start_z)
    animate_slide(zero_obj, reorder_start_frame, reorder_end_frame, zero_obj.location, new_zero_loc)

    current_frame = end_frame
    bpy.context.scene.frame_current = current_frame

    # --- Scene 3: Factoring by Grouping - Part 1 (15-25 seconds) ---
    # Frames: 360 - 600
    start_frame = current_frame
    end_frame = start_frame + 240

    step2_text = create_text_object("Step 2: Factor the polynomial.", "Step2Text",
                                    location=(0, eq_y, eq_start_z - 1.5), size=0.5, depth=0.03, material=materials["TextMat"])
    add_object_to_collection(step2_text, main_coll)
    animate_fade(step1_text, start_frame + 10, start_frame + 20, 1.0, 0.0) # Fade out previous text
    animate_fade(step2_text, start_frame + 10, start_frame + 20, 0.0, 1.0) # Fade in new text

    # Parentheses animate to group (x^3 - x^2)
    group1_left_paren, group1_right_paren = create_parentheses("Group1Paren", height=2.0, thickness=0.1, material=materials["ParenthesesMat"])
    add_object_to_collection(group1_left_paren, main_coll)
    add_object_to_collection(group1_right_paren, main_coll)

    group1_start_loc_left = (-obj_dist * 3.5, eq_y, eq_start_z)
    group1_end_loc_left = (new_x3_loc[0] - 1.0, eq_y, eq_start_z)
    group1_start_loc_right = (new_x2_loc[0] + 1.0, eq_y, eq_start_z) # Original location
    group1_end_loc_right = (new_x2_loc[0] + 1.0, eq_y, eq_start_z) # No change needed

    group1_left_paren.location = group1_start_loc_left
    group1_right_paren.location = group1_start_loc_right
    animate_fade(group1_left_paren, start_frame + 30, start_frame + 40, 0.0, 1.0)
    animate_fade(group1_right_paren, start_frame + 30, start_frame + 40, 0.0, 1.0)
    animate_slide(group1_left_paren, start_frame + 40, start_frame + 50, group1_start_loc_left, group1_end_loc_left)
    # Right paren is already correctly positioned by default
    animate_glow(group1_left_paren, start_frame + 50, start_frame + 60, start_frame + 70, peak_strength=3.0)
    animate_glow(group1_right_paren, start_frame + 50, start_frame + 60, start_frame + 70, peak_strength=3.0)

    # x^2 highlights as common factor
    animate_glow(new_minus_x2_obj, start_frame + 70, start_frame + 80, start_frame + 90, peak_strength=3.0) # It's -x^2 now. We need the x^2 part to glow. This is conceptual.

    # Factor out x^2 (symbol flies out)
    factor_x2_arrow, factor_x2_symbol = create_operation_arrow("FactorX2Arrow", "x^2", materials["OpArrowFactorMat"],
                                                               location=(new_x3_loc[0], eq_y, eq_start_z + 1.5), rotation_euler=(math.radians(90),0,0), scale=(0.5,0.5,0.5))
    add_object_to_collection(factor_x2_arrow, main_coll)
    animate_slide(factor_x2_arrow, start_frame + 90, start_frame + 100, (new_x3_loc[0], eq_y, eq_start_z + 1.5), (new_x3_loc[0] - 2.0, eq_y, eq_start_z))
    animate_fade(factor_x2_arrow, start_frame + 90, start_frame + 100, 0.0, 1.0)

    # Visual "shedding" for (x - 1)
    # Hide original x^3 and -x^2
    animate_fade(x3_obj, start_frame + 100, start_frame + 110, 1.0, 0.0)
    animate_fade(new_minus_arrow_reorder, start_frame + 100, start_frame + 110, 1.0, 0.0)
    animate_fade(new_minus_x2_obj, start_frame + 100, start_frame + 110, 1.0, 0.0)

    # New (x - 1) group
    new_x_in_paren, _ = create_variable_box("XInParen1", "x", None, box_type='cube', size=0.8, location=(factor_x2_arrow.location.x + 1.0, eq_y, eq_start_z), material=materials["VariableXMat"], text_material=materials["TextMat"])
    new_minus_in_paren, _ = create_operation_arrow("MinusInParen1", "-", materials["OpArrowMinusMat"], location=(factor_x2_arrow.location.x + 2.0, eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    new_const1_in_paren, _ = create_constant_block("Const1InParen1", 1, size=0.7, location=(factor_x2_arrow.location.x + 3.0, eq_y, eq_start_z), material=materials["ConstantMat"], text_material=materials["TextMat"])
    
    add_object_to_collection(new_x_in_paren, main_coll)
    add_object_to_collection(new_minus_in_paren, main_coll)
    add_object_to_collection(new_const1_in_paren, main_coll)

    animate_fade(new_x_in_paren, start_frame + 110, start_frame + 120, 0.0, 1.0)
    animate_fade(new_minus_in_paren, start_frame + 110, start_frame + 120, 0.0, 1.0)
    animate_fade(new_const1_in_paren, start_frame + 110, start_frame + 120, 0.0, 1.0)

    # Parentheses for x^2(x-1)
    x2_group_left_paren, x2_group_right_paren = create_parentheses("X2GroupParen", height=1.5, thickness=0.08, material=materials["ParenthesesMat"])
    add_object_to_collection(x2_group_left_paren, main_coll)
    add_object_to_collection(x2_group_right_paren, main_coll)

    x2_group_left_paren.location = (factor_x2_arrow.location.x + 0.5, eq_y, eq_start_z)
    x2_group_right_paren.location = (factor_x2_arrow.location.x + 3.5, eq_y, eq_start_z)
    animate_fade(x2_group_left_paren, start_frame + 120, start_frame + 130, 0.0, 1.0)
    animate_fade(x2_group_right_paren, start_frame + 120, start_frame + 130, 0.0, 1.0)

    # + lights up
    animate_glow(new_plus_arrow_reorder, start_frame + 140, start_frame + 150, start_frame + 160, peak_strength=3.0)

    # Group (x - 1)
    group2_left_paren, group2_right_paren = create_parentheses("Group2Paren", height=2.0, thickness=0.1, material=materials["ParenthesesMat"])
    add_object_to_collection(group2_left_paren, main_coll)
    add_object_to_collection(group2_right_paren, main_coll)

    # Current objects: new_plus_x_obj, new_minus_arrow_reorder2, const1_obj
    group2_start_loc_left = (new_plus_x_obj.location.x - 0.5, eq_y, eq_start_z)
    group2_end_loc_left = (new_plus_x_obj.location.x - 0.5, eq_y, eq_start_z) # Same as start for this
    group2_start_loc_right = (const1_obj.location.x + 0.5, eq_y, eq_start_z)
    group2_end_loc_right = (const1_obj.location.x + 0.5, eq_y, eq_start_z) # Same as start for this

    group2_left_paren.location = group2_start_loc_left
    group2_right_paren.location = group2_start_loc_right
    animate_fade(group2_left_paren, start_frame + 160, start_frame + 170, 0.0, 1.0)
    animate_fade(group2_right_paren, start_frame + 160, start_frame + 170, 0.0, 1.0)
    animate_glow(group2_left_paren, start_frame + 170, start_frame + 180, start_frame + 190, peak_strength=3.0)
    animate_glow(group2_right_paren, start_frame + 170, start_frame + 180, start_frame + 190, peak_strength=3.0)

    # Constant 1 highlights as common factor
    animate_glow(const1_obj, start_frame + 190, start_frame + 200, start_frame + 210, peak_strength=3.0)

    # Factor out 1 (symbol flies out)
    factor_1_arrow, factor_1_symbol = create_operation_arrow("Factor1Arrow", "1", materials["OpArrowFactorMat"],
                                                            location=(new_plus_x_obj.location.x, eq_y, eq_start_z + 1.5), rotation_euler=(math.radians(90),0,0), scale=(0.5,0.5,0.5))
    add_object_to_collection(factor_1_arrow, main_coll)
    animate_slide(factor_1_arrow, start_frame + 210, start_frame + 220, (new_plus_x_obj.location.x, eq_y, eq_start_z + 1.5), (factor_x2_arrow.location.x + 4.5, eq_y, eq_start_z))
    animate_fade(factor_1_arrow, start_frame + 210, start_frame + 220, 0.0, 1.0)

    # Hide original +x, -1
    animate_fade(new_plus_x_obj, start_frame + 220, start_frame + 230, 1.0, 0.0)
    animate_fade(new_minus_arrow_reorder2, start_frame + 220, start_frame + 230, 1.0, 0.0)
    animate_fade(const1_obj, start_frame + 220, start_frame + 230, 1.0, 0.0)

    # Result: x^2(x - 1) + 1(x - 1) = 0
    # The (x-1) elements from the first group are already there. We just need to ensure consistent naming/visibility.
    # The existing (x-1) (new_x_in_paren, new_minus_in_paren, new_const1_in_paren, x2_group_left_paren, x2_group_right_paren) will serve.
    # We need another set for +1(x-1)
    new_x_in_paren2, _ = create_variable_box("XInParen2", "x", None, box_type='cube', size=0.8, location=(factor_1_arrow.location.x + 0.5, eq_y, eq_start_z), material=materials["VariableXMat"], text_material=materials["TextMat"])
    new_minus_in_paren2, _ = create_operation_arrow("MinusInParen2", "-", materials["OpArrowMinusMat"], location=(factor_1_arrow.location.x + 1.5, eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    new_const1_in_paren2, _ = create_constant_block("Const1InParen2", 1, size=0.7, location=(factor_1_arrow.location.x + 2.5, eq_y, eq_start_z), material=materials["ConstantMat"], text_material=materials["TextMat"])
    
    add_object_to_collection(new_x_in_paren2, main_coll)
    add_object_to_collection(new_minus_in_paren2, main_coll)
    add_object_to_collection(new_const1_in_paren2, main_coll)

    animate_fade(new_x_in_paren2, start_frame + 230, start_frame + 240, 0.0, 1.0)
    animate_fade(new_minus_in_paren2, start_frame + 230, start_frame + 240, 0.0, 1.0)
    animate_fade(new_const1_in_paren2, start_frame + 230, start_frame + 240, 0.0, 1.0)

    # Parentheses for 1(x-1)
    one_group_left_paren, one_group_right_paren = create_parentheses("OneGroupParen", height=1.5, thickness=0.08, material=materials["ParenthesesMat"])
    add_object_to_collection(one_group_left_paren, main_coll)
    add_object_to_collection(one_group_right_paren, main_coll)

    one_group_left_paren.location = (factor_1_arrow.location.x, eq_y, eq_start_z)
    one_group_right_paren.location = (factor_1_arrow.location.x + 3.0, eq_y, eq_start_z)
    animate_fade(one_group_left_paren, start_frame + 240, start_frame + 250, 0.0, 1.0)
    animate_fade(one_group_right_paren, start_frame + 240, start_frame + 250, 0.0, 1.0)

    # Adjust current_frame based on the last animation end
    current_frame = start_frame + 250 # Extended slightly to finish factor 1 animation


    # Re-position everything slightly for the new equation x^2(x-1) + 1(x-1) = 0
    # Old objects to hide: new_plus_arrow_reorder, equals_obj, zero_obj
    animate_fade(new_plus_arrow_reorder, current_frame, current_frame + 10, 1.0, 0.0)
    
    # Hide original equals and zero to make way for the duplicated ones used in next step
    # Important: equals_obj and zero_obj are already keyframed. Creating new ones and fading
    # them in later is cleaner than trying to reuse and move the original ones across steps.
    animate_fade(equals_obj, current_frame, current_frame + 10, 1.0, 0.0)
    animate_fade(zero_obj, current_frame, current_frame + 10, 1.0, 0.0)

    # New Equals and Zero objects for next step (will be moved in Scene 4)
    equals_obj_next, _, _ = create_equals_bar("EqualsNext", length=1.5, location=(0, eq_y, eq_start_z), material=materials["EqBarMat"])
    zero_obj_next, _ = create_zero_block("ZeroNext", size=0.7, location=(0, eq_y, eq_start_z), material=materials["ZeroMat"], text_material=materials["TextMat"])
    add_object_to_collection(equals_obj_next, main_coll)
    add_object_to_collection(zero_obj_next, main_coll)
    
    # Fade them in now to be ready for re-positioning
    animate_fade(equals_obj_next, current_frame + 10, current_frame + 20, 0.0, 1.0)
    animate_fade(zero_obj_next, current_frame + 10, current_frame + 20, 0.0, 1.0)

    # Reposition elements to form: x^2(x-1) + 1(x-1) = 0
    x2_factor_loc = (-5.5, eq_y, eq_start_z)
    x1_group_loc = (-3.5, eq_y, eq_start_z)
    plus_op_loc = (-1.5, eq_y, eq_start_z)
    one_factor_loc = (0.5, eq_y, eq_start_z)
    x2_group_loc = (2.5, eq_y, eq_start_z)
    eq_loc = (4.5, eq_y, eq_start_z)
    zero_loc = (5.0, eq_y, eq_start_z)

    # Adjust factor_x2_arrow, x2_group_left/right_paren, new_x_in_paren, new_minus_in_paren, new_const1_in_paren
    # Adjust factor_1_arrow, one_group_left/right_paren, new_x_in_paren2, new_minus_in_paren2, new_const1_in_paren2

    animate_slide(factor_x2_arrow, current_frame, current_frame + 30, factor_x2_arrow.location, x2_factor_loc)
    animate_slide(x2_group_left_paren, current_frame, current_frame + 30, x2_group_left_paren.location, (x1_group_loc[0] - 0.5, x1_group_loc[1], x1_group_loc[2]))
    animate_slide(new_x_in_paren, current_frame, current_frame + 30, new_x_in_paren.location, x1_group_loc)
    animate_slide(new_minus_in_paren, current_frame, current_frame + 30, new_minus_in_paren.location, (x1_group_loc[0] + 1.0, x1_group_loc[1], x1_group_loc[2]))
    animate_slide(new_const1_in_paren, current_frame, current_frame + 30, new_const1_in_paren.location, (x1_group_loc[0] + 2.0, x1_group_loc[1], x1_group_loc[2]))
    animate_slide(x2_group_right_paren, current_frame, current_frame + 30, x2_group_right_paren.location, (x1_group_loc[0] + 2.5, x1_group_loc[1], x1_group_loc[2]))

    # New + operator between groups
    plus_op_between_groups, _ = create_operation_arrow("PlusOpBetweenGroups", "+", materials["OpArrowPlusMat"], location=(plus_op_loc[0], eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    add_object_to_collection(plus_op_between_groups, main_coll)
    animate_fade(plus_op_between_groups, current_frame, current_frame + 10, 0.0, 1.0)


    animate_slide(factor_1_arrow, current_frame, current_frame + 30, factor_1_arrow.location, one_factor_loc)
    animate_slide(one_group_left_paren, current_frame, current_frame + 30, one_group_left_paren.location, (x2_group_loc[0] - 0.5, x2_group_loc[1], x2_group_loc[2]))
    animate_slide(new_x_in_paren2, current_frame, current_frame + 30, new_x_in_paren2.location, x2_group_loc)
    animate_slide(new_minus_in_paren2, current_frame, current_frame + 30, new_minus_in_paren2.location, (x2_group_loc[0] + 1.0, x2_group_loc[1], x2_group_loc[2]))
    animate_slide(new_const1_in_paren2, current_frame, current_frame + 30, new_const1_in_paren2.location, (x2_group_loc[0] + 2.0, x2_group_loc[1], x2_group_loc[2]))
    animate_slide(one_group_right_paren, current_frame, current_frame + 30, one_group_right_paren.location, (x2_group_loc[0] + 2.5, x2_group_loc[1], x2_group_loc[2]))

    animate_slide(equals_obj_next, current_frame, current_frame + 30, equals_obj_next.location, eq_loc)
    animate_slide(zero_obj_next, current_frame, current_frame + 30, zero_obj_next.location, zero_loc)

    # Hide initial grouping parentheses
    animate_fade(group1_left_paren, current_frame, current_frame + 10, 1.0, 0.0)
    animate_fade(group1_right_paren, current_frame, current_frame + 10, 1.0, 0.0)
    animate_fade(group2_left_paren, current_frame, current_frame + 10, 1.0, 0.0)
    animate_fade(group2_right_paren, current_frame, current_frame + 10, 1.0, 0.0)

    current_frame = end_frame # Corrected to the actual end of this scene
    bpy.context.scene.frame_current = current_frame


    # --- Scene 4: Factoring by Grouping - Part 2 (25-30 seconds) ---
    # Frames: 600 - 720
    start_frame = current_frame
    end_frame = start_frame + 120

    # Both (x - 1) terms glow simultaneously
    animate_glow(x2_group_left_paren, start_frame + 10, start_frame + 20, start_frame + 30)
    animate_glow(x2_group_right_paren, start_frame + 10, start_frame + 20, start_frame + 30)
    animate_glow(new_x_in_paren, start_frame + 10, start_frame + 20, start_frame + 30)
    animate_glow(new_minus_in_paren, start_frame + 10, start_frame + 20, start_frame + 30)
    animate_glow(new_const1_in_paren, start_frame + 10, start_frame + 20, start_frame + 30)

    animate_glow(one_group_left_paren, start_frame + 10, start_frame + 20, start_frame + 30)
    animate_glow(one_group_right_paren, start_frame + 10, start_frame + 20, start_frame + 30)
    animate_glow(new_x_in_paren2, start_frame + 10, start_frame + 20, start_frame + 30)
    animate_glow(new_minus_in_paren2, start_frame + 10, start_frame + 20, start_frame + 30)
    animate_glow(new_const1_in_paren2, start_frame + 10, start_frame + 20, start_frame + 30)


    # One (x - 1) floats to the left, the other fades out
    x_minus_1_final_loc = (-3.5, eq_y, eq_start_z) # Final position for (x-1) factor

    animate_slide(x2_group_left_paren, start_frame + 30, start_frame + 60, x2_group_left_paren.location, (x_minus_1_final_loc[0] - 0.5, eq_y, eq_start_z))
    animate_slide(new_x_in_paren, start_frame + 30, start_frame + 60, new_x_in_paren.location, x_minus_1_final_loc)
    animate_slide(new_minus_in_paren, start_frame + 30, start_frame + 60, new_minus_in_paren.location, (x_minus_1_final_loc[0] + 1.0, eq_y, eq_start_z))
    animate_slide(new_const1_in_paren, start_frame + 30, start_frame + 60, new_const1_in_paren.location, (x_minus_1_final_loc[0] + 2.0, eq_y, eq_start_z))
    animate_slide(x2_group_right_paren, start_frame + 30, start_frame + 60, x2_group_right_paren.location, (x_minus_1_final_loc[0] + 2.5, eq_y, eq_start_z))

    # Fade out the second (x-1) group
    animate_fade(one_group_left_paren, start_frame + 30, start_frame + 60, 1.0, 0.0)
    animate_fade(one_group_right_paren, start_frame + 30, start_frame + 60, 1.0, 0.0)
    animate_fade(new_x_in_paren2, start_frame + 30, start_frame + 60, 1.0, 0.0)
    animate_fade(new_minus_in_paren2, start_frame + 30, start_frame + 60, 1.0, 0.0)
    animate_fade(new_const1_in_paren2, start_frame + 30, start_frame + 60, 1.0, 0.0)

    # Combine x^2 and +1 into (x^2 + 1)
    # Hide factor_x2_arrow, factor_1_arrow, plus_op_between_groups
    animate_fade(factor_x2_arrow, start_frame + 60, start_frame + 70, 1.0, 0.0)
    animate_fade(factor_1_arrow, start_frame + 60, start_frame + 70, 1.0, 0.0)
    animate_fade(plus_op_between_groups, start_frame + 60, start_frame + 70, 1.0, 0.0)

    # Create new (x^2 + 1) objects
    new_x2_in_paren, _ = create_variable_box("X2InParen", "x", "2", box_type='plane', size=1.0,
                                            location=(x_minus_1_final_loc[0] + 4.5, eq_y, eq_start_z), material=materials["VariableX2Mat"], text_material=materials["TextMat"])
    new_plus_in_paren, _ = create_operation_arrow("PlusInParen", "+", materials["OpArrowPlusMat"],
                                                 location=(x_minus_1_final_loc[0] + 5.5, eq_y, eq_start_z), rotation_euler=(math.radians(90),0,0))
    new_const1_in_paren_combined, _ = create_constant_block("Const1InParenCombined", 1, size=0.7,
                                                   location=(x_minus_1_final_loc[0] + 6.5, eq_y, eq_start_z), material=materials["ConstantMat"], text_material=materials["TextMat"])
    
    add_object_to_collection(new_x2_in_paren, main_coll)
    add_object_to_collection(new_plus_in_paren, main_coll)
    add_object_to_collection(new_const1_in_paren_combined, main_coll)

    animate_fade(new_x2_in_paren, start_frame + 70, start_frame + 80, 0.0, 1.0)
    animate_fade(new_plus_in_paren, start_frame + 70, start_frame + 80, 0.0, 1.0)
    animate_fade(new_const1_in_paren_combined, start_frame + 70, start_frame + 80, 0.0, 1.0)

    # Parentheses for (x^2 + 1)
    final_group_left_paren, final_group_right_paren = create_parentheses("FinalGroupParen", height=1.5, thickness=0.08, material=materials["ParenthesesMat"])
    add_object_to_collection(final_group_left_paren, main_coll)
    add_object_to_collection(final_group_right_paren, main_coll)

    final_group_left_paren.location = (x_minus_1_final_loc[0] + 4.0, eq_y, eq_start_z)
    final_group_right_paren.location = (x_minus_1_final_loc[0] + 7.0, eq_y, eq_start_z)
    animate_fade(final_group_left_paren, start_frame + 80, start_frame + 90, 0.0, 1.0)
    animate_fade(final_group_right_paren, start_frame + 80, start_frame + 90, 0.0, 1.0)

    # Move equals and zero to final position for this step
    equals_obj_next_loc = (x_minus_1_final_loc[0] + 8.0, eq_y, eq_start_z)
    zero_obj_next_loc = (x_minus_1_final_loc[0] + 8.5, eq_y, eq_start_z)
    animate_slide(equals_obj_next, start_frame + 90, start_frame + 100, equals_obj_next.location, equals_obj_next_loc)
    animate_slide(zero_obj_next, start_frame + 90, start_frame + 100, zero_obj_next.location, zero_obj_next_loc)

    current_frame = end_frame
    bpy.context.scene.frame_current = current_frame

    # --- Scene 5: Solving Each Factor - Case 1 (Real Solution) (30-38 seconds) ---
    # Frames: 720 - 912
    start_frame = current_frame
    end_frame = start_frame + 192 # 8 seconds

    step3_text = create_text_object("Step 3: Set each factor equal to zero and solve.", "Step3Text",
                                    location=(0, eq_y, eq_start_z - 1.5), size=0.5, depth=0.03, material=materials["TextMat"])
    add_object_to_collection(step3_text, main_coll)
    animate_fade(step2_text, start_frame + 10, start_frame + 20, 1.0, 0.0) # Fade out previous text
    animate_fade(step3_text, start_frame + 10, start_frame + 20, 0.0, 1.0) # Fade in new text

    # Define positions for split paths
    eq_top_z = eq_start_z + 1.5
    eq_bottom_z = eq_start_z - 1.5

    # Move current (x-1) equation elements up for the left path
    # x2_group_left_paren, new_x_in_paren, new_minus_in_paren, new_const1_in_paren, x2_group_right_paren
    animate_slide(x2_group_left_paren, start_frame + 30, start_frame + 50, x2_group_left_paren.location, (x2_group_left_paren.location.x, eq_y, eq_top_z))
    animate_slide(new_x_in_paren, start_frame + 30, start_frame + 50, new_x_in_paren.location, (new_x_in_paren.location.x, eq_y, eq_top_z))
    animate_slide(new_minus_in_paren, start_frame + 30, start_frame + 50, new_minus_in_paren.location, (new_minus_in_paren.location.x, eq_y, eq_top_z))
    animate_slide(new_const1_in_paren, start_frame + 30, start_frame + 50, new_const1_in_paren.location, (new_const1_in_paren.location.x, eq_y, eq_top_z))
    animate_slide(x2_group_right_paren, start_frame + 30, start_frame + 50, x2_group_right_paren.location, (x2_group_right_paren.location.x, eq_y, eq_top_z))
    
    # Hide right factor (x^2 + 1) for now
    animate_fade(new_x2_in_paren, start_frame + 30, start_frame + 40, 1.0, 0.0)
    animate_fade(new_plus_in_paren, start_frame + 30, start_frame + 40, 1.0, 0.0)
    animate_fade(new_const1_in_paren_combined, start_frame + 30, start_frame + 40, 1.0, 0.0)
    animate_fade(final_group_left_paren, start_frame + 30, start_frame + 40, 1.0, 0.0)
    animate_fade(final_group_right_paren, start_frame + 30, start_frame + 40, 1.0, 0.0)

    # Move Equals and Zero (reposition to left path)
    animate_slide(equals_obj_next, start_frame + 50, start_frame + 60, equals_obj_next.location, (x2_group_right_paren.location.x + 1.0, eq_y, eq_top_z))
    animate_slide(zero_obj_next, start_frame + 50, start_frame + 60, zero_obj_next.location, (x2_group_right_paren.location.x + 1.5, eq_y, eq_top_z))


    # Solve x - 1 = 0
    # -1 glows
    animate_glow(new_const1_in_paren, start_frame + 70, start_frame + 80, start_frame + 90)

    # +1 to both sides (arrow)
    plus1_arrow_solve, _ = create_operation_arrow("Plus1Solve", "+1", materials["OpArrowPlusMat"], location=(new_const1_in_paren.location.x + 1.0, eq_y, eq_top_z + 0.5), rotation_euler=(math.radians(90),0,math.radians(180)), scale=(0.5,0.5,0.5))
    add_object_to_collection(plus1_arrow_solve, main_coll)
    animate_slide(plus1_arrow_solve, start_frame + 90, start_frame + 100, plus1_arrow_solve.location, (zero_obj_next.location.x + 0.5, eq_y, eq_top_z + 0.5))
    animate_fade(plus1_arrow_solve, start_frame + 90, start_frame + 100, 0.0, 1.0)
    
    # -1 fades out, +1 appears on right
    animate_fade(new_const1_in_paren, start_frame + 100, start_frame + 110, 1.0, 0.0)
    animate_fade(new_minus_in_paren, start_frame + 100, start_frame + 110, 1.0, 0.0) # Minus sign also fades as it's part of the term

    const1_on_right_solve, _ = create_constant_block("Const1OnRightSolve", 1, size=0.7, location=(zero_obj_next.location.x, eq_y, eq_top_z), material=materials["ConstantMat"], text_material=materials["TextMat"])
    add_object_to_collection(const1_on_right_solve, main_coll)
    animate_fade(const1_on_right_solve, start_frame + 110, start_frame + 120, 0.0, 1.0)
    animate_fade(zero_obj_next, start_frame + 110, start_frame + 120, 1.0, 0.0) # 0 fades out

    animate_fade(plus1_arrow_solve, start_frame + 120, start_frame + 130, 1.0, 0.0)

    # Equation transforms to: x = 1
    x_loc_final_path1 = (x2_group_left_paren.location.x + 0.5, eq_y, eq_top_z)
    equals_loc_final_path1 = (x_loc_final_path1[0] + 1.5, eq_y, eq_top_z)
    one_loc_final_path1 = (equals_loc_final_path1[0] + 0.5, eq_y, eq_top_z)

    animate_slide(new_x_in_paren, start_frame + 130, start_frame + 140, new_x_in_paren.location, x_loc_final_path1)
    animate_slide(equals_obj_next, start_frame + 130, start_frame + 140, equals_obj_next.location, equals_loc_final_path1)
    animate_slide(const1_on_right_solve, start_frame + 130, start_frame + 140, const1_on_right_solve.location, one_loc_final_path1)

    # Hide parentheses
    animate_fade(x2_group_left_paren, start_frame + 140, start_frame + 150, 1.0, 0.0)
    animate_fade(x2_group_right_paren, start_frame + 140, start_frame + 150, 1.0, 0.0)

    # Solution blocks float down
    solution_zone_z = eq_start_z - 3.0
    x_equals_1_text = create_text_object("x = 1", "XEquals1Solution", location=(0, eq_y, solution_zone_z), size=0.8, depth=0.04, material=materials["TitleTextMat"])
    add_object_to_collection(x_equals_1_text, main_coll)
    animate_slide(new_x_in_paren, start_frame + 150, start_frame + 160, new_x_in_paren.location, (x_equals_1_text.location.x - 0.5, eq_y, x_equals_1_text.location.z + 0.5))
    animate_slide(equals_obj_next, start_frame + 150, start_frame + 160, equals_obj_next.location, (x_equals_1_text.location.x + 0.5, eq_y, x_equals_1_text.location.z + 0.5))
    animate_slide(const1_on_right_solve, start_frame + 150, start_frame + 160, const1_on_right_solve.location, (x_equals_1_text.location.x + 1.0, eq_y, x_equals_1_text.location.z + 0.5))
    
    # Hide old parts and show combined solution block
    animate_fade(new_x_in_paren, start_frame + 160, start_frame + 170, 1.0, 0.0)
    animate_fade(equals_obj_next, start_frame + 160, start_frame + 170, 1.0, 0.0)
    animate_fade(const1_on_right_solve, start_frame + 160, start_frame + 170, 1.0, 0.0)
    animate_fade(x_equals_1_text, start_frame + 160, start_frame + 170, 0.0, 1.0) # Fade in the actual solution text

    current_frame = end_frame
    bpy.context.scene.frame_current = current_frame


    # --- Scene 6: Solving Each Factor - Case 2 (Complex Solutions) (38-50 seconds) ---
    # Frames: 912 - 1200
    start_frame = current_frame
    end_frame = start_frame + 288 # 12 seconds

    # Re-show the x^2 + 1 = 0 part, at bottom position
    # Create duplicates to avoid moving originals that are already keyframed
    x2_plus_1_eq_loc_x = x_minus_1_final_loc[0] + 5.0 # Roughly where it was before
    x2_plus_1_eq_loc_z = eq_start_z - 0.5 # New vertical position for this path

    x2_in_paren_dup, _ = create_variable_box("X2InParen_Dup", "x", "2", box_type='plane', size=1.0,
                                            location=(x2_plus_1_eq_loc_x - 1.0, eq_y, x2_plus_1_eq_loc_z), material=materials["VariableX2Mat"], text_material=materials["TextMat"])
    plus_in_paren_dup, _ = create_operation_arrow("PlusInParen_Dup", "+", materials["OpArrowPlusMat"],
                                                 location=(x2_plus_1_eq_loc_x, eq_y, x2_plus_1_eq_loc_z), rotation_euler=(math.radians(90),0,0))
    const1_in_paren_dup, _ = create_constant_block("Const1InParen_Dup", 1, size=0.7,
                                                   location=(x2_plus_1_eq_loc_x + 1.0, eq_y, x2_plus_1_eq_loc_z), material=materials["ConstantMat"], text_material=materials["TextMat"])
    equals_dup, _, _ = create_equals_bar("Equals_Dup", length=1.5, location=(x2_plus_1_eq_loc_x + 2.0, eq_y, x2_plus_1_eq_loc_z), material=materials["EqBarMat"])
    zero_dup, _ = create_zero_block("Zero_Dup", size=0.7, location=(x2_plus_1_eq_loc_x + 2.5, eq_y, x2_plus_1_eq_loc_z), material=materials["ZeroMat"], text_material=materials["TextMat"])

    add_object_to_collection(x2_in_paren_dup, main_coll)
    add_object_to_collection(plus_in_paren_dup, main_coll)
    add_object_to_collection(const1_in_paren_dup, main_coll)
    add_object_to_collection(equals_dup, main_coll)
    add_object_to_collection(zero_dup, main_coll)

    animate_fade(x2_in_paren_dup, start_frame + 10, start_frame + 20, 0.0, 1.0)
    animate_fade(plus_in_paren_dup, start_frame + 10, start_frame + 20, 0.0, 1.0)
    animate_fade(const1_in_paren_dup, start_frame + 10, start_frame + 20, 0.0, 1.0)
    animate_fade(equals_dup, start_frame + 10, start_frame + 20, 0.0, 1.0)
    animate_fade(zero_dup, start_frame + 10, start_frame + 20, 0.0, 1.0)

    # +1 glows
    animate_glow(const1_in_paren_dup, start_frame + 30, start_frame + 40, start_frame + 50)

    # -1 to both sides (arrow)
    minus1_arrow_solve, _ = create_operation_arrow("Minus1Solve", "-1", materials["OpArrowMinusMat"], location=(const1_in_paren_dup.location.x + 1.0, eq_y, x2_plus_1_eq_loc_z + 0.5), rotation_euler=(math.radians(90),0,math.radians(180)), scale=(0.5,0.5,0.5))
    add_object_to_collection(minus1_arrow_solve, main_coll)
    animate_slide(minus1_arrow_solve, start_frame + 50, start_frame + 60, minus1_arrow_solve.location, (zero_dup.location.x + 0.5, eq_y, x2_plus_1_eq_loc_z + 0.5))
    animate_fade(minus1_arrow_solve, start_frame + 50, start_frame + 60, 0.0, 1.0)

    # +1 fades out, -1 appears on right
    animate_fade(const1_in_paren_dup, start_frame + 60, start_frame + 70, 1.0, 0.0)
    animate_fade(plus_in_paren_dup, start_frame + 60, start_frame + 70, 1.0, 0.0) # Plus sign also fades

    const_minus1_on_right_solve, _ = create_constant_block("ConstMinus1OnRightSolve", -1, size=0.7, location=(zero_dup.location.x, eq_y, x2_plus_1_eq_loc_z), material=materials["ConstantMat"], text_material=materials["TextMat"])
    add_object_to_collection(const_minus1_on_right_solve, main_coll)
    animate_fade(const_minus1_on_right_solve, start_frame + 70, start_frame + 80, 0.0, 1.0)
    animate_fade(zero_dup, start_frame + 70, start_frame + 80, 1.0, 0.0)

    animate_fade(minus1_arrow_solve, start_frame + 80, start_frame + 90, 1.0, 0.0)

    # Equation transforms to: x^2 = -1
    x2_loc_final_path2 = (x2_in_paren_dup.location.x, eq_y, x2_plus_1_eq_loc_z)
    equals_loc_final_path2 = (x2_loc_final_path2[0] + 1.5, eq_y, x2_plus_1_eq_loc_z)
    minus1_loc_final_path2 = (equals_loc_final_path2[0] + 0.5, eq_y, x2_plus_1_eq_loc_z)

    animate_slide(x2_in_paren_dup, start_frame + 90, start_frame + 100, x2_in_paren_dup.location, x2_loc_final_path2)
    animate_slide(equals_dup, start_frame + 90, start_frame + 100, equals_dup.location, equals_loc_final_path2)
    animate_slide(const_minus1_on_right_solve, start_frame + 90, start_frame + 100, const_minus1_on_right_solve.location, minus1_loc_final_path2)

    # SquareRootSymbol animates into existence
    sq_root_symbol_left = create_square_root_symbol("SquareRootLeft", length=2.0, height=1.0, thickness=0.08, location=(x2_loc_final_path2[0] - 0.5, eq_y, x2_loc_final_path2[2] + 0.5), material=materials["SquareRootMat"])
    sq_root_symbol_right = create_square_root_symbol("SquareRootRight", length=2.0, height=1.0, thickness=0.08, location=(minus1_loc_final_path2[0] - 0.5, eq_y, minus1_loc_final_path2[2] + 0.5), material=materials["SquareRootMat"])
    add_object_to_collection(sq_root_symbol_left, main_coll)
    add_object_to_collection(sq_root_symbol_right, main_coll)
    animate_fade(sq_root_symbol_left, start_frame + 110, start_frame + 120, 0.0, 1.0)
    animate_fade(sq_root_symbol_right, start_frame + 110, start_frame + 120, 0.0, 1.0)
    animate_glow(sq_root_symbol_left, start_frame + 120, start_frame + 130, start_frame + 140)
    animate_glow(sq_root_symbol_right, start_frame + 120, start_frame + 130, start_frame + 140)

    # x^2 "de-squares" into x
    # Hide x2_in_paren_dup, create new x_only obj
    animate_fade(x2_in_paren_dup, start_frame + 140, start_frame + 150, 1.0, 0.0)
    x_only_obj, _ = create_variable_box("X_Only_Solve", "x", None, box_type='cube', size=0.8,
                                        location=x2_loc_final_path2, material=materials["VariableXMat"], text_material=materials["TextMat"])
    add_object_to_collection(x_only_obj, main_coll)
    animate_fade(x_only_obj, start_frame + 150, start_frame + 160, 0.0, 1.0)

    # -1 transforms into +/- i
    # Hide const_minus1_on_right_solve
    animate_fade(const_minus1_on_right_solve, start_frame + 150, start_frame + 160, 1.0, 0.0)

    imaginary_i_symbol_plus, _ = create_text_object("i", "ImaginaryI_Plus", location=(minus1_loc_final_path2[0], eq_y, minus1_loc_final_path2[2]), size=0.8, depth=0.04, material=materials["ImaginaryUnitMat"])
    imaginary_i_symbol_minus, _ = create_text_object("-i", "ImaginaryI_Minus", location=(minus1_loc_final_path2[0], eq_y, minus1_loc_final_path2[2]), size=0.8, depth=0.04, material=materials["ImaginaryUnitMat"])
    plus_minus_symbol, _ = create_text_object("±", "PlusMinus", location=(minus1_loc_final_path2[0] - 0.5, eq_y, minus1_loc_final_path2[2]), size=0.5, depth=0.04, material=materials["PlusMinusMat"])
    add_object_to_collection(imaginary_i_symbol_plus, main_coll)
    add_object_to_collection(imaginary_i_symbol_minus, main_coll)
    add_object_to_collection(plus_minus_symbol, main_coll)

    animate_fade(imaginary_i_symbol_plus, start_frame + 160, start_frame + 170, 0.0, 1.0)
    animate_fade(plus_minus_symbol, start_frame + 160, start_frame + 170, 0.0, 1.0)

    # Fade out square root symbols
    animate_fade(sq_root_symbol_left, start_frame + 170, start_frame + 180, 1.0, 0.0)
    animate_fade(sq_root_symbol_right, start_frame + 170, start_frame + 180, 1.0, 0.0)

    # Split ±i into two distinct blocks: x=i and x=-i
    # Hide plus_minus_symbol
    animate_fade(plus_minus_symbol, start_frame + 190, start_frame + 200, 1.0, 0.0)

    # Animate imaginary_i_symbol_plus to x=i position
    animate_slide(imaginary_i_symbol_plus, start_frame + 200, start_frame + 210, imaginary_i_symbol_plus.location, (equals_loc_final_path2[0] + 0.5, eq_y, eq_top_z + 0.5))
    animate_slide(imaginary_i_symbol_minus, start_frame + 200, start_frame + 210, imaginary_i_symbol_minus.location, (equals_loc_final_path2[0] + 0.5, eq_y, eq_bottom_z - 0.5))
    
    # Duplicate 'x' and '=' for the split
    x_only_dup_top, _ = create_variable_box("X_Only_Solve_Top", "x", None, box_type='cube', size=0.8,
                                            location=(equals_loc_final_path2[0] - 0.5, eq_y, eq_top_z + 0.5), material=materials["VariableXMat"], text_material=materials["TextMat"])
    equals_dup_top, _, _ = create_equals_bar("Equals_Dup_Top", length=0.8, location=(equals_loc_final_path2[0], eq_y, eq_top_z + 0.5), material=materials["EqBarMat"])
    
    x_only_dup_bottom, _ = create_variable_box("X_Only_Solve_Bottom", "x", None, box_type='cube', size=0.8,
                                               location=(equals_loc_final_path2[0] - 0.5, eq_y, eq_bottom_z - 0.5), material=materials["VariableXMat"], text_material=materials["TextMat"])
    equals_dup_bottom, _, _ = create_equals_bar("Equals_Dup_Bottom", length=0.8, location=(equals_loc_final_path2[0], eq_y, eq_bottom_z - 0.5), material=materials["EqBarMat"])

    add_object_to_collection(x_only_dup_top, main_coll)
    add_object_to_collection(equals_dup_top, main_coll)
    add_object_to_collection(x_only_dup_bottom, main_coll)
    add_object_to_collection(equals_dup_bottom, main_coll)
    
    animate_fade(x_only_obj, start_frame + 200, start_frame + 210, 1.0, 0.0) # Hide previous x
    animate_fade(equals_dup, start_frame + 200, start_frame + 210, 1.0, 0.0) # Hide previous =

    animate_fade(x_only_dup_top, start_frame + 210, start_frame + 220, 0.0, 1.0)
    animate_fade(equals_dup_top, start_frame + 210, start_frame + 220, 0.0, 1.0)
    animate_fade(x_only_dup_bottom, start_frame + 210, start_frame + 220, 0.0, 1.0)
    animate_fade(equals_dup_bottom, start_frame + 210, start_frame + 220, 0.0, 1.0)
    animate_fade(imaginary_i_symbol_minus, start_frame + 210, start_frame + 220, 0.0, 1.0) # Fade in the -i

    # Float solutions down to Solution Zone
    x_equals_i_text = create_text_object("x = i", "XEqualsI_Solution", location=(x_equals_1_text.location.x + 2.0, eq_y, solution_zone_z), size=0.8, depth=0.04, material=materials["ImaginaryUnitMat"])
    x_equals_minus_i_text = create_text_object("x = -i", "XEqualsMinusI_Solution", location=(x_equals_1_text.location.x + 4.0, eq_y, solution_zone_z), size=0.8, depth=0.04, material=materials["ImaginaryUnitMat"])
    add_object_to_collection(x_equals_i_text, main_coll)
    add_object_to_collection(x_equals_minus_i_text, main_coll)

    animate_slide(x_only_dup_top, start_frame + 220, start_frame + 230, x_only_dup_top.location, (x_equals_i_text.location.x - 0.5, eq_y, x_equals_i_text.location.z + 0.5))
    animate_slide(equals_dup_top, start_frame + 220, start_frame + 230, equals_dup_top.location, (x_equals_i_text.location.x + 0.5, eq_y, x_equals_i_text.location.z + 0.5))
    animate_slide(imaginary_i_symbol_plus, start_frame + 220, start_frame + 230, imaginary_i_symbol_plus.location, (x_equals_i_text.location.x + 1.0, eq_y, x_equals_i_text.location.z + 0.5))

    animate_slide(x_only_dup_bottom, start_frame + 220, start_frame + 230, x_only_dup_bottom.location, (x_equals_minus_i_text.location.x - 0.5, eq_y, x_equals_minus_i_text.location.z + 0.5))
    animate_slide(equals_dup_bottom, start_frame + 220, start_frame + 230, equals_dup_bottom.location, (x_equals_minus_i_text.location.x + 0.5, eq_y, x_equals_minus_i_text.location.z + 0.5))
    animate_slide(imaginary_i_symbol_minus, start_frame + 220, start_frame + 230, imaginary_i_symbol_minus.location, (x_equals_minus_i_text.location.x + 1.0, eq_y, x_equals_minus_i_text.location.z + 0.5))

    animate_fade(x_only_dup_top, start_frame + 230, start_frame + 240, 1.0, 0.0)
    animate_fade(equals_dup_top, start_frame + 230, start_frame + 240, 1.0, 0.0)
    animate_fade(imaginary_i_symbol_plus, start_frame + 230, start_frame + 240, 1.0, 0.0)
    animate_fade(x_equals_i_text, start_frame + 230, start_frame + 240, 0.0, 1.0)

    animate_fade(x_only_dup_bottom, start_frame + 230, start_frame + 240, 1.0, 0.0)
    animate_fade(equals_dup_bottom, start_frame + 230, start_frame + 240, 1.0, 0.0)
    animate_fade(imaginary_i_symbol_minus, start_frame + 230, start_frame + 240, 1.0, 0.0)
    animate_fade(x_equals_minus_i_text, start_frame + 230, start_frame + 240, 0.0, 1.0)


    current_frame = end_frame
    bpy.context.scene.frame_current = current_frame

    # --- Scene 7: Final Solutions & Summary (50-60 seconds) ---
    # Frames: 1200 - 1440
    start_frame = current_frame
    end_frame = start_frame + 240

    animate_fade(step3_text, start_frame + 10, start_frame + 20, 1.0, 0.0)

    # Camera pulls back to reveal all three solution blocks
    cam_final_loc = (0, -20, 10)
    cam_final_rot = (math.radians(50), 0, 0)
    animate_slide(cam, start_frame + 30, start_frame + 60, cam.location, cam_final_loc)
    cam.rotation_euler = cam_final_rot
    cam.keyframe_insert(data_path="rotation_euler", frame=start_frame + 30)
    cam.keyframe_insert(data_path="rotation_euler", frame=start_frame + 60)

    # Re-position solutions slightly for final presentation
    solution_x1_loc = (-2.0, eq_y, solution_zone_z)
    solution_xi_loc = (0.0, eq_y, solution_zone_z)
    solution_ximinus_loc = (2.0, eq_y, solution_zone_z)

    animate_slide(x_equals_1_text, start_frame + 60, start_frame + 70, x_equals_1_text.location, solution_x1_loc)
    animate_slide(x_equals_i_text, start_frame + 60, start_frame + 70, x_equals_i_text.location, solution_xi_loc)
    animate_slide(x_equals_minus_i_text, start_frame + 60, start_frame + 70, x_equals_minus_i_text.location, solution_ximinus_loc)

    # Text "Final Answer:"
    final_answer_text = create_text_object("Final Answer:", "FinalAnswerText",
                                           location=(0, eq_y, solution_zone_z + 1.0), size=0.6, depth=0.03, material=materials["TitleTextMat"])
    add_object_to_collection(final_answer_text, main_coll)
    animate_fade(final_answer_text, start_frame + 70, start_frame + 80, 0.0, 1.0)

    # Each solution block pulses gently.
    pulse_strength = 2.0
    pulse_frames = 20
    # Apply glowing material (e.g., VariableXMatGlowMat) for pulsing, then revert
    
    # x = 1
    # Store original material
    original_mat_x1 = x_equals_1_text.data.materials[0]
    # Set material for pulsing
    x_equals_1_text.data.materials[0] = materials["TitleTextMatGlowMat"]
    animate_glow(x_equals_1_text, start_frame + 90, start_frame + 90 + pulse_frames/2, start_frame + 90 + pulse_frames, peak_strength=pulse_strength, base_strength=0.5)
    # Revert material after pulse
    x_equals_1_text.data.materials[0].keyframe_insert(data_path="name", frame=start_frame + 90 + pulse_frames) # This won't work directly, need to assign via script
    bpy.context.scene.frame_current = start_frame + 90 + pulse_frames # Go to end frame of pulse to set material
    x_equals_1_text.data.materials[0] = original_mat_x1
    x_equals_1_text.data.materials[0].keyframe_insert(data_path="name", frame=start_frame + 90 + pulse_frames + 1) # Set material for the next frame

    # x = i
    original_mat_xi = x_equals_i_text.data.materials[0]
    x_equals_i_text.data.materials[0] = materials["ImaginaryUnitMatGlowMat"]
    animate_glow(x_equals_i_text, start_frame + 90 + pulse_frames, start_frame + 90 + pulse_frames + pulse_frames/2, start_frame + 90 + pulse_frames * 2, peak_strength=pulse_strength, base_strength=0.5)
    bpy.context.scene.frame_current = start_frame + 90 + pulse_frames * 2
    x_equals_i_text.data.materials[0] = original_mat_xi
    x_equals_i_text.data.materials[0].keyframe_insert(data_path="name", frame=start_frame + 90 + pulse_frames * 2 + 1)

    # x = -i
    original_mat_ximinus = x_equals_minus_i_text.data.materials[0]
    x_equals_minus_i_text.data.materials[0] = materials["ImaginaryUnitMatGlowMat"]
    animate_glow(x_equals_minus_i_text, start_frame + 90 + pulse_frames * 2, start_frame + 90 + pulse_frames * 2 + pulse_frames/2, start_frame + 90 + pulse_frames * 3, peak_strength=pulse_strength, base_strength=0.5)
    bpy.context.scene.frame_current = start_frame + 90 + pulse_frames * 3
    x_equals_minus_i_text.data.materials[0] = original_mat_ximinus
    x_equals_minus_i_text.data.materials[0].keyframe_insert(data_path="name", frame=start_frame + 90 + pulse_frames * 3 + 1)
    
    # Reset current frame after material operations
    bpy.context.scene.frame_current = current_frame

    # Whiteboard grid highlights path taken - skip complex tracing for now.
    # A generic glow on the whiteboard itself to signify completion/summary.
    # Can adjust this material (whiteboardmat) to have a procedural grid pattern with animated emission.
    # For now, just glow the whiteboard itself slightly.
    animate_glow(wb, start_frame + 120, start_frame + 140, start_frame + 160, peak_strength=0.5, base_strength=0.0)


    # Fade to black
    # Create a full screen plane that fades in from transparent to black
    black_fade_plane = create_plane("FadeToBlack", size=1, location=(0, -14, 7), material=materials["BlackFadeMat"])
    black_fade_plane.scale = (20, 10, 1) # Large enough to cover screen
    add_object_to_collection(black_fade_plane, cam_light_coll) # Keep it in camera collection, always visible
    animate_fade(black_fade_plane, end_frame - 60, end_frame, 0.0, 1.0)
    
    current_frame = end_frame
    bpy.context.scene.frame_current = current_frame

    # Set interpolation for all fcurves to Bezier (smoother animations)
    for obj in bpy.data.objects:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'BEZIER'

# Run the animation script
if __name__ == "__main__":
    run_animation()