# blvtf
VTFEdit inside Blender with a number of improvements and new features

# Installation. READ THIS SHORT SENTENCE I BEG YOU
Download this repo as zip, install as an addon AND RESTART BLENDER !


# Usage
Open "Image Editor" or "UV Editor" window, drag-n-drop an image so that it appears in blender and look for self-explanatory options in the N-Menu.
This addon also adds support for a variety of formats, basically if Blender opens it, then the addon is able to process it (this applies to batch convert too).
Aka the addon is capable of processing .psd files.

# TxtMax
This addon supports filename pattern matching.
It's possible to create a file defining which format to use when converting files with a certain pattern:
 - Go to the blVTF menu
 - Tick the "TxtMax" checkbox
 - Open Blender's text editor (It's just yet another Editor Type which could be found next to the "Dope Sheet" in the selection menu located in the top left corner)
 - Either create a new Text or import an existing one (it doesn't has to be saved or anything)
 - Specify this text file in the special field below the "TxtMax" checkbox

Each line inside this file represents a rule according to which the system would try assigning the encoding format.
Example:

	# You can comment lines like in Python
	# Syntax is as follows:
	# WILDCARD_PATTERN FORMAT SIZE_PARAMS|NONE FLAGS|NONE

	# Whitespaces in the WILDCARD_PATTERN are not allowed

	*_diffuse.psd DXT1   1024x1024 -NOMIP,NORMAL
	*_normal.psd  BGR888 -NOMIP,NORMAL

First line means:
 - Any file, which ends with _diffuse.psd
 - Should be converted to DXT1
 - Clamp dimensions to 1024x1024
 - Add "No Mipmap" and "Normal Map" flags. The flag array must start with "-", contain no whitespaces and always come as the last argument

Second line is the same, but the image size is not affected.

If two identical wildcards were specified - the earliest one gets replaced with the latest one.

The "Fallback" checkbox does the following:
It runs the regular batch process after TxtMax,
but only takes files which weren't already processed by TxtMax while using all the rules defined for the regular batch process.

For instance, a folder contains:
 - 3 .tga files
 - 1 .psd file
 - 1 .png file

And let's say that the following setup is present:
 - TxtMax is activated with some rules which would grab all 3 .tga files
 - Fallback checkbox is checked
 - The path to the source folder is as follows: "C:/custom/ies/*.psd"

What would happen:
 - The TxtMax process will run while completely ignoring the "*.psd" wildcard
 - All 3 .tga files get converted by TxtMax
 - The regular batch process is then being run
 - The "*.psd" wildcard is applied and therefore the regular batch process receives 1 .psd file
 - The .psd file gets converted and that's it



# Limitations
 - Animated textures are not supported yet
 - Images packed into the blend fille cannot be exported yet