bl_info = {
	'name': 'Blender VTF',
	'author': 'MrKleiner',
	'version': (0, 41),
	'blender': (3, 4, 1),
	'location': 'N menu in the Image Editor / UV Editor',
	'description': """VTF Edit GUI in Blender""",
	'doc_url': '',
	'category': 'Add Mesh',
}


# todo: batch syntax definition file
# todo: R/G/B/A channels switch in the blvtf GUI
# todo: Update button




import bpy

import hashlib, random, mathutils, time, datetime, subprocess, shutil, sys, os, json, math, re, sqlite3

from bpy_extras.object_utils import AddObjectHelper, object_data_add

from pathlib import Path

from bpy.props import (StringProperty,
					   BoolProperty,
					   IntProperty,
					   FloatProperty,
					   FloatVectorProperty,
					   EnumProperty,
					   PointerProperty,
					   )
from bpy.types import (Panel,
					   Operator,
					   AddonPreferences,
					   PropertyGroup,
					   )

addon_root_dir = Path(__file__).parent
vtfcmd_exe = addon_root_dir / 'bins' / 'vtfcmd' / 'VTFCmd.exe'
vtfcmd_exe_old = addon_root_dir / 'bins' / 'vtfcmd_old' / 'VTFCmd.exe'
magix_exe = addon_root_dir / 'bins' / 'imgmagick' / 'magick.exe'
tmp_folder = addon_root_dir / 'tmps'






# =========================================================
# ---------------------------------------------------------
#                        Entries
# ---------------------------------------------------------
# =========================================================


blvtf_interp_filters = (
	('POINT', 'Point', 'Point'),
	('BOX', 'Box', 'Box'),
	('TRIANGLE', 'Triangle', 'Triangle'),
	('QUADRATIC', 'Quadratic', 'Quadratic'),
	('CUBIC', 'Cubic', 'Cubic'),
	('CATROM', 'Catrom', 'Catrom'),
	('MITCHELL', 'Mitchell', 'Mitchell'),
	('GAUSSIAN', 'Gaussian', 'Gaussian'),
	('SINC', 'Sinc', 'Sinc'),
	('BESSEL', 'Bessel', 'Bessel'),
	('HANNING', 'Hanning', 'Hanning'),
	('HAMMING', 'Hamming', 'Hamming'),
	('BLACKMAN', 'Blackman', 'Blackman'),
	('KAISER', 'Kaiser', 'Kaiser')
)

blvtf_sharpen_filters = (
	('NONE', 'None', 'Do not apply this filter'),
	('NEGATIVE', 'Negative', 'Negative'),
	('LIGHTER', 'Lighter', 'Lighter'),
	('DARKER', 'Darker', 'Darker'),
	('CONTRASTMORE', 'Contrast More', 'Contrast More'),
	('CONTRASTLESS', 'Contrast Less', 'Contrast Less'),
	('SMOOTHEN', 'Smoothen', 'Smoothen'),
	('SHARPENSOFT', 'Sharpen Soft', 'Sharpen Soft'),
	('SHARPENMEDIUM', 'Sharpen Medium', 'Sharpen Medium'),
	('SHARPENSTRONG', 'Sharpen Strong', 'Sharpen Strong'),
	('FINDEDGES', 'Find Edges', 'Find Edges'),
	('CONTOUR', 'Contour', 'Contour'),
	('EDGEDETECT', 'Edge Detect', 'Edge Detect'),
	('EDGEDETECTSOFT', 'Edge Detect Soft', 'Edge Detect Soft'),
	('EMBOSS', 'Emboss', 'Emboss'),
	('MEANREMOVAL', 'Mean Removal', 'Mean Removal'),
	('UNSHARP', 'Unsharpen Mask', 'Unsharpen Mask'),
	('XSHARPEN', 'XSharpen', 'XSharpen'),
	('WARPSHARP', 'Warp Sharp', 'Warp Sharp'),
)

blvtf_sizes_tip = """Yes, this is possible.
	There are only two actual limitations to VTF dimensions: It cannot be bigger than 65536 pixels on any axis and the total amount of pixels cannot be more than 16.7 million.
	For instance, 4096 times 4096 = 16.7 million and 32768 times 512 is 16.7 million too.
	Yes, this will work totally fine without any performance impact.
	It's speculated that the resulting VTF should be less than 33mb in size for it to be loaded by the engine.
""".replace('\t', '').strip()

blvtf_applicable_sizes = (
	('32768', '32768', blvtf_sizes_tip),
	('16384', '16384', blvtf_sizes_tip),
	('8192', '8192', blvtf_sizes_tip),
	('4096', '4096', '4096'),
	('2048', '2048', '2048'),
	('1024', '1024', '1024'),
	('512', '512', '512'),
	('256', '256', '256'),
	('128', '128', '128'),
	('64', '64', '64'),
	('32', '32', '32'),
	('16', '16', '16'),
	('8', '8', '8'),
	('4', '4', '4'),
	('2', '2', '2'),
	# ('1', '1', 'ded2'),
)

blvtf_img_formats = (
	# Common RGB/RGBA
	('DXT1', 'DXT1', 'Lossy compression without alpha'),
	('DXT3', 'DXT3', 'Lossy compression with 1-bit alpha'),
	('DXT5', 'DXT5', 'Lossy compression with good alpha'),
	# uncompressed
	('BGR888', 'BGR888', 'Lossless encoding without Alpha'),
	('BGR565', 'BGR565', 'No compression, decreased bit depth, no Alpha'),
	('BGRA8888', 'BGRA8888', 'Lossless encoding with Alpha'),
	('BGRA4444', 'BGRA4444', 'No compression, decreased bit depth, no Alpha'),
	None,
	# Common BW
	('I8', 'I8', 'Lossless Luminance (BW single channel)'),
	('IA88', 'IA88', 'Lossless Luminance (BW) with Alpha'),
	('A8', 'A8', 'No RGB, alpha channel only (Lossless)'),
	None,
	# Other
	('DXT1_ONEBITALPHA', 'DXT1_ONEBITALPHA', 'DXT1, but with one bit Alpha'),
	('RGB888', 'RGB888', 'Lossless encoding without Alpha'),
	('RGB565', 'RGB565', 'No compression, decreased bit depth, no Alpha'),
	('RGBA8888', 'RGBA8888', 'Lossless encoding with Alpha'),

	('ABGR8888', 'ABGR8888', 'Lossless encoding with Alpha'),
	('RGB888_BLUESCREEN', 'RGB888_BLUESCREEN', 'RGB888_BLUESCREEN'),
	('BGR888_BLUESCREEN', 'BGR888_BLUESCREEN', 'BGR888_BLUESCREEN'),
	('ARGB8888', 'ARGB8888', 'Lossless encoding with Alpha'),
	('BGRX8888', 'BGRX8888', 'BGRX8888'),
	('BGRX5551', 'BGRX5551', 'No compression, decreased bit depth, no Alpha'),
	('BGRA5551', 'BGRA5551', 'No compression, decreased bit depth, no Alpha'),
	('UV88', 'UV88', '2-channel (RG) encoding for AMD Normal Maps'),
	('UVWQ8888', 'UVWQ8888', 'UVWQ8888'),
	('RGBA16161616F', 'RGBA16161616F', 'Lossless Float HDR encoding'),
	('RGBA16161616', 'RGBA16161616', 'Lossless Signed int HDR encoding'),
	('UVLX8888', 'UVLX8888', 'UVLX8888'),
)

blvtf_img_channels = (
	('COLOR_ALPHA', 'RGBA', 'RGBA'),
	('COLOR', 'RGB', 'RGB'),
	('RED', 'R', 'R'),
	('GREEN', 'G', 'G'),
	('BLUE', 'B', 'B'),
	('ALPHA', 'A', 'A'),
)

blvtf_vtf_versions = (
	('7.5', '7.5', 'The latest, released with Alien Swarm, not supported in everything below Alien Swarm'),
	('7.4', '7.4', 'Released with Orange Box, the one used by current 2013SDK, tf2, etc.'),
	('7.3', '7.3', 'Released with tf2'),
	('7.2', '7.2', 'Small update after hl2 release (still dinosaurs, but with huge throbbing dicks)'),
	('7.1', '7.1', 'Released with hl2 (dinosaurs themselves used this)'),
)


blvtf_vtf_flags = (
	('POINTSAMPLE', 'Point Sample', 'Disable Bilinear filtering for "pixel art"-style texture filtering'),
	('TRILINEAR', 'Trilinear', 'Always use Trilinear filtering, even when set to Bilinear in video settings'),
	('CLAMPS', 'Clamp S', 'Clamp S coordinates, to prevent horizontal texture wrapping'),
	('CLAMPT', 'Clamp T', 'Clamp T coordinates, to prevent vertical texture wrapping'),
	('ANISOTROPIC', 'Anisotropic', 'Always use Anisotropic filtering, even when set to Bilinear or Trilinear in video settings'),
	('HINT_DXT5', 'Hint DXT5', 'Used in skyboxes. Makes sure edges are seamless'),
	('NORMAL', 'Normal Map', 'Texture is a normal map'),
	('NOMIP', 'No Mipmap', 'Load largest mipmap only. (Does not delete existing mipmaps, just disables them)'),
	('NOLOD', 'No Level Of Detail', 'Not affected by texture resolution settings'),
	('MINMIP', 'No Minimum Mipmap', 'If set, load mipmaps below 32x32 pixels'),
	('PROCEDURAL', 'Procedural', 'Texture is an procedural texture (code can modify it)'),
	('RENDERTARGET', 'Rendertarget', 'Texture is a render target'),
	('DEPTHRENDERTARGET', 'Depth Render Target', 'Texture is a depth render target'),
	('NODEBUGOVERRIDE', 'No Debug Override', 'ded2'),
	('SINGLECOPY', 'Single Copy', 'Signal the system that only once instance of this file may exist'),
	('NODEPTHBUFFER', 'No Depth Buffer', 'Do not buffer for Video Processing, generally render distance'),
	('CLAMPU', 'Clamp U', 'Clamp U coordinates (for volumetric textures)'),
	('VERTEXTEXTURE', 'Vertex Texture', 'Usable as a vertex texture'),
	('SSBUMP', 'SSBump', 'Texture is an SSBump'),
	('BORDER', 'Clamp All', 'Clamp to border colour on all texture coordinates'),
)

blvtf_vtf_flags_s = (
	'POINTSAMPLE',
	'TRILINEAR',
	'CLAMPS',
	'CLAMPT',
	'ANISOTROPIC',
	'HINT_DXT5',
	'NORMAL',
	'NOMIP',
	'NOLOD',
	'MINMIP',
	'PROCEDURAL',
	'RENDERTARGET',
	'DEPTHRENDERTARGET',
	'NODEBUGOVERRIDE',
	'SINGLECOPY',
	'NODEPTHBUFFER',
	'CLAMPU',
	'VERTEXTEXTURE',
	'SSBUMP',
	'BORDER',
)

blvtf_resize_methods = (
	('NEAREST', 'Nearest Power Of 2', '1023 -> 1024, 570 -> 512'),
	('BIGGEST', 'Biggest Power of 2', '1023 -> 1024, 570 -> 1024'),
	('SMALLEST', 'Smallest Power of 2', '1023 -> 512, 570 -> 512')
)

# file extensions supported by VTFCmd. Everything else has to be converted with imagemagick beforehand
blvtf_vtfcmd_supported = (
	'.tga',
	'.jpeg',
	'.jpg',
	'.png',
	'.bmp',
	'.dds',
	'.gif'
)

blvtf_power_of_two = (
	32_768,
	16_384,
	8192,
	4096,
	2048,
	1024,
	512,
	256,
	128,
	64,
	32,
	16,
	8,
	4,
	2,
)


blvtf_img_formats_lone = (
	'DXT1',
	'DXT3',
	'DXT5',
	'BGR888',
	'BGR565',
	'BGRA8888',
	'BGRA4444',
	'I8',
	'IA88',
	'A8',
	'DXT1_ONEBITALPHA',
	'RGB888',
	'RGB565',
	'RGBA8888',
	'ABGR8888',
	'RGB888_BLUESCREEN',
	'BGR888_BLUESCREEN',
	'ARGB8888',
	'BGRX8888',
	'BGRX5551',
	'BGRA5551',
	'UV88',
	'UVWQ8888',
	'RGBA16161616F',
	'RGBA16161616',
	'UVLX8888',
)















# =========================================================
# ---------------------------------------------------------
#                  Actual shit. Functions
# ---------------------------------------------------------
# =========================================================

def blvtf_ensure_addon_setup():
	if not vtfcmd_exe.is_file():
		# unpack VTF Edit cmd
		unpk_prms = [
			str(addon_root_dir / 'bins' / '7z' / '7z.exe'),
			'x',
			'-o' + str(addon_root_dir / 'bins' / 'vtfcmd'),
			str(addon_root_dir / 'bins' / 'vtfcmd.orgn'),
			'-aoa'
		]

		# exec vtfcmd unpacking
		subprocess.run(unpk_prms, stdout=subprocess.DEVNULL)

	if not vtfcmd_exe_old.is_file():
		# unpack VTF Edit cmd Old version with image sharpening
		unpk_prms = [
			str(addon_root_dir / 'bins' / '7z' / '7z.exe'),
			'x',
			'-o' + str(addon_root_dir / 'bins' / 'vtfcmd_old'),
			str(addon_root_dir / 'bins' / 'vtfcmd_old.orgn'),
			'-aoa'
		]

		# exec vtfcmd unpacking
		subprocess.run(unpk_prms, stdout=subprocess.DEVNULL)

	if not magix_exe.is_file():
		# unpack imgmagick exe
		unpk_prms = [
			str(addon_root_dir / 'bins' / '7z' / '7z.exe'),
			'x',
			'-o' + str(addon_root_dir / 'bins'),
			str(addon_root_dir / 'bins' / 'imgmagick.orgn'),
			'-aoa'
		]

		# exec magix unpacking
		subprocess.run(unpk_prms, stdout=subprocess.DEVNULL)


blvtf_ensure_addon_setup()

# get image XY dimensions in pixels
# returns XY tuple
def blvtf_get_img_dims(imgpath):
	magix_prms = [
		str(magix_exe),
		'convert',
		str(imgpath),
		'json:'
	]

	json_echo = None
	with subprocess.Popen(magix_prms, stdout=subprocess.PIPE, bufsize=10**8) as img_pipe:
		# fuck = img_pipe.stdout.read()
		# print('got json echo', fuck)
		json_echo = json.loads(img_pipe.stdout.read())

	geometry = json_echo[0]['image']['geometry']

	return (geometry['width'], geometry['height'])

def blvtf_resize_img_to_xy(imgpath, dims):
	src_path = Path(imgpath)
	tgt_path = tmp_folder / f'{src_path.stem}.tga'
	magix_prms = [
		str(magix_exe),
		str(imgpath),
		'-resize', f'{dims[0]}x{dims[1]}!',
		str(tgt_path)
	]

	resize_echo = None
	with subprocess.Popen(magix_prms, stdout=subprocess.PIPE, bufsize=10**8) as img_pipe:
		resize_echo = img_pipe.stdout.read()

	if not tgt_path.is_file():
		return False

	return tgt_path

# convert an image to tga using imagemagick
def blvtf_img_to_tga(imgpath):
	src_path = Path(imgpath)
	tgt_path = tmp_folder / f'{src_path.stem}.tga'
	tgt_path.unlink(missing_ok=True)
	magix_prms = [
		str(magix_exe),
		f'{imgpath}[0]',
		str(tgt_path)
	]

	tga_echo = None
	with subprocess.Popen(magix_prms, stdout=subprocess.PIPE, bufsize=10**8) as img_pipe:
		tga_echo = img_pipe.stdout.read()

	print('TGA ECHO', tga_echo.decode())

	if not tgt_path.is_file():
		return False

	return tgt_path

# embed an image into the alpha channel of another one
def blvtf_emb_alpha(rgb, alpha):
	rgb = Path(rgb)
	alpha = Path(alpha)

	# if alpha is not of the same size as rgb - rescale it to fit
	rgb_dims = blvtf_get_img_dims(rgb)
	alpha_dims = blvtf_get_img_dims(alpha)

	resized_alpha = None
	if rgb_dims != alpha_dims:
		resized_alpha = blvtf_resize_img_to_xy(alpha, rgb_dims)


	tgt_path = tmp_folder / f'{rgb.stem}.wa.tga'
	tgt_path.unlink(missing_ok=True)
	magix_prms = [
		str(magix_exe),
		# rgb
		f'{rgb}[0]',
		# alpha
		str(resized_alpha or alpha),
		'-alpha', 'off',
		'-compose', 'CopyOpacity',
		'-composite', str(tgt_path)
	]

	alpha_echo = None
	with subprocess.Popen(magix_prms, stdout=subprocess.PIPE, bufsize=10**8) as img_pipe:
		alpha_echo = img_pipe.stdout.read()

	# since resized alpha is a separate image - delete it, because only resulting composite is needed
	# (which is present already)
	if resized_alpha != None:
		resized_alpha.unlink(missing_ok=True)

	if not tgt_path.is_file():
		return False

	return tgt_path

# this simply first applies bpy.path.abspath and then Path()
def aPath(pth):
	# todo: this str conversion is some rubbish
	return Path(bpy.path.abspath(str(pth)))

# hash string with sha256
def strhash(s):
	try:
		return hashlib.sha256(s).hexdigest()
	except Exception as e:
		return hashlib.sha256(str(s).encode()).hexdigest()


# Evaluate active flags from source and return an array
def blvtf_get_active_flags(src):
	if not src:
		return []

	vtf_flags = []
	for flg in blvtf_flag_props:
		if src.get(flg) == True:
			# important todo: this 'replace()' is just retarded
			vtf_flags.append(flg.replace('vtf_flag_', ''))

	return vtf_flags


def blvtf_set_view_channel(self, context):
	context.space_data.display_channels = context.scene.blvtf_exp_params.display_channel

# get flags from batch list and insert at current cursor position in the specified txtmax file
def blvtf_insert_flags_at_cursor(self, context):
	context.scene.blvtf_batch_params.txtmax_file.write(f"""-{','.join(blvtf_get_active_flags(context.scene.blvtf_batch_params))}""")

# self.report({'WARNING'}, str(e))

# Convert image from path to vtf
# takes a dict of params
{
	'enc': ('(no alpha) DXT1', '(w alpha) DXT5'),
	'mips': False or ('resize_filter', 'sharpen_filter'),
	'comp_refl': True,
	'src': 'W:/vid_dl/sex.tga',
	'dest': 'W:/vid_dl/bdsm/pootis.vtf',
	'emb_alpha': 'W:/vid_dl/specular.tga',
	'resize': False or ('resizing_rule', 'resize_filter', 'sharpen_filter'),
	'clamp_dims': False or (512, 512),
	'flags': ('NORMAL', 'NOMIP', 'MINMIP'),
}
def blvtf_export_img_to_vtf(img_info, reporter=None):
	img_src = Path(img_info['src'])
	vtf_dest = Path(img_info['dest'])
	emb_alpha = Path(str(img_info['emb_alpha']))

	# check whether the destination folder exists
	if not vtf_dest.parent.is_dir():
		if reporter:
			reporter.report({'WARNING'}, f'The destination folder >{vtf_dest.parent}< For the image >{img_src.name}< does not exist, skipping')
		return

	# check whether the image is of applicable size
	img_dims = blvtf_get_img_dims(img_src)
	if (not img_dims[0] in blvtf_power_of_two or not img_dims[1] in blvtf_power_of_two) and not img_info['resize']:
		if reporter:
			reporter.report({'WARNING'}, f"""Skipping image {img_src.name}, because it's of unapplicable size! {img_dims}, please enable resizing""")
		return

	shared_params = bpy.context.scene.blvtf_exp_params

	# embed alpha, if any
	img_src_w_alpha = None
	if emb_alpha.is_file():
		print('BLVTF: Trying to add alpha...')
		img_src_w_alpha = blvtf_emb_alpha(img_src, emb_alpha)

	# convert to applicable format, if needed
	img_src_converted = None
	if not img_src.suffix in blvtf_vtfcmd_supported and img_src_w_alpha == None:
		img_src_converted = blvtf_img_to_tga(img_src)

	input_filepath = img_src_w_alpha or img_src or img_src_converted

	vtfcmd_args = [
		str(vtfcmd_exe if shared_params.vtfcmd_ver == 'new' else vtfcmd_exe_old),
		'-file',
		str(input_filepath),
	]

	# resize to power of 2
	if img_info['resize']:
		vtfcmd_args.extend([
			'-resize',
			'-rmethod', img_info['resize'][0],
			'-rfilter', img_info['resize'][1],
		])
		if shared_params.vtfcmd_ver == 'old':
			vtfcmd_args.extend([
				'-rsharpen', img_info['resize'][2]
			])

	# clamp image XY
	if img_info['resize'] and img_info['clamp_dims']:
		vtfcmd_args.extend([
			'-rclampwidth', img_info['clamp_dims'][0],
			'-rclampheight', img_info['clamp_dims'][1],
		])

	# Specify vtf format
	vtfcmd_args.extend([
		'-format', img_info['enc'][0],
		'-alphaformat', img_info['enc'][1],
	])

	# Mipmaps generation
	if img_info['mips']:
		vtfcmd_args.extend([
			'-mfilter', img_info['mips'][0],
		])
		if shared_params.vtfcmd_ver == 'old':
			vtfcmd_args.extend([
				'-msharpen', img_info['mips'][1],
			])
	else:
		vtfcmd_args.append('-nomipmaps')

	# Specify vtf version
	vtfcmd_args.extend(['-version', shared_params.vtf_version])

	if img_info['comp_refl'] != True:
		vtfcmd_args.append('-noreflectivity')

	if shared_params.vtf_generate_thumb != True:
		vtfcmd_args.append('-nothumbnail')

	# Add flags
	for addflg in img_info['flags']:
		vtfcmd_args.extend(['-flag', addflg])

	# Specify output folder
	vtfcmd_args.extend([
		'-output', str(vtf_dest.parent),
	])

	# execute conversion
	print('Executing VTF conversion', str(input_filepath), vtfcmd_args)
	vtf_echo = None
	with subprocess.Popen(vtfcmd_args, stdout=subprocess.PIPE, bufsize=10**8) as vtf_pipe:
		vtf_echo = vtf_pipe.stdout.read()

	print('echo:', vtf_echo.decode())

	# rename
	# important todo: IS THIS EVEN LEGAL ?!
	shutil.move(str(vtf_dest.parent / f'{input_filepath.stem}.vtf'), str(vtf_dest.with_suffix('.vtf')))

	# Delete leftovers
	if img_src_w_alpha:
		img_src_w_alpha.unlink(missing_ok=True)

	if img_src_converted:
		img_src_converted.unlink(missing_ok=True)


def blvtf_export_img_datablock(self, context, img):
	img_data = img
	img_vtf_prms = img_data.blvtf_img_params
	shared_params = bpy.context.scene.blvtf_exp_params

	# todo: Packed images are not supported yet
	if img_data.is_embedded_data:
		# todo: this reports with the datablock name, while other reporters use actual filename. This might be confusing at times
		self.report({'WARNING'}, f'Image {img_data.name} is packed, but packed images are not supported yet. Skipping...')
		return

	# Check whether the source image exists
	# Because why not...
	if not aPath(img_data.filepath).is_file():
		self.report({'WARNING'}, f'The Image {img_data.name} is missing from disk, skipping')
		return

	add_alpha = False
	if img_vtf_prms.embed_to_alpha:
		if not img_vtf_prms.image_to_embed:
			self.report({'WARNING'}, f'The Image {img_data.name} has "Embed Alpha" enabled, but the target image is missing. No alpha would be embedded')
		else:
			add_alpha = aPath(img_vtf_prms.image_to_embed.filepath)
		

	src_file = aPath(img_data.filepath)
	# export_filename = aPath(img_vtf_prms.vtf_export_path) / image.name_full
	# by default the export destination is target path + source file name with suffix changed to .vtf
	export_filename = aPath(img_vtf_prms.vtf_export_path) / f'{src_file.stem}.vtf'
	# but if rename is enabled - get the new name and add .vtf suffix to it
	if img_vtf_prms.vtf_named_export:
		export_filename = export_filename.parent / f'{img_vtf_prms.vtf_new_name}.vtf'

	resulting_flags = blvtf_get_active_flags(img_vtf_prms)

	blvtf_export_img_to_vtf({
		'enc': (img_vtf_prms.vtf_format, img_vtf_prms.vtf_format_w_alph),
		'mips': (shared_params.vtf_mipmap_filter, shared_params.vtf_mipmap_sharpen_filter) if img_vtf_prms.vtf_mipmaps_enable else False,
		'comp_refl': img_vtf_prms.vtf_compute_refl,
		'src': aPath(img_data.filepath),
		'dest': export_filename,
		'emb_alpha': add_alpha,
		'resize': (img_vtf_prms.vtf_resize_method, shared_params.vtf_resize_filter, shared_params.vtf_resize_sharpen_filter) if img_vtf_prms.vtf_enable_resize else False,
		'clamp_dims': (img_vtf_prms.vtf_resize_clamp_maxwidth, img_vtf_prms.vtf_resize_clamp_maxheight) if img_vtf_prms.vtf_resize_clamp else False,
		# todo: oh fuck
		'flags': tuple(resulting_flags),
	}, self)













# =========================================================
# ---------------------------------------------------------
#                       Operators
# ---------------------------------------------------------
# =========================================================

class OBJECT_OT_blvtf_export_active_img(Operator, AddObjectHelper):
	bl_idname = 'mesh.blvtf_export_active_img'
	bl_label = 'Export Active Image'
	bl_options = {'REGISTER'}
	bl_description = """Export the image you're looking at right now"""

	def execute(self, context):
		# img_data = context.space_data.image
		# img_vtf_prms = context.space_data.image.blvtf_img_params

		blvtf_export_img_datablock(self, context, context.space_data.image)
		return {'FINISHED'}


class OBJECT_OT_blvtf_export_marked_imgs(Operator, AddObjectHelper):
	bl_idname = 'mesh.blvtf_export_marked_imgs'
	bl_label = 'Export Marked Images'
	bl_options = {'REGISTER'}
	bl_description = 'Export all the images from this blend file which were marked for export according to their settings ("Export this image" checkbox)'

	def execute(self, context):
		for eimg in bpy.data.images:
			if eimg.blvtf_img_params.do_export == True:
				blvtf_export_img_datablock(self, context, eimg)

		return {'FINISHED'}



class OBJECT_OT_blvtf_folder_convert(Operator, AddObjectHelper):
	bl_idname = 'mesh.blvtf_folder_export'
	bl_label = 'Batch Convert'
	bl_options = {'REGISTER'}
	bl_description = 'Take images from the specified folder and convert them to VTF'

	def execute(self, context):

		shared_params = context.scene.blvtf_exp_params
		batch_params = context.scene.blvtf_batch_params

		input_folder = aPath(batch_params.batch_folder_input)
		output_folder = aPath(batch_params.batch_folder_output)

		# If TextMax is enabled, then a text file has to be specified
		if batch_params.txtmax_enabled and not batch_params.txtmax_file:
			self.report({'WARNING'}, 'TxtMax is enabled, but no text file selected. Aborting')
			return {'FINISHED'}

		# Output has to be a valid dir
		if not output_folder.is_dir():
			self.report({'WARNING'}, 'The destination folder does not exist. Aborting')
			return {'FINISHED'}

		# Glob or Rglob
		if batch_params.batch_recursive:
			traverse_src = input_folder.rglob
		else:
			traverse_src = input_folder.glob

		# collect flags right away
		batch_vtf_flags = blvtf_get_active_flags(batch_params)

		print('Batch Flags', batch_vtf_flags)

		# important todo: proper wildcard detection
		wcard_symbols = (
			'!',
			'?',
			'*',
			'/',
			'\\',
			'<',
			'>',
			'|'
		)
		glob_pattern = '*.*'
		if len(set(wcard_symbols) & set(input_folder.name)) != 0:
			glob_pattern = input_folder.name
			input_folder = input_folder.parent


		# collect tasks
		# (image files to process, including all the info n shit)
		tasks = {}

		# Collect tasks from TxtMax, if any
		if batch_params.txtmax_enabled:
			patterns = {}

			# collect patterns
			for ln in batch_params.txtmax_file.lines:
				ln = ln.body.strip()
				if ln.startswith('#') or ln == '':
					continue
				raw_rule = list(filter(None, ln.replace('\t', ' ').split(' ')))
				rname = raw_rule[0]

				patterns[rname] = {
					'format': batch_params.vtf_format if raw_rule[1] == '*' else raw_rule[1],
					'sclamp': False,
					'flags': []
				}

				# Flag array
				if raw_rule[-1].startswith('-'):
					if raw_rule[-1] == '-*':
						patterns[rname]['flags'] = tuple(batch_vtf_flags)
					else:
						patterns[rname]['flags'] = tuple(set(filter(None, raw_rule[-1].replace('-', '').upper().split(','))) & set(blvtf_vtf_flags_s))
					del raw_rule[-1]

				# Size Clamp
				if len(raw_rule) > 2:
					sclamp = raw_rule[2].lower()
					if 'x' in sclamp:
						sclamp = sclamp.split('x')
						patterns[rname]['sclamp'] = (
							str(batch_params.vtf_resize_clamp_maxwidth) if sclamp[0] == '*' else sclamp[0],
							str(batch_params.vtf_resize_clamp_maxheight) if sclamp[1] == '*' else sclamp[1],
						)

			# Go through each pattern and get file paths from them
			for pat in patterns:
				for imgf in traverse_src(pat):
					tasks[strhash(imgf)] = {
						'enc': (patterns[pat]['format'], patterns[pat]['format']),
						'mips': (shared_params.vtf_mipmap_filter, shared_params.vtf_mipmap_sharpen_filter) if batch_params.vtf_mipmaps_enable else False,
						'comp_refl': batch_params.vtf_compute_refl,
						'src': imgf,
						'dest': output_folder / imgf.relative_to(input_folder).with_suffix('.vtf'),
						'emb_alpha': False,
						# Aligning to the nearest power of 2 is always on for txtmax
						'resize': (batch_params.vtf_resize_method, shared_params.vtf_resize_filter, shared_params.vtf_resize_sharpen_filter),
						'clamp_dims': (patterns[pat]['sclamp'][0], patterns[pat]['sclamp'][1]) if patterns[pat]['sclamp'] else False,
						# todo: oh fuck
						'flags': patterns[pat]['flags'],
					}


		# Collect tasks from main batch
		if not batch_params.txtmax_enabled or (batch_params.txtmax_enabled and batch_params.txtmax_use_fallback):
			for tsk_file in traverse_src(glob_pattern):
				tsk_hash = strhash(tsk_file)
				if not tsk_hash in tasks:
					tasks[tsk_hash] = {
						'enc': (batch_params.vtf_format, batch_params.vtf_format_w_alph),
						'mips': (shared_params.vtf_mipmap_filter, shared_params.vtf_mipmap_sharpen_filter) if batch_params.vtf_mipmaps_enable else False,
						'comp_refl': batch_params.vtf_compute_refl,
						'src': tsk_file,
						'dest': output_folder / tsk_file.relative_to(input_folder).with_suffix('.vtf'),
						'emb_alpha': False,
						'resize': (batch_params.vtf_resize_method, shared_params.vtf_resize_filter, shared_params.vtf_resize_sharpen_filter) if batch_params.vtf_enable_resize else False,
						'clamp_dims': (batch_params.vtf_resize_clamp_maxwidth, batch_params.vtf_resize_clamp_maxheight) if batch_params.vtf_resize_clamp else False,
						# todo: oh fuck
						'flags': tuple(batch_vtf_flags),
					}


		# Process all tasks
		for process_task in tasks:
			if tasks[process_task]['dest'].parent != output_folder:
				tasks[process_task]['dest'].parent.mkdir(parents=True, exist_ok=True)
			blvtf_export_img_to_vtf(tasks[process_task], self)


		return {'FINISHED'}








class OBJECT_OT_blvtf_append_flags_to_txtmax_definition(Operator, AddObjectHelper):
	bl_idname = 'mesh.blvtf_append_flags_to_txtmax_definition'
	bl_label = 'Append Flags'
	bl_options = {'REGISTER'}
	bl_description = 'Append flags enabled in the batch convert list to the TxtMax text file at the current cursor position using appropriate syntax (Just click this and see what it does)'

	def execute(self, context):
		if context.scene.blvtf_batch_params.txtmax_file:
			context.scene.blvtf_batch_params.txtmax_file.write(f"""-{','.join(blvtf_get_active_flags(context.scene.blvtf_batch_params))}""")
		return {'FINISHED'}




























# =========================================================
# ---------------------------------------------------------
#                   Property declarations
# ---------------------------------------------------------
# =========================================================
# dumpster.prop_search(context.scene, 'blvtfsex', bpy.data, 'images')




blvtf_flag_props = (
	'vtf_flag_POINTSAMPLE',
	'vtf_flag_TRILINEAR',
	'vtf_flag_CLAMPS',
	'vtf_flag_CLAMPT',
	'vtf_flag_ANISOTROPIC',
	'vtf_flag_HINT_DXT5',
	'vtf_flag_NORMAL',
	'vtf_flag_NOMIP',
	'vtf_flag_NOLOD',
	'vtf_flag_MINMIP',
	'vtf_flag_PROCEDURAL',
	'vtf_flag_RENDERTARGET',
	'vtf_flag_DEPTHRENDERTARGET',
	'vtf_flag_NODEBUGOVERRIDE',
	'vtf_flag_SINGLECOPY',
	'vtf_flag_NODEPTHBUFFER',
	'vtf_flag_CLAMPU',
	'vtf_flag_VERTEXTEXTURE',
	'vtf_flag_SSBUMP',
	'vtf_flag_BORDER',
)




class blvtf_individual_image_props_declaration(PropertyGroup):
	# Whether to export this texture or not
	do_export : BoolProperty(
		name='Export this image',
		description='Whether to include this image to the mass blend file export or not',
		default=False
	)

	# VTF format, like DXT1
	vtf_format : EnumProperty(
		items=blvtf_img_formats,
		name='Encoding',
		description='Encoding format to use, the most common ones are DXT1 and DXT5',
		default='DXT1'
	)

	# VTF format for images with an alpha channel
	vtf_format_w_alph : EnumProperty(
		items=blvtf_img_formats,
		name='Encoding if alpha channel is present',
		description='Encoding format to use, if image has an alpha channel',
		default='DXT5'
	)

	# Mipmaps Onn/Off
	vtf_mipmaps_enable : BoolProperty(
		name='Generate Mipmaps',
		description='Whether to generate the mipamps or not',
		default=True
	)

	# Export VTF to the desired location
	vtf_export_path : StringProperty(
		name='Destination folder',
		description='Export the fucking shit',
		default='nil',
		subtype='DIR_PATH'
	)

	# Re-Assign names
	vtf_named_export: BoolProperty(
		name='Rename',
		# description='Rename resulting VTF to the specified name. Else - use image datablock name',
		description='Rename resulting VTF to the specified name. Else - use original image name (and not datablock name)',
		default = False
	)
	# new name to assign
	vtf_new_name : StringProperty(
		name='New Name',
		description='Filename to assign to the resulting VTF',
		default='nil'
	)


	# Embed an image into the alpha channel of the resulting VTF
	embed_to_alpha: BoolProperty(
		name='Embed to alpha channel',
		description='Embed the selected image into the alpha channel of the resulting VTF',
		default=False
	)
	image_to_embed : PointerProperty(
		name='Image to Embed',
		type=bpy.types.Image
	)











	# -------
	# Resize
	# -------

	# Enable/Disable resizing
	vtf_enable_resize : BoolProperty(
		name='Resize',
		description='Scale down or align the image size',
		default = False
	)
	# nearest/biggest/smallest
	vtf_resize_method : EnumProperty(
		items=blvtf_resize_methods,
		name='Resize Method',
		description='If image is non-power of 2 (e.g. 570x635), then resize it',
		default='NEAREST'
	)


	# Clamp W/H
	vtf_resize_clamp : BoolProperty(
		name='Resize Clamp',
		description='Clamp image dimensions to max height/width',
		default = False
	)
	# W
	vtf_resize_clamp_maxwidth : EnumProperty(
		items=blvtf_applicable_sizes,
		name='Max. Width',
		description='X Dimension',
		default='4096'
		)
	# H
	vtf_resize_clamp_maxheight : EnumProperty(
		items=blvtf_applicable_sizes,
		name='Max. Height',
		description='Y Dimension',
		default='4096'
	)




	# -------
	# Misc
	# -------

	vtf_compute_refl : BoolProperty(
		name='Compute Reflectivity',
		description='Compute Reflectivity',
		default=True
	)




	# -------
	# Flags
	# -------
	vtf_flag_POINTSAMPLE : BoolProperty(
		name='Point Sample',
		description='POINTSAMPLE',
		default = False
		)
	vtf_flag_TRILINEAR : BoolProperty(
		name='Trilinear',
		description='TRILINEAR',
		default = False
		)
	vtf_flag_CLAMPS : BoolProperty(
		name='Clamp S',
		description='CLAMPS',
		default = False
		)
	vtf_flag_CLAMPT : BoolProperty(
		name='Clamp T',
		description='CLAMPT',
		default = False
		)
	vtf_flag_ANISOTROPIC : BoolProperty(
		name='Anisotropic',
		description='ANISOTROPIC',
		default = False
		)
	vtf_flag_HINT_DXT5 : BoolProperty(
		name='Hint DXT5',
		description='HINT_DXT5',
		default = False
		)
	vtf_flag_NORMAL : BoolProperty(
		name='Normal Map',
		description='NORMAL',
		default = False
		)
	vtf_flag_NOMIP : BoolProperty(
		name='No Mipmap',
		description='NOMIP',
		default = False
		)
	vtf_flag_NOLOD : BoolProperty(
		name='No Level Of Detail',
		description='NOLOD',
		default = False
		)
	vtf_flag_MINMIP : BoolProperty(
		name='No Minimum Mipmap',
		description='MINMIP',
		default = False
		)
	vtf_flag_PROCEDURAL : BoolProperty(
		name='Procedural',
		description='PROCEDURAL',
		default = False
		)
	vtf_flag_RENDERTARGET : BoolProperty(
		name='Rendertarget',
		description='RENDERTARGET',
		default = False
		)
	vtf_flag_DEPTHRENDERTARGET: BoolProperty(
		name='Depth Render Target',
		description='DEPTHRENDERTARGET',
		default = False
		)
	vtf_flag_NODEBUGOVERRIDE: BoolProperty(
		name='No Debug Override',
		description='NODEBUGOVERRIDE',
		default = False
		)
	vtf_flag_SINGLECOPY: BoolProperty(
		name='Single Copy',
		description='SINGLECOPY',
		default = False
		)
	vtf_flag_NODEPTHBUFFER: BoolProperty(
		name='No Depth Buffer',
		description='NODEPTHBUFFER',
		default = False
		)
	vtf_flag_CLAMPU: BoolProperty(
		name='Clamp U',
		description='CLAMPU',
		default = False
		)
	vtf_flag_VERTEXTEXTURE: BoolProperty(
		name='Vertex Texture',
		description='VERTEXTEXTURE',
		default = False
		)
	vtf_flag_SSBUMP: BoolProperty(
		name='SSBump',
		description='SSBUMP',
		default = False
		)
	vtf_flag_BORDER: BoolProperty(
		name='Clamp All',
		description='BORDER',
		default = False
		)




class blvtf_shared_image_props_declaration(PropertyGroup):

	# shortcut to display channels Enum in the top right corner
	display_channel : EnumProperty(
		items=blvtf_img_channels,
		name='Display Channel',
		description="""Image Channel to Preview. This doesn't affect export, this is just a shortcut to the dropdown in the top right corner of the editor""",
		# default='COLOR_ALPHA',
		update=blvtf_set_view_channel,
	)


	vtfcmd_ver : EnumProperty(
		items=(
			('new', 'Reloaded', 'Modern converter'),
			('old', 'OG', 'Original converter'),
		),
		name='Encoder Version',
		description='Which VTF encoder version to use. Reloaded (new) is supposedly better in everything',
		default='new'
	)


	vtf_version : EnumProperty(
		items=blvtf_vtf_versions,
		name='VTF Version',
		description='VTF Version to use',
		default = '7.4'
	)


	#
	# Size alignment filters
	#

	# downsample filter
	vtf_resize_filter : EnumProperty(
		items=blvtf_interp_filters,
		name='Resize Filter',
		description='Filter applied when resizing the image',
		default='CUBIC'
	)
	# additional filter
	vtf_resize_sharpen_filter : EnumProperty(
		items=blvtf_sharpen_filters,
		name='Sharpen Filter',
		description='Apply this filter on top of the resized images to make them look sharper',
		default='SHARPENMEDIUM'
	)


	#
	# Mipmap resizing filters
	#

	# downsample filter
	vtf_mipmap_filter : EnumProperty(
		items=blvtf_interp_filters,
		name='Mipmap Filter',
		description='Which filter to use when downscaling the image'
	)
	# additional filter
	vtf_mipmap_sharpen_filter : EnumProperty(
		items=blvtf_sharpen_filters,
		name='Sharpen Filter',
		description='I want to play with lizards tail',
		default='SHARPENSOFT'
	)


	#
	# Other
	#

	# Generate thumbnails
	vtf_generate_thumb : BoolProperty(
		name='Generate Thumbnail',
		description='Generate Thumbnail',
		default=True
	)




class blvtf_batch_convert_property_declaration(PropertyGroup):

	# -------
	# Source/Dest
	# -------

	# souce folder
	batch_folder_input : StringProperty(
		name='Source Folder',
		description='take images from this folder. Supports wildcards (lizard*.png)',
		default = '',
		subtype='DIR_PATH'
	)
	# destination folder
	batch_folder_output : StringProperty(
		name='Destination Folder',
		description='Lizard Sex',
		default = '',
		subtype='DIR_PATH'
	)

	# Recursion
	batch_recursive : BoolProperty(
		name='Recursive',
		description='Enable recursion and structure reconstruction',
		default=False
	)


	# -------
	# Format
	# -------

	# txtmax
	txtmax_enabled : BoolProperty(
		name='Enable TextMax',
		description='TextMax batch syntax shite. This discards any wildcards and resizing present in the source folder path',
		default=False
	)

	txtmax_use_fallback : BoolProperty(
		name='Fallback',
		description="""Don't ignore the rest of the files inside the source folder and apply regular batch options to them (Including wildcard)""",
		default=False
	)

	txtmax_file : PointerProperty(
		name='TxtMax File',
		type=bpy.types.Text
	)


	# VTF format for images with no alpha channel, like DXT1
	vtf_format : EnumProperty(
		items=blvtf_img_formats,
		name='Encoding',
		description='Encoding format to use, the most common ones are DXT1 and DXT5',
		default='DXT1'
	)

	# VTF format for images with an alpha channel
	vtf_format_w_alph : EnumProperty(
		items=blvtf_img_formats,
		name='Encoding if alpha channel is present',
		description='Encoding format to use, if image has an alpha channel',
		default='DXT5'
	)


	# Mipmaps Onn/Off
	vtf_mipmaps_enable : BoolProperty(
		name='Generate Mipmaps',
		description='Whether to generate the mipamps or not',
		default=True
	)




	# -------
	# Resize
	# -------

	# Enable/Disable resizing
	vtf_enable_resize : BoolProperty(
		name='Resize',
		description='Scale down or align the image size',
		default = False
	)
	# nearest/biggest/smallest
	vtf_resize_method : EnumProperty(
		items=blvtf_resize_methods,
		name='Resize Method',
		description='If image is non-power of 2 (e.g. 570x635), then resize it',
		default='NEAREST'
	)

	# Clamp W/H
	vtf_resize_clamp : BoolProperty(
		name='Resize Clamp',
		description='Clamp image dimensions to max height/width',
		default = False
	)
	# W
	vtf_resize_clamp_maxwidth : EnumProperty(
		items=blvtf_applicable_sizes,
		name='Max. Width',
		description='X Dimension',
		default='4096'
		)
	# H
	vtf_resize_clamp_maxheight : EnumProperty(
		items=blvtf_applicable_sizes,
		name='Max. Height',
		description='Y Dimension',
		default='4096'
	)





	# -------
	# Misc
	# -------

	vtf_compute_refl : BoolProperty(
		name='Compute Reflectivity',
		description='Compute Reflectivity',
		default=True
	)






	# -------
	# Flags
	# -------
	vtf_flag_POINTSAMPLE : BoolProperty(
		name='Point Sample',
		description='POINTSAMPLE',
		default = False
		)
	vtf_flag_TRILINEAR : BoolProperty(
		name='Trilinear',
		description='TRILINEAR',
		default = False
		)
	vtf_flag_CLAMPS : BoolProperty(
		name='Clamp S',
		description='CLAMPS',
		default = False
		)
	vtf_flag_CLAMPT : BoolProperty(
		name='Clamp T',
		description='CLAMPT',
		default = False
		)
	vtf_flag_ANISOTROPIC : BoolProperty(
		name='Anisotropic',
		description='ANISOTROPIC',
		default = False
		)
	vtf_flag_HINT_DXT5 : BoolProperty(
		name='Hint DXT5',
		description='HINT_DXT5',
		default = False
		)
	vtf_flag_NORMAL : BoolProperty(
		name='Normal Map',
		description='NORMAL',
		default = False
		)
	vtf_flag_NOMIP : BoolProperty(
		name='No Mipmap',
		description='NOMIP',
		default = False
		)
	vtf_flag_NOLOD : BoolProperty(
		name='No Level Of Detail',
		description='NOLOD',
		default = False
		)
	vtf_flag_MINMIP : BoolProperty(
		name='No Minimum Mipmap',
		description='MINMIP',
		default = False
		)
	vtf_flag_PROCEDURAL : BoolProperty(
		name='Procedural',
		description='PROCEDURAL',
		default = False
		)
	vtf_flag_RENDERTARGET : BoolProperty(
		name='Rendertarget',
		description='RENDERTARGET',
		default = False
		)
	vtf_flag_DEPTHRENDERTARGET: BoolProperty(
		name='Depth Render Target',
		description='DEPTHRENDERTARGET',
		default = False
		)
	vtf_flag_NODEBUGOVERRIDE: BoolProperty(
		name='No Debug Override',
		description='NODEBUGOVERRIDE',
		default = False
		)
	vtf_flag_SINGLECOPY: BoolProperty(
		name='Single Copy',
		description='SINGLECOPY',
		default = False
		)
	vtf_flag_NODEPTHBUFFER: BoolProperty(
		name='No Depth Buffer',
		description='NODEPTHBUFFER',
		default = False
		)
	vtf_flag_CLAMPU: BoolProperty(
		name='Clamp U',
		description='CLAMPU',
		default = False
		)
	vtf_flag_VERTEXTEXTURE: BoolProperty(
		name='Vertex Texture',
		description='VERTEXTEXTURE',
		default = False
		)
	vtf_flag_SSBUMP: BoolProperty(
		name='SSBump',
		description='SSBUMP',
		default = False
		)
	vtf_flag_BORDER: BoolProperty(
		name='Clamp All',
		description='BORDER',
		default = False
		)



























# =========================================================
# ---------------------------------------------------------
#                          GUI
# ---------------------------------------------------------
# =========================================================

#
# Individual params
#
class IMAGE_EDITOR_PT_blvtf_individual_img_params_panel(bpy.types.Panel):
	bl_idname = 'IMAGE_EDITOR_PT_blvtf_individual_img_params_panel'
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'blVTF'
	bl_label = 'Active Image Params'
	# https://youtu.be/sT3joXENOb0

	@classmethod
	def poll(cls, context):
		sima = context.space_data
		return (sima.image)

	def draw(self, context):
		layout = self.layout
		
		# dumpster = layout.column(align=True)
		# dumpster.use_property_split = True
		# dumpster.use_property_decorate = False

		# active image data
		current_img = context.space_data.image
		img_vtf_prms = current_img.blvtf_img_params
		layout.alignment = 'RIGHT'

		layout.row().label(text='Image Channel to Preview')
		layout.row().prop(context.scene.blvtf_exp_params, 'display_channel', expand=True)

		#
		# Main params
		#
		row = layout.row()
		row.prop(img_vtf_prms, 'do_export')
		row.enabled = not current_img.is_embedded_data
		layout.prop(img_vtf_prms, 'vtf_format')
		layout.prop(img_vtf_prms, 'vtf_format_w_alph')

		col = layout.column(align=True)
		col.prop(img_vtf_prms, 'vtf_mipmaps_enable')
		col.prop(img_vtf_prms, 'vtf_compute_refl')

		layout.prop(img_vtf_prms, 'vtf_export_path')

		# renaming
		col = layout.column(align=True)
		col.prop(img_vtf_prms, 'vtf_named_export')
		new_name_row = col.row()
		new_name_row.prop(img_vtf_prms, 'vtf_new_name')
		new_name_row.enabled = img_vtf_prms.vtf_named_export

		# Embed to alpha
		col = layout.column(align=True)
		col.prop(img_vtf_prms, 'embed_to_alpha')
		emb_to_alpha = col.row()
		emb_to_alpha.prop_search(img_vtf_prms, 'image_to_embed', bpy.data, 'images')
		emb_to_alpha.enabled = img_vtf_prms.embed_to_alpha



		#
		# Resizing
		#

		# display a warning if image is of unapplicable size
		if (not current_img.size[0] in blvtf_power_of_two or not current_img.size[1] in blvtf_power_of_two) and not img_vtf_prms.vtf_enable_resize:
			layout.row().label(
				text=f'WARNING: This image is of unapplicable size {tuple(current_img.size)}, enable resizing or this image will be skipped on export'
			)

		col = layout.column(align=True)
		col.prop(img_vtf_prms, 'vtf_enable_resize')
		resize_col = col.column()
		resize_col.enabled = img_vtf_prms.vtf_enable_resize

		resize_col.prop(img_vtf_prms, 'vtf_resize_method')

		resize_col.prop(img_vtf_prms, 'vtf_resize_clamp')

		clamp_col = resize_col.column(align=True)
		clamp_col.prop(img_vtf_prms, 'vtf_resize_clamp_maxwidth')
		clamp_col.prop(img_vtf_prms, 'vtf_resize_clamp_maxheight')
		clamp_col.enabled = img_vtf_prms.vtf_resize_clamp

# Individual flags
class IMAGE_EDITOR_PT_blvtf_individual_img_params_panel_flags(bpy.types.Panel):
	bl_parent_id = 'IMAGE_EDITOR_PT_blvtf_individual_img_params_panel'
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'blVTF'
	bl_label = 'Flags'
	bl_options = {'DEFAULT_CLOSED'}
	# https://youtu.be/sT3joXENOb0

	@classmethod
	def poll(cls, context):
		sima = context.space_data
		return (sima.image)

	def draw(self, context):
		layout = self.layout

		# active image data
		img_vtf_prms = context.space_data.image.blvtf_img_params
		layout.alignment = 'RIGHT'

		#
		# Flags
		#
		col = layout.column(align=True)

		for flg in blvtf_flag_props:
			col.prop(img_vtf_prms, flg)

#
# Shared params
#
class IMAGE_EDITOR_PT_blvtf_shared_img_params_panel(bpy.types.Panel):
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'blVTF'
	bl_label = 'Shared Image Params'
	# https://youtu.be/sT3joXENOb0

	def draw(self, context):
		layout = self.layout

		# dumpster = layout.column(align=True)
		# dumpster.use_property_split = True
		# dumpster.use_property_decorate = False

		# Shared Scene params
		shared_vtf_prms = context.scene.blvtf_exp_params

		convertor_ver = layout.row()
		convertor_ver.prop(shared_vtf_prms, 'vtfcmd_ver', expand=True)

		layout.prop(shared_vtf_prms, 'vtf_version')

		col = layout.column(align=True)
		col.prop(shared_vtf_prms, 'vtf_resize_filter')
		if shared_vtf_prms.vtfcmd_ver == 'old':
			col.prop(shared_vtf_prms, 'vtf_resize_sharpen_filter')

		col = layout.column(align=True)
		col.prop(shared_vtf_prms, 'vtf_mipmap_filter')
		if shared_vtf_prms.vtfcmd_ver == 'old':
			col.prop(shared_vtf_prms, 'vtf_mipmap_sharpen_filter')

		layout.prop(shared_vtf_prms, 'vtf_generate_thumb')

#
# Batch Export
#
class IMAGE_EDITOR_PT_blvtf_batch_export_prms_panel(bpy.types.Panel):
	bl_idname = 'IMAGE_EDITOR_PT_blvtf_batch_export_prms_panel'
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'blVTF'
	bl_label = 'Batch Convert'
	# https://youtu.be/sT3joXENOb0

	def draw(self, context):
		layout = self.layout

		# dumpster = layout.column(align=True)
		# dumpster.use_property_split = True
		# dumpster.use_property_decorate = False

		# Shared Scene params
		batch_vtf_prms = context.scene.blvtf_batch_params

		layout.row().prop(batch_vtf_prms, 'batch_recursive')

		# Input / Output
		col = layout.column(align=True)
		col.prop(batch_vtf_prms, 'batch_folder_input')
		col.prop(batch_vtf_prms, 'batch_folder_output')


		# TextMax
		layout.row().prop(batch_vtf_prms, 'txtmax_enabled')
		if batch_vtf_prms.txtmax_enabled:
			col = layout.column(align=True)
			col.prop(batch_vtf_prms, 'txtmax_use_fallback')
			col.prop(batch_vtf_prms, 'txtmax_file')

			row = col.row()
			row.alignment = 'LEFT'
			row.operator('mesh.blvtf_append_flags_to_txtmax_definition')
			row.enabled = not not batch_vtf_prms.txtmax_file


		# Formats
		col = layout.column(align=True)
		col.prop(batch_vtf_prms, 'vtf_format')
		col.prop(batch_vtf_prms, 'vtf_format_w_alph')
		col.prop(batch_vtf_prms, 'vtf_mipmaps_enable')
		col.prop(batch_vtf_prms, 'vtf_compute_refl')


		#
		# Resizing
		#
		col = layout.column(align=True)
		col.prop(batch_vtf_prms, 'vtf_enable_resize')
		resize_col = col.column()
		resize_col.enabled = batch_vtf_prms.vtf_enable_resize

		resize_col.prop(batch_vtf_prms, 'vtf_resize_method')

		resize_col.prop(batch_vtf_prms, 'vtf_resize_clamp')

		clamp_col = resize_col.column(align=True)
		clamp_col.prop(batch_vtf_prms, 'vtf_resize_clamp_maxwidth')
		clamp_col.prop(batch_vtf_prms, 'vtf_resize_clamp_maxheight')
		clamp_col.enabled = batch_vtf_prms.vtf_resize_clamp

# batch export - Flags
class IMAGE_EDITOR_PT_blvtf_batch_export_prms_panel_flags(bpy.types.Panel):
	bl_parent_id = 'IMAGE_EDITOR_PT_blvtf_batch_export_prms_panel'
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'blVTF'
	bl_label = 'Flags'
	bl_options = {'DEFAULT_CLOSED'}
	# https://youtu.be/sT3joXENOb0

	def draw(self, context):
		layout = self.layout

		# Shared Scene params
		batch_vtf_prms = context.scene.blvtf_batch_params

		col = layout.column(align=True)

		for flg in blvtf_flag_props:
			col.prop(batch_vtf_prms, flg)


#
# Execute functions
#
class IMAGE_EDITOR_PT_blvtf_execute_actions(bpy.types.Panel):
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'blVTF'
	bl_label = 'Execute'
	# https://youtu.be/sT3joXENOb0

	def draw(self, context):
		layout = self.layout
		# img_vtf_prms = context.space_data.image.blvtf_img_params

		active_img = context.space_data.image

		# if active_img:
		row = layout.row()
		row.operator('mesh.blvtf_export_active_img')
		row.enabled = False
		if active_img:
			if not active_img.is_embedded_data:
				row.enabled = True
			else:
				row.enabled = False

		layout.operator('mesh.blvtf_export_marked_imgs')
		layout.operator('mesh.blvtf_folder_export')















rclasses = (
	blvtf_individual_image_props_declaration,
	blvtf_shared_image_props_declaration,
	blvtf_batch_convert_property_declaration,
	IMAGE_EDITOR_PT_blvtf_individual_img_params_panel,
	IMAGE_EDITOR_PT_blvtf_shared_img_params_panel,
	IMAGE_EDITOR_PT_blvtf_individual_img_params_panel_flags,
	IMAGE_EDITOR_PT_blvtf_batch_export_prms_panel,
	IMAGE_EDITOR_PT_blvtf_batch_export_prms_panel_flags,
	IMAGE_EDITOR_PT_blvtf_execute_actions,
	OBJECT_OT_blvtf_export_active_img,
	OBJECT_OT_blvtf_export_marked_imgs,
	OBJECT_OT_blvtf_folder_convert,
	OBJECT_OT_blvtf_append_flags_to_txtmax_definition
)

register_, unregister_ = bpy.utils.register_classes_factory(rclasses)

def register():
	register_()

	bpy.types.Image.blvtf_img_params = PointerProperty(type=blvtf_individual_image_props_declaration)
	bpy.types.Scene.blvtf_exp_params = PointerProperty(type=blvtf_shared_image_props_declaration)
	bpy.types.Scene.blvtf_batch_params = PointerProperty(type=blvtf_batch_convert_property_declaration)



def unregister():
	unregister_()
	# del bpy.types.Image.hobo_image_params



