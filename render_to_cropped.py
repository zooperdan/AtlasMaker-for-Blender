import bpy
import os
import tempfile
import json
import sys

def delete_all_files_in_folder(folder_path):
    """Delete all files in the specified folder."""
    
    # Check if the folder exists
    if os.path.exists(folder_path):
        # Loop through the files in the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Check if it's a file (not a directory)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)  # Delete the file
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
    else:
        print(f"Folder {folder_path} does not exist.")
        
def render_to_temp_png():

    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, "temp_render.png")

    scene = bpy.context.scene
    scene.render.filepath = tmp_path

    bpy.ops.render.render(write_still=True)

    return tmp_path

def crop_and_save_image(path, output_path, alpha_threshold=0.01):
    
    # Load the rendered image
    img = bpy.data.images.load(path)
    img.update()
    width, height = img.size
    pixels = list(img.pixels)

    def get_alpha(x, y):
        return pixels[(y * width + x) * 4 + 3]

    # Find visible area
    min_x, min_y = width, height
    max_x, max_y = 0, 0

    for y in range(height):
        for x in range(width):
            if get_alpha(x, y) > alpha_threshold:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if min_x >= max_x or min_y >= max_y:
#        print("⚠️ No visible pixels found in image.")
        return

    cropped_width = max_x - min_x + 1
    cropped_height = max_y - min_y + 1

    screen_coords = {
        "x": min_x,
        "y": VIEWPORT_HEIGHT - max_y,
        "w": cropped_width,
        "h": cropped_height
    }

    # Extract cropped pixels
    cropped_pixels = []
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            idx = (y * width + x) * 4
            cropped_pixels.extend(pixels[idx:idx+4])

    # Create and save new image
    cropped_img = bpy.data.images.new("CroppedImage", width=cropped_width, height=cropped_height, alpha=True)
    cropped_img.pixels = cropped_pixels

    final_path = bpy.path.abspath(output_path)
    cropped_img.filepath_raw = final_path
    cropped_img.file_format = 'PNG'
    cropped_img.save()

    return { 
        'screen_coords': screen_coords,
        "filename": os.path.basename(output_path)
    }


def hide_all_objects_except_collection(collection_name):
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return

    allowed_objects = set(collection.objects)

    for obj in bpy.data.objects:
        if not obj in allowed_objects:
            obj.hide_viewport = True
            obj.hide_render = True
    
    
def show_all_objects_except_collection(collection_name):
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return

    allowed_objects = set(collection.objects)

    for obj in bpy.data.objects:
        if not obj in allowed_objects:
            obj.hide_viewport = False
            obj.hide_render = False
    
def unhide_object_and_children(object_name):
    obj = bpy.data.objects.get(object_name)
    if not obj:
        return

    obj.hide_viewport = False
    obj.hide_render = False

    for child in obj.children_recursive:
        child.hide_viewport = False
        child.hide_render = False


def set_object_show_in_render(obj_name: str, hide: bool):
    obj = bpy.data.objects.get(obj_name)
    if obj:
        obj.hide_render = not hide
    else:
        print(f"Object not found: {obj_name}")
      
def render_layer(atlas_name, layer_obj, dungeon_depth, dungeon_width, dest_path):

    hide_all_objects_except_collection("Environment")

    unhide_object_and_children(layer_obj["name"])

    obj = bpy.data.objects.get(layer_obj["name"])

    layer = {
        "tiles": []
    }            

    index = 1
    
    for z in range(dungeon_depth):
        for x in range(-dungeon_width, dungeon_width+1):
#            if layer_obj["render_zero"]:
            
            if "render_zero" in layer_obj and layer_obj["render_zero"] == False and z == 0 and x == 0: # skip tile zero
                continue
            
            obj.location = (x*3.0, z*3.0, 0.0)
            temp_path = render_to_temp_png()
            filename = f"{atlas_name.lower()}_{layer_obj['name'].lower()}_{index:03}.png"
            result = crop_and_save_image(temp_path, f"{dest_path}{filename}")
            if result and isinstance(result, dict):
                layer["tiles"].append({
                    "x": x,
                    "z": -z,
                    "screen_coords": result["screen_coords"],
                    "filename": result["filename"],
                })
                index += 1
                
    return layer            
            
def render_atlas(atlas):


    set_object_show_in_render("Shadow plane", atlas["shadows"])

    if atlas["front_light"]:
        set_object_show_in_render("Light (Front)", True)
        set_object_show_in_render("Light (Object)", False)
    else:
        set_object_show_in_render("Light (Front)", False)
        set_object_show_in_render("Light (Object)", True)

    atlas_name = atlas["name"].lower()

    hide_all_objects_except_collection("Environment")

    dest_path = atlas["output_path"] + "/" + atlas_name + "/"

    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    else:
        delete_all_files_in_folder(dest_path)

    atlas_json = {
        "settings": {
            "name": atlas_name,
            "dungeon_depth": DUNGEON_DEPTH,
            "dungeon_width": DUNGEON_WIDTH,
            "viewport_width": VIEWPORT_WIDTH,
            "viewport_height": VIEWPORT_HEIGHT,
        },
        "layers": {}
    }

    for layer_obj in atlas["objects"]:

        layer = render_layer(atlas_name, layer_obj, atlas["dungeon_depth"], atlas["dungeon_width"], dest_path)

        if layer and isinstance(layer, dict):
            layer["mode"] = 0
            layer["type"] = 1
            layer["name"] = layer_obj["name"].lower()
            atlas_json["layers"][layer_obj["name"].lower()] = layer

        
    json_str = json.dumps(atlas_json, indent=4)

    save_path = bpy.path.abspath(f"{dest_path}{atlas_name}.json")

    with open(save_path, "w") as f:
        f.write(json_str)


    show_all_objects_except_collection("Environment")            

# ========================================================================================
# declarations

DUNGEON_WIDTH = 3 # 3 to the left, 1 middle, 3 to the right = total of 7 tiles wide
DUNGEON_DEPTH = 6

VIEWPORT_WIDTH = 1024
VIEWPORT_HEIGHT = 720

# ========================================================================================
# output path for the generated atlases

output_path = "c://Users/danth/source/repos/AtlasMaker for Blender/atlas_converter/files/"

# ========================================================================================
# Set up render engine

scene = bpy.context.scene

scene.render.engine = 'CYCLES'
scene.cycles.noise_threshold = 0.01
scene.cycles.samples = 512
scene.cycles.time_limit = 2

scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
scene.render.resolution_x = VIEWPORT_WIDTH
scene.render.resolution_y = VIEWPORT_HEIGHT

# ========================================================================================
# Set up scene


# ========================================================================================
# Set up atlases

atlases = [
    {
        "name": "dungeon",
        "objects": [
            {"name": "Wall", "render_zero": False},
            {"name": "Ground"},
            {"name": "Ceiling"}
        ],
        "output_path": output_path,
        "dungeon_depth": DUNGEON_DEPTH,
        "dungeon_width": DUNGEON_WIDTH,
        "front_light": True,
        "shadows": False
    },
    {
        "name": "enemies",
        "objects": [
            {"name": "rat", "render_zero": False},
            {"name": "rat_attack", "render_zero": False},
            {"name": "rat_die", "render_zero": False}
        ],
        "output_path": output_path,
        "dungeon_depth": DUNGEON_DEPTH,
        "dungeon_width": DUNGEON_WIDTH,
        "front_light": False,
        "shadows": True
    },
    {
        "name": "containers",
        "objects": [
            {"name": "crate", "render_zero": False}
        ],
        "output_path": output_path,
        "dungeon_depth": DUNGEON_DEPTH,
        "dungeon_width": DUNGEON_WIDTH,
        "front_light": False,
        "shadows": True
    }      
]

# ========================================================================================
# render atlases

render_atlas(atlases[0])
#render_atlas(atlases[1])
#render_atlas(atlases[2])

# ========================================================================================
# done

sys.stdout.write('\a')  # beep
sys.stdout.flush()

print("Done!")

