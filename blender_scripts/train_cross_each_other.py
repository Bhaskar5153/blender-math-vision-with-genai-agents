import bpy
import bmesh
from math import radians
import os # While not directly used for path access, it's good practice for general Python scripts

# --- Configuration ---
FPS = 25
TOTAL_ANIMATION_SECONDS = 14 # Total duration in seconds
TOTAL_FRAMES = int(TOTAL_ANIMATION_SECONDS * FPS)

# Dimensions (scaled down for Blender units, e.g., 1 Blender unit = 10 meters)
SCALE_FACTOR = 2  # Lower scale factor for larger objects
TRAIN_WIDTH = 4.0 / SCALE_FACTOR
TRAIN_HEIGHT = 6.0 / SCALE_FACTOR
TRAIN_A_LENGTH_REAL = 200.0
TRAIN_B_LENGTH_REAL = 300.0
TRAIN_A_LENGTH = TRAIN_A_LENGTH_REAL / SCALE_FACTOR
TRAIN_B_LENGTH = TRAIN_B_LENGTH_REAL / SCALE_FACTOR
INITIAL_SEPARATION_REAL = 500.0 # Initial distance between centers of trains
INITIAL_SEPARATION = INITIAL_SEPARATION_REAL / SCALE_FACTOR

# Visual text parameters
TEXT_SCALE_BASE = 0.08 # Base scale for text objects
TEXT_DEPTH = 0.02 # Extrusion depth for text
TEXT_OFFSET_Y = -0.5 # Offset text slightly forward in Y

# Animation timing (in frames)
FADE_DURATION_FRAMES = int(1 * FPS) # 1 second
HOLD_DURATION_FRAMES = int(1.5 * FPS) # 1.5 seconds
MOVE_DURATION_FRAMES = int(5 * FPS) # 5 seconds for trains to meet
HIGHLIGHT_DURATION_FRAMES = int(1 * FPS) # 1 second for highlight
SEPARATION_DURATION_FRAMES = int(2 * FPS) # 2 seconds for trains to separate

# --- Utility Functions ---

def clear_scene():
    """Clear all existing objects in the scene."""
    bpy.ops.object.select_all(action='DESELECT')
    if bpy.data.objects:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
    # Remove all collections except the default 'Collection'
    for coll in list(bpy.data.collections):
        if coll.name != 'Collection':
            bpy.data.collections.remove(coll)
    # Ensure the default collection exists and is linked to the scene
    if 'Collection' not in bpy.data.collections:
        bpy.data.collections.new('Collection')
    if 'Collection' not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(bpy.data.collections['Collection'])
    # Clear all meshes, materials, and curves (fonts)
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block)
    for block in bpy.data.curves:
        bpy.data.curves.remove(block)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 250
    bpy.context.scene.frame_current = 1


def create_collection(name, parent_collection=None):
    """Create a new collection or get an existing one."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    
    new_collection = bpy.data.collections.new(name)
    if parent_collection:
        parent_collection.children.link(new_collection)
    else:
        bpy.context.scene.collection.children.link(new_collection)
    return new_collection

def create_material(name, base_color=(1, 1, 1, 1), emission_color=(0, 0, 0, 1), emission_strength=0.0):
    """Create a new material with a given color and optional emission."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = base_color
        bsdf.inputs['Emission Color'].default_value = emission_color
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    else:
        # Fallback for older Blender versions or if Principled BSDF isn't default
        if not mat.node_tree.nodes:
            mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
            mat.node_tree.links.new(mat.node_tree.nodes['Principled BSDF'].outputs['BSDF'], 
                                   mat.node_tree.nodes['Material Output'].inputs['Surface'])
            bsdf = mat.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = base_color
            bsdf.inputs['Emission Color'].default_value = emission_color
            bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat

def create_text_object(name, text_content, font_size_multiplier=1.0, collection=None):
    """Create a Blender text object with explicit selection management."""
    curve_data = bpy.data.curves.new(name=f'{name}_Curve', type='FONT')
    curve_data.body = text_content
    curve_data.align_x = 'CENTER'
    curve_data.align_y = 'CENTER'
    curve_data.size = TEXT_SCALE_BASE * font_size_multiplier
    curve_data.extrude = TEXT_DEPTH

    text_obj = bpy.data.objects.new(name, curve_data)

    if collection:
        collection.objects.link(text_obj)
        # Unlink from default 'Collection' if it was linked there by default
        if text_obj.name in bpy.data.collections.get('Collection', []).objects:
            bpy.data.collections['Collection'].objects.unlink(text_obj)
    
    # Select and activate the object before modification, then deselect
    bpy.ops.object.select_all(action='DESELECT')
    text_obj.select_set(True)
    bpy.context.view_layer.objects.active = text_obj
    
    # Ensure text is rendered smoothly
    text_obj.data.resolution_u = 3 # Increase resolution for smoother text curves
    
    text_obj.select_set(False)
    bpy.context.view_layer.objects.active = None
    
    return text_obj

def fade_object_visibility(obj, start_frame, duration_frames, fade_in=True):
    """Animates the hide_viewport and hide_render properties of an object."""
    end_frame = start_frame + duration_frames
    
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Keyframe initial state
    obj.hide_viewport = not fade_in
    obj.hide_render = not fade_in
    obj.keyframe_insert(data_path='hide_viewport', frame=start_frame)
    obj.keyframe_insert(data_path='hide_render', frame=start_frame)
    
    # Keyframe final state
    obj.hide_viewport = fade_in
    obj.hide_render = fade_in
    obj.keyframe_insert(data_path='hide_viewport', frame=end_frame)
    obj.keyframe_insert(data_path='hide_render', frame=end_frame)
        
    obj.select_set(False)
    bpy.context.view_layer.objects.active = None

def animate_material_emission(obj, material_name, start_frame, duration_frames, highlight_emission_color, normal_emission_color=(0,0,0,1)):
    """Animates the emission color and strength of a material."""
    mat = bpy.data.materials.get(material_name)
    if not mat or not mat.use_nodes:
        print(f"Material {material_name} not found or not using nodes.")
        return

    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if not bsdf:
        print("Principled BSDF node not found in material.")
        return

    # Start of highlight (return to normal)
    bsdf.inputs['Emission Color'].default_value = normal_emission_color
    bsdf.inputs['Emission Strength'].default_value = 0.0
    bsdf.inputs['Emission Color'].keyframe_insert(data_path="default_value", frame=start_frame)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=start_frame)

    # Peak highlight
    bsdf.inputs['Emission Color'].default_value = highlight_emission_color
    bsdf.inputs['Emission Strength'].default_value = 5.0 # Strong emission
    bsdf.inputs['Emission Color'].keyframe_insert(data_path="default_value", frame=start_frame + duration_frames // 2)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=start_frame + duration_frames // 2)
    
    # End of highlight, return to normal
    bsdf.inputs['Emission Color'].default_value = normal_emission_color
    bsdf.inputs['Emission Strength'].default_value = 0.0
    bsdf.inputs['Emission Color'].keyframe_insert(data_path="default_value", frame=start_frame + duration_frames)
    bsdf.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=start_frame + duration_frames)

# --- Main Script ---

def create_train_animation():
    clear_scene() # Start with a clean scene

    # --- Scene Setup ---
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = TOTAL_FRAMES
    bpy.context.scene.frame_current = 1
    
    # Set render engine to Eevee (faster for simple animations and good for emission)
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'

    # --- Creative Background ---
    # Add a large green plane for grass
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0,0,-0.1))
    grass = bpy.context.active_object
    grass.name = 'Grass'
    mat_grass = create_material('GrassMat', base_color=(0.2, 0.6, 0.2, 1))
    grass.data.materials.append(mat_grass)
    # Add a blue sky dome
    bpy.ops.mesh.primitive_uv_sphere_add(radius=60, location=(0,0,30), segments=64, ring_count=32)
    sky = bpy.context.active_object
    sky.name = 'SkyDome'
    mat_sky = create_material('SkyMat', base_color=(0.5, 0.7, 1.0, 1))
    sky.data.materials.append(mat_sky)
    sky.scale = (1,1,0.5)
    sky.hide_render = False

    # --- Collections ---
    main_collection = create_collection("Animation_Main")
    trains_collection = create_collection("Trains", parent_collection=main_collection)
    text_collection = create_collection("Text_Elements", parent_collection=main_collection)
    environment_collection = create_collection("Environment", parent_collection=main_collection)
    environment_collection.objects.link(grass)
    environment_collection.objects.link(sky)

    # --- Materials ---
    mat_train_a = create_material("TrainAMat", base_color=(0.1, 0.6, 1.0, 1)) # Blue
    mat_train_b = create_material("TrainBMat", base_color=(1.0, 0.3, 0.1, 1)) # Orange
    mat_track = create_material("TrackMat", base_color=(0.1, 0.1, 0.1, 1)) # Black
    mat_text_white = create_material("TextWhiteMat", base_color=(1.0, 1.0, 1.0, 1))
    mat_text_yellow = create_material("TextYellowMat", base_color=(1.0, 1.0, 0.0, 1))
    
    # --- Camera Setup ---
    cam_data = bpy.data.cameras.new("Main_Camera")
    cam_obj = bpy.data.objects.new("Main_Camera", cam_data)
    environment_collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    cam_obj.location = (0, -40, 18)
    cam_obj.rotation_euler = (radians(70), 0, 0) # Look down and slightly forward

    # --- Lighting Setup ---
    light_data = bpy.data.lights.new("Main_Sun_Light", type='SUN')
    light_obj = bpy.data.objects.new("Main_Sun_Light", light_data)
    environment_collection.objects.link(light_obj)
    
    bpy.ops.object.select_all(action='DESELECT')
    light_obj.select_set(True)
    bpy.context.view_layer.objects.active = light_obj
    
    light_obj.location = (0, -2 * INITIAL_SEPARATION, 2 * INITIAL_SEPARATION)
    light_obj.rotation_euler = (radians(-45), radians(0), radians(45))
    light_data.energy = 5.0
    
    light_obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    # --- Ground/Track ---
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
    track_obj = bpy.context.active_object
    track_obj.name = "Track"
    track_obj.scale = (40, 1.2, 0.15)
    track_obj.data.materials.append(mat_track)
    environment_collection.objects.link(track_obj)
    bpy.context.scene.collection.objects.unlink(track_obj)

    # --- Train A ---
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
    train_a_obj = bpy.context.active_object
    train_a_obj.name = "Train_A"
    train_a_obj.scale = (TRAIN_A_LENGTH / 2, TRAIN_WIDTH / 2, TRAIN_HEIGHT / 2)
    train_a_obj.location = (-INITIAL_SEPARATION / 2, 0, TRAIN_HEIGHT / 2 + 0.15)
    train_a_obj.data.materials.append(mat_train_a)
    trains_collection.objects.link(train_a_obj)
    bpy.context.scene.collection.objects.unlink(train_a_obj)

    # --- Train B ---
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
    train_b_obj = bpy.context.active_object
    train_b_obj.name = "Train_B"
    train_b_obj.scale = (TRAIN_B_LENGTH / 2, TRAIN_WIDTH / 2, TRAIN_HEIGHT / 2)
    train_b_obj.location = (INITIAL_SEPARATION / 2, 0, TRAIN_HEIGHT / 2 + 0.15)
    train_b_obj.data.materials.append(mat_train_b)
    trains_collection.objects.link(train_b_obj)
    bpy.context.scene.collection.objects.unlink(train_b_obj)

    # --- Text Elements ---
    
    # Preprocess text strings as per requirement
    text_separation_content = f"Initial Separation: {INITIAL_SEPARATION_REAL:.0f}m"
    text_train_a_label_content = "Train A"
    text_train_a_length_content = f"Length: {TRAIN_A_LENGTH_REAL:.0f}m"
    text_train_b_label_content = "Train B"
    text_train_b_length_content = f"Length: {TRAIN_B_LENGTH_REAL:.0f}m"
    text_direction_content = "Running in opposite directions"
    text_meeting_point_content = "Meeting Point!"
    
    text_separation = create_text_object("Text_Separation", text_separation_content, 1.2, collection=text_collection)
    text_separation.location = (0, TEXT_OFFSET_Y, TRAIN_HEIGHT + 0.5)
    text_separation.data.materials.append(mat_text_white)
    
    text_train_a_label = create_text_object("Text_Train_A_Label", text_train_a_label_content, 1.0, collection=text_collection)
    text_train_a_label.location = (train_a_obj.location.x, TEXT_OFFSET_Y, TRAIN_HEIGHT + 0.3)
    text_train_a_label.data.materials.append(mat_text_white)

    text_train_a_length = create_text_object("Text_Train_A_Length", text_train_a_length_content, 0.8, collection=text_collection)
    text_train_a_length.location = (train_a_obj.location.x, TEXT_OFFSET_Y, TRAIN_HEIGHT + 0.1)
    text_train_a_length.data.materials.append(mat_text_white)

    text_train_b_label = create_text_object("Text_Train_B_Label", text_train_b_label_content, 1.0, collection=text_collection)
    text_train_b_label.location = (train_b_obj.location.x, TEXT_OFFSET_Y, TRAIN_HEIGHT + 0.3)
    text_train_b_label.data.materials.append(mat_text_white)

    text_train_b_length = create_text_object("Text_Train_B_Length", text_train_b_length_content, 0.8, collection=text_collection)
    text_train_b_length.location = (train_b_obj.location.x, TEXT_OFFSET_Y, TRAIN_HEIGHT + 0.1)
    text_train_b_length.data.materials.append(mat_text_white)

    text_direction = create_text_object("Text_Direction", text_direction_content, 1.2, collection=text_collection)
    text_direction.location = (0, TEXT_OFFSET_Y, TRAIN_HEIGHT + 0.5)
    text_direction.data.materials.append(mat_text_white)
    
    text_meeting_point = create_text_object("Text_Meeting_Point", text_meeting_point_content, 1.5, collection=text_collection)
    text_meeting_point.location = (0, TEXT_OFFSET_Y, TRAIN_HEIGHT + 0.5)
    text_meeting_point.data.materials.append(mat_text_yellow)
    
    # --- Animation ---
    current_frame = bpy.context.scene.frame_start

    # Ensure all text objects are hidden initially
    text_objects_to_hide = [
        text_separation, text_train_a_label, text_train_a_length, 
        text_train_b_label, text_train_b_length, text_direction, text_meeting_point
    ]
    for obj in text_objects_to_hide:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path='hide_viewport', frame=current_frame)
        obj.keyframe_insert(data_path='hide_render', frame=current_frame)
        obj.select_set(False)
        bpy.context.view_layer.objects.active = None
        
    # 1. Fade in initial setup texts (Train A/B labels, lengths, initial separation)
    fade_object_visibility(text_separation, current_frame, FADE_DURATION_FRAMES, fade_in=True)
    fade_object_visibility(text_train_a_label, current_frame, FADE_DURATION_FRAMES, fade_in=True)
    fade_object_visibility(text_train_a_length, current_frame, FADE_DURATION_FRAMES, fade_in=True)
    fade_object_visibility(text_train_b_label, current_frame, FADE_DURATION_FRAMES, fade_in=True)
    fade_object_visibility(text_train_b_length, current_frame, FADE_DURATION_FRAMES, fade_in=True)
    
    current_frame += FADE_DURATION_FRAMES + HOLD_DURATION_FRAMES # Hold initial display

    # 2. Fade out "Initial Separation", Fade in "Running in opposite directions"
    fade_object_visibility(text_separation, current_frame, FADE_DURATION_FRAMES, fade_in=False)
    fade_object_visibility(text_direction, current_frame, FADE_DURATION_FRAMES, fade_in=True)
    
    current_frame += FADE_DURATION_FRAMES # Move to next stage after fade

    # 3. Trains move towards each other
    start_move_frame = current_frame
    end_move_frame = current_frame + MOVE_DURATION_FRAMES

    # Keyframe initial positions
    bpy.ops.object.select_all(action='DESELECT')
    train_a_obj.select_set(True)
    bpy.context.view_layer.objects.active = train_a_obj
    train_a_obj.keyframe_insert(data_path='location', frame=start_move_frame)
    train_a_obj.select_set(False)
    bpy.context.view_layer.objects.active = None
    
    bpy.ops.object.select_all(action='DESELECT')
    train_b_obj.select_set(True)
    bpy.context.view_layer.objects.active = train_b_obj
    train_b_obj.keyframe_insert(data_path='location', frame=start_move_frame)
    train_b_obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    # Calculate final positions for crossing over
    # They should meet and slightly overlap for visual effect
    # Meeting point at X=0
    final_a_x = TRAIN_B_LENGTH / 2 + 0.1 # Train A passes origin
    final_b_x = -TRAIN_A_LENGTH / 2 - 0.1 # Train B passes origin

    # Keyframe final positions
    bpy.ops.object.select_all(action='DESELECT')
    train_a_obj.select_set(True)
    bpy.context.view_layer.objects.active = train_a_obj
    train_a_obj.location.x = final_a_x
    train_a_obj.keyframe_insert(data_path='location', frame=end_move_frame)
    train_a_obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    bpy.ops.object.select_all(action='DESELECT')
    train_b_obj.select_set(True)
    bpy.context.view_layer.objects.active = train_b_obj
    train_b_obj.location.x = final_b_x
    train_b_obj.keyframe_insert(data_path='location', frame=end_move_frame)
    train_b_obj.select_set(False)
    bpy.context.view_layer.objects.active = None
    
    current_frame = end_move_frame

    # 4. Fade out "Running in opposite directions", Fade in "Meeting Point"
    fade_object_visibility(text_direction, current_frame, FADE_DURATION_FRAMES, fade_in=False)
    fade_object_visibility(text_meeting_point, current_frame, FADE_DURATION_FRAMES, fade_in=True)
    
    current_frame += FADE_DURATION_FRAMES # Move to next stage after fade

    # 5. Highlight Trains at meeting point
    animate_material_emission(train_a_obj, mat_train_a.name, current_frame, HIGHLIGHT_DURATION_FRAMES, (0.2, 1.0, 0.2, 1)) # Green emission
    animate_material_emission(train_b_obj, mat_train_b.name, current_frame, HIGHLIGHT_DURATION_FRAMES, (1.0, 0.2, 0.2, 1)) # Red emission
    
    current_frame += HIGHLIGHT_DURATION_FRAMES + HOLD_DURATION_FRAMES # Hold highlight

    # 6. Trains separate and move off screen
    start_separate_frame = current_frame
    end_separate_frame = current_frame + SEPARATION_DURATION_FRAMES

    # Fade out "Meeting Point"
    fade_object_visibility(text_meeting_point, start_separate_frame, FADE_DURATION_FRAMES, fade_in=False)
    
    # Keyframe current positions for separation
    bpy.ops.object.select_all(action='DESELECT')
    train_a_obj.select_set(True)
    bpy.context.view_layer.objects.active = train_a_obj
    train_a_obj.keyframe_insert(data_path='location', frame=start_separate_frame)
    train_a_obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    bpy.ops.object.select_all(action='DESELECT')
    train_b_obj.select_set(True)
    bpy.context.view_layer.objects.active = train_b_obj
    train_b_obj.keyframe_insert(data_path='location', frame=start_separate_frame)
    train_b_obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    # Keyframe final positions for trains moving far off screen
    bpy.ops.object.select_all(action='DESELECT')
    train_a_obj.select_set(True)
    bpy.context.view_layer.objects.active = train_a_obj
    train_a_obj.location.x = INITIAL_SEPARATION * 1.5 # Far off screen right
    train_a_obj.keyframe_insert(data_path='location', frame=end_separate_frame)
    train_a_obj.select_set(False)
    bpy.context.view_layer.objects.active = None

    bpy.ops.object.select_all(action='DESELECT')
    train_b_obj.select_set(True)
    bpy.context.view_layer.objects.active = train_b_obj
    train_b_obj.location.x = -INITIAL_SEPARATION * 1.5 # Far off screen left
    train_b_obj.keyframe_insert(data_path='location', frame=end_separate_frame)
    train_b_obj.select_set(False)
    bpy.context.view_layer.objects.active = None
    
    current_frame = end_separate_frame + FADE_DURATION_FRAMES # Add some padding

    # Set final frame to ensure entire animation plays
    bpy.context.scene.frame_end = current_frame

    print("Blender train animation script finished.")

# Run the animation creation function when the script is executed
if __name__ == "__main__":
    create_train_animation()
