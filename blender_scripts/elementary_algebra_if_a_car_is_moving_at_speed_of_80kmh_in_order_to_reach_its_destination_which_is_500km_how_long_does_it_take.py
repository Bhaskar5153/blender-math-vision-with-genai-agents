import bpy
import math
from mathutils import Vector, Euler

# --- Global Settings ---
FPS = 30
TOTAL_FRAMES = 400
# IMPORTANT: Adjust this path to a font available on your system.
# On Windows, 'C:/Windows/Fonts/arial.ttf' is common.
# On macOS, '/System/Library/Fonts/Arial.ttf' is common.
# On Linux, '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf' or similar.
TEXT_FONT_PATH = "C:/Windows/Fonts/arial.ttf" 

# --- Colors (RGBA, 0-1 range) ---
WHITE = (1, 1, 1, 1)
LIGHT_BLUE_BG = (0.6, 0.8, 1.0, 1)
YELLOW = (1, 1, 0, 1)
GREEN = (0, 1, 0, 1)
BLUE = (0, 0, 1, 1)
RED = (1, 0, 0, 1)
TRANSPARENT_COLOR = (0, 0, 0, 0) # Used for alpha value in fade

# --- Utility Functions ---

def clear_scene():
    """Clears all objects, collections, materials, and meshes from the scene."""
    # Deselect all objects first
    bpy.ops.object.select_all(action='DESELECT')

    # Delete only objects in the current view layer
    for obj in list(bpy.context.view_layer.objects):
        obj.select_set(True)
    bpy.ops.object.delete(use_global=False)

    # Delete all collections except the master "Scene Collection"
    for collection in list(bpy.data.collections):
        if collection.name != "Scene Collection":
            bpy.data.collections.remove(collection)

    # Delete all materials
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)

    # Delete all meshes
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)

    # Delete all lights
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)

    # Delete all cameras
    for camera in list(bpy.data.cameras):
        bpy.data.cameras.remove(camera)

    print("Scene cleared.")

def create_text_material(name, color, alpha=1.0):
    """Creates a principled BSDF material for text with given color and alpha."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color[:3] + (alpha,) # Set color including alpha
    bsdf.inputs["Alpha"].default_value = alpha # Explicitly set alpha input
    
    # For transparency to work in Eevee, blend mode needs to be set
    mat.blend_method = 'HASHED' # 'ALPHA_BLEND' or 'HASHED'

    return mat

def create_text_object(name, text_content, font_path, size, color, collection_name, location=(0, 0, 0), rotation=(0, 0, 0)):
    """Creates a text object, sets its properties, and links it to a collection."""
    # Ensure nothing is selected before adding new object
    bpy.ops.object.select_all(action='DESELECT')
    
    bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = text_content

    # Set font
    try:
        font = bpy.data.fonts.load(font_path)
        obj.data.font = font
    except RuntimeError:
        print(f"Warning: Font not found at {font_path}. Using default Blender font.")

    obj.data.size = size
    obj.data.extrude = 0.05 # Give some depth to the text
    obj.data.align_x = 'CENTER'
    obj.data.align_y = 'CENTER'

    # Assign material
    mat = create_text_material(f"{name}_Material", color)
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # Link to collection
    if collection_name not in bpy.data.collections:
        new_col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(new_col)
    
    # Remove from default collection if it's still there
    for coll in list(obj.users_collection): # Iterate over a copy
        coll.objects.unlink(obj)

    bpy.data.collections[collection_name].objects.link(obj)

    obj.hide_set(False) # Ensure visible in viewport by default
    obj.hide_render = True # Ensure visible in render by default

    return obj

def animate_fade(obj, start_frame, end_frame, start_alpha, end_alpha):
    """Animates the alpha value of an object's material. Handles viewport/render hide."""
    if not obj.data.materials:
        print(f"Object {obj.name} has no materials to animate fade.")
        return

    mat = obj.data.materials[0]
    if not mat or not mat.use_nodes:
        print(f"Object {obj.name}'s material is not node-based for fade animation.")
        return

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        print(f"Object {obj.name}'s material has no Principled BSDF node for fade animation.")
        return

    # Keyframe hide_viewport and hide_render based on alpha values
    if start_alpha == 0:
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=start_frame - 1)
        obj.keyframe_insert(data_path="hide_render", frame=start_frame - 1)
    else:
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=start_frame - 1)
        obj.keyframe_insert(data_path="hide_render", frame=start_frame - 1)

    if end_alpha == 0:
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=end_frame)
        obj.keyframe_insert(data_path="hide_render", frame=end_frame)
    else:
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=end_frame)
        obj.keyframe_insert(data_path="hide_render", frame=end_frame)

    # Set initial alpha and keyframe
    bsdf.inputs["Alpha"].default_value = start_alpha
    bsdf.inputs["Alpha"].keyframe_insert(data_path="default_value", frame=start_frame)

    # Set final alpha and keyframe
    bsdf.inputs["Alpha"].default_value = end_alpha
    bsdf.inputs["Alpha"].keyframe_insert(data_path="default_value", frame=end_frame)

def animate_slide(obj, start_frame, end_frame, start_loc, end_loc, hide_before=True):
    """Animates an object's location. Can hide the object before the animation starts."""
    if hide_before:
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=start_frame - 1)
        obj.keyframe_insert(data_path="hide_render", frame=start_frame - 1)
        
    obj.location = Vector(start_loc)
    obj.keyframe_insert(data_path="location", frame=start_frame)
    
    if hide_before:
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=start_frame)
        obj.keyframe_insert(data_path="hide_render", frame=start_frame)

    obj.location = Vector(end_loc)
    obj.keyframe_insert(data_path="location", frame=end_frame)

def animate_highlight_color(obj, start_frame, end_frame, highlight_color, original_color):
    """Animates text color to highlight and revert."""
    if not obj.data.materials:
        print(f"Object {obj.name} has no materials to animate color highlight.")
        return

    mat = obj.data.materials[0]
    if not mat or not mat.use_nodes:
        print(f"Object {obj.name}'s material is not node-based for color highlight.")
        return

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        print(f"Object {obj.name}'s material has no Principled BSDF node for color highlight.")
        return

    # Store current alpha to reapply
    current_alpha = bsdf.inputs["Alpha"].default_value

    # Keyframe original color
    bsdf.inputs["Base Color"].default_value = original_color[:3] + (current_alpha,)
    bsdf.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=start_frame)

    # Keyframe highlight color
    bsdf.inputs["Base Color"].default_value = highlight_color[:3] + (current_alpha,)
    bsdf.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=start_frame + (end_frame - start_frame) / 2)

    # Keyframe back to original color
    bsdf.inputs["Base Color"].default_value = original_color[:3] + (current_alpha,)
    bsdf.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=end_frame)

def animate_highlight_scale(obj, start_frame, end_frame, scale_factor=1.1, original_scale=(1,1,1)):
    """Animates object scale to highlight and revert."""
    # Keyframe original scale
    obj.scale = Vector(original_scale)
    obj.keyframe_insert(data_path="scale", frame=start_frame)

    # Keyframe highlighted scale
    obj.scale = Vector(original_scale) * scale_factor
    obj.keyframe_insert(data_path="scale", frame=start_frame + (end_frame - start_frame) / 2)

    # Keyframe back to original scale
    obj.scale = Vector(original_scale)
    obj.keyframe_insert(data_path="scale", frame=end_frame)


# --- Scene Setup Functions ---

def setup_scene():
    """Sets up camera, lights, and rendering settings."""
    # Set render settings
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = TOTAL_FRAMES
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT' # Eevee for faster rendering (Blender 4.x)

    # Set background color
    bpy.data.worlds["World"].use_nodes = True
    bg_node = bpy.data.worlds["World"].node_tree.nodes["Background"]
    bg_node.inputs[0].default_value = LIGHT_BLUE_BG # Color input
    bg_node.inputs[1].default_value = 1.0 # Strength

    # Camera setup
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_obj = bpy.data.objects.new("MainCamera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    cam_obj.location = (0, -10, 5) # Example camera position
    cam_obj.rotation_euler = Euler((math.radians(60), 0, 0)) # Look down towards origin

    cam_obj.keyframe_insert(data_path="location", frame=1)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=1)

    # Light setup (remove default light, add an area light)
    # Ensure all objects are deselected before selecting for deletion
    bpy.ops.object.select_all(action='DESELECT')
    if "Light" in bpy.data.objects:
        obj_to_remove = bpy.data.objects["Light"]
        obj_to_remove.select_set(True)
        bpy.ops.object.delete()

    light_data = bpy.data.lights.new(name="AreaLight", type='AREA')
    light_data.energy = 2000 # Adjust as needed
    light_data.size = 2 # Area light size
    light_obj = bpy.data.objects.new(name="AreaLight", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = (0, -5, 10)
    light_obj.rotation_euler = Euler((math.radians(30), 0, 0)) # Point slightly down

    # Set up collections
    collections_to_create = ["Question", "Scenario Elements", "Calculations", "Solution", "Lights", "Cameras"]
    for col_name in collections_to_create:
        if col_name not in bpy.data.collections:
            new_col = bpy.data.collections.new(col_name)
            bpy.context.scene.collection.children.link(new_col)
    
    # Link camera and light to their respective collections
    # Unlink from default collection first
    for coll in list(cam_obj.users_collection):
        coll.objects.unlink(cam_obj)
    bpy.data.collections["Cameras"].objects.link(cam_obj)

    for coll in list(light_obj.users_collection):
        coll.objects.unlink(light_obj)
    bpy.data.collections["Lights"].objects.link(light_obj)

    print("Scene setup complete.")


# --- Object Creation ---

def create_scenario_elements():
    """Creates creative objects for car, road, destination, and background."""
    # --- Road (Plane with dashed lines) ---
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_plane_add(size=20, enter_editmode=False, align='WORLD', location=(0, 0, -0.1))
    road_obj = bpy.context.active_object
    road_obj.name = "Road"
    road_mat = create_text_material("Road_Material", (0.1, 0.1, 0.1, 1))
    if road_obj.data.materials:
        road_obj.data.materials[0] = road_mat
    else:
        road_obj.data.materials.append(road_mat)
    for coll in list(road_obj.users_collection):
        coll.objects.unlink(road_obj)
    bpy.data.collections["Scenario Elements"].objects.link(road_obj)
    # Add dashed lines
    dash_count = 8
    for i in range(-dash_count//2, dash_count//2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(i*2.5, 0, 0.01))
        dash = bpy.context.active_object
        dash.name = f"Dash_{i}"
        dash.scale = (0.7, 0.08, 0.01)
        dash_mat = create_text_material(f"Dash_Mat_{i}", (1,1,1,1))
        dash.data.materials.append(dash_mat)
        for coll in list(dash.users_collection):
            coll.objects.unlink(dash)
        bpy.data.collections["Scenario Elements"].objects.link(dash)
    # --- Car (Stylized) ---
    # Car body
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-10, 0, 0.3))
    car_body = bpy.context.active_object
    car_body.name = "Car_Body"
    car_body.scale = (1.2, 0.5, 0.25)
    car_body_mat = create_text_material("Car_Body_Mat", (1.0, 0.3, 0.1, 1))
    car_body.data.materials.append(car_body_mat)
    # Car roof
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-10, 0, 0.6))
    car_roof = bpy.context.active_object
    car_roof.name = "Car_Roof"
    car_roof.scale = (0.6, 0.5, 0.18)
    car_roof_mat = create_text_material("Car_Roof_Mat", (0.9, 0.2, 0.05, 1))
    car_roof.data.materials.append(car_roof_mat)
    # Car windows
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-10, 0, 0.65))
    car_win = bpy.context.active_object
    car_win.name = "Car_Window"
    car_win.scale = (0.5, 0.48, 0.13)
    car_win_mat = create_text_material("Car_Win_Mat", (0.2, 0.5, 0.8, 0.7))
    car_win.data.materials.append(car_win_mat)
    # Wheels
    wheels = []
    for x in [-0.6, 0.6]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.12, location=(-10+x, 0.32, 0.13))
        wheel = bpy.context.active_object
        wheel.name = f"Car_Wheel_L{x}"
        wheel_mat = create_text_material(f"Wheel_Mat_{x}", (0.1,0.1,0.1,1))
        wheel.data.materials.append(wheel_mat)
        wheels.append(wheel)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.13, location=(-10+x, 0.32, 0.13))
        hub = bpy.context.active_object
        hub.name = f"Car_Hub_L{x}"
        hub_mat = create_text_material(f"Hub_Mat_{x}", (0.8,0.8,0.8,1))
        hub.data.materials.append(hub_mat)
        wheels.append(hub)
    # Group car parts
    car_parts = [car_body, car_roof, car_win] + wheels
    car_obj = car_body
    for part in car_parts[1:]:
        part.parent = car_obj
    for part in car_parts:
        for coll in list(part.users_collection):
            coll.objects.unlink(part)
        bpy.data.collections["Scenario Elements"].objects.link(part)
    # --- Destination Marker (Map Pin) ---
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.5, location=(10, 0, 0.25))
    pin_stem = bpy.context.active_object
    pin_stem.name = "Pin_Stem"
    pin_stem_mat = create_text_material("Pin_Stem_Mat", (1,0.2,0.2,1))
    pin_stem.data.materials.append(pin_stem_mat)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(10, 0, 0.6))
    pin_head = bpy.context.active_object
    pin_head.name = "Pin_Head"
    pin_head_mat = create_text_material("Pin_Head_Mat", (1,0.2,0.2,1))
    pin_head.data.materials.append(pin_head_mat)
    bpy.ops.mesh.primitive_circle_add(radius=0.18, location=(10, 0, 0.75))
    pin_center = bpy.context.active_object
    pin_center.name = "Pin_Center"
    pin_center_mat = create_text_material("Pin_Center_Mat", (1,1,1,1))
    pin_center.data.materials.append(pin_center_mat)
    # Group pin parts
    marker_obj = pin_stem
    pin_head.parent = marker_obj
    pin_center.parent = marker_obj
    for part in [marker_obj, pin_head, pin_center]:
        for coll in list(part.users_collection):
            coll.objects.unlink(part)
        bpy.data.collections["Scenario Elements"].objects.link(part)
    # --- Cityscape Background (optional) ---
    for i in range(-4, 5):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(i*2.2, -2.5, 1.2))
        bldg = bpy.context.active_object
        bldg.name = f"Bldg_{i}"
        bldg.scale = (0.8, 0.8, 1.2 + 0.7*abs(i)%2)
        bldg_mat = create_text_material(f"Bldg_Mat_{i}", (0.8,0.8,0.85,1))
        bldg.data.materials.append(bldg_mat)
        for coll in list(bldg.users_collection):
            coll.objects.unlink(bldg)
        bpy.data.collections["Scenario Elements"].objects.link(bldg)
    return car_obj, road_obj, marker_obj


# --- Main Animation Sequence ---

def animate_story():
    """Defines the full animation sequence based on the plan."""
    # Ensure scene is clean and ready
    clear_scene()
    setup_scene()

    # Create all objects upfront, hide those that appear later
    
    # Question Text
    question_text_content = "If a car is moving at a speed of 80 km/h. In order to reach its destination..."
    question_obj = create_text_object(
        "QuestionText", question_text_content, TEXT_FONT_PATH, 1.0, WHITE, "Question", location=(0, 4, 0))
    question_obj.hide_viewport = True
    question_obj.hide_render = True

    # Scenario Elements
    car_obj, road_obj, marker_obj = create_scenario_elements()
    car_obj.hide_viewport = True
    car_obj.hide_render = True
    road_obj.hide_viewport = True
    road_obj.hide_render = True
    marker_obj.hide_viewport = True
    marker_obj.hide_render = True

    # Formula Parts
    formula_part1_content = "Speed (S) = 80 km/h"
    formula_part1_obj = create_text_object(
        "Formula_Part_1", formula_part1_content, TEXT_FONT_PATH, 0.8, YELLOW, "Calculations", location=(-4, 2, 0))
    formula_part1_obj.hide_viewport = True
    formula_part1_obj.hide_render = True
    
    formula_part2_content = "Distance (D) = ?"
    formula_part2_obj = create_text_object(
        "Formula_Part_2_Initial", formula_part2_content, TEXT_FONT_PATH, 0.8, YELLOW, "Calculations", location=(-4, 1, 0))
    formula_part2_obj.hide_viewport = True
    formula_part2_obj.hide_render = True

    formula_part3_content = "Time (T) = ?"
    formula_part3_obj = create_text_object(
        "Formula_Part_3", formula_part3_content, TEXT_FONT_PATH, 0.8, YELLOW, "Calculations", location=(-4, 0, 0))
    formula_part3_obj.hide_viewport = True
    formula_part3_obj.hide_render = True

    main_formula_content = "D = S × T"
    main_formula_obj = create_text_object(
        "Main_Formula", main_formula_content, TEXT_FONT_PATH, 1.0, GREEN, "Calculations", location=(4, 1, 0))
    main_formula_obj.hide_viewport = True
    main_formula_obj.hide_render = True

    # Dynamic Calculation Texts (create upfront and hide)
    # The approach for changing text needs careful handling,
    # as `obj.data.body` cannot be keyframed directly.
    # Instead, we create multiple text objects and fade them in/out.
    
    # Text for "Distance (D) = 80 km/h * T"
    formula_part2_updated_content = "Distance (D) = 80 km/h * T"
    formula_part2_updated_obj = create_text_object(
        "Formula_Part_2_Updated_1", formula_part2_updated_content, TEXT_FONT_PATH, 0.8, YELLOW, "Calculations", location=(-4, 1, 0))
    formula_part2_updated_obj.hide_viewport = True
    formula_part2_updated_obj.hide_render = True

    # Text for "D = 80 * T"
    calc_step1_content = "D = 80 * T"
    calc_step1_obj = create_text_object(
        "Calculation_Step_1", calc_step1_content, TEXT_FONT_PATH, 1.0, BLUE, "Calculations", location=(0, 0, 0))
    calc_step1_obj.hide_viewport = True
    calc_step1_obj.hide_render = True
    
    # Text for "Time to reach destination: 2 hours"
    time_info_content = "Time to reach destination: 2 hours"
    time_info_obj = create_text_object(
        "Time_Info", time_info_content, TEXT_FONT_PATH, 0.7, WHITE, "Calculations", location=(0, -1, 0))
    time_info_obj.hide_viewport = True
    time_info_obj.hide_render = True

    # Text for "D = 80 * 2"
    calc_step2_content = "D = 80 * 2"
    calc_step2_obj = create_text_object(
        "Calculation_Step_2", calc_step2_content, TEXT_FONT_PATH, 1.0, BLUE, "Calculations", location=(0, 0, 0))
    calc_step2_obj.hide_viewport = True
    calc_step2_obj.hide_render = True

    # Text for "D = 160 km"
    calc_step3_content = "D = 160 km"
    calc_step3_obj = create_text_object(
        "Calculation_Step_3", calc_step3_content, TEXT_FONT_PATH, 1.0, BLUE, "Calculations", location=(0, 0, 0))
    calc_step3_obj.hide_viewport = True
    calc_step3_obj.hide_render = True

    # Solution Text
    solution_text_content = "The car will travel 160 km in 2 hours."
    solution_obj = create_text_object(
        "SolutionText", solution_text_content, TEXT_FONT_PATH, 0.9, BLUE, "Solution", location=(0, 0, 0))
    solution_obj.hide_viewport = True
    solution_obj.hide_render = True


    # --- Animation Timeline ---

    # 1. Introduction of the Problem (Frames 10-80)
    # Frame 10: Question text appears (fade in).
    animate_fade(question_obj, 10, 30, 0, 1) # Fade in from frame 10 to 30

    # Frame 30: Car model appears (slide in from left).
    animate_slide(car_obj, 30, 50, (-10, 0, 0), (-5, 0, 0), hide_before=True)

    # Frame 40: Road appears (fade in).
    animate_fade(road_obj, 40, 60, 0, 1)

    # Frame 50: Destination marker appears (slide in from right).
    animate_slide(marker_obj, 50, 70, (10, 0, 0.5), (5, 0, 0.5), hide_before=True)

    # 2. Car Movement (Frames 80-150)
    # Frame 80: Car starts moving towards the destination.
    animate_slide(car_obj, 80, 150, (-5, 0, 0), (5, 0, 0), hide_before=False) # Car is already visible

    # Frame 150: Car reaches destination, pauses. (implicit by end of slide)

    # 3. Displaying Given Information (Frames 160-220)
    # Frame 160: Question text fades out.
    animate_fade(question_obj, 160, 170, 1, 0)

    # Frame 170: Formula Part 1 slides in from top.
    animate_slide(formula_part1_obj, 170, 190, (-4, 5, 0), (-4, 2, 0), hide_before=True)

    # Frame 180: Formula Part 2 slides in from top, below Part 1.
    animate_slide(formula_part2_obj, 180, 200, (-4, 4, 0), (-4, 1, 0), hide_before=True)

    # Frame 190: Formula Part 3 slides in from top, below Part 2.
    animate_slide(formula_part3_obj, 190, 210, (-4, 3, 0), (-4, 0, 0), hide_before=True)

    # Frame 200: Main Formula "D = S × T" slides in from bottom.
    animate_slide(main_formula_obj, 200, 220, (4, -5, 0), (4, 1, 0), hide_before=True)

    # Frame 210-220: Highlight "80 km/h" in Formula Part 1 (scale up, change color to red, then back).
    # This highlights the *entire* Formula_Part_1 text, as Blender's text objects don't support partial styling out of the box.
    animate_highlight_scale(formula_part1_obj, 210, 220, scale_factor=1.1, original_scale=(1,1,1))
    animate_highlight_color(formula_part1_obj, 210, 220, RED, YELLOW)


    # 4. Calculation Steps (Frames 230-320)
    # Frame 230: Formula Part 2 changes to "Distance (D) = 80 km/h * T"
    # Fade out old Formula_Part_2, Fade in Formula_Part_2_Updated_1
    animate_fade(formula_part2_obj, 230, 240, 1, 0)
    animate_fade(formula_part2_updated_obj, 235, 245, 0, 1) # Slight overlap for smooth transition

    # Frame 240: Main Formula fades out.
    animate_fade(main_formula_obj, 240, 250, 1, 0)

    # Frame 250: New Formula text "D = 80 * T" appears (fade in).
    animate_fade(calc_step1_obj, 250, 260, 0, 1)

    # Frame 260-270: Highlight the `T` (scale up, change color).
    # Highlighting the whole calc_step1_obj.
    animate_highlight_scale(calc_step1_obj, 260, 270, scale_factor=1.1, original_scale=(1,1,1))
    animate_highlight_color(calc_step1_obj, 260, 270, RED, BLUE)

    # Frame 280: "Time to reach destination: 2 hours" appears (fade in).
    animate_fade(time_info_obj, 280, 290, 0, 1)

    # Frame 290: Formula text updates to "D = 80 * 2". (Fade out old, fade in new)
    animate_fade(calc_step1_obj, 290, 300, 1, 0)
    animate_fade(time_info_obj, 290, 300, 1, 0) # Fade out time info as well
    animate_fade(calc_step2_obj, 295, 305, 0, 1) # New formula D=80*2 appears

    # Frame 300: Formula text updates to "D = 160 km". (Fade out old, fade in new)
    animate_fade(calc_step2_obj, 300, 310, 1, 0)
    animate_fade(calc_step3_obj, 305, 315, 0, 1)

    # 5. Conclusion (Frames 330-400)
    # Frame 330: All previous formula texts fade out.
    animate_fade(formula_part1_obj, 330, 340, 1, 0)
    animate_fade(formula_part2_updated_obj, 330, 340, 1, 0)
    animate_fade(formula_part3_obj, 330, 340, 1, 0)
    animate_fade(calc_step3_obj, 330, 340, 1, 0)

    # Frame 340: Solution text "The car will travel 160 km in 2 hours." appears (slide in from bottom).
    animate_slide(solution_obj, 340, 360, (0, -5, 0), (0, 0, 0), hide_before=True)

    # Frame 350-380: Solution text glows/pulses (scale slightly, color changes).
    animate_highlight_scale(solution_obj, 350, 380, scale_factor=1.05, original_scale=(1,1,1))
    animate_highlight_color(solution_obj, 350, 380, YELLOW, BLUE)

    # Frame 390: Solution text fades out.
    animate_fade(solution_obj, 390, 400, 1, 0)

    print("Animation sequence planned.")


# --- Run the Script ---
if __name__ == "__main__":
    animate_story()