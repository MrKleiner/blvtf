bl_info = {
	'name': 'Blender VTF',
	'author': 'MrKleiner',
	'version': (0, 15),
	'blender': (3, 4, 1),
	'location': 'N menu',
	'description': """VTF Edit GUI in Blender""",
	'doc_url': '',
	'category': 'Add Mesh',
}







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
magix_exe = addon_root_dir / 'bins' / 'imgmagick' / 'magick.exe'







# =========================================================
# ---------------------------------------------------------
#                   Applicable entries
# ---------------------------------------------------------
# =========================================================


blvtf_interp_filters = [
	('Point', 'Point', 'ded2'),
	('Box', 'Box', 'ded2'),
	('Triangle', 'Triangle', 'ded2'),
	('Quadratic', 'Quadratic', 'ded2'),
	('Cubic', 'Cubic', 'ded2'),
	('Catrom', 'Catrom', 'ded2'),
	('Mitchell', 'Mitchell', 'ded2'),
	('Gaussian', 'Gaussian', 'ded2'),
	('Sinc', 'Sinc', 'ded2'),
	('Bessel', 'Bessel', 'ded2'),
	('Hanning', 'Hanning', 'ded2'),
	('Hamming', 'Hamming', 'ded2'),
	('Blackman', 'Blackman', 'ded2'),
	('Kaiser', 'Kaiser', 'ded2')
]

blvtf_sharpen_filters = [
	('None', 'None', 'ded2'),
	('Negative', 'Negative', 'ded2'),
	('Lighter', 'Lighter', 'ded2'),
	('Darker', 'Darker', 'ded2'),
	('Contrast More', 'Contrast More', 'ded2'),
	('Contrast Less', 'Contrast Less', 'ded2'),
	('Smoothen', 'Smoothen', 'ded2'),
	('Sharpen Soft', 'Sharpen Soft', 'ded2'),
	('Sharpen Medium', 'Sharpen Medium', 'ded2'),
	('Sharpen Strong', 'Sharpen Strong', 'ded2'),
	('Find Edges', 'Find Edges', 'ded2'),
	('Contour', 'Contour', 'ded2'),
	('Edge Detect', 'Edge Detect', 'ded2'),
	('Edge Detect Soft', 'Edge Detect Soft', 'ded2'),
	('Emboss', 'Emboss', 'ded2'),
	('Mean Removal', 'Mean Removal', 'ded2'),
	('Unsharpen Mask', 'Unsharpen Mask', 'ded2'),
	('XSharpen', 'XSharpen', 'ded2'),
	('Warp Sharp', 'Warp Sharp', 'ded2'),
]

blvtf_applicable_sizes = [
	('4096', '4096', 'ded2'),
	('2048', '2048', 'ded2'),
	('1024', '1024', 'ded2'),
	('512', '512', 'ded2'),
	('256', '256', 'ded2'),
	('128', '128', 'ded2'),
	('64', '64', 'ded2'),
	('32', '32', 'ded2'),
	('16', '16', 'ded2'),
	('8', '8', 'ded2'),
	('4', '4', 'ded2'),
	('2', '2', 'ded2'),
	# ('1', '1', 'ded2'),
]

blvtf_img_formats = [
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
]

blvtf_vtf_versions = [
	('7.5', '7.5', 'The latest, released with Alien Swarm, not supported in everything below Alien Swarm'),
	('7.4', '7.4', 'Released with Orange Box, the one used by current 2013SDK, tf2, etc.'),
	('7.3', '7.3', 'Released with tf2'),
	('7.2', '7.2', 'Small update after hl2 release'),
	('7.1', '7.1', 'Released with hl2 (dinosaurs themselves used this)'),
]


blvtf_vtf_flags = [
	('Point Sample', 'Point Sample', 'ded2'),
	('Trilinear', 'Trilinear', 'ded2'),
	('Clamp S', 'Clamp S', 'ded2'),
	('Clamp T', 'Clamp T', 'ded2'),
	('Anisotropic', 'Anisotropic', 'ded2'),
	('Hint DXT5', 'Hint DXT5', 'ded2'),
	('Normal Map', 'Normal Map', 'ded2'),
	('No Mipmap', 'No Mipmap', 'ded2'),
	('No Level Of Detail', 'No Level Of Detail', 'ded2'),
	('No Minimum Mipmap', 'No Minimum Mipmap', 'ded2'),
	('Procedural', 'Procedural', 'ded2'),
	('Rendertarget', 'Rendertarget', 'ded2'),
	('Depth Render Target', 'Depth Render Target', 'ded2'),
	('No Debug Override', 'No Debug Override', 'ded2'),
	('Single Copy', 'Single Copy', 'ded2'),
	('No Depth Buffer', 'No Depth Buffer', 'ded2'),
	('Clamp U', 'Clamp U', 'ded2'),
	('Vertex Texture', 'Vertex Texture', 'ded2'),
	('SSBump', 'SSBump', 'ded2'),
	('Clamp All', 'Clamp All', 'ded2'),
]














# =========================================================
# ---------------------------------------------------------
#                  Actual shit. Functions
# ---------------------------------------------------------
# =========================================================

def ensure_addon_setup():
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


ensure_addon_setup()






















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
		name='Export here',
		description='Export the fucking shit',
		default='nil',
		subtype='DIR_PATH'
	)

	# Re-Assign names
	vtf_named_export: BoolProperty(
		name='Rename',
		description='Rename resulting VTF to the specified name. Else - use image datablock name',
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
		items=[
			('Nearest Power Of 2', 'Nearest Power Of 2', '1023 -> 1024, 570 -> 512'),
			('Biggest Power of 2', 'Biggest Power of 2', '1023 -> 1024, 570 -> 1024'),
			('Smallest Power of 2', 'Smallest Power of 2', '1023 -> 512, 570 -> 1024')
		],
		name='Resize Method',
		description='If image is non-power of 2 (e.g. 570x635), then resize it',
		default='Nearest Power Of 2'
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
		name='Maximum Width',
		description='Dimensions',
		# default = "nil"
		)
	# H
	vtf_resize_clamp_maxheight : EnumProperty(
		items=blvtf_applicable_sizes,
		name='Maximum Height',
		description='Dimensions'
		# default = "nil"
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
		description='Point Sample',
		default = False
		)
	vtf_flag_TRILINEAR : BoolProperty(
		name='Trilinear',
		description='Point Sample',
		default = False
		)
	vtf_flag_CLAMPS : BoolProperty(
		name='Clamp S',
		description='Point Sample',
		default = False
		)
	vtf_flag_CLAMPT : BoolProperty(
		name='Clamp T',
		description='Point Sample',
		default = False
		)
	vtf_flag_ANISOTROPIC : BoolProperty(
		name='Anisotropic',
		description='Point Sample',
		default = False
		)
	vtf_flag_HINT_DXT5 : BoolProperty(
		name='Hint DXT5',
		description='Hint DXT5',
		default = False
		)
	vtf_flag_NORMAL : BoolProperty(
		name='Normal Map',
		description='Normal Map',
		default = False
		)
	vtf_flag_NOMIP : BoolProperty(
		name='No Mipmap',
		description='No Mipmap',
		default = False
		)
	vtf_flag_NOLOD : BoolProperty(
		name='No Level Of Detail',
		description='No Level Of Detail',
		default = False
		)
	vtf_flag_MINMIP : BoolProperty(
		name='No Minimum Mipmap',
		description='No Minimum Mipmap',
		default = False
		)
	vtf_flag_PROCEDURAL : BoolProperty(
		name='Procedural',
		description='Procedural',
		default = False
		)
	vtf_flag_RENDERTARGET : BoolProperty(
		name='Rendertarget',
		description='Rendertarget',
		default = False
		)
	vtf_flag_DEPTHRENDERTARGET: BoolProperty(
		name='Depth Render Target',
		description='Depth Render Target',
		default = False
		)
	vtf_flag_NODEBUGOVERRIDE: BoolProperty(
		name='No Debug Override',
		description='No Debug Override',
		default = False
		)
	vtf_flag_SINGLECOPY: BoolProperty(
		name='Single Copy',
		description='Single Copy',
		default = False
		)
	vtf_flag_NODEPTHBUFFER: BoolProperty(
		name='No Depth Buffer',
		description='No Depth Buffer',
		default = False
		)
	vtf_flag_CLAMPU: BoolProperty(
		name='Clamp U',
		description='Clamp U',
		default = False
		)
	vtf_flag_VERTEXTEXTURE: BoolProperty(
		name='Vertex Texture',
		description='Vertex Texture',
		default = False
		)
	vtf_flag_SSBUMP: BoolProperty(
		name='SSBump',
		description='SSBump',
		default = False
		)
	vtf_flag_BORDER: BoolProperty(
		name='Clamp All',
		description='Clamp All',
		default = False
		)





class blvtf_shared_image_props_declaration(PropertyGroup):
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
		default='Cubic'
	)
	# additional filter
	vtf_resize_sharpen_filter : EnumProperty(
		items=blvtf_sharpen_filters,
		name='Sharpen Filter',
		description='Apply this filter on top of the resized images to make them look sharper',
		default='Sharpen Medium'
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
		default='Sharpen Soft'
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




	# -------
	# Format
	# -------

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
		items=[
			('Nearest Power Of 2', 'Nearest Power Of 2', '1023 -> 1024, 570 -> 512'),
			('Biggest Power of 2', 'Biggest Power of 2', '1023 -> 1024, 570 -> 1024'),
			('Smallest Power of 2', 'Smallest Power of 2', '1023 -> 512, 570 -> 1024')
		],
		name='Resize Method',
		description='If image is non-power of 2 (e.g. 570x635), then resize it',
		default='Nearest Power Of 2'
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
		name='Maximum Width',
		description='Dimensions',
		# default = "nil"
		)
	# H
	vtf_resize_clamp_maxheight : EnumProperty(
		items=blvtf_applicable_sizes,
		name='Maximum Height',
		description='Dimensions'
		# default = "nil"
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
		description='Point Sample',
		default = False
		)
	vtf_flag_TRILINEAR : BoolProperty(
		name='Trilinear',
		description='Point Sample',
		default = False
		)
	vtf_flag_CLAMPS : BoolProperty(
		name='Clamp S',
		description='Point Sample',
		default = False
		)
	vtf_flag_CLAMPT : BoolProperty(
		name='Clamp T',
		description='Point Sample',
		default = False
		)
	vtf_flag_ANISOTROPIC : BoolProperty(
		name='Anisotropic',
		description='Point Sample',
		default = False
		)
	vtf_flag_HINT_DXT5 : BoolProperty(
		name='Hint DXT5',
		description='Hint DXT5',
		default = False
		)
	vtf_flag_NORMAL : BoolProperty(
		name='Normal Map',
		description='Normal Map',
		default = False
		)
	vtf_flag_NOMIP : BoolProperty(
		name='No Mipmap',
		description='No Mipmap',
		default = False
		)
	vtf_flag_NOLOD : BoolProperty(
		name='No Level Of Detail',
		description='No Level Of Detail',
		default = False
		)
	vtf_flag_MINMIP : BoolProperty(
		name='No Minimum Mipmap',
		description='No Minimum Mipmap',
		default = False
		)
	vtf_flag_PROCEDURAL : BoolProperty(
		name='Procedural',
		description='Procedural',
		default = False
		)
	vtf_flag_RENDERTARGET : BoolProperty(
		name='Rendertarget',
		description='Rendertarget',
		default = False
		)
	vtf_flag_DEPTHRENDERTARGET: BoolProperty(
		name='Depth Render Target',
		description='Depth Render Target',
		default = False
		)
	vtf_flag_NODEBUGOVERRIDE: BoolProperty(
		name='No Debug Override',
		description='No Debug Override',
		default = False
		)
	vtf_flag_SINGLECOPY: BoolProperty(
		name='Single Copy',
		description='Single Copy',
		default = False
		)
	vtf_flag_NODEPTHBUFFER: BoolProperty(
		name='No Depth Buffer',
		description='No Depth Buffer',
		default = False
		)
	vtf_flag_CLAMPU: BoolProperty(
		name='Clamp U',
		description='Clamp U',
		default = False
		)
	vtf_flag_VERTEXTEXTURE: BoolProperty(
		name='Vertex Texture',
		description='Vertex Texture',
		default = False
		)
	vtf_flag_SSBUMP: BoolProperty(
		name='SSBump',
		description='SSBump',
		default = False
		)
	vtf_flag_BORDER: BoolProperty(
		name='Clamp All',
		description='Clamp All',
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
		img_vtf_prms = context.space_data.image.blvtf_img_params
		layout.alignment = 'RIGHT'

		#
		# Main params
		#
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

		layout.prop(shared_vtf_prms, 'vtf_version')

		col = layout.column(align=True)
		col.prop(shared_vtf_prms, 'vtf_resize_filter')
		col.prop(shared_vtf_prms, 'vtf_resize_sharpen_filter')

		col = layout.column(align=True)
		col.prop(shared_vtf_prms, 'vtf_mipmap_filter')
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


		col = layout.column(align=True)
		col.prop(batch_vtf_prms, 'batch_folder_input')
		col.prop(batch_vtf_prms, 'batch_folder_output')


		col = layout.column(align=True)
		col.prop(batch_vtf_prms, 'vtf_format')
		col.prop(batch_vtf_prms, 'vtf_format_w_alph')
		col.prop(batch_vtf_prms, 'vtf_mipmaps_enable')
		col.prop(batch_vtf_prms, 'vtf_compute_refl')

# batch export Flags
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





















rclasses = (
	blvtf_individual_image_props_declaration,
	blvtf_shared_image_props_declaration,
	blvtf_batch_convert_property_declaration,
	IMAGE_EDITOR_PT_blvtf_individual_img_params_panel,
	IMAGE_EDITOR_PT_blvtf_shared_img_params_panel,
	IMAGE_EDITOR_PT_blvtf_individual_img_params_panel_flags,
	IMAGE_EDITOR_PT_blvtf_batch_export_prms_panel,
	IMAGE_EDITOR_PT_blvtf_batch_export_prms_panel_flags
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