import bpy

import subprocess, shutil, math

from pathlib import Path

from bpy.props import (
	StringProperty,
	BoolProperty,
	IntProperty,
	EnumProperty,
	PointerProperty,
)
from bpy.types import (
	Panel,
	Operator,
	AddonPreferences,
	PropertyGroup,
)

from .simple_vmt import simple_vmt


addon_root_dir = Path(__file__).parent
vtfcmd_exe = addon_root_dir / 'bins' / 'vtfcmd' / 'VTFCmd.exe'
vtfcmd_exe_old = addon_root_dir / 'bins' / 'vtfcmd_old' / 'VTFCmd.exe'
magix_exe = addon_root_dir / 'bins' / 'imgmagick' / 'magick.exe'
tmp_folder = addon_root_dir / 'tmps'









# =========================================================
# ---------------------------------------------------------
#                   Base functionality
# ---------------------------------------------------------
# =========================================================

class blvtf_skybox_progress_report:
	"""What the fuck, Blender?"""
	def __init__(self, prog_min=0, prog_max=24):
		self.wm = bpy.context.window_manager
		self.pmin = prog_min
		self.pmax = prog_max

	def __enter__(self):
		self.wm.progress_begin(self.pmin, self.pmax)
		return self.update

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.wm.progress_end()

	def update(self, prog):
		self.wm.progress_update(prog)



def blvtf_skybox_maker_cleanup():
	try:
		targets = [
			bpy.data.cameras,
			bpy.data.objects,
			bpy.data.images,
		]

		for dtblock_list in targets:
			for datablock in dtblock_list:
				if datablock.get('_blvtf_cleanup_todelete'):
					dtblock_list.remove(datablock)

		for tgt_scene in bpy.data.scenes:
			if 'blfoil_skyboxer_settings_save' in tgt_scene:

				defdict = tgt_scene['blfoil_skyboxer_settings_save']

				tgt_scene.render.resolution_x = defdict['res_x']
				tgt_scene.render.resolution_y = defdict['res_y']
				tgt_scene.render.resolution_percentage = defdict['res_perc']

				tgt_scene.render.pixel_aspect_x = defdict['aspectx']
				tgt_scene.render.pixel_aspect_y = defdict['aspecty']

				tgt_scene.render.use_border = defdict['render_region']

				# Colour management
				tgt_scene.display_settings.display_device = defdict['display_device']
				tgt_scene.view_settings.view_transform = defdict['view_transform']
				tgt_scene.view_settings.look = defdict['look']
				tgt_scene.view_settings.exposure = defdict['exposure']
				tgt_scene.view_settings.gamma = defdict['gamma']


				# Output mode
				tgt_scene.render.filepath = defdict['render_filepath']
				tgt_scene.render.use_file_extension = defdict['use_file_extension']
				tgt_scene.render.use_render_cache = defdict['use_render_cache']
				tgt_scene.render.image_settings.file_format = defdict['file_format']
				tgt_scene.render.image_settings.color_mode = defdict['color_mode']
				tgt_scene.render.use_overwrite = defdict['use_overwrite']
				tgt_scene.render.use_placeholder = defdict['use_placeholder']
				tgt_scene.render.image_settings.color_depth = defdict['img_color_depth']
				tgt_scene.render.image_settings.exr_codec = defdict['exr_codec']
				tgt_scene.render.image_settings.use_preview = defdict['use_preview']
				tgt_scene.render.use_compositing = defdict['use_compositing']
				tgt_scene.render.use_sequencer = defdict['use_sequencer']
				tgt_scene.render.dither_intensity = defdict['dither_intensity']

				tgt_scene.camera = defdict['camera']

				del tgt_scene['blfoil_skyboxer_settings_save']
	except Exception as e:
		print('Please report this bug that occured in blvtf to github:', e)
		return





def blvtf_skybox_maker(tgt_scene):
	# exception raiser
	# todo: get rid of this ?
	def except_raiser(details=''):
		# self.report({'WARNING'}, 'Game path invalid, go kys, fucker: Unable to locate vtex.exe')
		raise Exception("""Something's very wrong: """ + str(details))


	# Blender render
	# LDR tga
	# HDR tga
	# PFM
	# VTF
	# Skybox settings
	sk_settings = tgt_scene.blvtf_skyboxer_params

	with blvtf_skybox_progress_report(prog_max=(24 if sk_settings.hdrldr != 'HDR' else 30)) as prog_report:

		# Absolute path to the current blend file
		this_blend = bpy.path.abspath('//')

		# Path to magick.exe image converter
		magix = addon_root_dir / 'bins' / 'imgmagick' / 'magick.exe'


		# Check if game path exists. If not - stop script execution and throw a warning
		# but first - check if we use SourceOps Game path and if SourceOps is available at all
		# check if we use source ops
		# todo: YES, "try:" allows to go straight to the point istead of checking every part of the chain
		# All that matters is if there's a valid game or not, the presence or abscense of SourceOps doesn't say anything 
		if sk_settings.use_sourceops_gpath == True:
			try:
				sky_foil_gpath = tgt_scene.sourceops.game_items[tgt_scene.sourceops.game_index]['game']
			except:
				except_raiser('It was requested to use SourceOps game path, but SourceOps could not be located OR game is invalid')
		else:
			sky_foil_gpath = bpy.path.abspath(sk_settings.game_path)

		# Path to 'Half-Life 2/ep2'
		game_path = Path(bpy.path.abspath(sky_foil_gpath))

		# vtex has to be present. Else - can't do shit
		vtex_path = game_path.parent / 'bin' / 'vtex.exe'
		print(str(vtex_path))
		if not vtex_path.is_file():
			except_raiser('Game path invalid, go kys: Unable to locate vtex.exe')


		sky_is_rect = sk_settings.halfsize

		sky_dimx = int(sk_settings.size)
		sky_dimy = int(sky_dimx / 2 if sky_is_rect else None or sky_dimx)


		# Check the destination folder condition: If exists, but overwrite is False - stop and throw error
		dest_folder = game_path / 'materialsrc' / 'skybox' / sk_settings.sky_name

		if dest_folder.is_dir() and sk_settings.overwrite_shit == False:
			except_raiser('Skybox destination folder exists, but overwrite is set to False')


		# delete materialsrc dir if any
		shutil.rmtree(str(dest_folder), ignore_errors=True)


		# Overengineering shit again ?!
		destinations = [
			sk_settings.sky_name + '_exr_src',
			sk_settings.sky_name + '_generated_pfm',
			sk_settings.sky_name + '_tga_src'
		]
		for ds in destinations:
			(dest_folder / ds).mkdir(parents=True, exist_ok=True)


		# Save scene settings
		# todo: some stuff is missing
		tgt_scene['blfoil_skyboxer_settings_save'] = {
			# Dimensions
			'res_x': 	tgt_scene.render.resolution_x,
			'res_y': 	tgt_scene.render.resolution_y,
			'res_perc': tgt_scene.render.resolution_percentage,
			
			'aspectx': tgt_scene.render.pixel_aspect_x,
			'aspecty': tgt_scene.render.pixel_aspect_y,
			
			'render_region': tgt_scene.render.use_border,

			# Colour management
			'display_device': 	tgt_scene.display_settings.display_device,
			'view_transform': 	tgt_scene.view_settings.view_transform,
			'look': 			tgt_scene.view_settings.look,
			'exposure': 		tgt_scene.view_settings.exposure,
			'gamma': 			tgt_scene.view_settings.gamma,

			
			# Output mode
			'render_filepath': 		tgt_scene.render.filepath,
			'use_file_extension': 	tgt_scene.render.use_file_extension,
			'use_render_cache': 	tgt_scene.render.use_render_cache,
			'file_format': 			tgt_scene.render.image_settings.file_format,
			'color_mode': 			tgt_scene.render.image_settings.color_mode,
			'use_overwrite': 		tgt_scene.render.use_overwrite,
			'use_placeholder': 		tgt_scene.render.use_placeholder,
			'img_color_depth': 		tgt_scene.render.image_settings.color_depth,
			'exr_codec': 			tgt_scene.render.image_settings.exr_codec,
			'use_preview': 			tgt_scene.render.image_settings.use_preview,
			'use_compositing': 		tgt_scene.render.use_compositing,
			'use_sequencer': 		tgt_scene.render.use_sequencer,
			'dither_intensity': 	tgt_scene.render.dither_intensity,
			
			'camera': tgt_scene.camera
		}

		tgt_scene.view_settings.view_transform = sk_settings.ldr_colorspace

		# sidez = ['bk:90:0:-90', 'dn:0:0:-180', 'ft:90:0:90', 'lf:90:0:0', 'rt:90:0:-180', 'up:180:0:180']
		"""
		sidez = {
			'bk': (90, 0, -90),
			'dn': (0, 0, -180),
			'ft': (90, 0, 90),
			'lf': (90, 0, 0),
			'rt': (90, 0, -180),
			'up': (180, 0, 180)
		}
		"""

		# sky_is_rect = sky_dimy == sky_dimx / 2
		# sky_is_rect = sk_settings.halfsize
		# sky_dim

		# important: if not square and NOT a proper rectangle - stop
		# firstly - Y cannot be bigger than x
		# secondly - if X Y are not the same, check if triangle is proper
		# if sky_dimy > sky_dimx or (sky_dimy != sky_dimx and not sky_is_rect):
		#     except_raiser('Invalid sky size setup!')
		# Update: Now it cannot be otherwise: There's a set of dimensions you can have on X axis 
		# and a checkbox whether to half it on Y or not

		# better order so that it looks cooler visually in app
		# (the sides are being rendered and processed in this order)
		sidez = {
			'ft': (90, 0, 90),
			'lf': (90, 0, 0),
			'bk': (90, 0, -90),
			'up': (180, 0, 180),
			'rt': (90, 0, -180),
			'dn': (0, 0, -180)
		}

		# size dict
		side_sizes = {
			'ft': (sky_dimx, sky_dimy),
			'lf': (sky_dimx, sky_dimy),
			'bk': (sky_dimx, sky_dimy),
			'up': (sky_dimx, sky_dimx),
			'rt': (sky_dimx, sky_dimy),
			# 8 if nobottom or side is a rect else - defaults
			'dn': (8 if sk_settings.nobottom or sky_is_rect else sky_dimx, 8 if sk_settings.nobottom or sky_is_rect else sky_dimx)
		}

		# cam shift dict
		camshift = {
			'ft': 0.25 if sky_is_rect else 0,
			'lf': 0.25 if sky_is_rect else 0,
			'bk': 0.25 if sky_is_rect else 0,
			'up': 0,
			'rt': 0.25 if sky_is_rect else 0,
			'dn': 0
		}

		# create camera
		sky_camera_data = bpy.data.cameras.new(name='blvtf_skybox_maker_camera_data')
		
		sky_camera_data.type = 'PERSP'
		sky_camera_data.clip_end = 100000.0
		
		# Magic numbers
		sky_camera_data.lens = 64
		sky_camera_data.sensor_width = 128.5
		
		sky_camera_object = bpy.data.objects.new('blvtf_skybox_maker_camera', sky_camera_data)
		tgt_scene.collection.objects.link(sky_camera_object)
		# mark for deleteion, just in case
		sky_camera_object['_blvtf_cleanup_todelete'] = True

		# make this camera active
		tgt_scene.camera = sky_camera_object

		# Render each side into .exr OR .tga
		for side_idx, side in enumerate(sidez):
			prog_report(side_idx)


			# Set camera rotation
			csidex = sidez[side][0]
			csidey = sidez[side][1]
			csidez = sidez[side][2]

			sky_camera_object.rotation_euler[0] = math.radians(csidex)
			sky_camera_object.rotation_euler[1] = math.radians(csidey)
			sky_camera_object.rotation_euler[2] = math.radians(csidez)


			#
			# Setup camera and render settings
			#

			# render size
			tgt_scene.render.resolution_x = side_sizes[side][0]
			tgt_scene.render.resolution_y = side_sizes[side][1]

			# camera shift
			sky_camera_data.shift_y = camshift[side]
			sky_camera_data.shift_x = 0
			
			
			# set output prefs
			if sk_settings.hdrldr == 'HDR':
				tgt_scene.render.filepath = str(dest_folder / (sk_settings.sky_name + '_exr_src') / (sk_settings.sky_name + side + '.exr'))
				tgt_scene.render.image_settings.file_format = 'OPEN_EXR'
				tgt_scene.render.image_settings.color_mode = 'RGB'
				tgt_scene.render.image_settings.color_depth = '32'
				tgt_scene.render.image_settings.exr_codec = 'ZIP'
				tgt_scene.render.image_settings.use_preview = False
			else:
				tgt_scene.render.filepath = str(dest_folder / (sk_settings.sky_name + '_tga_src') / (sk_settings.sky_name + side + '.tga'))
				tgt_scene.render.image_settings.file_format = 'TARGA_RAW'
				tgt_scene.render.image_settings.color_mode = 'RGB'
				
			tgt_scene.render.use_file_extension = True
			tgt_scene.render.use_render_cache = False
			tgt_scene.render.use_overwrite = True
			tgt_scene.render.use_placeholder = False

			# set sequencer to false and dither to 1
			tgt_scene.render.use_sequencer = False
			tgt_scene.render.use_compositing = True
			tgt_scene.render.dither_intensity = 1.0


			# Do Render
			bpy.ops.render.render(write_still=1)
			
			

			# AFTER done rendering, check if HDR then we need stupid LDR fallbacks
			# fuck them really - downscale them fuckers by a factor of fucking 2
			# simply re-save it with blender
			# important todo: it seems like the image is not being downscaled when saving as render
			if sk_settings.hdrldr == 'HDR':

				# Set export settings to .png
				tgt_scene.render.image_settings.file_format = 'TARGA_RAW'
				tgt_scene.render.image_settings.color_mode = 'RGB'
				# tgt_scene.render.image_settings.compression = 15

				# half the resolution
				tgt_scene.render.resolution_x = int(tgt_scene.render.resolution_x / 2)
				tgt_scene.render.resolution_y = int(tgt_scene.render.resolution_y / 2)

				# set filepath
				# tgt_scene.render.filepath = str(game_path / 'materialsrc' / 'skybox' / sk_settings.sky_name / (sk_settings.sky_name + '_tga_src') / (sk_settings.sky_name + side + '.tga'))

				# load resulting .exr or
				apply_filmic = bpy.data.images.load(str(dest_folder / (sk_settings.sky_name + '_exr_src') / (sk_settings.sky_name + side + '.exr')))
				apply_filmic['_blvtf_cleanup_todelete'] = True

				# export exr with filmic applied
				apply_filmic.save_render(str(dest_folder / (sk_settings.sky_name + '_tga_src') / (sk_settings.sky_name + side + '.tga')))

				# unlink rubbish
				bpy.data.images.remove(apply_filmic)




		# Remove camera once done rendering
		bpy.data.objects.remove(sky_camera_object)


		# Make some paths for later use
		vtex_exe = game_path.parent / 'bin' / 'vtex.exe'
		vtex_outdir = game_path / 'materials' / 'skybox' / sk_settings.sky_name


		#
		# create pfms and text files for vtex.exe
		#

		# clean output directory
		shutil.rmtree(str(vtex_outdir), ignore_errors=True)


		for tside_idx, tside in enumerate(sidez):
			# construct pfm output
			# todo: shorten game_path / 'materialsrc' / 'skybox' /
			# or even
			# game_path / 'materialsrc' / 'skybox' / sk_settings.sky_name / sk_settings.sky_name
			pfmoutpath = dest_folder / (sk_settings.sky_name + '_generated_pfm') / (sk_settings.sky_name + '_hdr' + tside + '.pfm')
		
			# construct exr inp path
			exrinpath = dest_folder / (sk_settings.sky_name + '_exr_src') / (sk_settings.sky_name + tside + '.exr')
		


			# Literally the heart of this exporter: Converting .exr to PROPER .pfms
			# -endian LSB !!!!!
			print(magix)

			prog_report(tside_idx + 6)
			if sk_settings.hdrldr == 'HDR':
				# convert with image magick 
				magic_args = [str(magix), exrinpath, '-endian', 'LSB', pfmoutpath]
				subprocess.call(magic_args)


			# write text file for vtex
			# todo: create a class for vtex manipulations
			# todo: create a class for imgmagick manips

			# important todo: Portal 2 cannot have ignorez 1
			
			# HDR
			# todo: this still lacks common sense
			# just move this inside if HDR ??
			text_file_content = [
				'nolod 1',
				'nomip 1',
				# important todo: wtf is actually nonice ???? What EXACTLY does it do ?
				'nonice 1' if sky_dimx > 256 else '',
				'pfm 1' if sk_settings.hdrldr == 'HDR' else '',
				'pfmscale 1' if sk_settings.hdrldr == 'HDR' else '',
				# Not specifying nocompress 1 automatically means that it will be compressed
				'nocompress 1' if sk_settings.hdrldr == 'HDR' and sk_settings.hdr_compressed == False else '',
				# Rectangle skyboxes should not repeat. Clamp
				'clamps 1',
				'clampt 1',
				'pointsample 1' if sk_settings.hdr_compressed == True else '',
			]

			# ' '.join(filter(None, strings))

			# vmt_content = [
			#     '"sky"',
			#     '{',
			#     '',
			#     '}'
			# ]

			

			# There are always targas
			# this is static for now
			# (till there's a noz 1 switch)
			ldr_tga_txt = [
				'nolod 1',
				'clamps 1',
				'clampt 1',
				'nomip 1',
				'nonice 1',
				'nocompress 1'
			]

			vmtbasepath = Path('skybox') / sk_settings.sky_name / sk_settings.sky_name

			# Additional conversions if there's HDR
			if sk_settings.hdrldr == 'HDR':
				txtfile_path = dest_folder / (sk_settings.sky_name + '_generated_pfm') / (sk_settings.sky_name + '_hdr' + tside + '.txt')

				# Write the vtex text file for HDR
				with open(str(txtfile_path), 'w') as txtfile:
					# join in a specific way because there are empty entries
					txtfile.write('\n'.join(filter(None, text_file_content)))

				# convert HDR .pfm to .vtf
				vtex_args = [str(vtex_exe), '-nopause', '-outdir', vtex_outdir, txtfile_path]
				prog_report(tside_idx + 6 + 1)
				subprocess.call(vtex_args)

				# write VMT

				hdr_vmt = simple_vmt()
				# HDR skybox uses "sky" shader
				hdr_vmt.shader = 'sky'
				hdr_vmt.setparams({
					# LDR fallback
					'basetexture': str(vmtbasepath) + tside,
					# HDR shit
					'hdrcompressedtexture' if sk_settings.hdr_compressed else 'hdrbasetexture': str(vmtbasepath) + '_hdr' + tside,
					# transform. If sky is rectangular and if current side is not down or up
					'basetexturetransform': 'center 0 0 scale 1 2 rotate 0 translate 0 0' if sky_is_rect and tside != 'up' and tside != 'dn' else None 
				})

				# write resulting vmt
				with open(str(vtex_outdir / (sk_settings.sky_name + '_hdr' + tside + '.vmt')), 'w') as vmtfile:
					vmtfile.write(hdr_vmt.to_vmt())



			# write LDR (which should always be there)
			# basically, targas are always there
			txtfile_path = str(dest_folder / (sk_settings.sky_name + '_tga_src') / (sk_settings.sky_name + tside + '.txt'))
			with open(txtfile_path, 'w') as txtfile:
				txtfile.write('\n'.join(filter(None, ldr_tga_txt)))


			# convert Targas tp vtf
			vtex_args = [str(vtex_exe), '-nopause', '-outdir', vtex_outdir, txtfile_path]
			prog_report(tside_idx + 6 + (2 if sk_settings.hdrldr == 'HDR' else 1))
			subprocess.call(vtex_args)


			# write LDR VMT

			ldr_vmt = simple_vmt()
			# LDR skies use UnlitGeneric
			ldr_vmt.shader = 'UnlitGeneric'
			ldr_vmt.setparams({
				'nofog': 1,
				# important todo: Portal 2 SHOULD NOT HAVE ignorez
				'ignorez': 1,
				'basetexture': str(vmtbasepath) + tside,
				# transform. If sky is rectangular and if current side is not down or up
				'basetexturetransform': 'center 0 0 scale 1 2 rotate 0 translate 0 0' if sky_is_rect and tside != 'up' and tside != 'dn' else None 
			})

			# write resulting vmt
			with open(str(vtex_outdir / (sk_settings.sky_name + tside + '.vmt')), 'w') as vmtfile:
				vmtfile.write(ldr_vmt.to_vmt())






























# =========================================================
# ---------------------------------------------------------
#                       Operators
# ---------------------------------------------------------
# =========================================================

# Full skybox export

class OBJECT_OT_blvtf_full_skybox_compile(bpy.types.Operator):
	bl_idname = 'mesh.blvtf_exec_compile_skybox'
	bl_label = 'Compile skybox'
	# bl_options = {'REGISTER'}

	def execute(self, context):

		# cleanup from the last time
		blvtf_skybox_maker_cleanup()

		# execute the conversion
		# thr = threading.Thread(target=blvtf_skybox_maker, args=(context.scene,), daemon=True).start()
		blvtf_skybox_maker(context.scene)

		# cleanup
		blvtf_skybox_maker_cleanup()

		return {'FINISHED'}











# =========================================================
# ---------------------------------------------------------
#                       PROPERTIES
# ---------------------------------------------------------
# =========================================================


# 
# Dedicated and shared params, like brush material and special entity config, like light/light_spot properties 
#

class blvtf_skyboxer_properties_declaration(PropertyGroup):
	# -----------------------------------
	#              Skyboxer
	# -----------------------------------
	game_path : StringProperty(
		name='Path to the game directory. Such as "/half-life 2/ep2"',
		description='Has to point to a valid source engine game setup. Such as "/half-life 2/ep2", where "half-life 2/bin" contains stuff like vtex.exe. Pro tip: you can create a default path by specifying the target path and then hitting File -> Defaults -> Save Startup File',
		default='',
		subtype='DIR_PATH'
	)

	use_sourceops_gpath: BoolProperty(
		name='Use SourceOps game path',
		description='My dick so big so really big, black holes move towards my huge dick',
		default=False 
	)

	sky_name : StringProperty(
		name='The name of the baked skybox',
		description='Doctor Sex is calling, are you answering the call?',
		default=''
	)

	size : EnumProperty(
		items= [
			('8', '8', 'lmfao'),
			('16', '16', 'wat ??'),
			('32', '32', 'rly'),
			('64', '64', 'why'),
			('128', '128', 'Gaming on consoles be like'),
			('256', '256', 'As small as your'),
			('512', '512', 'Rubbish'),
			('1024', '1024', 'Ery noice'),
			('2048', '2048', 'Giga Chad'),
			('4096', '4096', """Doesn't work (real)"""),
		],
		name='Square Sizes',
		description='The size of each skybox square',
		default='1024'
	)

	halfsize : BoolProperty(
		name='Half Size',
		description='Each square will be cut in half. Only top part remains visible',
		default=False
	)

	keep_src_f_exr : BoolProperty(
		name='Whether to keep the source EXR files or not',
		description='Disabling this will result into EXR files being deleted',
		default=False
	)

	keep_src_f_pfm : BoolProperty(
		name='Whether to keep the source PFM files or not',
		description='Disabling this will result into PFM files being deleted',
		default=False
	)

	moveto_afterb_path : StringProperty(
		name='Copy compiled stuff here',
		description='Should point to the "materials" folder. Will write to materials/skybox if present and overwrite any existing stuff. This description is redundant',
		default = '',
		subtype='FILE_PATH'
	)

	moveto_afterb_movecopy : BoolProperty(
		name='Move',
		description='Move skybox to the target destination. Otherwise - copy',
		default=True
	)

	hdrldr : EnumProperty(
		items=[
			('HDR', 'HDR', 'Giga Chad'),
			('LDR', 'LDR', 'Rubbish'),
		],
		name='LDR/HDR'
	)

	ldr_colorspace : EnumProperty(
		items=[
			('AgX', 'AgX', 'New fancy shit'),
			('Filmic', 'Filmic', 'Regular Filmic'),
		],
		name='LDR colour space'
	)

	hdr_compressed : BoolProperty(
		name='Compress into 8 bit + alpha',
		description='Useless shit',
		default=False
	)

	projectonly : BoolProperty(
		name='Simple projection',
		description='If set - seimply project whatever is plugged into the world on a cube, avoiding any renders',
		default=False
	)

	overwrite_shit : BoolProperty(
		name='Overwrite',
		description='If this is unchecked and the target skybox aready exists - an error occurs',
		default=False 
	)

	nobottom : BoolProperty(
		name='No bottom',
		description='Welcom 2 Bottom Gear mates (the bottom face of the skybox will be downscaled to a tiny 4x4 square)',
		default=False 
	)

	mkenvmap : BoolProperty(
		name='Make envmap',
		description='Pootis',
		default = False 
	)

	mkenvmap_only : BoolProperty(
		name='Only envmap',
		description='Pootis',
		default = False 
	)


	progress_report : StringProperty(
		name='Progress Report',
		description='Progress Report',
		default='Progress: '
	)

	progress_report_shown : BoolProperty(
		name='Progress Report',
		description='Progress Report',
		default=False
	)












# =========================================================
# ---------------------------------------------------------
#                          GUI
# ---------------------------------------------------------
# =========================================================

class VIEW3D_PT_blfoil_skyboxer(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Skyboxer'
	bl_label = 'Sugarplum Gaben'
	# https://youtu.be/sT3joXENOb0

	def draw(self, context):
		layout = self.layout

		sk_settings = context.scene.blvtf_skyboxer_params


		general_col = layout.column(align=False)
		general_col.label(text='Skybox exporter')
		# general_col.label(text="""Please read this: For whatever fucking reason, VTEX decides to flip you off if any side of skybox is single colour only. Basically: If you have a skybox where bottom is just a black void - add any kind of visible and renderable object below the world origin, so that the bottom side of the skybox is diluted with some colour""")
		general_col.label(text="""Please read this: For whatever fucking reason,""")
		general_col.label(text="""VTEX decides to flip you off""")
		general_col.label(text="""if any side of the skybox is single colour only""")
		general_col.label(text="""Basically: If you have a skybox where bottom""")
		general_col.label(text="""is just a black void - add any kind of""")
		general_col.label(text="""visible and renderable object""")
		general_col.label(text="""below the world origin, so that the""")
		general_col.label(text="""side of the skybox is diluted with some colour""")
		
		usesrcops = general_col.row()
		# todo: maybe make it disappear if not sourceops? make it disabled if no items in source ops?
		usesrcops.prop(sk_settings, 'use_sourceops_gpath', text='Use SourceOps game path')
		if hasattr(context.scene, 'sourceops'):
			usesrcops.enabled = True
		else:
			usesrcops.enabled = False
		general_col.prop(sk_settings, 'game_path', text='Game path')
		general_col.prop(sk_settings, 'sky_name', text='Skybox name')
		
		
		dimensions_col = layout.column(align=True)
		dimensions_col.use_property_split = True
		dimensions_col.use_property_decorate = False
		
		# dimensions_col.prop(sk_settings, 'size_x')
		# dimensions_col.prop(sk_settings, 'size_x')
		dimensions_col.prop(sk_settings, 'size', text='Skybox size')
		dimensions_col.prop(sk_settings, 'halfsize', text='Half the size')
		
		
		dimensions_col.prop(sk_settings, 'nobottom', text='No bottom')


		leave_src_files = layout.column(align=False)
		if sk_settings.hdrldr == 'HDR': 
			leave_src_files.prop(sk_settings, 'keep_src_f_exr', text='Keep .exr src files')
			leave_src_files.prop(sk_settings, 'keep_src_f_pfm', text='Keep .pfm src files')
		else:
			leave_src_files.prop(sk_settings, 'keep_src_f_exr', text='Keep .tga src files')
			dim_exrsrc = leave_src_files.row()
			dim_exrsrc.enabled = False
			dim_exrsrc.prop(sk_settings, 'keep_src_f_pfm', text='Keep .pfm src files')

			
		
		move_vtf_here = layout.column(align=False)
		leave_src_files.prop(sk_settings, 'moveto_afterb_path', text='Copy/Move to')
		leave_src_files.prop(sk_settings, 'moveto_afterb_movecopy', text='Move')

		"""
		mkenvmap_r = layout.column(align=False)
		mkenvmap_r.prop(sk_settings, 'mkenvmap', text='Make envmap')
		
		envmaponlyrow = mkenvmap_r.row()
		if sk_settings.mkenvmap == True:
			envmaponlyrow.enabled = True
		else:
			envmaponlyrow.enabled = False
		envmaponlyrow.prop(sk_settings, 'mkenvmap_only', text='Envmap only')
		"""

		hdrldr = layout.column(align=False)
		hdrldr.row().label(text='Skybox mode')
		hdrldr.row().prop(sk_settings, 'hdrldr', expand=True)

		hdrldr.row()
		hdrldr.row()

		hdrldr.row().label(text='LDR view transform')
		hdrldr.row().prop(sk_settings, 'ldr_colorspace', expand=True)
		
		compr_sw = hdrldr.row()
		compr_sw.prop(sk_settings, 'hdr_compressed', text='Compressed 8 bit HDR (make it look rubbish)')
		
		# todo: maybe make it appear and disappear ??
		if sk_settings.hdrldr == 'LDR':
			compr_sw.enabled = False
		else:
			compr_sw.enabled = True
		
		overwrite_sh = layout.column(align=False)
		# overwrite_sh.prop(context.scene.blfoil, 'blfoil_sky_projectonly', text='Project only')
		overwrite_sh.prop(sk_settings, 'overwrite_shit', text='Overwrite')

		mabaker_op = layout.column(align=False)
		self.layout.operator('mesh.blvtf_exec_compile_skybox',
			text='Compile skybox'
		)























