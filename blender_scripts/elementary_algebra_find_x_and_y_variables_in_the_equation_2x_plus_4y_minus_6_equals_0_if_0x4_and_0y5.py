import bpy
import math
import mathutils

# --- Configuration ---
FPS = 30
DURATION_FADE = 30  # Frames for fade in/out material or visibility
DURATION_SLIDE = 30 # Frames for sliding animation
DURATION_HIGHLIGHT = 60 # Frames for highlight to stay
TEXT_EXTRUDE = 0.02 # Small extrusion for text
FONT_PATH = "//Bfont.ttf" # Use Blender's default font. Change if a specific font is needed.

# --- Utility Functions ---
def select_and_activate_object(obj):
    """Selects and activates an object. Deselects all others first."""
    bpy.ops.object.select_all(action='DESELECT')
    if obj:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

def clear_scene():
    """Clears all objects from the scene and deletes orphaned data blocks."""
    if bpy.context.view_layer.objects:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

    # Delete all collections except the master scene collection
    for collection in bpy.data.collections:
        if collection.name != "Scene Collection":
            bpy.data.collections.remove(collection)

    # Delete orphan data (meshes, materials, textures, images, etc.)
    for block_type in [bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights, bpy.data.cameras]:
        for block in block_type:
            if block.users == 0:
                block_type.remove(block)

def setup_render_settings():
    """Sets up render engine, resolution, frame rate, and output."""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    # scene.frame_end will be set at the end of the script

    # Output settings (customize path as needed)
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM' # Good balance quality/size
    scene.render.ffmpeg.gopsize = 18 # Keyframe interval
    scene.render.filepath = "//render/" # Relative path to blend file. User should change this.

def setup_camera_and_light():
    """Sets up the camera and a sun light."""
    scene = bpy.context.scene

    # Camera
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 10 # Adjust based on scene scale
    camera = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    
    # Position and orient camera
    camera.location = (0, -10, 5) # From description
    camera.rotation_euler = (math.radians(90 + 26.565), math.radians(0), math.radians(0)) 

    # Sun Light
    light_data = bpy.data.lights.new("SunLight", type='SUN')
    light = bpy.data.objects.new("SunLight", light_data)
    scene.collection.objects.link(light)
    light.location = (0, 0, 10) # Position doesn't matter much for sun, only rotation
    light.rotation_euler = (math.radians(30), math.radians(-30), math.radians(0)) # Angle for shadows
    light.data.energy = 5
    light.data.angle = 0.5 # Soften shadows

def create_material(name, color_rgba, emission_strength=0.0):
    """Creates a PBR material with a given color and optional emission."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf: # If Principled BSDF doesn't exist, create it (should always exist by default)
        bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0,0)
        output_node = mat.node_tree.nodes.get("Material Output")
        if output_node:
            mat.node_tree.links.new(bsdf.outputs['BSDF'], output_node.inputs['Surface'])

    bsdf.inputs['Base Color'].default_value = color_rgba
    bsdf.inputs['Emission Strength'].default_value = emission_strength
    bsdf.inputs['Emission Color'].default_value = color_rgba # Use base color for emission color
    return mat

def set_visible(obj):
    obj.hide_viewport = False
    obj.hide_render = False

def create_text_object(text_str, obj_name, size, location, material, collection, align_x='CENTER', align_y='CENTER', extrude=TEXT_EXTRUDE):
    """Creates a text object with specified properties and links it to a collection."""
    # Preprocess string to avoid potential f-string or Blender text body issues
    # Example: safe_text = text_str.replace('±', 'pm').replace('√', 'sqrt')
    # For this specific plan, the strings are generally safe.
    safe_text = text_str

    text_curve = bpy.data.curves.new(name=f"{obj_name}_Curve", type='FONT')
    text_curve.body = safe_text
    
    # Load font from Blender's internal font, or a custom path
    try:
        text_curve.font = bpy.data.fonts.load(FONT_PATH)
    except RuntimeError:
        print(f"Warning: Font not found at {FONT_PATH}. Using default Blender font.")
        # Blender's default font is typically 'Bfont.ttf', which is loaded implicitly if not specified.
        # No action needed if it defaults, or load a different known font.

    text_curve.size = size
    text_curve.extrude = extrude
    text_curve.align_x = align_x
    text_curve.align_y = align_y

    obj = bpy.data.objects.new(name=obj_name, object_data=text_curve)
    obj.location = location
    collection.objects.link(obj)
    # Assign material and color
    if material:
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    obj.color = material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
    set_visible(obj)

    return obj

def animate_visibility(obj, start_frame, duration, visible=True):
    """Animates an object's viewport and render visibility with constant interpolation."""
    end_frame = start_frame + duration
    
    select_and_activate_object(obj)

    obj.hide_viewport = not visible
    obj.hide_render = not visible
    obj.keyframe_insert(data_path="hide_viewport", frame=start_frame)
    obj.keyframe_insert(data_path="hide_render", frame=start_frame)

    obj.hide_viewport = visible
    obj.hide_render = visible
    obj.keyframe_insert(data_path="hide_viewport", frame=end_frame)
    obj.keyframe_insert(data_path="hide_render", frame=end_frame)
    
    # Ensure constant interpolation for discrete visibility changes
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path in ["hide_viewport", "hide_render"]:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'CONSTANT'

def animate_fade_out_material(obj, start_frame, duration, initial_color_rgba):
    """Animates an object's material to fade out by reducing alpha and emission, then hides it."""
    end_frame = start_frame + duration
    
    select_and_activate_object(obj)

    mat = obj.data.materials[0]
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        print(f"Warning: No Principled BSDF found for {obj.name}. Cannot animate fade.")
        return

    # Set start keyframe for current color and emission
    bsdf.inputs['Base Color'].default_value = initial_color_rgba
    bsdf.inputs['Emission Strength'].default_value = 0.0 # Assuming no initial emission for general text
    bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=start_frame)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=start_frame)

    # Set end keyframe for transparent color and no emission
    fade_color = list(initial_color_rgba)
    fade_color[3] = 0.0 # Set alpha to 0 for transparency
    bsdf.inputs['Base Color'].default_value = tuple(fade_color)
    bsdf.inputs['Emission Strength'].default_value = 0.0
    bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=end_frame)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=end_frame)

    # After fading out, make it completely hidden
    obj.hide_viewport = True
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_viewport", frame=end_frame + 1)
    obj.keyframe_insert(data_path="hide_render", frame=end_frame + 1)
    
    # Set interpolation to linear for smooth fade
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if "Base Color" in fcurve.data_path or "Emission Strength" in fcurve.data_path:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'LINEAR'

def animate_location(obj, start_frame, duration, start_loc, end_loc):
    """Animates an object's location."""
    end_frame = start_frame + duration
    
    select_and_activate_object(obj)

    obj.location = start_loc
    obj.keyframe_insert(data_path="location", frame=start_frame)

    obj.location = end_loc
    obj.keyframe_insert(data_path="location", frame=end_frame)
    
    # Default interpolation for location is Bezier, which is usually smooth enough.

def animate_material_color_change(obj, start_frame, duration, target_color_rgba, original_color_rgba, emission_strength=0.5):
    """Animates an object's material color to a target color, holds, then returns to original."""
    
    select_and_activate_object(obj)

    mat = obj.data.materials[0]
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        print(f"Warning: No Principled BSDF found for {obj.name}. Cannot animate material color.")
        return

    # Start with original color (1 frame before actual highlight to ensure state)
    bsdf.inputs['Base Color'].default_value = original_color_rgba
    bsdf.inputs['Emission Strength'].default_value = 0.0
    bsdf.inputs['Emission Color'].default_value = original_color_rgba # Emission color should match base
    bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=start_frame - 1)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=start_frame - 1)
    bsdf.inputs['Emission Color'].keyframe_insert(data_path="default_value", frame=start_frame - 1)

    # Transition to target color (over DURATION_FADE)
    bsdf.inputs['Base Color'].default_value = target_color_rgba
    bsdf.inputs['Emission Strength'].default_value = emission_strength
    bsdf.inputs['Emission Color'].default_value = target_color_rgba
    bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE)
    bsdf.inputs['Emission Color'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE)

    # Hold target color for 'duration'
    bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE + duration)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE + duration)
    bsdf.inputs['Emission Color'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE + duration)

    # Transition back to original color (over DURATION_FADE)
    bsdf.inputs['Base Color'].default_value = original_color_rgba
    bsdf.inputs['Emission Strength'].default_value = 0.0
    bsdf.inputs['Emission Color'].default_value = original_color_rgba
    bsdf.inputs['Base Color'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE + duration + DURATION_FADE)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE + duration + DURATION_FADE)
    bsdf.inputs['Emission Color'].keyframe_insert(data_path="default_value", frame=start_frame + DURATION_FADE + duration + DURATION_FADE)
    
    # Set interpolation to linear for smooth color transition
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if "Base Color" in fcurve.data_path or "Emission Strength" in fcurve.data_path or "Emission Color" in fcurve.data_path:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'LINEAR'

def setup_axes_and_grid(collection):
    """Creates 3D X, Y, Z axes with arrows and number labels, plus a grid floor."""
    # Materials for axes
    mat_x = create_material("AxisX", (1, 0, 0, 1), emission_strength=1.0)
    mat_y = create_material("AxisY", (0, 1, 0, 1), emission_strength=1.0)
    mat_z = create_material("AxisZ", (0, 0, 1, 1), emission_strength=1.0)
    # Grid material
    mat_grid = create_material("GridMat", (0.8, 0.8, 0.8, 1))

    # Create grid floor
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 0, 0))
    grid = bpy.context.active_object
    grid.name = "GridFloor"
    grid.data.materials.append(mat_grid)
    collection.objects.link(grid)
    bpy.context.scene.collection.objects.unlink(grid)

    # Create axes (cylinders + cones for arrows)
    def create_axis(start, end, mat, name):
        # Cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=(math.dist(start, end)), location=((start[0]+end[0])/2, (start[1]+end[1])/2, (start[2]+end[2])/2))
        axis = bpy.context.active_object
        axis.name = f"{name}_Axis"
        axis.data.materials.append(mat)
        collection.objects.link(axis)
        bpy.context.scene.collection.objects.unlink(axis)
        # Arrow head
        bpy.ops.mesh.primitive_cone_add(radius1=0.18, depth=0.5, location=end)
        arrow = bpy.context.active_object
        arrow.name = f"{name}_Arrow"
        arrow.data.materials.append(mat)
        collection.objects.link(arrow)
        bpy.context.scene.collection.objects.unlink(arrow)
        # Rotate axis and arrow
        vec = (end[0]-start[0], end[1]-start[1], end[2]-start[2])
        axis.rotation_mode = 'QUATERNION'
        arrow.rotation_mode = 'QUATERNION'
        quat = mathutils.Vector(vec).to_track_quat('Z', 'Y')
        axis.rotation_quaternion = quat
        arrow.rotation_quaternion = quat
        return axis, arrow

    # X axis: red
    create_axis((-7, 0, 0), (7, 0, 0), mat_x, "X")
    # Y axis: green
    create_axis((0, -7, 0), (0, 7, 0), mat_y, "Y")
    # Z axis: blue
    create_axis((0, 0, 0), (0, 0, 7), mat_z, "Z")

    # Number labels for axes
    for i in range(-7, 8):
        if i == 0: continue
        # X labels
        create_text_object(str(i), f"XLabel_{i}", 0.6, (i, -0.5, 0), mat_x, collection)
        # Y labels
        create_text_object(str(i), f"YLabel_{i}", 0.6, (-0.5, i, 0), mat_y, collection)
        # Z labels
        create_text_object(str(i), f"ZLabel_{i}", 0.6, (0.5, 0, i), mat_z, collection)

    # Large axis labels at ends (colored)
    label_x = create_text_object('X', 'AxisLabel_X', 1.2, (7.5, 0, 0.5), mat_x, collection)
    label_y = create_text_object('Y', 'AxisLabel_Y', 1.2, (0, 7.5, 0.5), mat_y, collection)
    label_z = create_text_object('Z', 'AxisLabel_Z', 1.2, (0, 0, 7.5), mat_z, collection)
    label_x.color = (1,0,0,1); label_y.color = (0,1,0,1); label_z.color = (0,0,1,1)
    set_visible(label_x); set_visible(label_y); set_visible(label_z)
    # Number ticks as large colored text
    for i in range(-7, 8):
        if i == 0: continue
        tx = create_text_object(str(i), f"XTick_{i}", 0.7, (i, 0, 0.1), mat_x, collection)
        ty = create_text_object(str(i), f"YTick_{i}", 0.7, (0, i, 0.1), mat_y, collection)
        tz = create_text_object(str(i), f"ZTick_{i}", 0.7, (0, 0, i+0.1), mat_z, collection)
        tx.color = (1,0,0,1); ty.color = (0,1,0,1); tz.color = (0,0,1,1)
        set_visible(tx); set_visible(ty); set_visible(tz)
    # Creative solution region frame with thin cylinders
    # Solution region: 0 < x < 3, 0 < y < 1.5
    sol_x_min, sol_x_max = 0, 3
    sol_y_min, sol_y_max = 0, 1.5
    z_height = 0.15
    cube_size_x = sol_x_max - sol_x_min
    cube_size_y = sol_y_max - sol_y_min
    cube_size_z = 0.05
    cube_loc = (sol_x_min + cube_size_x/2, sol_y_min + cube_size_y/2, z_height)
    bpy.ops.mesh.primitive_cube_add(size=1, location=cube_loc)
    sol_cube = bpy.context.active_object
    sol_cube.name = "SolutionCube"
    sol_cube.scale = (cube_size_x/2, cube_size_y/2, cube_size_z)
    mat_sol_cube = create_material("SolutionCubeMat", (1,0.5,0,0.3), emission_strength=0.5)
    sol_cube.data.materials.append(mat_sol_cube)
    set_visible(sol_cube)
    collection.objects.link(sol_cube)
    bpy.context.scene.collection.objects.unlink(sol_cube)

def create_axis_tick(axis, value, color_rgba, collection):
    loc = {
        'x': (value, 0, 0),
        'y': (0, value, 0),
        'z': (0, 0, value)
    }[axis]
    bpy.ops.mesh.primitive_cube_add(size=0.18, location=loc)
    tick = bpy.context.active_object
    tick.name = f"{axis.upper()}_Tick_{value}"
    mat = create_material(f"{axis.upper()}_Tick_Mat", color_rgba, emission_strength=0.7)
    tick.data.materials.append(mat)
    collection.objects.link(tick)
    bpy.context.scene.collection.objects.unlink(tick)
    # Add number label
    create_text_object(str(value), f"{axis.upper()}_Tick_Label_{value}", 0.3, (loc[0], loc[1], loc[2]+0.3), mat, collection)
    return tick

def create_variable_sphere(var_name, color_rgba, location, collection):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=location)
    sphere = bpy.context.active_object
    sphere.name = f"{var_name}_Sphere"
    mat = create_material(f"{var_name}_Mat", color_rgba, emission_strength=1.0)
    sphere.data.materials.append(mat)
    collection.objects.link(sphere)
    bpy.context.scene.collection.objects.unlink(sphere)
    set_visible(sphere)
    # Add label with matching color
    label = create_text_object(var_name, f"{var_name}_Label", 0.5, (location[0], location[1], location[2]+0.5), mat, collection)
    label.color = color_rgba
    set_visible(label)
    return sphere

def main_animation_script():
    """Main function to create and animate the math explanation."""
    clear_scene()
    setup_render_settings()
    setup_camera_and_light()

    # --- Materials ---
    # Standard white text material (default)
    mat_white = create_material("WhiteText", (1, 1, 1, 1))

    # Highlight materials (with some emission for glow effect)
    mat_red_highlight = create_material("RedHighlight", (1, 0, 0, 1), emission_strength=1.0)
    mat_blue_highlight = create_material("BlueHighlight", (0, 0, 1, 1), emission_strength=1.0)
    mat_green_highlight = create_material("GreenHighlight", (0, 1, 0, 1), emission_strength=1.0)
    mat_yellow_highlight = create_material("YellowHighlight", (1, 1, 0, 1), emission_strength=1.0)
    mat_purple_highlight = create_material("PurpleHighlight", (0.5, 0, 0.5, 1), emission_strength=1.0)

    # Main collection for all animated objects
    math_collection = bpy.data.collections.new("MathAnimation")
    bpy.context.scene.collection.children.link(math_collection)

    # Add axes and grid
    setup_axes_and_grid(math_collection)

    # Add variable spheres for x and y (distinct colors)
    x_sphere = create_variable_sphere('x', (1,0,0,1), (0,0,0.3), math_collection)
    y_sphere = create_variable_sphere('y', (0,1,0,1), (0,0,0.3), math_collection)

    # Animate x and y spheres along the solution curve: y = (6 - 2x)/4, 0 < x < 3
    frames = 60
    for i in range(frames+1):
        t = i / frames
        x_val = 0 + t * 3
        y_val = (6 - 2*x_val) / 4
        frame_num = 1 + i
        # Animate x sphere
        x_sphere.location = (x_val, 0, 0.3)
        x_sphere.keyframe_insert(data_path="location", frame=frame_num)
        # Animate y sphere
        y_sphere.location = (x_val, y_val, 0.3)
        y_sphere.keyframe_insert(data_path="location", frame=frame_num)
        # Highlight current tick
        if i % 10 == 0 or i == frames:
            tick_x_name = f"X_Tick_{round(x_val)}"
            tick_y_name = f"Y_Tick_{round(y_val)}"
            if tick_x_name in bpy.data.objects:
                tick_x = bpy.data.objects[tick_x_name]
                animate_material_color_change(tick_x, frame_num, 10, (1,1,0,1), (1,0,0,1), emission_strength=1.0)
            if tick_y_name in bpy.data.objects:
                tick_y = bpy.data.objects[tick_y_name]
                animate_material_color_change(tick_y, frame_num, 10, (1,1,0,1), (0,1,0,1), emission_strength=1.0)
    animate_visibility(x_sphere, 1, frames, visible=True)
    animate_visibility(y_sphere, 1, frames, visible=True)

    current_frame = 1

    # --- Section: Title ---
    title_text_str = "Find x and y variables in the equation 2x + 4y - 6 = 0 if 0 < x < 4 and 0 < y < 5"
    obj_title = create_text_object(title_text_str, "Title", 0.8, (0, 4, 0), mat_white, math_collection)
    
    # Initial state is hidden
    obj_title.hide_viewport = True
    obj_title.hide_render = True
    select_and_activate_object(obj_title)
    obj_title.keyframe_insert(data_path="hide_viewport", frame=current_frame)
    obj_title.keyframe_insert(data_path="hide_render", frame=current_frame)

    # Make visible
    animate_visibility(obj_title, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_FADE # Appear duration
    current_frame += 120 # Stay for 120 frames

    # Fade out using material alpha and then hide
    animate_fade_out_material(obj_title, current_frame, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    # --- Section: Equation Introduction ---
    # "2x + 4y - 6 = 0"
    eq_intro_parts_data = [
        {"text": "2x", "name_suffix": "_2x", "base_x": -2.5},
        {"text": " + 4y", "name_suffix": "_plus_4y", "base_x": -1.0},
        {"text": " - 6 = 0", "name_suffix": "_minus_6_equals_0", "base_x": 1.2},
    ]
    eq_intro_objects = []
    
    # Create objects and set initial hidden state
    for i, part in enumerate(eq_intro_parts_data):
        obj = create_text_object(
            part["text"], f"EqIntro{part['name_suffix']}", 1.0, 
            (part["base_x"], 0, 0), # Temporary location for creation
            mat_white, math_collection,
            align_x='LEFT' # Adjust alignment for multi-part text
        )
        eq_intro_objects.append(obj)

    current_frame += 30 # Short pause after title fades
    
    slide_start_x = -10 # Starting X position for the whole group
    for obj_idx, obj in enumerate(eq_intro_objects):
        # Calculate actual start_loc for each object relative to the group's slide
        # obj.location initially holds the intended final local position (e.g., (-2.5, 0, 0))
        start_loc = (slide_start_x + eq_intro_parts_data[obj_idx]["base_x"], obj.location.y, obj.location.z)
        end_loc = obj.location.copy() # The location it was created with is its final resting place
        
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True) # Make visible during slide
    
    current_frame += DURATION_SLIDE + 90 # Slide in (30) + Stay (90)

    # --- Section: Constraint Introduction ---
    constraint_text_str = "Constraints: 0 < x < 4 and 0 < y < 5"
    obj_constraints = create_text_object(constraint_text_str, "Constraints", 0.7, (0, -2, 0), mat_white, math_collection)
    
    slide_start_loc = (10, -2, 0)
    slide_end_loc = (0, -2, 0)
    animate_location(obj_constraints, current_frame, DURATION_SLIDE, slide_start_loc, slide_end_loc)
    animate_visibility(obj_constraints, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE + 60 # Slide in (30) + Stay (60)

    # --- Section: Step 1: Isolate x and y terms ---
    # Fade out previous equation (eq_intro_objects)
    fade_start = current_frame
    for obj in eq_intro_objects:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    # New equation: "2x + 4y = 6"
    eq1_parts_data = [
        {"text": "2x + 4y", "name_suffix": "_2x_plus_4y", "base_x": -1.0},
        {"text": " = ", "name_suffix": "_equals", "base_x": 0.5},
        {"text": "6", "name_suffix": "_6", "base_x": 1.2},
    ]
    eq1_objects = []
    
    for i, part in enumerate(eq1_parts_data):
        obj = create_text_object(
            part["text"], f"Eq1{part['name_suffix']}", 1.0, 
            (part["base_x"], 0, 0), # Temporary location for creation
            mat_white, math_collection,
            align_x='LEFT'
        )
        eq1_objects.append(obj)

    slide_start_y = 5 # From top
    for obj_idx, obj in enumerate(eq1_objects):
        start_loc = (obj.location.x, slide_start_y, obj.location.z)
        end_loc = obj.location.copy()
        
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    # Highlight "2x + 4y" in yellow, "6" in green
    animate_material_color_change(eq1_objects[0], current_frame, DURATION_HIGHLIGHT, mat_yellow_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    animate_material_color_change(eq1_objects[2], current_frame, DURATION_HIGHLIGHT, mat_green_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30 # Highlight (60) + Pause (30)

    # --- Section: Step 2: Express y in terms of x ---
    # Fade out previous equation (eq1_objects) and constraints
    fade_start = current_frame
    for obj in eq1_objects:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    animate_fade_out_material(obj_constraints, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    # New equation: "4y = 6 - 2x"
    eq2_parts_data = [
        {"text": "4y", "name_suffix": "_4y", "base_x": -1.0},
        {"text": " = ", "name_suffix": "_equals", "base_x": 0.0},
        {"text": "6 - 2x", "name_suffix": "_6minus2x", "base_x": 1.0},
    ]
    eq2_objects = []
    for i, part in enumerate(eq2_parts_data):
        obj = create_text_object(
            part["text"], f"Eq2{part['name_suffix']}", 1.0, 
            (part["base_x"], 0, 0), mat_white, math_collection, align_x='LEFT'
        )
        eq2_objects.append(obj)
    
    slide_start_x = 10 # From right
    for obj_idx, obj in enumerate(eq2_objects):
        start_loc = (slide_start_x + eq2_parts_data[obj_idx]["base_x"], obj.location.y, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    # Highlight "6 - 2x" in blue
    animate_material_color_change(eq2_objects[2], current_frame, DURATION_HIGHLIGHT, mat_blue_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # New equation: "y = (6 - 2x) / 4"
    fade_start = current_frame
    for obj in eq2_objects:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    eq3_parts_data = [
        {"text": "y", "name_suffix": "_y", "base_x": -1.0},
        {"text": " = ", "name_suffix": "_equals", "base_x": -0.5},
        {"text": "(6 - 2x) / 4", "name_suffix": "_expr", "base_x": 1.0},
    ]
    eq3_objects = []
    for i, part in enumerate(eq3_parts_data):
        obj = create_text_object(
            part["text"], f"Eq3{part['name_suffix']}", 1.0, 
            (part["base_x"], 0, 0), mat_white, math_collection, align_x='LEFT'
        )
        eq3_objects.append(obj)

    slide_start_y = -5 # From bottom
    for obj_idx, obj in enumerate(eq3_objects):
        start_loc = (obj.location.x, slide_start_y, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    # Highlight "y" in red
    animate_material_color_change(eq3_objects[0], current_frame, DURATION_HIGHLIGHT, mat_red_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # --- Section: Step 3: Apply Constraints to x ---
    # Recall: 0 < x < 4
    recall_x_constraint_str = "Recall: 0 < x < 4"
    obj_recall_x = create_text_object(recall_x_constraint_str, "RecallXConstraint", 0.7, (0, 2, 0), mat_white, math_collection)
    animate_visibility(obj_recall_x, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_FADE # Appear duration
    current_frame += 60 # Stay for 60 frames

    # Since y = (6 - 2x) / 4 and 0 < y < 5
    since_y_text_str = "Since y = (6 - 2x) / 4 and 0 < y < 5"
    obj_since_y = create_text_object(since_y_text_str, "SinceYExpr", 0.7, (0, 0, 0), mat_white, math_collection)
    animate_visibility(obj_since_y, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_FADE # Appear duration
    current_frame += 60 # Stay for 60 frames

    # Fade out recall text and y expression text
    fade_start = current_frame
    animate_fade_out_material(obj_recall_x, fade_start, DURATION_FADE, (1,1,1,1))
    animate_fade_out_material(obj_since_y, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    # 0 < (6 - 2x) / 4 < 5
    ineq1_parts_data = [
        {"text": "0 < ", "name_suffix": "_0less", "base_x": -2.0},
        {"text": "(6 - 2x) / 4", "name_suffix": "_expr", "base_x": 0.0},
        {"text": " < 5", "name_suffix": "_less5", "base_x": 2.0},
    ]
    ineq1_objects = []
    target_y_pos_ineq1 = -2 # Desired Y position for the whole inequality
    for i, part in enumerate(ineq1_parts_data):
        obj = create_text_object(
            part["text"], f"Ineq1{part['name_suffix']}", 1.0, 
            (part["base_x"], target_y_pos_ineq1, 0), mat_white, math_collection, align_x='LEFT'
        )
        ineq1_objects.append(obj)

    slide_start_x = -10 # From left
    for obj_idx, obj in enumerate(ineq1_objects):
        start_loc = (slide_start_x + ineq1_parts_data[obj_idx]["base_x"], target_y_pos_ineq1, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    # Highlight "(6 - 2x) / 4" in purple
    animate_material_color_change(ineq1_objects[1], current_frame, DURATION_HIGHLIGHT, mat_purple_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # --- Section: Step 4: Solve the inequality for x ---
    # Fade out previous inequality (ineq1_objects) and eq3_objects (y = ...)
    fade_start = current_frame
    for obj in ineq1_objects + eq3_objects:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    # Multiply by 4: 0 < 6 - 2x < 20
    ineq2_parts_data = [
        {"text": "0 < ", "name_suffix": "_0less", "base_x": -2.0},
        {"text": "6 - 2x", "name_suffix": "_6minus2x", "base_x": 0.0},
        {"text": " < 20", "name_suffix": "_less20", "base_x": 2.0},
    ]
    ineq2_objects = []
    for i, part in enumerate(ineq2_parts_data):
        obj = create_text_object(
            part["text"], f"Ineq2{part['name_suffix']}", 1.0, 
            (part["base_x"], 0, 0), mat_white, math_collection, align_x='LEFT'
        )
        ineq2_objects.append(obj)
    
    slide_start_y = 5 # From top
    for obj_idx, obj in enumerate(ineq2_objects):
        start_loc = (obj.location.x, slide_start_y, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    # Highlight "6 - 2x" in yellow
    animate_material_color_change(ineq2_objects[1], current_frame, DURATION_HIGHLIGHT, mat_yellow_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # Subtract 6: -6 < -2x < 14
    fade_start = current_frame
    for obj in ineq2_objects:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    ineq3_parts_data = [
        {"text": "-6 < ", "name_suffix": "_minus6less", "base_x": -2.0},
        {"text": "-2x", "name_suffix": "_minus2x", "base_x": 0.0},
        {"text": " < 14", "name_suffix": "_less14", "base_x": 2.0},
    ]
    ineq3_objects = []
    for i, part in enumerate(ineq3_parts_data):
        obj = create_text_object(
            part["text"], f"Ineq3{part['name_suffix']}", 1.0, 
            (part["base_x"], 0, 0), mat_white, math_collection, align_x='LEFT'
        )
        ineq3_objects.append(obj)

    slide_start_x = 10 # From right
    for obj_idx, obj in enumerate(ineq3_objects):
        start_loc = (slide_start_x + ineq3_parts_data[obj_idx]["base_x"], obj.location.y, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    # Highlight "-2x" in green
    animate_material_color_change(ineq3_objects[1], current_frame, DURATION_HIGHLIGHT, mat_green_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # Divide by -2 (reverse signs): 3 > x > -7
    fade_start = current_frame
    for obj in ineq3_objects:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    ineq4_parts_data = [
        {"text": "3 > ", "name_suffix": "_3greater", "base_x": -2.0},
        {"text": "x", "name_suffix": "_x", "base_x": 0.0},
        {"text": " > -7", "name_suffix": "_greaterMinus7", "base_x": 2.0},
    ]
    ineq4_objects = []
    for i, part in enumerate(ineq4_parts_data):
        obj = create_text_object(
            part["text"], f"Ineq4{part['name_suffix']}", 1.0, 
            (part["base_x"], 0, 0), mat_white, math_collection, align_x='LEFT'
        )
        ineq4_objects.append(obj)

    slide_start_y = -5 # From bottom
    for obj_idx, obj in enumerate(ineq4_objects):
        start_loc = (obj.location.x, slide_start_y, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    # Highlight "x" in red
    animate_material_color_change(ineq4_objects[1], current_frame, DURATION_HIGHLIGHT, mat_red_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # Combined with 0 < x < 4, we get 0 < x < 3
    combined_text_str = "Combined with 0 < x < 4, we get"
    obj_combined_text = create_text_object(combined_text_str, "CombinedText", 0.7, (0, 0.5, 0), mat_white, math_collection)
    
    final_x_ineq_parts_data = [
        {"text": "0 < ", "name_suffix": "_0less", "base_x": -2.0},
        {"text": "x", "name_suffix": "_x", "base_x": 0.0},
        {"text": " < 3", "name_suffix": "_less3", "base_x": 2.0},
    ]
    final_x_objects = []
    target_y_pos_final_x = -2 # Desired Y position for this inequality
    for i, part in enumerate(final_x_ineq_parts_data):
        obj = create_text_object(
            part["text"], f"FinalX{part['name_suffix']}", 1.0, 
            (part["base_x"], target_y_pos_final_x, 0), mat_white, math_collection, align_x='LEFT'
        )
        final_x_objects.append(obj)
    
    # Slide in the combined text first
    animate_location(obj_combined_text, current_frame, DURATION_SLIDE, (-10, 0.5, 0), (0, 0.5, 0))
    animate_visibility(obj_combined_text, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE # For combined text

    # Then slide in the inequality
    slide_start_x_final_x = -10
    for obj_idx, obj in enumerate(final_x_objects):
        start_loc = (slide_start_x_final_x + final_x_ineq_parts_data[obj_idx]["base_x"], target_y_pos_final_x, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE
    
    # Highlight "0 < x < 3" in blue
    for obj_part in final_x_objects:
        animate_material_color_change(obj_part, current_frame, DURATION_HIGHLIGHT, mat_blue_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # --- Section: Step 5: Find the range for y ---
    # Fade out previous inequalities (ineq4_objects, final_x_objects) and combined text
    fade_start = current_frame
    for obj in ineq4_objects + final_x_objects + [obj_combined_text]:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    # Recall: y = (6 - 2x) / 4 and 0 < x < 3
    recall_y_expr_str = "Recall: y = (6 - 2x) / 4 and 0 < x < 3"
    obj_recall_y = create_text_object(recall_y_expr_str, "RecallYExpr", 0.7, (0, 2, 0), mat_white, math_collection)
    animate_visibility(obj_recall_y, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_FADE
    current_frame += 60 # Stay

    # Substitute x=0: y = (6 - 2*0) / 4 = 6 / 4 = 1.5
    sub_x0_str = "Substitute x=0: y = (6 - 2*0) / 4 = 6 / 4 = 1.5"
    obj_sub_x0 = create_text_object(sub_x0_str, "SubX0", 0.8, (0, 0.5, 0), mat_white, math_collection)
    animate_location(obj_sub_x0, current_frame, DURATION_SLIDE, (10, 0.5, 0), (0, 0.5, 0))
    animate_visibility(obj_sub_x0, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE
    current_frame += 30 # Short pause after slide

    # Substitute x=3: y = (6 - 2*3) / 4 = 0 / 4 = 0
    sub_x3_str = "Substitute x=3: y = (6 - 2*3) / 4 = 0 / 4 = 0"
    obj_sub_x3 = create_text_object(sub_x3_str, "SubX3", 0.8, (0, -0.5, 0), mat_white, math_collection)
    animate_location(obj_sub_x3, current_frame, DURATION_SLIDE, (10, -0.5, 0), (0, -0.5, 0))
    animate_visibility(obj_sub_x3, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE
    current_frame += 30 # Short pause after slide
    
    # Fade out recall text and substitution lines
    fade_start = current_frame
    for obj in [obj_recall_y, obj_sub_x0, obj_sub_x3]:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    # So, 0 < y < 1.5
    final_y_ineq_parts_data = [
        {"text": "0 < ", "name_suffix": "_0less", "base_x": -2.0},
        {"text": "y", "name_suffix": "_y", "base_x": 0.0},
        {"text": " < 1.5", "name_suffix": "_less1_5", "base_x": 2.0},
    ]
    final_y_objects = []
    target_y_pos_final_y = -2 # Desired Y position for this inequality
    for i, part in enumerate(final_y_ineq_parts_data):
        obj = create_text_object(
            part["text"], f"FinalY{part['name_suffix']}", 1.0, 
            (part["base_x"], target_y_pos_final_y, 0), mat_white, math_collection, align_x='LEFT'
        )
        final_y_objects.append(obj)
    
    slide_start_y = -7 # From bottom
    for obj_idx, obj in enumerate(final_y_objects):
        start_loc = (obj.location.x, slide_start_y, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    # Highlight "0 < y < 1.5" in purple
    for obj_part in final_y_objects:
        animate_material_color_change(obj_part, current_frame, DURATION_HIGHLIGHT, mat_purple_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # --- Section: Conclusion ---
    # Fade out final_y_objects
    fade_start = current_frame
    for obj in final_y_objects:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE

    # Final Answer:
    obj_final_answer_title = create_text_object("Final Answer:", "FinalAnswerTitle", 0.9, (0, 2, 0), mat_white, math_collection)
    animate_visibility(obj_final_answer_title, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_FADE
    current_frame += 60 # Stay

    # The variables x and y for the equation 2x + 4y - 6 = 0
    obj_final_eq_context = create_text_object("The variables x and y for the equation 2x + 4y - 6 = 0", "FinalEqContext", 0.8, (0, 0.5, 0), mat_white, math_collection)
    animate_location(obj_final_eq_context, current_frame, DURATION_SLIDE, (-10, 0.5, 0), (0, 0.5, 0))
    animate_visibility(obj_final_eq_context, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE
    current_frame += 30 # Short pause

    # with constraints 0 < x < 4 and 0 < y < 5 are:
    obj_final_constraints_context = create_text_object("with constraints 0 < x < 4 and 0 < y < 5 are:", "FinalConstraintsContext", 0.8, (0, -0.5, 0), mat_white, math_collection)
    animate_location(obj_final_constraints_context, current_frame, DURATION_SLIDE, (-10, -0.5, 0), (0, -0.5, 0))
    animate_visibility(obj_final_constraints_context, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE
    current_frame += 30 # Short pause

    # Fade out title and context text
    fade_start = current_frame
    for obj in [obj_final_answer_title, obj_final_eq_context, obj_final_constraints_context]:
        animate_fade_out_material(obj, fade_start, DURATION_FADE, (1,1,1,1))
    current_frame += DURATION_FADE + 30 # Extra pause before final answer


    # 0 < x < 3
    final_x_result_parts_data = [
        {"text": "0 < ", "name_suffix": "_0less", "base_x": -2.0},
        {"text": "x", "name_suffix": "_x", "base_x": 0.0},
        {"text": " < 3", "name_suffix": "_less3", "base_x": 2.0},
    ]
    final_x_result_objects = []
    target_y_pos_final_x_result = -2.5
    for i, part in enumerate(final_x_result_parts_data):
        obj = create_text_object(
            part["text"], f"FinalResultX{part['name_suffix']}", 1.2, 
            (part["base_x"], target_y_pos_final_x_result, 0), mat_white, math_collection, align_x='LEFT'
        )
        final_x_result_objects.append(obj)
    
    slide_start_x = 10 # From right
    for obj_idx, obj in enumerate(final_x_result_objects):
        start_loc = (slide_start_x + final_x_result_parts_data[obj_idx]["base_x"], target_y_pos_final_x_result, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE
    
    for obj_part in final_x_result_objects:
        animate_material_color_change(obj_part, current_frame, DURATION_HIGHLIGHT, mat_yellow_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30

    # 0 < y < 1.5
    final_y_result_parts_data = [
        {"text": "0 < ", "name_suffix": "_0less", "base_x": -2.0},
        {"text": "y", "name_suffix": "_y", "base_x": 0.0},
        {"text": " < 1.5", "name_suffix": "_less1_5", "base_x": 2.0},
    ]
    final_y_result_objects = []
    target_y_pos_final_y_result = -3.5
    for i, part in enumerate(final_y_result_parts_data):
        obj = create_text_object(
            part["text"], f"FinalResultY{part['name_suffix']}", 1.2, 
            (part["base_x"], target_y_pos_final_y_result, 0), mat_white, math_collection, align_x='LEFT'
        )
        final_y_result_objects.append(obj)

    slide_start_x = 10 # From right
    for obj_idx, obj in enumerate(final_y_result_objects):
        start_loc = (slide_start_x + final_y_result_parts_data[obj_idx]["base_x"], target_y_pos_final_y_result, obj.location.z)
        end_loc = obj.location.copy()
        animate_location(obj, current_frame, DURATION_SLIDE, start_loc, end_loc)
        animate_visibility(obj, current_frame, DURATION_FADE, visible=True)
    current_frame += DURATION_SLIDE

    for obj_part in final_y_result_objects:
        animate_material_color_change(obj_part, current_frame, DURATION_HIGHLIGHT, mat_green_highlight.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value, (1, 1, 1, 1), emission_strength=1.0)
    current_frame += DURATION_HIGHLIGHT + 30
    
    # Set final frame
    bpy.context.scene.frame_end = current_frame + 60 # Add some buffer at the end

# Run the script
if __name__ == "__main__":
    main_animation_script()
