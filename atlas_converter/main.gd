extends Node2D

var texture_packer:TexturePacker = TexturePacker.new()

func _ready() -> void:

	var atlas_filename:String = ""
	var dest_path:String = ""

	if !OS.has_feature("editor"):
		var args = Array(OS.get_cmdline_args())
		if args.size() != 2:
			print("Invalid number of arguments.")	
			quit_app()
		atlas_filename = args[0]
		if atlas_filename == "" or !FileAccess.file_exists(atlas_filename):
			print("The .json file does not exist.")	
			quit_app()
		dest_path = args[1]
		if !DirAccess.dir_exists_absolute(dest_path):
			print("Destination path does not exist.")	
			quit_app()
	else:
		dest_path = "res://files/converted/"
		atlas_filename = "res://files/Enemies.json"

	process_atlas(atlas_filename, dest_path)

	quit_app()

func _input(event):
	
	if event is InputEventKey and event.pressed:
		if Input.is_action_pressed("escape"):
			get_tree().quit()
				
func load_json(filename:String) -> Variant:
	var result = null
	var json_string = FileAccess.get_file_as_string(filename)
	if json_string:
		var json_data = JSON.parse_string(json_string)
		if json_data:
			result = json_data
	return result
	
func process_atlas(atlas_filename:String, dest_path:String):
	
	var source_path = atlas_filename.get_base_dir()
	var json_base_name = atlas_filename.get_file().to_lower()
	var atlas_base_name = atlas_filename.get_file().get_basename().to_lower() + ".png"

	var atlas_json = load_json(atlas_filename)

	if atlas_json:
		
		texture_packer.init(Vector2i(1024, 1024), 2)
		
		for key in atlas_json.layers:
			for tile in atlas_json.layers[key].tiles:
				var image_filename:String = source_path.path_join(tile.filename)
				var image = Image.load_from_file(image_filename)
				if image:
					var pack_result = texture_packer.pack_image(image)
					tile.atlas_coords = pack_result.atlas_coords
#
		var json_string = JSON.stringify(atlas_json)
		var json_filename = dest_path.path_join(json_base_name)
		var file = FileAccess.open(json_filename,FileAccess.WRITE)
		if file:
			file.store_string(json_string)
			file.close()
			file = null

		var packed_image = texture_packer.get_atlas_image()
		var filename = dest_path.path_join(atlas_base_name)
		packed_image.save_png(filename)
	
		print(atlas_base_name + " has been converted.")
		
	
func quit_app():
	get_tree().quit()
