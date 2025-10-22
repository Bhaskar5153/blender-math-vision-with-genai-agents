import bpy
import mathutils
import math
import os

# --- 0. Scene Setup and Global Parameters ---
def setup_scene():
    # Clear existing objects in the scene
    # Select all objects
    bpy.ops.object.select_all(action='SELECT')
    # Delete selected objects
    bpy.ops.object.delete()

    # Create a main collection for all animation assets
    if "Animation_Assets" in bpy.data.collections:
        animation_collection = bpy.data.collections["Animation_Assets"]
    else:
        animation_collection = bpy.data.collections.new("Animation_Assets")
    # Only link if not already linked
    if animation_collection.name not in [col.name for col in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(animation_collection)

    # Set render engine to Cycles (compatible)
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.fps = 24
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 1  # Will be updated dynamically

    # Camera setup
    camera_data = bpy.data.cameras.new(name="MainCamera")
    camera_object = bpy.data.objects.new("MainCamera", camera_data)
    animation_collection.objects.link(camera_object)
    bpy.context.scene.camera = camera_object
    camera_object.location = (0, -15, 5)
    camera_object.rotation_euler = mathutils.Euler((math.radians(70), 0, math.radians(0)), 'XYZ') # Looking down at origin

    # Light setup (Sun light for general illumination)
    light_data = bpy.data.lights.new(name="SunLight", type='SUN')
    light_object = bpy.data.objects.new("SunLight", light_data)
    animation_collection.objects.link(light_object)
    light_object.location = (-5, -5, 10)
    light_object.rotation_euler = mathutils.Euler((math.radians(45), math.radians(-30), math.radians(135)), 'XYZ')
    light_data.energy = 5 # Increase energy for brightness

    print("Scene setup complete.")
    return animation_collection, camera_object

main_collection, camera = setup_scene()

# --- 1. Global Animation Parameters ---
FPS = bpy.context.scene.render.fps
FRAME_CURRENT = 0

def set_frame(frame):
    global FRAME_CURRENT
    FRAME_CURRENT = frame
    bpy.context.scene.frame_current = frame

def add_frame(frames):
    global FRAME_CURRENT
    FRAME_CURRENT += frames
    bpy.context.scene.frame_current = FRAME_CURRENT

# --- 2. Material Definitions ---
materials = {}

def create_emission_material(name, color, strength=5.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        mat.node_tree.nodes.remove(bsdf)

    emission = mat.node_tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = color
    emission.inputs['Strength'].default_value = strength
    output = mat.node_tree.nodes.get("Material Output")
    mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    materials[name] = mat
    return mat

def create_simple_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    principled_bsdf = mat.node_tree.nodes.get("Principled BSDF")
    principled_bsdf.inputs['Base Color'].default_value = color
    materials[name] = mat
    return mat

# Create common materials
create_simple_material("Mat_White", (1, 1, 1, 1))
create_simple_material("Mat_DarkGray", (0.1, 0.1, 0.1, 1))
create_simple_material("Mat_LightGray", (0.7, 0.7, 0.7, 1))
create_simple_material("Mat_Wood", (0.4, 0.2, 0, 1))
create_simple_material("Mat_Glass", (0, 0.2, 0.4, 0.5))
materials["Mat_Glass"].blend_method = 'BLEND'

create_emission_material("Mat_GlowBlue", (0.2, 0.4, 1, 1), strength=3.0)
create_emission_material("Mat_GlowGreen", (0.2, 1, 0.2, 1), strength=3.0)
create_emission_material("Mat_GlowYellow", (1, 1, 0.2, 1), strength=3.0)
create_emission_material("Mat_GlowRed", (1, 0.2, 0.2, 1), strength=3.0)
create_emission_material("Mat_GlowOrange", (1, 0.5, 0.2, 0.5), strength=3.0) # Translucent orange
materials["Mat_GlowOrange"].blend_method = 'BLEND'

create_emission_material("Mat_GlowPurple", (0.6, 0.2, 1, 1), strength=3.0)
create_emission_material("Mat_GlowGold", (1, 0.8, 0.2, 1), strength=3.0)
create_emission_material("Mat_TextDefault", (0.05, 0.05, 0.05, 1), strength=0.0) # Dark text, no glow by default

# --- 3. Asset Creation Helper Functions ---

def create_text_object(name, text_content, location=(0,0,0), rotation=(0,0,0), scale=1, material=None, extrude=0.01, font_size=1.0, collection=main_collection):
    font_curve = bpy.data.curves.new(name=f"Curve_{name}", type='FONT')
    font_curve.body = str(text_content)
    font_curve.extrude = extrude
    font_curve.size = font_size
    font_curve.align_x = 'CENTER'
    font_curve.align_y = 'CENTER'

    text_obj = bpy.data.objects.new(name, font_curve)
    collection.objects.link(text_obj)
    text_obj.location = location
    text_obj.rotation_euler = rotation
    text_obj.scale = (scale, scale, scale)
    if material:
        if material.name not in text_obj.data.materials:
            text_obj.data.materials.append(material)

    text_obj.hide_set(True)
    text_obj.hide_render = True
    return text_obj

def create_cube_with_text(name, text_content, size=1, location=(0,0,0), material=None, text_color=None, collection=main_collection):
    bpy.ops.mesh.primitive_cube_add(size=size, enter_editmode=False, align='WORLD', location=location)
    cube_obj = bpy.context.active_object
    cube_obj.name = name
    collection.objects.link(cube_obj)
    bpy.context.scene.collection.objects.unlink(cube_obj) # Unlink from scene collection

    if material:
        if material.name not in cube_obj.data.materials:
            cube_obj.data.materials.append(material)

    text_obj = create_text_object(f"{name}_Text", text_content, 
                                  location=(0,0,size/2 + 0.01), 
                                  rotation=(mathutils.radians(90), 0, 0), 
                                  scale=0.8/size, 
                                  material=text_color or materials["Mat_TextDefault"], 
                                  extrude=0.005,
                                  collection=collection)
    
    # Parent text to cube
    text_obj.parent = cube_obj
    text_obj.matrix_parent_inverse = cube_obj.matrix_world.inverted()
    
    cube_obj.hide_set(True)
    cube_obj.hide_render = True
    return cube_obj, text_obj

def create_straight_arrow(name, start_loc, end_loc, material=None, radius=0.05, head_length=0.2, head_radius=0.15, collection=main_collection):
    # Calculate vector for arrow direction
    vec = mathutils.Vector(end_loc) - mathutils.Vector(start_loc)
    length = vec.length
    if length == 0:
        return None
    direction = vec.normalized()

    # Create cylinder for arrow shaft
    shaft_length = length - head_length
    if shaft_length < 0: shaft_length = 0 # Avoid negative length if arrow is very short
    
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=shaft_length, 
        enter_editmode=False, align='WORLD', 
        location=start_loc + direction * shaft_length / 2
    )
    shaft_obj = bpy.context.active_object
    shaft_obj.name = f"{name}_Shaft"
    collection.objects.link(shaft_obj)
    bpy.context.scene.collection.objects.unlink(shaft_obj)

    # Rotate shaft to align with direction
    quat = direction.to_track_quat('Z', 'Y')
    shaft_obj.rotation_mode = 'QUATERNION'
    shaft_obj.rotation_quaternion = quat

    # Create cone for arrowhead
    bpy.ops.mesh.primitive_cone_add(
        radius1=head_radius, depth=head_length, 
        enter_editmode=False, align='WORLD', 
        location=start_loc + direction * (shaft_length + head_length / 2)
    )
    head_obj = bpy.context.active_object
    head_obj.name = f"{name}_Head"
    collection.objects.link(head_obj)
    bpy.context.scene.collection.objects.unlink(head_obj)

    # Rotate head to align with direction
    head_obj.rotation_mode = 'QUATERNION'
    head_obj.rotation_quaternion = quat

    # Parent head to shaft
    head_obj.parent = shaft_obj
    head_obj.matrix_parent_inverse = shaft_obj.matrix_world.inverted()

    if material:
        if material.name not in shaft_obj.data.materials:
            shaft_obj.data.materials.append(material)
        if material.name not in head_obj.data.materials:
            head_obj.data.materials.append(material)

    shaft_obj.hide_set(True)
    shaft_obj.hide_render = True
    return shaft_obj # Return the parent object

def create_equals_bar(name, location=(0,0,0), scale=1, material=None, collection=main_collection):
    bpy.ops.mesh.primitive_plane_add(size=scale, enter_editmode=False, align='WORLD', location=location)
    bar_obj_1 = bpy.context.active_object
    bar_obj_1.name = f"{name}_Top"
    bar_obj_1.scale = (scale * 1, scale * 0.1, scale * 0.1) # Thin rectangle
    bar_obj_1.location.y += scale * 0.2
    collection.objects.link(bar_obj_1)
    bpy.context.scene.collection.objects.unlink(bar_obj_1)

    bpy.ops.mesh.primitive_plane_add(size=scale, enter_editmode=False, align='WORLD', location=location)
    bar_obj_2 = bpy.context.active_object
    bar_obj_2.name = f"{name}_Bottom"
    bar_obj_2.scale = (scale * 1, scale * 0.1, scale * 0.1)
    bar_obj_2.location.y -= scale * 0.2
    collection.objects.link(bar_obj_2)
    bpy.context.scene.collection.objects.unlink(bar_obj_2)

    if material:
        if material.name not in bar_obj_1.data.materials:
            bar_obj_1.data.materials.append(material)
        if material.name not in bar_obj_2.data.materials:
            bar_obj_2.data.materials.append(material)

    # Create an empty to parent both bars for easier manipulation
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    equals_empty = bpy.context.active_object
    equals_empty.name = name
    collection.objects.link(equals_empty)
    bpy.context.scene.collection.objects.unlink(equals_empty)

    bar_obj_1.parent = equals_empty
    bar_obj_2.parent = equals_empty

    equals_empty.hide_set(True)
    equals_empty.hide_render = True
    return equals_empty

def create_number_line(name, start_x, end_x, step, y_pos=0, z_pos=0, material=None, collection=main_collection):
    # Main line
    line_data = bpy.data.curves.new(name=f"Curve_{name}", type='CURVE')
    line_data.dimensions = '3D'
    line_spline = line_data.splines.new('POLY')
    line_spline.points.add(1)
    line_spline.points[0].co = (start_x, y_pos, z_pos, 1)
    line_spline.points[1].co = (end_x, y_pos, z_pos, 1)
    line_data.bevel_depth = 0.02
    line_data.bevel_resolution = 4
    
    line_obj = bpy.data.objects.new(name, line_data)
    collection.objects.link(line_obj)
    if material:
        if material.name not in line_obj.data.materials:
            line_obj.data.materials.append(material)

    # Tick marks and labels
    ticks_parent = bpy.data.objects.new(f"{name}_Ticks", None)
    collection.objects.link(ticks_parent)

    for i, x_val in enumerate(range(int(start_x), int(end_x) + 1, int(step))):
        # Tick mark
        bpy.ops.mesh.primitive_plane_add(size=0.1, enter_editmode=False, align='WORLD', location=(x_val, y_pos, z_pos))
        tick = bpy.context.active_object
        tick.name = f"{name}_Tick_{x_val}"
        tick.scale = (0.01, 0.2, 0.01)
        collection.objects.link(tick)
        bpy.context.scene.collection.objects.unlink(tick)
        tick.parent = ticks_parent
        if material:
            if material.name not in tick.data.materials:
                tick.data.materials.append(material)
        
        # Label
        label = create_text_object(f"{name}_Label_{x_val}", str(x_val), 
                                   location=(x_val, y_pos + 0.3, z_pos), 
                                   rotation=(mathutils.radians(90), 0, 0), 
                                   scale=0.3, 
                                   material=materials["Mat_TextDefault"],
                                   collection=collection)
        label.parent = ticks_parent
        
    line_obj.hide_set(True)
    line_obj.hide_render = True
    ticks_parent.hide_set(True)
    ticks_parent.hide_render = True
    return line_obj, ticks_parent

def create_graph_plane(name, size_x=10, size_y=10, step=1, z_pos=-0.01, material=None, collection=main_collection):
    # Main plane
    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0,0,z_pos))
    plane_obj = bpy.context.active_object
    plane_obj.name = name
    plane_obj.scale = (size_x/2, size_y/2, 1)
    collection.objects.link(plane_obj)
    bpy.context.scene.collection.objects.unlink(plane_obj)
    if material:
        if material.name not in plane_obj.data.materials:
            plane_obj.data.materials.append(material)
    
    # Grid lines (optional, can be done with procedural texture or separate objects)
    # For simplicity, we'll just have the main plane and axis lines.

    # X-axis
    x_axis = create_straight_arrow(f"{name}_X_Axis", (-size_x/2, 0, z_pos + 0.01), (size_x/2, 0, z_pos + 0.01), materials["Mat_DarkGray"], radius=0.03, head_length=0.2, head_radius=0.1, collection=collection)
    x_label = create_text_object(f"{name}_X_Label", "X", (size_x/2 + 0.5, 0, z_pos + 0.01), (mathutils.radians(90),0,0), 0.5, materials["Mat_TextDefault"], collection=collection)
    
    # Y-axis
    y_axis = create_straight_arrow(f"{name}_Y_Axis", (0, -size_y/2, z_pos + 0.01), (0, size_y/2, z_pos + 0.01), materials["Mat_DarkGray"], radius=0.03, head_length=0.2, head_radius=0.1, collection=collection)
    y_label = create_text_object(f"{name}_Y_Label", "Y", (0, size_y/2 + 0.5, z_pos + 0.01), (mathutils.radians(90),0,0), 0.5, materials["Mat_TextDefault"], collection=collection)

    # Create an empty to parent all graph components
    graph_empty = bpy.data.objects.new(name + "_Empty", None)
    collection.objects.link(graph_empty)
    plane_obj.parent = graph_empty
    x_axis.parent = graph_empty
    x_label.parent = graph_empty
    y_axis.parent = graph_empty
    y_label.parent = graph_empty
    
    graph_empty.hide_set(True)
    graph_empty.hide_render = True
    return graph_empty

def create_solution_line(name, start_point, end_point, material=None, thickness=0.05, collection=main_collection):
    line_data = bpy.data.curves.new(name=f"Curve_{name}", type='CURVE')
    line_data.dimensions = '3D'
    line_spline = line_data.splines.new('POLY')
    line_spline.points.add(1)
    line_spline.points[0].co = (start_point[0], start_point[1], start_point[2], 1)
    line_spline.points[1].co = (end_point[0], end_point[1], end_point[2], 1)
    line_data.bevel_depth = thickness
    line_data.bevel_resolution = 4
    
    line_obj = bpy.data.objects.new(name, line_data)
    collection.objects.link(line_obj)
    if material:
        if material.name not in line_obj.data.materials:
            line_obj.data.materials.append(material)
    
    line_obj.hide_set(True)
    line_obj.hide_render = True
    return line_obj

def create_sphere(name, radius=0.1, location=(0,0,0), material=None, collection=main_collection):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    sphere_obj = bpy.context.active_object
    sphere_obj.name = name
    collection.objects.link(sphere_obj)
    bpy.context.scene.collection.objects.unlink(sphere_obj)
    if material:
        if material.name not in sphere_obj.data.materials:
            sphere_obj.data.materials.append(material)
    sphere_obj.hide_set(True)
    sphere_obj.hide_render = True
    return sphere_obj

# --- 4. Animation Helper Functions ---

def animate_hide_show(obj, start_frame, show=True):
    set_frame(start_frame)
    obj.hide_viewport = not show
    obj.hide_render = not show
    obj.keyframe_insert(data_path='hide_viewport', index=-1)
    obj.keyframe_insert(data_path='hide_render', index=-1)

def animate_fade_in(obj, start_frame, duration_frames, initial_strength=0.0, final_strength=1.0):
    if not obj or not obj.data or not obj.data.materials:
        return
    
    mat = obj.data.materials[0] # Assuming first material
    if not mat.use_nodes:
        return

    emission_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    
    if not emission_node: # Fallback to Principled BSDF if no emission node
        principled_bsdf_node = mat.node_tree.nodes.get("Principled BSDF")
        if principled_bsdf_node:
            set_frame(start_frame)
            principled_bsdf_node.inputs['Alpha'].default_value = 0.0
            principled_bsdf_node.keyframe_insert(data_path='inputs["Alpha"].default_value')
            set_frame(start_frame + duration_frames)
            principled_bsdf_node.inputs['Alpha'].default_value = 1.0
            principled_bsdf_node.keyframe_insert(data_path='inputs["Alpha"].default_value')
            mat.blend_method = 'BLEND'
            return

    # For emission nodes
    set_frame(start_frame)
    emission_node.inputs['Strength'].default_value = initial_strength
    emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')

    set_frame(start_frame + duration_frames)
    emission_node.inputs['Strength'].default_value = final_strength
    emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')

    # Ensure it's visible during the fade
    animate_hide_show(obj, start_frame, show=True)

def animate_fade_out(obj, start_frame, duration_frames, initial_strength=1.0, final_strength=0.0):
    if not obj or not obj.data or not obj.data.materials:
        return
    
    mat = obj.data.materials[0]
    if not mat.use_nodes:
        return

    emission_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    
    if not emission_node: # Fallback to Principled BSDF if no emission node
        principled_bsdf_node = mat.node_tree.nodes.get("Principled BSDF")
        if principled_bsdf_node:
            set_frame(start_frame)
            principled_bsdf_node.inputs['Alpha'].default_value = 1.0
            principled_bsdf_node.keyframe_insert(data_path='inputs["Alpha"].default_value')
            set_frame(start_frame + duration_frames)
            principled_bsdf_node.inputs['Alpha'].default_value = 0.0
            principled_bsdf_node.keyframe_insert(data_path='inputs["Alpha"].default_value')
            return

    set_frame(start_frame)
    emission_node.inputs['Strength'].default_value = initial_strength
    emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')

    set_frame(start_frame + duration_frames)
    emission_node.inputs['Strength'].default_value = final_strength
    emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')
    
    # Hide after fade out
    animate_hide_show(obj, start_frame + duration_frames, show=False)


def animate_move(obj, start_frame, end_frame, start_loc, end_loc, rotation_start=None, rotation_end=None, scale_start=None, scale_end=None):
    set_frame(start_frame)
    obj.location = start_loc
    obj.keyframe_insert(data_path='location')
    if rotation_start:
        obj.rotation_euler = rotation_start
        obj.keyframe_insert(data_path='rotation_euler')
    if scale_start:
        obj.scale = scale_start
        obj.keyframe_insert(data_path='scale')

    set_frame(end_frame)
    obj.location = end_loc
    obj.keyframe_insert(data_path='location')
    if rotation_end:
        obj.rotation_euler = rotation_end
        obj.keyframe_insert(data_path='rotation_euler')
    if scale_end:
        obj.scale = scale_end
        obj.keyframe_insert(data_path='scale')
    
    animate_hide_show(obj, start_frame, show=True)

def animate_text_typing(text_obj, start_frame, duration_frames):
    full_text = text_obj.data.body
    num_chars = len(full_text)
    frames_per_char = duration_frames / num_chars

    for i in range(num_chars + 1):
        set_frame(start_frame + int(i * frames_per_char))
        text_obj.data.body = full_text[:i]
        text_obj.keyframe_insert(data_path='body')
    
    animate_hide_show(text_obj, start_frame, show=True)

def animate_glow_pulse(obj, start_frame, duration_frames, initial_strength=1.0, peak_strength=5.0, pulses=2):
    if not obj or not obj.data or not obj.data.materials:
        return
    mat = obj.data.materials[0]
    emission_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    if not emission_node: return

    frame_interval = duration_frames / (pulses * 2)

    for i in range(pulses):
        set_frame(start_frame + i * frame_interval * 2)
        emission_node.inputs['Strength'].default_value = initial_strength
        emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')

        set_frame(start_frame + i * frame_interval * 2 + frame_interval)
        emission_node.inputs['Strength'].default_value = peak_strength
        emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')
    
    set_frame(start_frame + duration_frames)
    emission_node.inputs['Strength'].default_value = initial_strength # End on initial strength
    emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')
    animate_hide_show(obj, start_frame, show=True)

def animate_material_color_change(obj, start_frame, end_frame, start_color_rgba, end_color_rgba, strength=3.0):
    if not obj or not obj.data or not obj.data.materials:
        return
    
    mat = obj.data.materials[0]
    if not mat.use_nodes:
        return

    emission_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    if not emission_node: return

    set_frame(start_frame)
    emission_node.inputs['Color'].default_value = start_color_rgba
    emission_node.inputs['Strength'].default_value = strength
    emission_node.keyframe_insert(data_path='inputs["Color"].default_value')
    emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')

    set_frame(end_frame)
    emission_node.inputs['Color'].default_value = end_color_rgba
    emission_node.inputs['Strength'].default_value = strength
    emission_node.keyframe_insert(data_path='inputs["Color"].default_value')
    emission_node.keyframe_insert(data_path='inputs["Strength"].default_value')
    animate_hide_show(obj, start_frame, show=True)

def animate_scale(obj, start_frame, end_frame, scale_start, scale_end):
    set_frame(start_frame)
    obj.scale = scale_start
    obj.keyframe_insert(data_path='scale')
    set_frame(end_frame)
    obj.scale = scale_end
    obj.keyframe_insert(data_path='scale')
    animate_hide_show(obj, start_frame, show=True)

# --- 5. Environment Assets (Classroom & Whiteboard) ---

# Classroom Background (simple floor and back wall for now)
bpy.ops.mesh.primitive_plane_add(size=20, enter_editmode=False, location=(0,0,-0.5))
floor_obj = bpy.context.active_object
bpy.context.scene.collection.objects.unlink(floor_obj)
main_collection.objects.link(floor_obj)
floor_obj.name = "Classroom_Floor"
floor_obj.data.materials.append(materials["Mat_Wood"])

bpy.ops.mesh.primitive_plane_add(size=20, enter_editmode=False, location=(0,10,5))
back_wall_obj = bpy.context.active_object
bpy.context.scene.collection.objects.unlink(back_wall_obj)
main_collection.objects.link(back_wall_obj)
back_wall_obj.name = "Classroom_BackWall"
back_wall_obj.rotation_euler = (math.radians(90), 0, 0)
back_wall_obj.data.materials.append(materials["Mat_LightGray"])

bpy.ops.mesh.primitive_plane_add(size=8, enter_editmode=False, location=(0,5,3))
whiteboard_obj = bpy.context.active_object
bpy.context.scene.collection.objects.unlink(whiteboard_obj)
main_collection.objects.link(whiteboard_obj)
whiteboard_obj.name = "Whiteboard"
whiteboard_obj.rotation_euler = (math.radians(90), 0, 0)
whiteboard_obj.data.materials.append(materials["Mat_White"])

# --- 6. Animation Plan Implementation ---

# Adjust camera for initial view
set_frame(0)
camera.location = (0, -15, 5)
camera.rotation_euler = (math.radians(70), 0, 0) # Look at whiteboard from front
camera.keyframe_insert(data_path='location')
camera.keyframe_insert(data_path='rotation_euler')
animate_hide_show(floor_obj, 0, show=True)
animate_hide_show(back_wall_obj, 0, show=True)
animate_hide_show(whiteboard_obj, 0, show=True)


# --- Scene 1: Introduction - Presenting the Problem (4 seconds) ---
print("Animating Scene 1...")
scene1_duration = 4 * FPS # 4 seconds

# Camera pan to whiteboard
set_frame(FRAME_CURRENT)
camera_start_loc = (0, -15, 5)
camera_start_rot = (math.radians(70), 0, 0)
camera_end_loc = (0, -8, 3.5)
camera_end_rot = (math.radians(70), 0, 0) # Closer to whiteboard

animate_move(camera, FRAME_CURRENT, FRAME_CURRENT + scene1_duration, camera_start_loc, camera_end_loc, camera_start_rot, camera_end_rot)

# Problem text on whiteboard
text_problem_title = create_text_object("Problem_Title", "Problem: Find the value of variable x and y if", (0, 4.9, 5.5), (math.radians(90), 0, 0), 0.5, materials["Mat_TextDefault"])
text_equation = create_text_object("Problem_Equation", "x + 2y - 10 = 5", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.6, materials["Mat_TextDefault"])
text_constraint = create_text_object("Problem_Constraint", "where 0 < x > 5", (0, 4.9, 3.5), (math.radians(90), 0, 0), 0.5, materials["Mat_TextDefault"])

animate_text_typing(text_problem_title, FRAME_CURRENT + 0.5 * FPS, 1 * FPS)
animate_text_typing(text_equation, FRAME_CURRENT + 1.5 * FPS, 1 * FPS)
animate_text_typing(text_constraint, FRAME_CURRENT + 2.5 * FPS, 1 * FPS)

# Gentle glow highlight
animate_glow_pulse(text_equation, FRAME_CURRENT + 3 * FPS, 0.5 * FPS, initial_strength=0.0, peak_strength=5.0, pulses=1)
animate_glow_pulse(text_constraint, FRAME_CURRENT + 3.5 * FPS, 0.5 * FPS, initial_strength=0.0, peak_strength=5.0, pulses=1)

add_frame(scene1_duration)


# --- Scene 2: Step 1 - Simplify the Equation (10 seconds) ---
print("Animating Scene 2...")
scene2_duration = 10 * FPS

# Clear/hide previous texts
animate_fade_out(text_problem_title, FRAME_CURRENT, FPS)
animate_fade_out(text_equation, FRAME_CURRENT, FPS)
animate_fade_out(text_constraint, FRAME_CURRENT, FPS)
add_frame(FPS)

# Equation components
# Initial x + 2y - 10 = 5
eq_x_1, eq_x_text_1 = create_cube_with_text("Eq1_X", "x", (1,1,0.2), (-3.5, 4.9, 4.5), materials["Mat_Glass"], materials["Mat_GlowBlue"])
eq_plus_1 = create_straight_arrow("Eq1_Plus1", (-2.5, 4.9, 4.5), (-1.5, 4.9, 4.5), materials["Mat_GlowYellow"])
eq_2, eq_2_text = create_cube_with_text("Eq1_2", "2", (1,1,0.2), (-1, 4.9, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])
eq_y_1, eq_y_text_1 = create_cube_with_text("Eq1_Y", "y", (1,1,0.2), (0, 4.9, 4.5), materials["Mat_Glass"], materials["Mat_GlowGreen"])
eq_minus_1 = create_straight_arrow("Eq1_Minus1", (1, 4.9, 4.5), (2, 4.9, 4.5), materials["Mat_GlowRed"])
eq_10_1, eq_10_text_1 = create_cube_with_text("Eq1_10", "10", (1,1,0.2), (2.5, 4.9, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])
eq_equals_1 = create_equals_bar("Eq1_Equals", (4.5, 4.9, 4.5), 1.5, materials["Mat_GlowBlue"])
eq_5_1, eq_5_text_1 = create_cube_with_text("Eq1_5", "5", (1,1,0.2), (6, 4.9, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])

objs_eq1 = [eq_x_1, eq_plus_1, eq_2, eq_y_1, eq_minus_1, eq_10_1, eq_equals_1, eq_5_1]
for obj in objs_eq1: animate_hide_show(obj, FRAME_CURRENT, show=True)

# 1. -10 on left side glows
animate_glow_pulse(eq_10_1, FRAME_CURRENT, FPS, initial_strength=materials["Mat_White"].node_tree.nodes.get("Principled BSDF").inputs['Base Color'].default_value[0], peak_strength=5.0, pulses=1)
animate_glow_pulse(eq_minus_1, FRAME_CURRENT, FPS, initial_strength=materials["Mat_GlowRed"].inputs['Strength'].default_value, peak_strength=5.0, pulses=1)
add_frame(FPS)

# 2. +10 slides in from off-screen left
plus_10_left = create_straight_arrow("Eq1_Plus10_L_Arrow", (-5, 4.9, 4.5), (-4, 4.9, 4.5), materials["Mat_GlowYellow"])
block_10_left, block_10_left_text = create_cube_with_text("Eq1_Plus10_L_Block", "10", (1,1,0.2), (-3.5, 4.9, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])

animate_move(plus_10_left, FRAME_CURRENT, FRAME_CURRENT + FPS, (-6, 4.9, 4.5), (3.5, 4.9, 4.5))
animate_move(block_10_left, FRAME_CURRENT, FRAME_CURRENT + FPS, (-6.5, 4.9, 4.5), (4, 4.9, 4.5))
add_frame(FPS)

# 3. +10 slides in from off-screen right
plus_10_right = create_straight_arrow("Eq1_Plus10_R_Arrow", (10, 4.9, 4.5), (11, 4.9, 4.5), materials["Mat_GlowYellow"])
block_10_right, block_10_right_text = create_cube_with_text("Eq1_Plus10_R_Block", "10", (1,1,0.2), (11.5, 4.9, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])

animate_move(plus_10_right, FRAME_CURRENT, FRAME_CURRENT + FPS, (10, 4.9, 4.5), (6.5, 4.9, 4.5))
animate_move(block_10_right, FRAME_CURRENT, FRAME_CURRENT + FPS, (10.5, 4.9, 4.5), (7, 4.9, 4.5))
add_frame(FPS)

# 4. On the left, -10 and +10 objects briefly flash, then fade out
animate_glow_pulse(eq_10_1, FRAME_CURRENT, FPS*0.5, peak_strength=8.0)
animate_glow_pulse(eq_minus_1, FRAME_CURRENT, FPS*0.5, peak_strength=8.0)
animate_glow_pulse(block_10_left, FRAME_CURRENT, FPS*0.5, peak_strength=8.0)
animate_glow_pulse(plus_10_left, FRAME_CURRENT, FPS*0.5, peak_strength=8.0)
add_frame(FPS*0.5)

animate_fade_out(eq_10_1, FRAME_CURRENT, FPS*0.5, final_strength=0.0)
animate_fade_out(eq_minus_1, FRAME_CURRENT, FPS*0.5, final_strength=0.0)
animate_fade_out(block_10_left, FRAME_CURRENT, FPS*0.5, final_strength=0.0)
animate_fade_out(plus_10_left, FRAME_CURRENT, FPS*0.5, final_strength=0.0)
add_frame(FPS*0.5)

# Shift remaining left side elements
animate_move(eq_x_1, FRAME_CURRENT, FRAME_CURRENT + FPS, eq_x_1.location, (-2, 4.9, 4.5))
animate_move(eq_plus_1, FRAME_CURRENT, FRAME_CURRENT + FPS, eq_plus_1.location, (-1, 4.9, 4.5))
animate_move(eq_2, FRAME_CURRENT, FRAME_CURRENT + FPS, eq_2.location, (0, 4.9, 4.5))
animate_move(eq_y_1, FRAME_CURRENT, FRAME_CURRENT + FPS, eq_y_1.location, (1, 4.9, 4.5))
animate_move(eq_equals_1, FRAME_CURRENT, FRAME_CURRENT + FPS, eq_equals_1.location, (3, 4.9, 4.5))
add_frame(FPS)


# 5. On the right, 5 and 10 smoothly merge into 15
animate_scale(eq_5_1, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, eq_5_1.scale, (1.2,1.2,0.2)) # Grow
animate_scale(block_10_right, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, block_10_right.scale, (1.2,1.2,0.2))
animate_move(block_10_right, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, block_10_right.location, eq_5_1.location) # Move 10 to 5
animate_fade_out(plus_10_right, FRAME_CURRENT, FPS*0.5, final_strength=0.0) # Fade arrow
add_frame(FPS*0.5)

animate_fade_out(block_10_right, FRAME_CURRENT, FPS*0.5, final_strength=0.0) # Fade 10
eq_5_1.name = "Eq1_15" # Rename 5 to 15
eq_5_text_1.data.body = "15" # Change text to 15
animate_scale(eq_5_1, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, eq_5_1.scale, (1,1,0.2)) # Shrink back
add_frame(FPS*0.5)


# 7. Whiteboard updates to show the simplified equation: x + 2y = 15
animate_fade_out(eq_x_1, FRAME_CURRENT + FPS, FPS)
animate_fade_out(eq_plus_1, FRAME_CURRENT + FPS, FPS)
animate_fade_out(eq_2, FRAME_CURRENT + FPS, FPS)
animate_fade_out(eq_y_1, FRAME_CURRENT + FPS, FPS)
animate_fade_out(eq_equals_1, FRAME_CURRENT + FPS, FPS)
animate_fade_out(eq_5_1, FRAME_CURRENT + FPS, FPS)

text_simplified_eq = create_text_object("Simplified_Equation", "x + 2y = 15", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_fade_in(text_simplified_eq, FRAME_CURRENT + FPS, FPS)

add_frame(FPS * 1.5)


# --- Scene 3: Step 2 - Interpret the Constraint (12 seconds) ---
print("Animating Scene 3...")
scene3_duration = 12 * FPS

animate_fade_out(text_simplified_eq, FRAME_CURRENT, FPS)
add_frame(FPS)

# 1. The text 0 < x > 5 appears on the whiteboard.
text_constraint_full = create_text_object("Constraint_Full", "0 < x > 5", (0, 4.9, 5.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_text_typing(text_constraint_full, FRAME_CURRENT, FPS)
add_frame(FPS)

# 2. NumberLine emerges
num_line_obj, num_line_ticks_parent = create_number_line("NumberLine", -2, 12, 1, y_pos=4.9, z_pos=3, material=materials["Mat_LightGray"])
num_line_x_var, num_line_x_text = create_cube_with_text("NumLine_X_Var", "x", (0.8,0.8,0.2), (0, 4.9, 3.8), materials["Mat_Glass"], materials["Mat_GlowBlue"])

animate_fade_in(num_line_obj, FRAME_CURRENT, FPS)
animate_fade_in(num_line_ticks_parent, FRAME_CURRENT, FPS)
animate_fade_in(num_line_x_var, FRAME_CURRENT, FPS)
add_frame(FPS)

# 2. constraint 0 < x: hollow circle at 0, green arrow extends, x_var moves
text_0_lt_x_glow = create_text_object("0_lt_x_glow", "0 < x", (-1.5, 4.9, 5.0), (math.radians(90), 0, 0), 0.5, materials["Mat_GlowGreen"])
animate_fade_in(text_0_lt_x_glow, FRAME_CURRENT, FPS * 0.5)

circle_0 = create_sphere("Circle_0", 0.2, (0, 4.9, 3), materials["Mat_White"])
circle_0.data.materials[0].blend_method = 'HASHED' # Make it appear hollow for effect
animate_fade_in(circle_0, FRAME_CURRENT, FPS*0.5)

arrow_x_gt_0 = create_straight_arrow("Arrow_x_gt_0", (0, 4.9, 3), (10, 4.9, 3), materials["Mat_GlowGreen"], radius=0.07, head_length=0.4, head_radius=0.25)
arrow_x_gt_0.scale = (0.01,0.01,0.01) # Start small
animate_move(arrow_x_gt_0, FRAME_CURRENT, FRAME_CURRENT + FPS, arrow_x_gt_0.location, arrow_x_gt_0.location, scale_start=(0.01,0.01,0.01), scale_end=(1,1,1))
animate_move(num_line_x_var, FRAME_CURRENT, FRAME_CURRENT + FPS, num_line_x_var.location, (5, 4.9, 3.8))
add_frame(FPS * 1.5)

# 3. Next, x > 5: second hollow circle at 5, blue arrow extends
text_x_gt_5_glow = create_text_object("x_gt_5_glow", "x > 5", (1.5, 4.9, 5.0), (math.radians(90), 0, 0), 0.5, materials["Mat_GlowBlue"])
animate_fade_in(text_x_gt_5_glow, FRAME_CURRENT, FPS * 0.5)

circle_5 = create_sphere("Circle_5", 0.2, (5, 4.9, 3), materials["Mat_White"])
circle_5.data.materials[0].blend_method = 'HASHED'
animate_fade_in(circle_5, FRAME_CURRENT, FPS*0.5)

arrow_x_gt_5 = create_straight_arrow("Arrow_x_gt_5", (5, 4.9, 3), (10, 4.9, 3), materials["Mat_GlowBlue"], radius=0.07, head_length=0.4, head_radius=0.25)
arrow_x_gt_5.scale = (0.01,0.01,0.01)
animate_move(arrow_x_gt_5, FRAME_CURRENT, FRAME_CURRENT + FPS, arrow_x_gt_5.location, arrow_x_gt_5.location, scale_start=(0.01,0.01,0.01), scale_end=(1,1,1))
add_frame(FPS * 1.5)

# 4. LogicalANDSymbol (∧) appears
logical_and = create_text_object("Logical_AND", "∧", (0, 4.9, 5.0), (math.radians(90), 0, 0), 0.7, materials["Mat_GlowGold"])
animate_fade_in(logical_and, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

# 5. NumberLine visually processes the "AND": only the overlapping segment, from 5 onwards, remains brightly highlighted.
# This is tricky without modifiers. We'll fade out the green arrow and keep blue.
animate_fade_out(arrow_x_gt_0, FRAME_CURRENT, FPS)
animate_fade_out(text_0_lt_x_glow, FRAME_CURRENT, FPS)
animate_fade_out(logical_and, FRAME_CURRENT, FPS*0.5)
animate_fade_out(circle_0, FRAME_CURRENT, FPS)
add_frame(FPS)

# 6. VariableBox(x) settles over the highlighted x > 5 region.
animate_move(num_line_x_var, FRAME_CURRENT, FRAME_CURRENT + FPS, num_line_x_var.location, (7, 4.9, 3.8))
add_frame(FPS)

# 7. Text concludes: "Constraint simplifies to: x > 5".
animate_fade_out(text_x_gt_5_glow, FRAME_CURRENT, FPS*0.5)
animate_fade_out(text_constraint_full, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

text_constraint_simplified = create_text_object("Constraint_Simplified", "Constraint simplifies to: x > 5", (0, 4.9, 5.0), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_text_typing(text_constraint_simplified, FRAME_CURRENT, FPS)
add_frame(FPS * 1.5)


# --- Scene 4: Step 3 - Analyze the System (No Unique Solution) (12 seconds) ---
print("Animating Scene 4...")
scene4_duration = 12 * FPS

animate_fade_out(num_line_obj, FRAME_CURRENT, FPS)
animate_fade_out(num_line_ticks_parent, FRAME_CURRENT, FPS)
animate_fade_out(num_line_x_var, FRAME_CURRENT, FPS)
animate_fade_out(arrow_x_gt_5, FRAME_CURRENT, FPS)
animate_fade_out(circle_5, FRAME_CURRENT, FPS)
animate_fade_out(text_constraint_simplified, FRAME_CURRENT, FPS)
add_frame(FPS)

# Display simplified equation and refined constraint
text_eq_s4 = create_text_object("Eq_S4", "x + 2y = 15", (-3, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
text_const_s4 = create_text_object("Const_S4", "x > 5", (3, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_fade_in(text_eq_s4, FRAME_CURRENT, FPS)
animate_fade_in(text_const_s4, FRAME_CURRENT, FPS)
add_frame(FPS)

# Fade classroom slightly (not implemented here, but would be material alpha on floor/wall)
# Create and animate GraphPlane
graph_plane_empty = create_graph_plane("GraphPlane", size_x=15, size_y=15, z_pos=2.9, material=materials["Mat_LightGray"])
graph_plane_empty.location = (0, 4.9, 3) # Position on whiteboard
graph_plane_empty.rotation_euler = (math.radians(90), 0, 0)
graph_plane_empty.scale = (0.01,0.01,0.01) # Start small

animate_move(graph_plane_empty, FRAME_CURRENT, FRAME_CURRENT + FPS, graph_plane_empty.location, graph_plane_empty.location, scale_start=(0.01,0.01,0.01), scale_end=(0.8,0.8,0.8))
add_frame(FPS)

# 1. Equation x + 2y = 15 drawn as glowing LineSolution
# Points: (15,0) and (0, 7.5) in graph coordinates
line_solution = create_solution_line("LineSolution", (7.5, 0, 3.01), (-7.5, 7.5, 3.01), materials["Mat_GlowBlue"], thickness=0.1) # (15,0) and (0,7.5) for graph_plane centered at 0,0, but offset for whiteboard.
line_solution.location = (0, 4.9, 0) # Position relative to whiteboard
line_solution.rotation_euler = (math.radians(90), 0, 0)

# Animate line drawing using scale
line_solution.scale = (0.01, 1, 1) # Scale along X to draw
animate_move(line_solution, FRAME_CURRENT, FRAME_CURRENT + FPS*1.5, line_solution.location, line_solution.location, scale_start=(0.01,1,1), scale_end=(1,1,1))
add_frame(FPS*1.5)

# 2. Constraint x > 5: Dashed ConstraintLine at x = 5, shaded region
constraint_line_x5 = create_solution_line("ConstraintLine_X5", (5, -7.5, 3.01), (5, 7.5, 3.01), materials["Mat_GlowYellow"], thickness=0.07)
constraint_line_x5.location = (0, 4.9, 0)
constraint_line_x5.rotation_euler = (math.radians(90), 0, 0)
animate_fade_in(constraint_line_x5, FRAME_CURRENT, FPS)
add_frame(FPS)

# ConstraintShade (plane) for x > 5
constraint_shade = bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, location=(7.5, 0, 3.005))
constraint_shade = bpy.context.active_object
constraint_shade.name = "ConstraintShade_X_gt_5"
main_collection.objects.link(constraint_shade)
bpy.context.scene.collection.objects.unlink(constraint_shade)
constraint_shade.scale = (2.5, 7.5, 1) # Covers x > 5
constraint_shade.location = (2.5 + 5, 4.9, 3.005) # Center X at 7.5 for x>5, adjust Y for full graph
constraint_shade.rotation_euler = (math.radians(90), 0, 0)
constraint_shade.data.materials.append(materials["Mat_GlowOrange"])
animate_fade_in(constraint_shade, FRAME_CURRENT, FPS)
add_frame(FPS)

# 3. Portion of LineSolution within x > 5 pulses
# This is hard to do with a single object. We'll just make the entire line pulse.
animate_glow_pulse(line_solution, FRAME_CURRENT, FPS*2, initial_strength=materials["Mat_GlowBlue"].inputs['Strength'].default_value, peak_strength=8.0, pulses=2)
add_frame(FPS*2)

# 4. Text appears: "One equation with two variables..." followed by "...plus a range constraint."
text_s4_p1 = create_text_object("S4_Text_P1", "One equation with two variables...", (0, 4.9, 6.5), (math.radians(90), 0, 0), 0.5, materials["Mat_TextDefault"])
text_s4_p2 = create_text_object("S4_Text_P2", "...plus a range constraint.", (0, 4.9, 6.0), (math.radians(90), 0, 0), 0.5, materials["Mat_TextDefault"])
animate_text_typing(text_s4_p1, FRAME_CURRENT, FPS*1.5)
animate_text_typing(text_s4_p2, FRAME_CURRENT + FPS, FPS*1.5)
add_frame(FPS*2)

# 5. QuestionMarkIcon spins in, transforms into text "No Unique Solution," and pulses.
qm_icon = create_text_object("QuestionMark_Icon", "?", (0, 4.9, 5), (math.radians(90), 0, 0), 2, materials["Mat_GlowGold"])
qm_icon.rotation_euler = (math.radians(90), math.radians(0), 0)
animate_fade_in(qm_icon, FRAME_CURRENT, FPS*0.5)
animate_move(qm_icon, FRAME_CURRENT, FRAME_CURRENT + FPS, qm_icon.location, qm_icon.location, rotation_start=(math.radians(90), math.radians(0), 0), rotation_end=(math.radians(90), math.radians(360*2), 0))
add_frame(FPS)

text_no_unique = create_text_object("No_Unique_Solution", "No Unique Solution", (0, 4.9, 5), (math.radians(90), 0, 0), 1, materials["Mat_GlowRed"])
animate_fade_out(qm_icon, FRAME_CURRENT, FPS*0.5)
animate_fade_in(text_no_unique, FRAME_CURRENT + FPS*0.5, FPS*0.5)
animate_glow_pulse(text_no_unique, FRAME_CURRENT + FPS, FPS, initial_strength=materials["Mat_GlowRed"].inputs['Strength'].default_value, peak_strength=8.0, pulses=2)
add_frame(FPS*2)


# --- Scene 5: Step 4 - Expressing the Solution Set (18 seconds) ---
print("Animating Scene 5...")
scene5_duration = 18 * FPS

animate_fade_out(text_eq_s4, FRAME_CURRENT, FPS)
animate_fade_out(text_const_s4, FRAME_CURRENT, FPS)
animate_fade_out(graph_plane_empty, FRAME_CURRENT, FPS)
animate_fade_out(line_solution, FRAME_CURRENT, FPS)
animate_fade_out(constraint_line_x5, FRAME_CURRENT, FPS)
animate_fade_out(constraint_shade, FRAME_CURRENT, FPS)
animate_fade_out(text_s4_p1, FRAME_CURRENT, FPS)
animate_fade_out(text_s4_p2, FRAME_CURRENT, FPS)
animate_fade_out(text_no_unique, FRAME_CURRENT, FPS)
add_frame(FPS)

# Camera zoom in on equation area
set_frame(FRAME_CURRENT)
camera_start_loc = camera.location
camera_start_rot = camera.rotation_euler
camera_end_loc = (0, -6, 4.5)
camera_end_rot = (math.radians(90), 0, 0) # Directly facing whiteboard

animate_move(camera, FRAME_CURRENT, FRAME_CURRENT + FPS, camera_start_loc, camera_end_loc, camera_start_rot, camera_end_rot)
add_frame(FPS)

# Initial equation text: x + 2y = 15
eq_s5_text = create_text_object("Eq_S5_Initial", "x + 2y = 15", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
const_s5_text = create_text_object("Const_S5_Initial", "x > 5", (0, 4.9, 3.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_fade_in(eq_s5_text, FRAME_CURRENT, FPS)
animate_fade_in(const_s5_text, FRAME_CURRENT, FPS)
add_frame(FPS)

# 1. VariableBox(x) in x + 2y = 15 glows and slides to the right
x_block_s5, x_text_s5 = create_cube_with_text("S5_X_Block", "x", (1,1,0.2), (-2, 4.8, 4.5), materials["Mat_Glass"], materials["Mat_GlowBlue"])
plus_arrow_s5 = create_straight_arrow("S5_Plus_Arrow", (-1, 4.8, 4.5), (0, 4.8, 4.5), materials["Mat_GlowYellow"])
two_block_s5, two_text_s5 = create_cube_with_text("S5_2_Block", "2", (1,1,0.2), (0.5, 4.8, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])
y_block_s5, y_text_s5 = create_cube_with_text("S5_Y_Block", "y", (1,1,0.2), (1.5, 4.8, 4.5), materials["Mat_Glass"], materials["Mat_GlowGreen"])
equals_s5 = create_equals_bar("S5_Equals", (3.5, 4.8, 4.5), 1.5, materials["Mat_GlowBlue"])
fifteen_block_s5, fifteen_text_s5 = create_cube_with_text("S5_15_Block", "15", (1,1,0.2), (5.5, 4.8, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])

objs_eq_s5 = [x_block_s5, plus_arrow_s5, two_block_s5, y_block_s5, equals_s5, fifteen_block_s5]
for obj in objs_eq_s5: animate_fade_in(obj, FRAME_CURRENT, FPS*0.5)
animate_fade_out(eq_s5_text, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

animate_glow_pulse(x_block_s5, FRAME_CURRENT, FPS, initial_strength=materials["Mat_Glass"].node_tree.nodes.get("Principled BSDF").inputs['Base Color'].default_value[0], peak_strength=5.0)
add_frame(FPS*0.5)

# Move x to right, change to -x
animate_move(x_block_s5, FRAME_CURRENT, FRAME_CURRENT + FPS, x_block_s5.location, (6.5, 4.8, 4.5))
x_text_s5.data.body = "-x"
animate_material_color_change(x_block_s5, FRAME_CURRENT, FRAME_CURRENT+FPS, materials["Mat_GlowBlue"].inputs['Color'].default_value, (1,0.2,0.2,1)) # Change color to red
add_frame(FPS)

# 2. Equation becomes: 2y = 15 - x
animate_fade_out(plus_arrow_s5, FRAME_CURRENT, FPS*0.5)
animate_move(two_block_s5, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, two_block_s5.location, (0.5, 4.8, 4.5))
animate_move(y_block_s5, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, y_block_s5.location, (1.5, 4.8, 4.5))
animate_move(equals_s5, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, equals_s5.location, (3, 4.8, 4.5))
animate_move(fifteen_block_s5, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, fifteen_block_s5.location, (4.5, 4.8, 4.5))
add_frame(FPS*0.5)

text_eq_2y = create_text_object("Eq_2y", "2y = 15 - x", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_fade_in(text_eq_2y, FRAME_CURRENT, FPS*0.5)
add_frame(FPS)

# 3. ConstantBlock(2) separates from y and floats down as denominator
animate_fade_out(two_block_s5, FRAME_CURRENT, FPS*0.5)
animate_fade_out(y_block_s5, FRAME_CURRENT, FPS*0.5)
animate_fade_out(fifteen_block_s5, FRAME_CURRENT, FPS*0.5)
animate_fade_out(x_block_s5, FRAME_CURRENT, FPS*0.5)
animate_fade_out(equals_s5, FRAME_CURRENT, FPS*0.5)
animate_fade_out(text_eq_2y, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

text_eq_y_divided = create_text_object("Eq_y_divided", "y = (15 - x) / 2", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_fade_in(text_eq_y_divided, FRAME_CURRENT, FPS*0.5)
add_frame(FPS)

# 5. Now, the ConstraintGreaterThanSymbol(>) and ConstantBlock(5) from x > 5 glow and move.
# This implies substituting y from the equation into the constraint to get a y-only constraint.
# x > 5  =>  15 - 2y > 5
animate_fade_out(text_eq_y_divided, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

text_intermediate_ineq = create_text_object("Intermediate_Ineq", "15 - 2y > 5", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_fade_in(text_intermediate_ineq, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

# 7. ConstantBlock(15) glows, then slides to the right, changing to -15.
block_15_ineq, block_15_text_ineq = create_cube_with_text("Ineq_15_Block", "15", (1,1,0.2), (-2.5, 4.8, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])
minus_2_y_ineq = create_text_object("Ineq_Minus_2Y", "-2y", (-0.5, 4.8, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
gt_symbol_ineq = create_text_object("Ineq_GT_Symbol", ">", (1.5, 4.8, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_GlowOrange"])
block_5_ineq, block_5_text_ineq = create_cube_with_text("Ineq_5_Block", "5", (1,1,0.2), (3, 4.8, 4.5), materials["Mat_White"], materials["Mat_TextDefault"])

objs_ineq_s5 = [block_15_ineq, minus_2_y_ineq, gt_symbol_ineq, block_5_ineq]
for obj in objs_ineq_s5: animate_fade_in(obj, FRAME_CURRENT, FPS*0.5)
animate_fade_out(text_intermediate_ineq, FRAME_CURRENT, FPS*0.5)
animate_fade_out(const_s5_text, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

animate_glow_pulse(block_15_ineq, FRAME_CURRENT, FPS*0.5, peak_strength=5.0)
add_frame(FPS*0.5)

animate_move(block_15_ineq, FRAME_CURRENT, FRAME_CURRENT + FPS, block_15_ineq.location, (4.5, 4.8, 4.5))
block_15_text_ineq.data.body = "-15"
add_frame(FPS)

# 8. Inequality becomes: -2y > 5 - 15
animate_move(minus_2_y_ineq, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, minus_2_y_ineq.location, (-1.5, 4.8, 4.5))
animate_move(gt_symbol_ineq, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, gt_symbol_ineq.location, (0, 4.8, 4.5))
animate_move(block_5_ineq, FRAME_CURRENT, FRAME_CURRENT + FPS*0.5, block_5_ineq.location, (1.5, 4.8, 4.5))
add_frame(FPS*0.5)

text_ineq_step2 = create_text_object("Ineq_Step2", "-2y > 5 - 15", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_fade_in(text_ineq_step2, FRAME_CURRENT, FPS*0.5)
add_frame(FPS)

# 9. 5 and -15 combine into -10
animate_fade_out(minus_2_y_ineq, FRAME_CURRENT, FPS*0.5)
animate_fade_out(gt_symbol_ineq, FRAME_CURRENT, FPS*0.5)
animate_fade_out(block_5_ineq, FRAME_CURRENT, FPS*0.5)
animate_fade_out(block_15_ineq, FRAME_CURRENT, FPS*0.5)
animate_fade_out(text_ineq_step2, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

text_ineq_step3 = create_text_object("Ineq_Step3", "-2y > -10", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
animate_fade_in(text_ineq_step3, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

# 11. -2 separates from y and slides under -10. > flips to <.
minus_2_y_final = create_text_object("Ineq_Minus_2Y_Final", "-2y", (-1, 4.8, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
gt_symbol_final = create_text_object("Ineq_GT_Symbol_Final", ">", (0, 4.8, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_GlowOrange"])
minus_10_final = create_text_object("Ineq_Minus_10_Final", "-10", (1, 4.8, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])

for obj in [minus_2_y_final, gt_symbol_final, minus_10_final]:
    animate_fade_in(obj, FRAME_CURRENT, FPS*0.5)
animate_fade_out(text_ineq_step3, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

animate_glow_pulse(minus_2_y_final, FRAME_CURRENT, FPS*0.5, peak_strength=5.0)
add_frame(FPS*0.5)

# Inequality flip animation
set_frame(FRAME_CURRENT)
gt_symbol_final.rotation_euler = (math.radians(90), 0, 0)
gt_symbol_final.keyframe_insert(data_path='rotation_euler')
set_frame(FRAME_CURRENT + FPS*0.75)
gt_symbol_final.rotation_euler = (math.radians(90), math.radians(180), 0)
gt_symbol_final.data.body = "<" # Change text as it flips
gt_symbol_final.keyframe_insert(data_path='rotation_euler')
gt_symbol_final.keyframe_insert(data_path='body')
add_frame(FPS*0.75)

animate_fade_out(minus_2_y_final, FRAME_CURRENT, FPS*0.5)
animate_fade_out(gt_symbol_final, FRAME_CURRENT, FPS*0.5)
animate_fade_out(minus_10_final, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

# 12-14. Final conclusion appears: y < 5.
text_ineq_final = create_text_object("Ineq_Final_Y_lt_5", "y < 5", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_GlowGreen"])
animate_text_typing(text_ineq_final, FRAME_CURRENT, FPS)
animate_glow_pulse(text_ineq_final, FRAME_CURRENT + FPS, FPS, initial_strength=materials["Mat_GlowGreen"].inputs['Strength'].default_value, peak_strength=5.0)
add_frame(FPS*2)


# --- Scene 6: Conclusion - Examples and Final Summary (14 seconds) ---
print("Animating Scene 6...")
scene6_duration = 14 * FPS

animate_fade_out(text_ineq_final, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

# Whiteboard displays x + 2y = 15, x > 5, and y < 5.
text_final_eq = create_text_object("Final_Eq", "x + 2y = 15", (0, 4.9, 6.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
text_final_const_x = create_text_object("Final_Const_X", "x > 5", (0, 4.9, 5.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
text_final_const_y = create_text_object("Final_Const_Y", "y < 5", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])

for obj in [text_final_eq, text_final_const_x, text_final_const_y]:
    animate_fade_in(obj, FRAME_CURRENT, FPS)
add_frame(FPS)

# GraphPlane reappears
animate_fade_in(graph_plane_empty, FRAME_CURRENT, FPS)
animate_fade_in(line_solution, FRAME_CURRENT, FPS)
animate_fade_in(constraint_line_x5, FRAME_CURRENT, FPS)
animate_fade_in(constraint_shade, FRAME_CURRENT, FPS)
add_frame(FPS)

# Example solutions
examples_parent = bpy.data.objects.new("Examples_Parent", None)
main_collection.objects.link(examples_parent)
examples_parent.location = (0, 4.9, 3) # Offset for whiteboard
animate_hide_show(examples_parent, FRAME_CURRENT, show=True)

# Example 1: If x = 6, y = 4.5
text_ex1_if = create_text_object("Ex1_If", "If x = 6:", (-5, 0, 1.5), (math.radians(90), 0, 0), 0.4, materials["Mat_TextDefault"])
text_ex1_calc = create_text_object("Ex1_Calc", "6 + 2y = 15 -> 2y = 9 -> y = 4.5", (1, 0, 1.5), (math.radians(90), 0, 0), 0.4, materials["Mat_TextDefault"])
text_ex1_pair = create_text_object("Ex1_Pair", "(6, 4.5)", (0, 0, 0.5), (math.radians(90), 0, 0), 0.5, materials["Mat_GlowBlue"])
solution_point_1 = create_sphere("SolPoint1", 0.2, (6, 4.5, 3.02), materials["Mat_GlowBlue"])
solution_point_1.parent = examples_parent

for obj in [text_ex1_if, text_ex1_calc, text_ex1_pair]:
    obj.parent = examples_parent
    animate_fade_in(obj, FRAME_CURRENT, FPS*0.5)
animate_fade_in(solution_point_1, FRAME_CURRENT, FPS*0.5)
animate_glow_pulse(solution_point_1, FRAME_CURRENT + FPS*0.5, FPS, initial_strength=materials["Mat_GlowBlue"].inputs['Strength'].default_value, peak_strength=8.0)
add_frame(FPS*1.5)

# Example 2: If x = 7, y = 4
text_ex2_if = create_text_object("Ex2_If", "If x = 7:", (-5, 0, 0), (math.radians(90), 0, 0), 0.4, materials["Mat_TextDefault"])
text_ex2_calc = create_text_object("Ex2_Calc", "7 + 2y = 15 -> 2y = 8 -> y = 4", (1, 0, 0), (math.radians(90), 0, 0), 0.4, materials["Mat_TextDefault"])
text_ex2_pair = create_text_object("Ex2_Pair", "(7, 4)", (0, 0, -1), (math.radians(90), 0, 0), 0.5, materials["Mat_GlowBlue"])
solution_point_2 = create_sphere("SolPoint2", 0.2, (7, 4, 3.02), materials["Mat_GlowBlue"])
solution_point_2.parent = examples_parent

for obj in [text_ex2_if, text_ex2_calc, text_ex2_pair]:
    obj.parent = examples_parent
    animate_fade_in(obj, FRAME_CURRENT, FPS*0.5)
animate_fade_in(solution_point_2, FRAME_CURRENT, FPS*0.5)
animate_glow_pulse(solution_point_2, FRAME_CURRENT + FPS*0.5, FPS, initial_strength=materials["Mat_GlowBlue"].inputs['Strength'].default_value, peak_strength=8.0)
add_frame(FPS*1.5)

# Example 3: If x = 10, y = 2.5
text_ex3_if = create_text_object("Ex3_If", "If x = 10:", (-5, 0, -1.5), (math.radians(90), 0, 0), 0.4, materials["Mat_TextDefault"])
text_ex3_calc = create_text_object("Ex3_Calc", "10 + 2y = 15 -> 2y = 5 -> y = 2.5", (1, 0, -1.5), (math.radians(90), 0, 0),  0.4, materials["Mat_TextDefault"])
text_ex3_pair = create_text_object("Ex3_Pair", "(10, 2.5)", (0, 0, -2.5), (math.radians(90), 0, 0), 0.5, materials["Mat_GlowBlue"])
solution_point_3 = create_sphere("SolPoint3", 0.2, (10, 2.5, 3.02), materials["Mat_GlowBlue"])
solution_point_3.parent = examples_parent

for obj in [text_ex3_if, text_ex3_calc, text_ex3_pair]:
    obj.parent = examples_parent
    animate_fade_in(obj, FRAME_CURRENT, FPS*0.5)
animate_fade_in(solution_point_3, FRAME_CURRENT, FPS*0.5)
animate_glow_pulse(solution_point_3, FRAME_CURRENT + FPS*0.5, FPS, initial_strength=materials["Mat_GlowBlue"].inputs['Strength'].default_value, peak_strength=8.0)
add_frame(FPS*1.5)

# All three solution points pulse in unison.
animate_glow_pulse(solution_point_1, FRAME_CURRENT, FPS*1.5, initial_strength=materials["Mat_GlowBlue"].inputs['Strength'].default_value, peak_strength=8.0, pulses=2)
animate_glow_pulse(solution_point_2, FRAME_CURRENT, FPS*1.5, initial_strength=materials["Mat_GlowBlue"].inputs['Strength'].default_value, peak_strength=8.0, pulses=2)
animate_glow_pulse(solution_point_3, FRAME_CURRENT, FPS*1.5, initial_strength=materials["Mat_GlowBlue"].inputs['Strength'].default_value, peak_strength=8.0, pulses=2)
add_frame(FPS*1.5)

# Final summary text
animate_fade_out(text_final_eq, FRAME_CURRENT, FPS*0.5)
animate_fade_out(text_final_const_x, FRAME_CURRENT, FPS*0.5)
animate_fade_out(text_final_const_y, FRAME_CURRENT, FPS*0.5)
animate_fade_out(examples_parent, FRAME_CURRENT, FPS*0.5)
add_frame(FPS*0.5)

final_summary_p1 = create_text_object("FinalSummary_P1", "Conclusion: There is no single, unique value for x and y.", (0, 4.9, 5.5), (math.radians(90), 0, 0), 0.7, materials["Mat_TextDefault"])
final_summary_p2 = create_text_object("FinalSummary_P2", "The solutions are any pairs (x, y) such that:", (0, 4.9, 4.5), (math.radians(90), 0, 0), 0.6, materials["Mat_TextDefault"])
final_summary_p3 = create_text_object("FinalSummary_P3", "x + 2y = 15 AND x > 5 (which implies y < 5).", (0, 4.9, 3.5), (math.radians(90), 0, 0), 0.6, materials["Mat_TextDefault"])

animate_text_typing(final_summary_p1, FRAME_CURRENT, FPS*1.5)
animate_text_typing(final_summary_p2, FRAME_CURRENT + FPS*1.5, FPS*1.5)
animate_text_typing(final_summary_p3, FRAME_CURRENT + FPS*3, FPS*2)
add_frame(FPS*5)

# Camera slowly zooms out
set_frame(FRAME_CURRENT)
camera_start_loc = camera.location
camera_start_rot = camera.rotation_euler
camera_end_loc = (0, -15, 5)
camera_end_rot = (math.radians(70), 0, 0)
animate_move(camera, FRAME_CURRENT, FRAME_CURRENT + FPS*3, camera_start_loc, camera_end_loc, camera_start_rot, camera_end_rot)
add_frame(FPS*3)

# --- Final Render Settings ---
bpy.context.scene.frame_end = FRAME_CURRENT + FPS * 2 # Add buffer at the end
print(f"Total animation duration: {bpy.context.scene.frame_end / FPS} seconds ({bpy.context.scene.frame_end} frames)")

# Set default interpolation to Bezier for all F-curves
for fcurve in bpy.context.scene.animation_data.action.fcurves:
    fcurve.modifiers.new(type='LIMITS') # Add limits modifier to prevent unwanted extrapolation
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'BEZIER'
        
print("Animation script finished. Render settings applied.")
