
import bpy
import math
import mathutils

# --- General Setup ---
def clean_scene():
    """Cleans up the scene by deleting all objects."""
    if bpy.context.mode == 'EDIT_MESH':
        bpy.ops.object.editmode_toggle() # Exit edit mode if active

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Delete collections if they exist and are not part of the default scene
    for collection in bpy.data.collections:
        if collection.name not in ["Scene Collection", "Light", "Camera"]: # Keep default collections
            for obj in collection.objects:
                if obj.users == 0: # Only delete if no users link to it
                    bpy.data.objects.remove(obj, do_unlink=True)
            if collection.users == 0: # Only delete if no users link to it
                bpy.data.collections.remove(collection)

    # Clean up orphaned data (meshes, materials, textures, etc.)
    for block in bpy.data.meshes:
        if block.users == 0: bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0: bpy.data.materials.remove(block)
    for block in bpy.data.textures:
        if block.users == 0: bpy.data.textures.remove(block)
    for block in bpy.data.images:
        if block.users == 0: bpy.data.images.remove(block)
    for block in bpy.data.curves:
        if block.users == 0: bpy.data.curves.remove(block)
    for block in bpy.data.actions:
        if block.users == 0: bpy.data.actions.remove(block)


def setup_scene_properties():
    """Sets up render engine, frame rate, and timeline."""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.fps = 30
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.ffmpeg.gop_size = 18
    scene.render.ffmpeg.frame_rate = '30'

    scene.frame_start = 0
    # scene.frame_end will be set dynamically at the end

    # Eevee settings
    bpy.context.scene.eevee.use_bloom = True
    bpy.context.scene.eevee.bloom_threshold = 0.5
    bpy.context.scene.eevee.bloom_intensity = 0.05
    bpy.context.scene.eevee.bloom_radius = 6.0
    bpy.context.scene.eevee.use_ssr = True
    bpy.context.scene.eevee.use_ssao = True
    bpy.context.scene.eevee.ssao_distance_max = 2.0


def create_lighting():
    """Creates basic lighting for the scene."""
    # Delete default lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    # Main Area Light (Softbox)
    bpy.ops.object.light_add(type='AREA', location=(0, -5, 5))
    area_light = bpy.context.object
    area_light.rotation_euler = (math.radians(45), 0, 0)
    area_light.data.energy = 500
    area_light.data.size = 5
    area_light.name = "MainAreaLight"

    # Fill Light (Smaller, less intense)
    bpy.ops.object.light_add(type='AREA', location=(0, 5, 3))
    fill_light = bpy.context.object
    fill_light.rotation_euler = (math.radians(-45), math.radians(180), 0)
    fill_light.data.energy = 200
    fill_light.data.size = 3
    fill_light.name = "FillAreaLight"

    # Back Light (Rim light)
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 10))
    back_light = bpy.context.object
    back_light.rotation_euler = (math.radians(180), 0, 0)
    back_light.data.energy = 150
    back_light.data.size = 4
    back_light.name = "BackAreaLight"


def create_camera():
    """Creates and positions the main camera."""
    bpy.ops.object.camera_add(location=(0, -15, 5))
    camera = bpy.context.object
    camera.rotation_euler = (math.radians(70), 0, 0) # Pointing down towards origin
    bpy.context.scene.camera = camera
    return camera

# --- Material Definitions ---
def create_material(name, color=(0.8, 0.8, 0.8, 1), emission=(0,0,0,1), metallic=0.0, roughness=0.5):
    """Creates a PBR material with optional emission."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness

    if emission != (0,0,0,1):
        # Create Emission node
        emission_node = mat.node_tree.nodes.new(type="ShaderNodeEmission")
        emission_node.inputs["Color"].default_value = emission
        emission_node.inputs["Strength"].default_value = 0.0 # Start with no emission

        # Create Mix Shader to combine Principled BSDF and Emission
        mix_shader = mat.node_tree.nodes.new(type="ShaderNodeMixShader")
        mat.node_tree.links.new(bsdf.outputs["BSDF"], mix_shader.inputs[1])
        mat.node_tree.links.new(emission_node.outputs["Emission"], mix_shader.inputs[2])
        mix_shader.inputs["Factor"].default_value = 0.0 # Start with 0 emission factor

        mat.node_tree.links.new(mix_shader.outputs["Shader"], mat.node_tree.nodes["Material Output"].inputs["Surface"])
    
    # Enable transparency if alpha is less than 1
    if color[3] < 1.0:
        mat.blend_method = 'BLEND'
        mat.shadow_method = 'HASHED'

    return mat

def create_glass_material(name, color=(0.8, 0.8, 0.8, 1), roughness=0.1, ior=1.45):
    """Creates a glass material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create new nodes
    glass_shader = nodes.new(type='ShaderNodeBsdfGlass')
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # Connect nodes
    links.new(glass_shader.outputs['BSDF'], output_node.inputs['Surface'])

    # Set properties
    glass_shader.inputs['Color'].default_value = color
    glass_shader.inputs['Roughness'].default_value = roughness
    glass_shader.inputs['IOR'].default_value = ior
    return mat

# --- Asset Creation Functions ---
def create_whiteboard(size=20, grid_spacing=1, thickness=0.1):
    """Creates a whiteboard plane with a grid texture."""
    bpy.ops.mesh.primitive_plane_add(size=size, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    board = bpy.context.object
    board.name = "WhiteboardGrid"
    
    # Create whiteboard material
    mat = bpy.data.materials.new(name="Whiteboard_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Principled BSDF and Output
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # Grid Texture
    grid_tex = nodes.new(type='ShaderNodeTexGrid')
    grid_tex.inputs['Size'].default_value = grid_spacing
    grid_tex.inputs['Line Thickness'].default_value = 0.02
    grid_tex.inputs['Blur'].default_value = 0.005 # Subtle blur for marker effect

    # Mix Color for grid lines
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    mix_rgb.blend_type = 'MIX'
    mix_rgb.inputs['Factor'].default_value = 1.0 # Use grid as factor
    mix_rgb.inputs['Color1'].default_value = (0.9, 0.9, 0.9, 1) # Whiteboard color
    mix_rgb.inputs['Color2'].default_value = (0.3, 0.3, 0.3, 1) # Grid line color

    links.new(grid_tex.outputs['Color'], mix_rgb.inputs['Factor'])
    links.new(mix_rgb.outputs['Color'], principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.8 # Matte whiteboard

    board.data.materials.append(mat)
    
    # Add a subtle thickness
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    board.modifiers["Solidify"].thickness = thickness
    board.location.z = -thickness / 2 # To keep top surface at Z=0
    return board

def create_text_object(name, text_string, font_size=1.0, location=(0,0,0), rotation=(0,0,0), material=None, parent=None):
    """Creates a Blender text object."""
    font_curve = bpy.data.curves.new(type="FONT", name=name + "_Curve")
    font_curve.body = text_string
    font_curve.align_x = 'CENTER'
    font_curve.align_y = 'CENTER'
    font_curve.size = font_size
    font_curve.extrude = 0.05 # For 3D text
    font_curve.resolution_u = 2 # Higher resolution for smoother curves

    text_obj = bpy.data.objects.new(name, font_curve)
    bpy.context.collection.objects.link(text_obj)
    text_obj.location = location
    text_obj.rotation_euler = rotation

    if material:
        if material.name not in text_obj.data.materials: # Check if material is already assigned
            text_obj.data.materials.append(material)

    if parent:
        text_obj.parent = parent
        text_obj.matrix_parent_inverse = parent.matrix_world.inverted()

    return text_obj

def create_variable_box(name, char, color, size=1.0):
    """Creates a rounded cube with embossed glowing text."""
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0,0,0))
    cube = bpy.context.object
    cube.name = name

    # Add Bevel modifier for rounded edges
    bpy.ops.object.modifier_add(type='BEVEL')
    cube.modifiers["Bevel"].width = 0.1 * size
    cube.modifiers["Bevel"].segments = 4
    bpy.ops.object.shade_smooth()

    # Create material
    mat = create_material(f"{name}_Mat", color=color + (1,), emission=color + (1,), metallic=0.2, roughness=0.3)
    cube.data.materials.append(mat)

    # Create embossed text
    text_obj = create_text_object(f"{name}_Text", char, font_size=size*0.7, location=(0,0,0.5 * size + 0.01), rotation=(math.radians(90),0,0), material=mat, parent=cube)
    
    # Add a solidify modifier to the text to give it depth
    # Select text object, make it active
    bpy.ops.object.select_all(action='DESELECT')
    text_obj.select_set(True)
    bpy.context.view_layer.objects.active = text_obj
    
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    text_obj.modifiers["Solidify"].thickness = -0.05 # Inward emboss
    text_obj.modifiers["Solidify"].offset = 0 # To push into the cube
    
    # Select original cube
    bpy.ops.object.select_all(action='DESELECT')
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube

    return cube

def create_constant_block(name, number_or_str, color, size=1.0):
    """Creates a polished glass-like block with a number/string inside."""
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0,0,0))
    cube = bpy.context.object
    cube.name = name

    # Add Bevel modifier for rounded edges
    bpy.ops.object.modifier_add(type='BEVEL')
    cube.modifiers["Bevel"].width = 0.1 * size
    cube.modifiers["Bevel"].segments = 4
    bpy.ops.object.shade_smooth()

    # Create glass material
    glass_mat = create_glass_material(f"{name}_GlassMat", color=color + (0.5,)) # Semi-transparent
    cube.data.materials.append(glass_mat)

    # Create internal text
    # Ensure text is string for text object creation
    text_content = str(number_or_str)
    
    text_obj = create_text_object(f"{name}_InternalText", text_content, font_size=size*0.6, location=(0,0,0), material=create_material(f"{name}_InternalTextMat", color=(0.8,0.8,0.8,1), emission=(0.5,0.5,0.5,1)), parent=cube)
    text_obj.rotation_euler = (math.radians(90), 0, 0) # Standing upright
    text_obj.location.z = size * 0.01 # Slightly offset to avoid z-fighting

    return cube

def create_operation_arrow(name, symbol, color, size=1.0):
    """Creates a simple arrow mesh with a symbol."""
    # Create arrow shape (simple cone + cylinder)
    bpy.ops.mesh.primitive_cone_add(radius1=0.2*size, depth=0.5*size, enter_editmode=False, align='WORLD', location=(0,0,0.25*size))
    cone = bpy.context.object
    cone.name = f"{name}_Cone"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1*size, depth=0.5*size, enter_editmode=False, align='WORLD', location=(0,0,-0.25*size))
    cyl = bpy.context.object
    cyl.name = f"{name}_Cylinder"
    
    # Join them
    bpy.ops.object.select_all(action='DESELECT')
    cone.select_set(True)
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cone
    bpy.ops.object.join()
    arrow_obj = bpy.context.object
    arrow_obj.name = name
    
    # Align arrow to point along X axis initially
    arrow_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

    # Create material (glowing)
    mat = create_material(f"{name}_Mat", color=color + (1,), emission=color + (1,), roughness=0.2)
    arrow_obj.data.materials.append(mat)

    # Add symbol text
    text_obj = create_text_object(f"{name}_Text", symbol, font_size=0.5*size, location=(-0.3*size,0,0), material=mat, parent=arrow_obj)
    text_obj.rotation_euler = (math.radians(90), 0, 0)

    return arrow_obj

# --- Animation Functions ---
def set_keyframe(obj, prop, frame, value):
    """Sets a keyframe for a given property directly."""
    # Ensure the object has animation data
    if not obj.animation_data:
        obj.animation_data_create()
    if not obj.animation_data.action:
        obj.animation_data.action = bpy.data.actions.new(name=f"{obj.name}_Action")

    # Insert keyframe and set value
    if isinstance(value, mathutils.Vector):
        for i in range(len(value)):
            obj.keyframe_insert(data_path=prop, index=i, frame=frame)
            fcurve = obj.animation_data.action.fcurves.find(prop, index=i)
            if fcurve:
                kp = fcurve.keyframe_points[-1]
                kp.co[1] = value[i]
    else:
        obj.keyframe_insert(data_path=prop, frame=frame)
        fcurve = obj.animation_data.action.fcurves.find(prop)
        if fcurve:
            kp = fcurve.keyframe_points[-1]
            kp.co[1] = value

def animate_location(obj, start_frame, end_frame, start_loc, end_loc, ease_in_out=True):
    """Animates an object's location."""
    obj.location = start_loc
    set_keyframe(obj, 'location', start_frame, start_loc)
    
    obj.location = end_loc
    set_keyframe(obj, 'location', end_frame, end_loc)

    if ease_in_out:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path == 'location':
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    kp.handle_left_type = 'AUTO'
                    kp.handle_right_type = 'AUTO'

def animate_scale(obj, start_frame, end_frame, start_scale, end_scale, ease_in_out=True):
    """Animates an object's scale."""
    obj.scale = mathutils.Vector((start_scale, start_scale, start_scale))
    set_keyframe(obj, 'scale', start_frame, obj.scale) # Use current scale value for keyframe
    
    obj.scale = mathutils.Vector((end_scale, end_scale, end_scale))
    set_keyframe(obj, 'scale', end_frame, obj.scale) # Use current scale value for keyframe

    if ease_in_out:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path == 'scale':
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    kp.handle_left_type = 'AUTO'
                    kp.handle_right_type = 'AUTO'

def animate_visibility(obj, start_frame, end_frame, hide_render_start, hide_render_end):
    """Animates hide_render property."""
    obj.hide_render = hide_render_start
    obj.keyframe_insert(data_path='hide_render', frame=start_frame)
    obj.hide_render = hide_render_end
    obj.keyframe_insert(data_path='hide_render', frame=end_frame)
    
    # Ensure visibility is immediate (constant interpolation)
    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.data_path == 'hide_render':
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'CONSTANT'
    
    # Also set hide_viewport for consistency during animation setup
    obj.hide_viewport = hide_render_start
    obj.keyframe_insert(data_path='hide_viewport', frame=start_frame)
    obj.hide_viewport = hide_render_end
    obj.keyframe_insert(data_path='hide_viewport', frame=end_frame)
    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.data_path == 'hide_viewport':
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'CONSTANT'

def animate_glow(obj, start_frame, end_frame, start_strength, end_strength, ease_in_out=True):
    """Animates the emission strength of an object's material."""
    if not obj.data.materials:
        # print(f"Object {obj.name} has no materials for glow animation.")
        return

    mat = obj.data.materials[0] # Assuming the first material is the one to animate
    if not mat.use_nodes:
        # print(f"Material {mat.name} does not use nodes for glow animation.")
        return

    emission_node = None
    mix_node = None
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
        if node.type == 'MIX_SHADER':
            mix_node = node # Assuming mix_shader is used for combining principled and emission

    if not emission_node and not mix_node: # If no emission nodes were setup in material
        # print(f"Material {mat.name} does not have the expected emission/mix shader setup for glow animation.")
        return

    # Animate Emission Strength (if emission node exists)
    if emission_node:
        emission_node.inputs["Strength"].default_value = start_strength
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=start_frame)
        emission_node.inputs["Strength"].default_value = end_strength
        emission_node.inputs["Strength"].keyframe_insert(data_path='default_value', frame=end_frame)

        if ease_in_out:
            fcurve = mat.node_tree.animation_data.action.fcurves.find('nodes["Emission"].inputs[1].default_value')
            if fcurve:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    kp.handle_left_type = 'AUTO'
                    kp.handle_right_type = 'AUTO'

    # Animate Mix Shader Factor (if mix node exists, to blend in emission)
    if mix_node:
        mix_node.inputs["Factor"].default_value = 0.0 if start_strength == 0 else 1.0 # If starting with no glow, factor is 0
        mix_node.inputs["Factor"].keyframe_insert(data_path='default_value', frame=start_frame)
        mix_node.inputs["Factor"].default_value = 1.0 if end_strength > 0 else 0.0 # If ending with glow, factor is 1, else 0
        mix_node.inputs["Factor"].keyframe_insert(data_path='default_value', frame=end_frame)
        
        if ease_in_out:
            fcurve_mix = mat.node_tree.animation_data.action.fcurves.find('nodes["Mix Shader"].inputs[0].default_value')
            if fcurve_mix:
                for kp in fcurve_mix.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    kp.handle_left_type = 'AUTO'
                    kp.handle_right_type = 'AUTO'


def animate_text_write_on(text_obj, start_frame, duration):
    """Simulates text writing itself by animating character visibility."""
    original_text = text_obj.data.body
    text_obj.data.body = ""
    text_obj.keyframe_insert(data_path='body', frame=start_frame)

    if len(original_text) == 0:
        return

    frame_per_char = duration / len(original_text)
    
    for i in range(len(original_text) + 1):
        text_obj.data.body = original_text[:i]
        text_obj.keyframe_insert(data_path='body', frame=start_frame + math.floor(i * frame_per_char))

    # Ensure last frame holds the full text
    text_obj.data.body = original_text
    text_obj.keyframe_insert(data_path='body', frame=start_frame + duration)
    
    # Set interpolation to constant for text
    fcurve = text_obj.animation_data.action.fcurves.find('body')
    if fcurve:
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'CONSTANT'


def animate_camera_dolly(camera_obj, target_obj, start_frame, end_frame, start_loc, end_loc, start_fov=50, end_fov=50):
    """Animates camera dolly and optionally FOV, keeping it pointed at a target."""
    # Check if a target empty already exists for this camera, otherwise create one
    camera_target = bpy.data.objects.get(f"{camera_obj.name}_Target")
    if not camera_target:
        bpy.ops.object.empty_add(location=target_obj.location)
        camera_target = bpy.context.object
        camera_target.name = f"{camera_obj.name}_Target"
        # Add Track To constraint to camera
        track_constraint = camera_obj.constraints.new(type='TRACK_TO')
        track_constraint.target = camera_target
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'
    
    # Animate camera location
    animate_location(camera_obj, start_frame, end_frame, start_loc, end_loc)
    
    # Animate FOV (focal length)
    camera_obj.data.lens = start_fov
    camera_obj.data.keyframe_insert(data_path='lens', frame=start_frame)
    camera_obj.data.lens = end_fov
    camera_obj.data.keyframe_insert(data_path='lens', frame=end_frame)
    for fcurve in camera_obj.data.animation_data.action.fcurves:
        if fcurve.data_path == 'lens':
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = 'AUTO'
                kp.handle_right_type = 'AUTO'

    # Animate target object location to follow target_obj, or stay fixed if target_obj is None
    if target_obj:
        camera_target.location = target_obj.location
        camera_target.keyframe_insert(data_path='location', frame=start_frame)
        camera_target.location = target_obj.location # If target is fixed, it will stay here
        camera_target.keyframe_insert(data_path='location', frame=end_frame)
    else: # If no specific target object, just make the empty static at initial target_obj location
        camera_target.keyframe_insert(data_path='location', frame=start_frame)
        camera_target.keyframe_insert(data_path='location', frame=end_frame)
    
    # Ensure interpolation is linear for target movement if it's supposed to follow rigidly
    for fcurve in camera_target.animation_data.action.fcurves:
        if fcurve.data_path == 'location':
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'


# --- Main Animation Logic ---
def create_animation():
    clean_scene()
    setup_scene_properties()
    camera = create_camera()
    create_lighting()
    whiteboard = create_whiteboard()

    # --- Materials ---
    mat_x_glow = create_material("Mat_X_Glow", color=(0.1, 0.5, 0.7, 1), emission=(0.1, 0.5, 0.7, 1), metallic=0.2, roughness=0.3)
    mat_y_glow = create_material("Mat_Y_Glow", color=(0.3, 0.8, 0.1, 1), emission=(0.3, 0.8, 0.1, 1), metallic=0.2, roughness=0.3)
    mat_num_glow = create_material("Mat_Num_Glow", color=(0.8, 0.8, 0.8, 1), emission=(0.5, 0.5, 0.5, 1), metallic=0.1, roughness=0.4)
    mat_op_plus = create_material("Mat_Op_Plus", color=(1.0, 0.5, 0.0, 1), emission=(1.0, 0.5, 0.0, 1))
    mat_op_minus = create_material("Mat_Op_Minus", color=(0.5, 0.0, 0.5, 1), emission=(0.5, 0.0, 0.5, 1))
    mat_op_multiply = create_material("Mat_Op_Multiply", color=(0.8, 0.0, 0.0, 1), emission=(0.8, 0.0, 0.0, 1))
    mat_op_divide = create_material("Mat_Op_Divide", color=(1.0, 1.0, 0.0, 1), emission=(1.0, 1.0, 0.0, 1))
    mat_op_equals = create_material("Mat_Op_Equals", color=(1.0, 1.0, 1.0, 1), emission=(1.0, 1.0, 1.0, 1))
    mat_i_unit = create_material("Mat_i_Unit", color=(0.8, 0.1, 0.8, 1), emission=(0.8, 0.1, 0.8, 1), metallic=0.2, roughness=0.3) # Imaginary 'i' color
    mat_equation_text = create_material("Mat_Equation_Text", color=(0.1, 0.1, 0.1, 1), emission=(0,0,0,1)) # Dark text, no emission by default
    mat_red_warning = create_material("Mat_Red_Warning", color=(1.0, 0.0, 0.0, 1), emission=(1.0, 0.0, 0.0, 1))

    # Define a consistent camera target for full-view formula.
    # It needs to be an object to be tracked.
    full_formula_target_loc = (0, 0, 1)
    full_formula_cam_loc = (0, -15, 5)
    camera_target_full_view = bpy.data.objects.get(f"{camera.name}_Target") # Reuse if exists
    if not camera_target_full_view:
        bpy.ops.object.empty_add(location=full_formula_target_loc)
        camera_target_full_view = bpy.context.object
        camera_target_full_view.name = f"{camera.name}_Target"
        # Add Track To constraint to camera
        track_constraint = camera.constraints.new(type='TRACK_TO')
        track_constraint.target = camera_target_full_view
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'
    else: # Update location if it's reused
        camera_target_full_view.location = full_formula_target_loc
        camera_target_full_view.keyframe_insert(data_path='location', frame=0) # Ensure it's keyed at start
    
    # --- Animation Timing (in frames) ---
    current_frame = bpy.context.scene.frame_start

    # Scene 1: Introduction - The Problem Statement (5 seconds = 150 frames)
    S1_START = current_frame
    S1_DURATION = 5 * 30
    S1_END = S1_START + S1_DURATION

    # Camera pull back
    animate_location(camera, S1_START, S1_START + 60, (0, -5, 2), full_formula_cam_loc)
    camera.data.lens = 50
    camera.data.keyframe_insert(data_path='lens', frame=S1_START)
    camera.data.lens = 50 # Keep same for S1 for now
    camera.data.keyframe_insert(data_path='lens', frame=S1_START + 60)

    # Equation text (pre-calculated positions for better alignment)
    equation_base_y = 1
    equation_y_prefix_loc = (-5.5, 0, equation_base_y) # Adjust based on font size/kerning
    equation_main_loc = (0, 0, equation_base_y)

    equation_text = create_text_object("Equation_Initial", "x^2 + 3x + 7 = 0", font_size=1.5, location=equation_main_loc, rotation=(math.radians(90), 0, 0), material=mat_equation_text)
    equation_text_y = create_text_object("Equation_Y_Prefix", "y =", font_size=1.5, location=equation_y_prefix_loc, rotation=(math.radians(90), 0, 0), material=mat_equation_text)
    
    # Hide initially for write-on
    equation_text.hide_render = True
    equation_text_y.hide_render = True
    equation_text.hide_viewport = True
    equation_text_y.hide_viewport = True

    # Fade/Write in equation
    animate_text_write_on(equation_text_y, S1_START + 30, 30)
    animate_visibility(equation_text_y, S1_START + 30, S1_START + 31, True, False) # Make visible at start of write-on
    
    animate_text_write_on(equation_text, S1_START + 60, 60)
    animate_visibility(equation_text, S1_START + 60, S1_START + 61, True, False) # Make visible

    # Glow briefly
    animate_glow(equation_text.data.materials[0], S1_START + 120, S1_START + 135, 0.0, 2.0)
    animate_glow(equation_text.data.materials[0], S1_START + 135, S1_START + 150, 2.0, 0.0)

    # Variable boxes
    x_box = create_variable_box("X_Var_Box", "x", (0.1, 0.5, 0.7), size=1.0)
    y_box = create_variable_box("Y_Var_Box", "y", (0.3, 0.8, 0.1), size=1.0)

    x_box_loc_target = (equation_main_loc[0] + 4, 0, 0.5) # Next to 'x' in equation
    y_box_loc_target = (equation_y_prefix_loc[0] - 2, 0, 0.5) # Next to 'y' in equation

    # Initial positions off screen, then slide in
    animate_location(x_box, S1_START + 90, S1_START + 120, (x_box_loc_target[0], -5, x_box_loc_target[2]), x_box_loc_target)
    animate_location(y_box, S1_START + 90, S1_START + 120, (y_box_loc_target[0], -5, y_box_loc_target[2]), y_box_loc_target)
    
    animate_glow(x_box.data.materials[0], S1_START + 120, S1_START + 150, 0.0, 1.0)
    animate_glow(y_box.data.materials[0], S1_START + 120, S1_START + 150, 0.0, 1.0)

    current_frame = S1_END + 30

    # Scene 2: Standard Form and Identifying Coefficients (8 seconds = 240 frames)
    S2_START = current_frame
    S2_DURATION = 8 * 30
    S2_END = S2_START + S2_DURATION

    # Shrink and move original equation
    equation_shrink_loc = (2, 0, 3) # Offset slightly to the right for 'ax^2' alignment
    animate_scale(equation_text, S2_START, S2_START + 30, 1.5, 1.0)
    animate_scale(equation_text_y, S2_START, S2_START + 30, 1.5, 1.0)
    animate_location(equation_text, S2_START, S2_START + 30, equation_main_loc, equation_shrink_loc)
    animate_location(equation_text_y, S2_START, S2_START + 30, equation_y_prefix_loc, (equation_shrink_loc[0] - 4, 0, 3)) # Relative to equation text
    
    animate_location(x_box, S2_START, S2_START + 30, x_box_loc_target, (equation_shrink_loc[0] + 2, 0, 2.5)) # Adjust x_box pos
    animate_location(y_box, S2_START, S2_START + 30, y_box_loc_target, (equation_shrink_loc[0] - 6, 0, 2.5)) # Adjust y_box pos
    
    animate_glow(x_box.data.materials[0], S2_START, S2_START + 30, 1.0, 0.0)
    animate_glow(y_box.data.materials[0], S2_START, S2_START + 30, 1.0, 0.0)

    # Standard form appears
    standard_form_loc = (0, 0, 1)
    standard_form_text = create_text_object("Standard_Form_Text", "ax^2 + bx + c = 0", font_size=1.2, location=(standard_form_loc[0], 5, standard_form_loc[2]), rotation=(math.radians(90), 0, 0), material=mat_equation_text)
    animate_visibility(standard_form_text, S2_START + 60, S2_START + 61, True, False)
    animate_location(standard_form_text, S2_START + 60, S2_START + 90, (standard_form_loc[0], 5, standard_form_loc[2]), standard_form_loc)

    # a, b, c blocks (positions aligned with equation_shrink_loc's terms)
    # x^2 is at equation_shrink_loc.x - 2.5 (from total length 1.5 * 10 = 15, x^2 part is first)
    # 3x is at equation_shrink_loc.x + 0.5
    # 7 is at equation_shrink_loc.x + 3.0
    a_block_loc = (equation_shrink_loc[0] - 2.5, 0, 0.5)
    b_block_loc = (equation_shrink_loc[0] + 0.5, 0, 0.5)
    c_block_loc = (equation_shrink_loc[0] + 3.0, 0, 0.5)

    a_block = create_constant_block("A_Block", 1, (0.8, 0.2, 0.2), size=0.8)
    b_block = create_constant_block("B_Block", 3, (0.2, 0.8, 0.2), size=0.8)
    c_block = create_constant_block("C_Block", 7, (0.2, 0.2, 0.8), size=0.8)

    animate_location(a_block, S2_START + 90, S2_START + 120, (a_block_loc[0], -5, a_block_loc[2]), a_block_loc)
    animate_location(b_block, S2_START + 120, S2_START + 150, (b_block_loc[0], -5, b_block_loc[2]), b_block_loc)
    animate_location(c_block, S2_START + 150, S2_START + 180, (c_block_loc[0], -5, c_block_loc[2]), c_block_loc)
    
    animate_glow(a_block.data.materials[1], S2_START + 120, S2_START + 150, 0.0, 0.5)
    animate_glow(b_block.data.materials[1], S2_START + 150, S2_START + 180, 0.0, 0.5)
    animate_glow(c_block.data.materials[1], S2_START + 180, S2_START + 210, 0.0, 0.5)

    current_frame = S2_END + 30

    # Scene 3: Introducing the Quadratic Formula (10 seconds = 300 frames)
    S3_START = current_frame
    S3_DURATION = 10 * 30
    S3_END = S3_START + S3_DURATION

    # Recede previous elements
    animate_location(equation_text, S3_START, S3_START + 30, equation_text.location, (equation_text.location.x, equation_text.location.y, 5))
    animate_location(equation_text_y, S3_START, S3_START + 30, equation_text_y.location, (equation_text_y.location.x, equation_text_y.location.y, 5))
    animate_location(standard_form_text, S3_START, S3_START + 30, standard_form_text.location, (standard_form_text.location.x, standard_form_text.location.y, 5))
    animate_location(a_block, S3_START, S3_START + 30, a_block.location, (a_block.location.x, a_block.location.y, 5))
    animate_location(b_block, S3_START, S3_START + 30, b_block.location, (b_block.location.x, b_block.location.y, 5))
    animate_location(c_block, S3_START, S3_START + 30, c_block.location, (c_block.location.x, c_block.location.y, 5))
    
    # Quadratic Formula Assembly - This will be many text objects
    formula_scale = 1.0 # Base scale for formula elements
    formula_offset_z = 1 # Z position for formula elements
    # These coordinates are relative to the whiteboard origin (0,0,0) and the text is rotated.
    # So X in these tuples is left-right, Y is depth, Z is height.
    formula_parts = [
        ("x", (-4.0, 0, formula_offset_z), mat_equation_text),
        ("=", (-3.5, 0, formula_offset_z), mat_op_equals),
        ("(", (-2.5, 0, formula_offset_z), mat_equation_text),
        ("-", (-2.0, 0, formula_offset_z), mat_op_minus),
        ("b", (-1.5, 0, formula_offset_z), mat_num_glow), # Placeholder b
        ("\u00B1", (-0.8, 0, formula_offset_z), mat_op_plus), # Plus/Minus symbol
        ("\u221A", (0.0, 0, formula_offset_z + 0.2), mat_op_divide), # Square root symbol
        ("b^2", (0.5, 0, formula_offset_z), mat_num_glow), # Placeholder b^2
        ("-", (1.2, 0, formula_offset_z), mat_op_minus),
        ("4", (1.6, 0, formula_offset_z), mat_num_glow),
        ("a", (2.0, 0, formula_offset_z), mat_num_glow), # Placeholder a
        ("c", (2.4, 0, formula_offset_z), mat_num_glow), # Placeholder c
        (")", (2.8, 0, formula_offset_z), mat_equation_text), # Closing paren for sqrt
        # Division line (mesh, not text) - will add as separate object later
        ("2", (-0.5, 0, formula_offset_z - 0.7), mat_num_glow),
        ("a", (-0.1, 0, formula_offset_z - 0.7), mat_num_glow), # Placeholder a
    ]
    
    formula_objs = []
    assemble_delay = 10 # frames between each part

    for i, (text_str, loc, mat) in enumerate(formula_parts):
        obj_name = f"Formula_Part_{i}_{text_str.replace(' ', '_').replace('^', 'pow').replace('\\u00B1', 'pm').replace('\\u221A', 'sqrt')}"
        obj = create_text_object(obj_name, text_str, font_size=formula_scale, location=(loc[0], loc[1] + 5, loc[2]), rotation=(math.radians(90), 0, 0), material=mat)
        
        animate_visibility(obj, S3_START + i * assemble_delay, S3_START + i * assemble_delay + 1, True, False) # Make visible
        animate_location(obj, S3_START + i * assemble_delay, S3_START + i * assemble_delay + 30, (loc[0], loc[1] + 5, loc[2]), loc)
        
        # Glow briefly on appearance
        if mat != mat_equation_text: # Don't glow plain text, only symbols/placeholders
            animate_glow(obj.data.materials[0], S3_START + i * assemble_delay + 20, S3_START + i * assemble_delay + 50, 0.0, 1.0)
            animate_glow(obj.data.materials[0], S3_START + i * assemble_delay + 50, S3_START + i * assemble_delay + 80, 1.0, 0.0)
        
        formula_objs.append(obj)
    
    # Division line (yellow, glowing bar)
    bpy.ops.mesh.primitive_plane_add(size=4.0, enter_editmode=False, align='WORLD', location=(0.0, 0, formula_offset_z - 0.2))
    division_line = bpy.context.object
    division_line.name = "Formula_Division_Line"
    division_line.rotation_euler = (math.radians(90), 0, 0)
    division_line.scale.z = 0.05 # Make it thin
    division_line.data.materials.append(mat_op_divide)
    
    # Animate division line
    div_line_appear_frame = S3_START + len(formula_parts) * assemble_delay + 30
    animate_visibility(division_line, div_line_appear_frame, div_line_appear_frame + 1, True, False)
    animate_scale(division_line, div_line_appear_frame, div_line_appear_frame + 30, 0.01, 1.0)
    animate_glow(division_line.data.materials[0], div_line_appear_frame + 20, div_line_appear_frame + 50, 0.0, 1.0)
    animate_glow(division_line.data.materials[0], div_line_appear_frame + 50, div_line_appear_frame + 80, 1.0, 0.0)

    # Move X_Var_Box next to formula x
    x_box_formula_loc = (formula_parts[0][1][0] - 0.8, 0, formula_offset_z)
    animate_location(x_box, div_line_appear_frame + 30, div_line_appear_frame + 60, x_box.location, x_box_formula_loc)
    animate_glow(x_box.data.materials[0], div_line_appear_frame + 60, div_line_appear_frame + 90, 0.0, 1.0)

    current_frame = S3_END + 30

    # Scene 4: Substitution (12 seconds = 360 frames)
    S4_START = current_frame
    S4_DURATION = 12 * 30
    S4_END = S4_START + S4_DURATION

    # Constants slide into place
    # Re-use original blocks from S2, adjust their visibility and location
    animate_visibility(a_block, S4_START, S4_START + 1, False, False) # Make them visible
    animate_visibility(b_block, S4_START, S4_START + 1, False, False)
    animate_visibility(c_block, S4_START, S4_START + 1, False, False)
    animate_glow(a_block.data.materials[1], S4_START, S4_START + 1, 0.0, 0.0) # Reset glow
    animate_glow(b_block.data.materials[1], S4_START, S4_START + 1, 0.0, 0.0)
    animate_glow(c_block.data.materials[1], S4_START, S4_START + 1, 0.0, 0.0)
    
    # Substitution locations (matched to formula_parts positions)
    b_sub_loc1 = formula_parts[4][1] # 'b' after '-'
    b_sub_loc2 = formula_parts[7][1] # 'b^2'
    a_sub_loc1 = formula_parts[10][1] # 'a' after '4'
    c_sub_loc1 = formula_parts[11][1] # 'c' after 'a'
    a_sub_loc2 = formula_parts[14][1] # 'a' in denominator

    # b to -(3)
    animate_location(b_block, S4_START + 30, S4_START + 60, b_block.location, (b_sub_loc1[0], 0, 0.5))
    animate_visibility(formula_objs[4], S4_START + 60, S4_START + 61, False, True) # Hide placeholder b
    animate_glow(b_block.data.materials[1], S4_START + 60, S4_START + 90, 0.0, 1.0)

    # b to (3)^2 (move a copy of b_block for a visual effect)
    b_block_copy_for_b2 = create_constant_block("B_Block_Copy_For_b2", 3, (0.2, 0.8, 0.2), size=0.8)
    b_block_copy_for_b2.location = (b_sub_loc1[0], 0, 0.5) # Start from first 'b' location
    animate_visibility(b_block_copy_for_b2, S4_START + 90, S4_START + 91, True, False) # Make visible
    animate_location(b_block_copy_for_b2, S4_START + 90, S4_START + 120, b_block_copy_for_b2.location, (b_sub_loc2[0], 0, 0.5))
    animate_visibility(formula_objs[7], S4_START + 120, S4_START + 121, False, True) # Hide placeholder b^2
    animate_glow(b_block_copy_for_b2.data.materials[1], S4_START + 120, S4_START + 150, 0.0, 1.0)
    
    # a to 4(1)
    animate_location(a_block, S4_START + 150, S4_START + 180, a_block.location, (a_sub_loc1[0], 0, 0.5))
    animate_visibility(formula_objs[10], S4_START + 180, S4_START + 181, False, True) # Hide placeholder a
    animate_glow(a_block.data.materials[1], S4_START + 180, S4_START + 210, 0.0, 1.0)

    # c to (7)
    animate_location(c_block, S4_START + 210, S4_START + 240, c_block.location, (c_sub_loc1[0], 0, 0.5))
    animate_visibility(formula_objs[11], S4_START + 240, S4_START + 241, False, True) # Hide placeholder c
    animate_glow(c_block.data.materials[1], S4_START + 240, S4_START + 270, 0.0, 1.0)

    # a to 2(1)
    a_block_copy_for_den = create_constant_block("A_Block_Copy_For_Den", 1, (0.8, 0.2, 0.2), size=0.8)
    a_block_copy_for_den.location = (a_sub_loc1[0], 0, 0.5) # Start from first 'a' location
    animate_visibility(a_block_copy_for_den, S4_START + 270, S4_START + 271, True, False) # Make visible
    animate_location(a_block_copy_for_den, S4_START + 270, S4_START + 300, a_block_copy_for_den.location, (a_sub_loc2[0], 0, 0.5)) # Move to denominator
    animate_visibility(formula_objs[14], S4_START + 300, S4_START + 301, False, True) # Hide placeholder a
    animate_glow(a_block_copy_for_den.data.materials[1], S4_START + 300, S4_START + 330, 0.0, 1.0)
    
    # Transition to new text objects representing the substituted formula for clarity
    substituted_formula_parts_text = [
        ("x", (-4.0, 0, formula_offset_z), mat_equation_text),
        ("=", (-3.5, 0, formula_offset_z), mat_op_equals),
        ("(", (-2.5, 0, formula_offset_z), mat_equation_text),
        ("-", (-2.0, 0, formula_offset_z), mat_op_minus),
        ("3", b_sub_loc1, mat_num_glow), # Actual '3'
        ("\u00B1", (-0.8, 0, formula_offset_z), mat_op_plus),
        ("\u221A", (0.0, 0, formula_offset_z + 0.2), mat_op_divide),
        ("3\u00B2", b_sub_loc2, mat_num_glow), # Actual '3^2'
        ("-", (1.2, 0, formula_offset_z), mat_op_minus),
        ("4", (1.6, 0, formula_offset_z), mat_num_glow),
        ("1", a_sub_loc1, mat_num_glow), # Actual '1'
        ("7", c_sub_loc1, mat_num_glow), # Actual '7'
        (")", (2.8, 0, formula_offset_z), mat_equation_text),
        ("2", (-0.5, 0, formula_offset_z - 0.7), mat_num_glow),
        ("1", a_sub_loc2, mat_num_glow), # Actual '1'
    ]

    substituted_formula_objs = []
    for i, (text_str, loc, mat) in enumerate(substituted_formula_parts_text):
        obj = create_text_object(f"Substituted_Formula_Text_{i}", text_str, font_size=formula_scale, location=loc, rotation=(math.radians(90),0,0), material=mat)
        animate_visibility(obj, S4_START + 330, S4_START + 331, True, True) # Initially hidden
        substituted_formula_objs.append(obj)

    # Hide all original formula parts and show substituted ones (except for blocks)
    for obj in formula_objs:
        animate_visibility(obj, S4_START + 330, S4_START + 331, False, True)
    animate_visibility(division_line, S4_START + 330, S4_START + 331, False, False) # Keep division line visible
    
    for obj in substituted_formula_objs:
        animate_visibility(obj, S4_START + 330, S4_START + 331, True, False) # Show new parts

    current_frame = S4_END + 30

    # Scene 5: Calculating the Discriminant - Part 1 (b^2) (7 seconds = 210 frames)
    S5_START = current_frame
    S5_DURATION = 7 * 30
    S5_END = S5_START + S5_DURATION
    
    # Zoom camera to (3)^2 (which is now '3^2' in substituted_formula_objs[7])
    target_obj_b2 = substituted_formula_objs[7]
    animate_camera_dolly(camera, target_obj_b2, S5_START, S5_START + 60, camera.location, (target_obj_b2.location.x, -5, 2.5), 50, 30)

    # (3)^2 becomes 9
    # Re-use b_block_copy_for_b2
    animate_location(b_block_copy_for_b2, S5_START + 60, S5_START + 61, b_block_copy_for_b2.location, (target_obj_b2.location.x - 0.2, 0, 0.5)) # Adjust initial position for animation
    animate_visibility(b_block_copy_for_b2, S5_START + 60, S5_START + 61, False, False) # Make visible again
    
    # Duplicate 3
    b_block_clone_calc = create_constant_block("B_Block_Clone_Calc", 3, (0.2, 0.8, 0.2), size=0.8)
    b_block_clone_calc.location = (target_obj_b2.location.x + 0.5, 0, 0.5)
    animate_visibility(b_block_clone_calc, S5_START + 90, S5_START + 91, True, False)
    
    # Show multiplication arrow
    multiply_arrow_1 = create_operation_arrow("Mult_Arrow_1", "\u00D7", (0.8, 0.0, 0.0), size=0.5)
    multiply_arrow_1.location = (target_obj_b2.location.x + 0.15, 0, 0.5) # Between the two 3's
    animate_visibility(multiply_arrow_1, S5_START + 120, S5_START + 121, True, False)
    animate_glow(multiply_arrow_1.data.materials[0], S5_START + 120, S5_START + 150, 0.0, 1.0)

    # Merge into 9
    nine_block = create_constant_block("Nine_Block", 9, (0.8, 0.2, 0.2), size=0.8)
    nine_block.location = (target_obj_b2.location.x, 0, 0.5) # Appears where (3)^2 was
    animate_visibility(nine_block, S5_START, S5_START + 1, True, True)

    animate_location(b_block_copy_for_b2, S5_START + 150, S5_START + 180, b_block_copy_for_b2.location, nine_block.location)
    animate_location(b_block_clone_calc, S5_START + 150, S5_START + 180, b_block_clone_calc.location, nine_block.location)
    animate_location(multiply_arrow_1, S5_START + 150, S5_START + 180, multiply_arrow_1.location, nine_block.location)

    animate_visibility(b_block_copy_for_b2, S5_START + 180, S5_START + 181, False, True)
    animate_visibility(b_block_clone_calc, S5_START + 180, S5_START + 181, False, True)
    animate_visibility(multiply_arrow_1, S5_START + 180, S5_START + 181, False, True)

    animate_visibility(nine_block, S5_START + 180, S5_START + 181, True, False)
    animate_glow(nine_block.data.materials[1], S5_START + 180, S5_START + 210, 0.0, 1.0)
    
    # Update formula text: '3^2' -> '9'
    animate_visibility(substituted_formula_objs[7], S5_START + 180, S5_START + 181, False, True) # Hide '3^2'
    nine_text_obj_formula = create_text_object("Nine_Text_Formula_Part", "9", font_size=formula_scale, location=target_obj_b2.location, rotation=(math.radians(90),0,0), material=mat_num_glow)
    animate_visibility(nine_text_obj_formula, S5_START + 180, S5_START + 181, True, False)
    
    current_frame = S5_END + 30

    # Scene 6: Calculating the Discriminant - Part 2 (4ac) (10 seconds = 300 frames)
    S6_START = current_frame
    S6_DURATION = 10 * 30
    S6_END = S6_START + S6_DURATION

    # Camera shift to 4(1)(7) (substituted_formula_objs[9], [10], [11])
    target_obj_4ac_group = bpy.data.objects.get("Substituted_Formula_Text_9") # Just target the '4' for general area
    animate_camera_dolly(camera, target_obj_4ac_group, S6_START, S6_START + 60, camera.location, (target_obj_4ac_group.location.x + 0.5, -5, 2.5), 30, 30)

    # Ensure a_block and c_block are back to their original S4 substituted positions for calc
    a_block.location = (substituted_formula_objs[10].location.x, 0, 0.5)
    c_block.location = (substituted_formula_objs[11].location.x, 0, 0.5)
    animate_visibility(a_block, S6_START + 60, S6_START + 61, False, False)
    animate_visibility(c_block, S6_START + 60, S6_START + 61, False, False)
    
    # Create a new 4 block for calculations to avoid conflicting animations
    four_block_calc = create_constant_block("Four_Block_Calc_A", 4, (0.8, 0.2, 0.2), size=0.8)
    four_block_calc.location = (substituted_formula_objs[9].location.x, 0, 0.5)
    animate_visibility(four_block_calc, S6_START + 60, S6_START + 61, True, False)

    multiply_arrow_2 = create_operation_arrow("Mult_Arrow_2", "\u00D7", (0.8, 0.0, 0.0), size=0.5)
    multiply_arrow_2.location = (substituted_formula_objs[9].location.x + 0.3, 0, 0.5)
    animate_visibility(multiply_arrow_2, S6_START + 90, S6_START + 91, True, False)
    animate_glow(multiply_arrow_2.data.materials[0], S6_START + 90, S6_START + 120, 0.0, 1.0)
    
    # 4 * 1 = 4 (visually merge blocks)
    new_four_block_result = create_constant_block("New_Four_Block_Result", 4, (0.8, 0.2, 0.2), size=0.8)
    new_four_block_result.location = four_block_calc.location
    animate_visibility(new_four_block_result, S6_START, S6_START + 1, True, True)

    animate_location(a_block, S6_START + 120, S6_START + 150, a_block.location, four_block_calc.location)
    animate_location(multiply_arrow_2, S6_START + 120, S6_START + 150, multiply_arrow_2.location, four_block_calc.location)
    
    animate_visibility(four_block_calc, S6_START + 150, S6_START + 151, False, True)
    animate_visibility(a_block, S6_START + 150, S6_START + 151, False, True)
    animate_visibility(multiply_arrow_2, S6_START + 150, S6_START + 151, False, True)
    animate_visibility(new_four_block_result, S6_START + 150, S6_START + 151, True, False)
    animate_glow(new_four_block_result.data.materials[1], S6_START + 150, S6_START + 180, 0.0, 1.0)

    # Hide '4' and '1' texts, make a new '4' text visible in formula
    animate_visibility(substituted_formula_objs[9], S6_START + 150, S6_START + 151, False, True)
    animate_visibility(substituted_formula_objs[10], S6_START + 150, S6_START + 151, False, True)
    
    new_four_text_obj_formula = create_text_object("New_Four_Text_Formula_Part", "4", font_size=formula_scale, location=substituted_formula_objs[9].location, rotation=(math.radians(90),0,0), material=mat_num_glow)
    animate_visibility(new_four_text_obj_formula, S6_START + 150, S6_START + 151, True, False)


    # Now (4) * 7 = 28 (visually merge blocks)
    multiply_arrow_3 = create_operation_arrow("Mult_Arrow_3", "\u00D7", (0.8, 0.0, 0.0), size=0.5)
    multiply_arrow_3.location = (new_four_block_result.location.x + 0.3, 0, 0.5)
    animate_visibility(multiply_arrow_3, S6_START + 210, S6_START + 211, True, False)
    animate_glow(multiply_arrow_3.data.materials[0], S6_START + 210, S6_START + 240, 0.0, 1.0)
    
    twenty_eight_block_calc = create_constant_block("TwentyEight_Block_Calc", 28, (0.8, 0.2, 0.2), size=0.8)
    twenty_eight_block_calc.location = new_four_block_result.location
    animate_visibility(twenty_eight_block_calc, S6_START, S6_START + 1, True, True)

    animate_location(c_block, S6_START + 240, S6_START + 270, c_block.location, new_four_block_result.location)
    animate_location(multiply_arrow_3, S6_START + 240, S6_START + 270, multiply_arrow_3.location, new_four_block_result.location)

    animate_visibility(new_four_block_result, S6_START + 270, S6_START + 271, False, True)
    animate_visibility(c_block, S6_START + 270, S6_START + 271, False, True)
    animate_visibility(multiply_arrow_3, S6_START + 270, S6_START + 271, False, True)
    animate_visibility(twenty_eight_block_calc, S6_START + 270, S6_START + 271, True, False)
    animate_glow(twenty_eight_block_calc.data.materials[1], S6_START + 270, S6_START + 300, 0.0, 1.0)

    # Hide '7' text, make '28' text visible in formula
    animate_visibility(substituted_formula_objs[11], S6_START + 270, S6_START + 271, False, True)
    twenty_eight_text_obj_formula = create_text_object("TwentyEight_Text_Formula_Part", "28", font_size=formula_scale, location=substituted_formula_objs[11].location, rotation=(math.radians(90),0,0), material=mat_num_glow)
    animate_visibility(twenty_eight_text_obj_formula, S6_START + 270, S6_START + 271, True, False)
    
    current_frame = S6_END + 30

    # Scene 7: Calculating the Discriminant - Part 3 (Subtraction) (7 seconds = 210 frames)
    S7_START = current_frame
    S7_DURATION = 7 * 30
    S7_END = S7_START + S7_DURATION

    # Camera zoom to 9 - 28
    target_obj_sub = nine_text_obj_formula # The '9' in the formula
    animate_camera_dolly(camera, target_obj_sub, S7_START, S7_START + 60, camera.location, (target_obj_sub.location.x + 0.75, -5, 2.5), 30, 30)

    # Ensure 9_block and 28_block_calc are visible and positioned for calculation
    nine_block.location = (target_obj_sub.location.x, 0, 0.5)
    twenty_eight_block_calc.location = (twenty_eight_text_obj_formula.location.x, 0, 0.5)
    animate_visibility(nine_block, S7_START + 60, S7_START + 61, False, False)
    animate_visibility(twenty_eight_block_calc, S7_START + 60, S7_START + 61, False, False)

    subtract_arrow = create_operation_arrow("Subtract_Arrow", "-", (0.5, 0.0, 0.5), size=0.5)
    subtract_arrow.location = (target_obj_sub.location.x + 0.75, 0, 0.5)
    animate_visibility(subtract_arrow, S7_START + 90, S7_START + 91, True, False)
    animate_glow(subtract_arrow.data.materials[0], S7_START + 90, S7_START + 120, 0.0, 1.0)
    
    # Merge into -19
    minus_19_block = create_constant_block("Minus19_Block", -19, (0.8, 0.2, 0.2), size=0.8)
    minus_19_block.location = (target_obj_sub.location.x + 1.25, 0, 0.5) # Location of the result
    animate_visibility(minus_19_block, S7_START, S7_START + 1, True, True)

    animate_location(nine_block, S7_START + 120, S7_START + 150, nine_block.location, minus_19_block.location)
    animate_location(twenty_eight_block_calc, S7_START + 120, S7_START + 150, twenty_eight_block_calc.location, minus_19_block.location)
    animate_location(subtract_arrow, S7_START + 120, S7_START + 150, subtract_arrow.location, minus_19_block.location)

    animate_visibility(nine_block, S7_START + 150, S7_START + 151, False, True)
    animate_visibility(twenty_eight_block_calc, S7_START + 150, S7_START + 151, False, True)
    animate_visibility(subtract_arrow, S7_START + 150, S7_START + 151, False, True)
    animate_visibility(minus_19_block, S7_START + 150, S7_START + 151, True, False)
    animate_glow(minus_19_block.data.materials[1], S7_START + 150, S7_START + 210, 0.0, 2.0) # Intense glow for negative

    # Update formula text: √(9 - 28) -> √(-19)
    # Hide old '9', '-', '28' texts
    animate_visibility(nine_text_obj_formula, S7_START + 150, S7_START + 151, False, True)
    animate_visibility(substituted_formula_objs[8], S7_START + 150, S7_START + 151, False, True) # The '-'
    animate_visibility(twenty_eight_text_obj_formula, S7_START + 150, S7_START + 151, False, True)
    
    minus19_formula_text = create_text_object("Minus19_Formula_Text_Part", "-19", font_size=formula_scale, location=target_obj_sub.location, rotation=(math.radians(90),0,0), material=mat_red_warning)
    animate_visibility(minus19_formula_text, S7_START + 150, S7_START + 151, True, False)
    animate_glow(minus19_formula_text.data.materials[0], S7_START + 150, S7_START + 210, 0.0, 2.0)

    current_frame = S7_END + 30

    # Scene 8: Addressing the Negative Discriminant - Complex Roots (15 seconds = 450 frames)
    S8_START = current_frame
    S8_DURATION = 15 * 30
    S8_END = S8_START + S8_DURATION

    # Camera back to full formula
    animate_camera_dolly(camera, camera_target_full_view, S8_START, S8_START + 60, camera.location, full_formula_cam_loc, 30, 50)
    
    # Ensure all formula parts are visible (now with -19)
    for obj in substituted_formula_objs:
        animate_visibility(obj, S8_START + 60, S8_START + 61, False, False)
    animate_visibility(minus19_formula_text, S8_START + 60, S8_START + 61, False, False)
    animate_visibility(division_line, S8_START + 60, S8_START + 61, False, False)
    animate_visibility(x_box, S8_START + 60, S8_START + 61, False, False)
    
    # Large red flashing "!" over sqrt(-19)
    warning_sign = create_text_object("Warning_Sign", "!", font_size=3.0, location=(0.5, 0, 3), rotation=(math.radians(90),0,0), material=mat_red_warning)
    animate_visibility(warning_sign, S8_START + 90, S8_START + 91, True, False)
    animate_glow(warning_sign.data.materials[0], S8_START + 90, S8_START + 150, 0.0, 5.0)
    animate_glow(warning_sign.data.materials[0], S8_START + 150, S8_START + 180, 5.0, 0.0)

    # Text overlay: "No REAL solutions!"
    no_real_text = create_text_object("No_Real_Solutions", "A negative number under the square root? No REAL solutions!", font_size=0.7, location=(0, -2, 2.5), rotation=(math.radians(90),0,0), material=mat_equation_text)
    animate_visibility(no_real_text, S8_START + 180, S8_START + 181, True, False)
    animate_location(no_real_text, S8_START + 180, S8_START + 210, (0, -5, 2.5), (0, -2, 2.5))
    animate_visibility(no_real_text, S8_START + 270, S8_START + 271, False, True)

    # sqrt(-19) block visually splits into sqrt(-1) and sqrt(19)
    sqrt_neg_1_block = create_constant_block("Sqrt_Neg_1_Block", "\u221A-1", (0.5, 0.5, 0.5), size=0.8)
    sqrt_19_block = create_constant_block("Sqrt_19_Block", "\u221A19", (0.5, 0.5, 0.5), size=0.8)
    
    # Position minus_19_block for the split animation
    minus_19_block.location = (minus19_formula_text.location.x, 0, 0.5)
    animate_location(minus_19_block, S8_START + 270, S8_START + 270, minus_19_block.location, (minus19_formula_text.location.x, 0, 0.5))
    
    # Hide original -19 block
    animate_visibility(minus_19_block, S8_START + 270, S8_START + 271, False, True)
    
    # Place new blocks and animate them splitting
    split_x_offset = 0.5
    sqrt_neg_1_block.location = (minus19_formula_text.location.x - split_x_offset, 0, 0.5)
    sqrt_19_block.location = (minus19_formula_text.location.x + split_x_offset, 0, 0.5)
    
    animate_visibility(sqrt_neg_1_block, S8_START + 270, S8_START + 271, True, False)
    animate_visibility(sqrt_19_block, S8_START + 270, S8_START + 271, True, False)
    
    animate_location(sqrt_neg_1_block, S8_START + 270, S8_START + 300, (minus19_formula_text.location.x, 0, 0.5), sqrt_neg_1_block.location)
    animate_location(sqrt_19_block, S8_START + 270, S8_START + 300, (minus19_formula_text.location.x, 0, 0.5), sqrt_19_block.location)
    animate_glow(sqrt_neg_1_block.data.materials[1], S8_START + 300, S8_START + 330, 0.0, 1.0)
    animate_glow(sqrt_19_block.data.materials[1], S8_START + 300, S8_START + 330, 0.0, 1.0)

    # sqrt(-1) transforms into 'i' block
    i_block = create_constant_block("I_Block", "i", (0.8, 0.1, 0.8), size=0.8)
    i_block.location = sqrt_neg_1_block.location # Start from sqrt(-1) location
    animate_visibility(i_block, S8_START, S8_START + 1, True, True) # Hide until needed

    animate_visibility(sqrt_neg_1_block, S8_START + 330, S8_START + 331, False, True) # Hide sqrt(-1)
    animate_visibility(i_block, S8_START + 330, S8_START + 331, True, False) # Show 'i'
    animate_glow(i_block.data.materials[1], S8_START + 330, S8_START + 360, 0.0, 2.0) # Bright glow for 'i'

    # Move i and sqrt(19) together
    merge_x_loc = minus19_formula_text.location.x
    animate_location(i_block, S8_START + 360, S8_START + 390, i_block.location, (merge_x_loc - 0.25, 0, 0.5))
    animate_location(sqrt_19_block, S8_START + 360, S8_START + 390, sqrt_19_block.location, (merge_x_loc + 0.25, 0, 0.5))
    
    # Hide original text of -19 and square root symbol (substituted_formula_objs[6])
    animate_visibility(minus19_formula_text, S8_START + 390, S8_START + 391, False, True)
    animate_visibility(substituted_formula_objs[6], S8_START + 390, S8_START + 391, False, True) # Hide 'sqrt' symbol
    animate_visibility(substituted_formula_objs[12], S8_START + 390, S8_START + 391, False, True) # Hide ')' symbol for sqrt

    # Create the i*sqrt(19) text
    i_sqrt_19_text = create_text_object("i_Sqrt_19_Text", "i\u221A19", font_size=formula_scale, location=(minus19_formula_text.location.x, 0, formula_offset_z), rotation=(math.radians(90),0,0), material=mat_i_unit)
    animate_visibility(i_sqrt_19_text, S8_START + 390, S8_START + 391, True, False)
    animate_glow(i_sqrt_19_text.data.materials[0], S8_START + 390, S8_START + 420, 0.0, 1.0)
    
    # Hide the blocks
    animate_visibility(i_block, S8_START + 420, S8_START + 421, False, True)
    animate_visibility(sqrt_19_block, S8_START + 420, S8_START + 421, False, True)

    current_frame = S8_END + 30

    # Scene 9: Final Simplification and Solutions (10 seconds = 300 frames)
    S9_START = current_frame
    S9_DURATION = 10 * 30
    S9_END = S9_START + S9_DURATION

    # Hide current formula parts and show simplified solutions
    # Iterating through all objects and hide those related to formula except for X_Var_Box
    for obj in bpy.data.objects:
        if ("Formula_Part" in obj.name or 
            "Substituted_Formula_Text" in obj.name or
            "Nine_Text_Formula_Part" in obj.name or
            "New_Four_Text_Formula_Part" in obj.name or
            "TwentyEight_Text_Formula_Part" in obj.name or
            "Minus19_Formula_Text_Part" in obj.name or
            "i_Sqrt_19_Text" in obj.name or
            "Formula_Division_Line" in obj.name):
            animate_visibility(obj, S9_START + 30, S9_START + 31, False, True) # Hide formula parts

        # Hide all constant/variable blocks used in calculations
        if "Block" in obj.name and "X_Var_Box" not in obj.name:
            animate_visibility(obj, S9_START + 30, S9_START + 31, False, True)
        
        # Hide all operation arrows
        if "Arrow" in obj.name:
            animate_visibility(obj, S9_START + 30, S9_START + 31, False, True)

    # Move X_Var_Box to a central position (will be reused for both solutions)
    animate_location(x_box, S9_START + 30, S9_START + 60, x_box.location, (-4.5, 0, 1))

    # Create the two solutions
    solution_1_loc = (0, 0, 1.5)
    solution_2_loc = (0, 0, 0.5)
    solution_1_text = create_text_object("Solution_1", "x\u2081 = (-3 + i\u221A19) / 2", font_size=1.0, location=(solution_1_loc[0], 5, solution_1_loc[2]), rotation=(math.radians(90), 0, 0), material=mat_equation_text)
    solution_2_text = create_text_object("Solution_2", "x\u2082 = (-3 - i\u221A19) / 2", font_size=1.0, location=(solution_2_loc[0], 5, solution_2_loc[2]), rotation=(math.radians(90), 0, 0), material=mat_equation_text)

    # Show and slide in solutions
    animate_visibility(solution_1_text, S9_START + 60, S9_START + 61, True, False)
    animate_location(solution_1_text, S9_START + 60, S9_START + 90, (solution_1_loc[0], 5, solution_1_loc[2]), solution_1_loc)
    animate_glow(solution_1_text.data.materials[0], S9_START + 90, S9_START + 150, 0.0, 1.0)

    animate_visibility(solution_2_text, S9_START + 120, S9_START + 121, True, False)
    animate_location(solution_2_text, S9_START + 120, S9_START + 150, (solution_2_loc[0], 5, solution_2_loc[2]), solution_2_loc)
    animate_glow(solution_2_text.data.materials[0], S9_START + 150, S9_START + 210, 0.0, 1.0)

    current_frame = S9_END + 30

    # Scene 10: Graphical Interpretation (12 seconds = 360 frames)
    S10_START = current_frame
    S10_DURATION = 12 * 30
    S10_END = S10_START + S10_DURATION

    # Whiteboard dissolves
    animate_scale(whiteboard, S10_START, S10_START + 60, 1.0, 0.0)
    animate_visibility(whiteboard, S10_START + 60, S10_START + 61, False, True)
    
    # Hide solutions for now
    animate_visibility(solution_1_text, S10_START, S10_START + 1, False, True)
    animate_visibility(solution_2_text, S10_START, S10_START + 1, False, True)
    animate_visibility(x_box, S10_START, S10_START + 1, False, True)

    # Create Cartesian system (Blender's X and Z axes for 2D plot)
    axis_mat = create_material("Axis_Mat", color=(0.2,0.2,0.2,1))
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=10, enter_editmode=False, align='WORLD', location=(0,0,0))
    x_axis = bpy.context.object
    x_axis.name = "X_Axis_Plot"
    x_axis.rotation_euler = (0, math.radians(90), 0) # Orient along Blender's X axis
    x_axis.data.materials.append(axis_mat)
    animate_scale(x_axis, S10_START + 60, S10_START + 90, 0.0, 1.0)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=10, enter_editmode=False, align='WORLD', location=(0,0,0))
    y_axis = bpy.context.object
    y_axis.name = "Y_Axis_Plot"
    y_axis.rotation_euler = (math.radians(90), 0, 0) # Orient along Blender's Z axis (up)
    y_axis.data.materials.append(axis_mat)
    animate_scale(y_axis, S10_START + 90, S10_START + 120, 0.0, 1.0)

    # Create parabola: y = x^2 + 3x + 7
    # For Blender's X-Z plane, X_plot = x, Z_plot = y
    parabola_points = []
    for i in range(-50, 51): # x from -5 to 5, at 0.1 intervals
        x_val = i / 10.0
        y_val = x_val**2 + 3*x_val + 7
        parabola_points.append(mathutils.Vector((x_val, 0, y_val))) # X is x_val, Z is y_val

    curve_data = bpy.data.curves.new('Parabola_Curve', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2
    
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(parabola_points) - 1)
    
    for i, point in enumerate(parabola_points):
        spline.bezier_points[i].co = point
        spline.bezier_points[i].handle_left_type = 'AUTO'
        spline.bezier_points[i].handle_right_type = 'AUTO'
        
    parabola_obj = bpy.data.objects.new('Parabola', curve_data)
    bpy.context.collection.objects.link(parabola_obj)
    
    # Give it some thickness
    parabola_obj.data.bevel_depth = 0.05
    parabola_obj.data.bevel_resolution = 4
    parabola_obj.data.materials.append(create_material("Parabola_Mat", color=(0.1, 0.1, 0.7, 1), emission=(0.1, 0.1, 0.7, 1)))
    
    # Animate drawing the parabola
    parabola_obj.data.use_fill_caps = True
    parabola_obj.data.path_render_factor = 0.0 # Start hidden
    parabola_obj.data.keyframe_insert(data_path='path_render_factor', frame=S10_START + 120)
    parabola_obj.data.path_render_factor = 1.0 # End full
    parabola_obj.data.keyframe_insert(data_path='path_render_factor', frame=S10_START + 210)
    
    # Camera pan and zoom to show vertex above x-axis
    animate_camera_dolly(camera, parabola_obj, S10_START + 150, S10_START + 240, camera.location, (0, -7, 4), 50, 40)
    
    # Text overlay: "The parabola does NOT intersect the x-axis!"
    no_intersection_text = create_text_object("No_Intersection_Text", "The parabola does NOT intersect the x-axis!", font_size=0.7, location=(0, -2, 4.5), rotation=(math.radians(90),0,0), material=mat_equation_text)
    animate_visibility(no_intersection_text, S10_START + 240, S10_START + 241, True, False)
    animate_location(no_intersection_text, S10_START + 240, S10_START + 270, (0, -5, 4.5), (0, -2, 4.5))
    animate_visibility(no_intersection_text, S10_START + 300, S10_START + 301, False, True)

    # Red pulsating "X" on x-axis
    red_x = create_text_object("Red_X_No_Solution", "X", font_size=2.0, location=(0,0,0.1), rotation=(math.radians(90), 0, 0), material=mat_red_warning)
    animate_visibility(red_x, S10_START + 300, S10_START + 301, True, False)
    animate_glow(red_x.data.materials[0], S10_START + 300, S10_START + 330, 0.0, 5.0)
    animate_glow(red_x.data.materials[0], S10_START + 330, S10_START + 360, 5.0, 0.0)

    current_frame = S10_END + 30

    # Scene 11: Conclusion (5 seconds = 150 frames)
    S11_START = current_frame
    S11_DURATION = 5 * 30
    S11_END = S11_START + S11_DURATION

    # Camera pulls back to WhiteboardGrid again
    animate_scale(whiteboard, S11_START, S11_START + 1, 0.0, 1.0) # Scale back up
    animate_visibility(whiteboard, S11_START, S11_START + 1, True, False) # Show again
    
    # Hide Axes and Parabola
    animate_visibility(x_axis, S11_START, S11_START + 1, False, True)
    animate_visibility(y_axis, S11_START, S11_START + 1, False, True)
    animate_visibility(parabola_obj, S11_START, S11_START + 1, False, True)
    animate_visibility(red_x, S11_START, S11_START + 1, False, True)

    animate_camera_dolly(camera, camera_target_full_view, S11_START, S11_START + 60, camera.location, full_formula_cam_loc, 40, 50)

    # Final solutions reappear
    animate_visibility(solution_1_text, S11_START + 60, S11_START + 61, True, False)
    animate_visibility(solution_2_text, S11_START + 60, S11_START + 61, True, False)
    
    animate_location(solution_1_text, S11_START + 60, S11_START + 90, (solution_1_loc[0], 5, solution_1_loc[2]), solution_1_loc)
    animate_location(solution_2_text, S11_START + 60, S11_START + 90, (solution_2_loc[0], 5, solution_2_loc[2]), solution_2_loc)

    animate_glow(solution_1_text.data.materials[0], S11_START + 90, S11_START + 120, 0.0, 1.0)
    animate_glow(solution_2_text.data.materials[0], S11_START + 90, S11_START + 120, 0.0, 1.0)

    # "Problem Solved!" text
    solved_text = create_text_object("Problem_Solved_Text", "Problem Solved!", font_size=1.5, location=(0,0,2.5), rotation=(math.radians(90),0,0), material=mat_equation_text)
    animate_visibility(solved_text, S11_START + 120, S11_START + 121, True, False)
    animate_location(solved_text, S11_START + 120, S11_START + 150, (0, 5, 2.5), (0, 0, 2.5))
    
    # Fade to black
    # Create a black plane in front of camera (closer than whiteboard)
    bpy.ops.mesh.primitive_plane_add(size=30, enter_editmode=False, align='WORLD', location=(0, -9, 5))
    black_plane = bpy.context.object
    black_plane.name = "Fade_To_Black_Plane"
    black_plane.rotation_euler = (math.radians(90), 0, 0) # Orient towards camera
    
    fade_mat = create_material("Fade_Mat", color=(0,0,0,1))
    fade_mat.blend_method = 'BLEND' # Enable transparency
    fade_mat.shadow_method = 'NONE' # No shadow from fade plane
    fade_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.0 # Start transparent
    
    black_plane.data.materials.append(fade_mat)
    
    # Animate alpha
    fade_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.0
    fade_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].keyframe_insert(data_path='default_value', frame=S11_END - 30)
    fade_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 1.0
    fade_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].keyframe_insert(data_path='default_value', frame=S11_END)

    bpy.context.scene.frame_end = S11_END + 30 # A little buffer at the end


# --- Execution ---
if __name__ == "__main__":
    create_animation()
