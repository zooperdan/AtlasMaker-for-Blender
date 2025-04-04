class_name TexturePacker

var _atlas_image:Image
var _atlas_size:Vector2i
var _current_pos:Vector2i
var _max_height:int
var _padding:int

func crop_image(image:Image) -> Variant:
	
	var crop_rect:Rect2i = Rect2i(0,0,0,0) 
	
	var w = image.get_width()
	var h = image.get_height()

	# find top
	for y in range(0,h):
		var opaque_pixels = 0
		for x in range(0,w):
			if image.get_pixel(x,y) != Color(0,0,0,0):
				opaque_pixels += 1
		if opaque_pixels > 0:
			# found top
			crop_rect.position.y = y
			break
			
	# find left
	for x in range(0,w):
		var opaque_pixels = 0
		for y in range(0,h):
			if image.get_pixel(x,y) != Color(0,0,0,0):
				opaque_pixels += 1
		if opaque_pixels > 0:
			# found left
			crop_rect.position.x = x
			break

	# find bottom
	for y in range(h-1,0,-1):
		var opaque_pixels = 0
		for x in range(0,w):
			if image.get_pixel(x,y) != Color(0,0,0,0):
				opaque_pixels += 1
		if opaque_pixels > 0:
			# found bottom
			crop_rect.size.y = y + 1
			break
			
	# find right
	for x in range(w-1,0,-1):
		var opaque_pixels = 0
		for y in range(0,h):
			if image.get_pixel(x,y) != Color(0,0,0,0):
				opaque_pixels += 1
		if opaque_pixels > 0:
			# found right
			crop_rect.size.x = x + 1
			break
		
	if crop_rect.size.x == 0 and crop_rect.size.y == 0:
		return null
			
	var cropped_width:int = crop_rect.size.x-crop_rect.position.x
	var cropped_height:int = crop_rect.size.y-crop_rect.position.y
		
	if cropped_width > 0 and cropped_height > 0:
		var cropped_image:Image = Image.create(cropped_width, cropped_height, false, Image.FORMAT_RGBA8)
		for y:int in cropped_height:
			for x:int in cropped_width:
				cropped_image.set_pixel(x,y, image.get_pixel(crop_rect.position.x + x, crop_rect.position.y + y))
		return {
			"image": cropped_image,
			"screen_coords": {
				"x": crop_rect.position.x,
				"y": crop_rect.position.y,
				"w": crop_rect.size.x - crop_rect.position.x,
				"h": crop_rect.size.y - crop_rect.position.y,
				}
			}
	else:
		return null
			
func draw_image(image:Image, pos:Vector2i):
	var iw = image.get_width()
	var ih = image.get_height()
	for y in range(0,ih):
		for x in range(0,iw):
			_atlas_image.set_pixel(pos.x + x, pos.y + y, image.get_pixel(x,y))	

func init(atlas_size, padding):

	_atlas_size = atlas_size
	_padding = padding
	
	# create the atlas image
	_atlas_image = Image.create(atlas_size.x,atlas_size.y, false, Image.FORMAT_RGBA8)

	# Initialize variables for packing
	_current_pos = Vector2i(0, 0)
	_max_height = 0
	
func pack_image(image, store_image:bool = true) -> Variant:

	var cropped_image_result = crop_image(image)

	if !cropped_image_result:
		return false

	var result = {
		"atlas_coords": {},
		"screen_coords": {},
	}

	var size = cropped_image_result.image.get_size()
	
	if size.x == 0 or size.y == 0:
		return null
		
	if store_image:
				
		# If current row is full, move to next row
		if _current_pos.x + size.x > _atlas_size.x:
			_current_pos.x = 0
			_current_pos.y += _max_height + _padding
			_max_height = 0

		# If current image exceeds maximum height, resize atlas
		if _current_pos.y + size.y > _atlas_size.y:
			var expand_height = _current_pos.y + size.y - _atlas_size.y
			_atlas_size.y += expand_height
			var expanded_image = Image.create(_atlas_size.x, _atlas_size.y, false, Image.FORMAT_RGBA8)
			expanded_image.blit_rect(_atlas_image, Rect2(0, 0, _atlas_size.x, _atlas_size.y - expand_height), Vector2(0, 0))
			_atlas_image = expanded_image

		# Paste image into the atlas
		#atlas_image.blit_rect(img, Rect2(current_pos, size), Vector2(0, 0))
		draw_image(cropped_image_result.image, Vector2i(_current_pos.x, _current_pos.y))

		result.atlas_coords = {
			"x": _current_pos.x,
			"y": _current_pos.y,
			"w": size.x,
			"h": size.y,
		}

		# Update current position and maximum height
		_current_pos.x += size.x + _padding
		_max_height = max(_max_height, size.y)

	else:
		result.atlas_coords = {
			"x": 0,
			"y": 0,
			"w": 0,
			"h": 0,
		}		

	result.screen_coords = cropped_image_result.screen_coords

	return result

func get_atlas_image() -> Image:
	return _atlas_image
