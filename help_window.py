import threadsafe_tkinter as tk

from supyr_struct.defs.frozen_dict import FrozenDict


TOOL_COMMAND_HELP = FrozenDict({
    #"animations": "",
    #"bitmap": "",
    #"bitmaps": "",
    "build-cache-file": '''
Builds a cache file with no Open Sauce enhancements whatsoever.
    (string)    scenario-name
        Name of the .scenario to build the mapfile from.''',
    "build-cache-file-ex": '''
Builds a cache file with extra Open Sauce arguments.
    (string)    mod-name
        The name of the mod this scenario belongs to.
        This will also be used when naming the new data-files.

    (boolean)   create-anew
        Should new data-files be created before building the cache?

    (boolean)   store-resources
        Store the scenario's bitmaps/sounds/locale data in the data-files?

    (boolean)   use-memory-upgrades
        Does the scenario require Open Sauce's memory upgrades to run?

    (string)    scenario-name
        Name of the .scenario to build the mapfile from.''',
    "build-cache-file-new": '''
Builds a cache file with extra Open Sauce arguments.
    (boolean)   create-anew
        Should new data-files be created before building the cache?

    (boolean)   store-resources
        Store the scenario's bitmaps/sounds/locale data in the data-files?

    (boolean)   use-memory-upgrades:
        Does the scenario require Open Sauce's memory upgrades to run?

    (directory) scenario-name
        Name of the .scenario to use.''',
    #"build-cpp-definition": "",
    "build-packed-file": '''unknown''',
    #"collision-geometry": "",
    #"compile-scripts": "",
    "compile-shader-postprocess": '''
Creates shader_postprocess_generic tags from HLSL .fx shaders in the data directory.
    (directory) shader-directory
        Path that contains the shaders to compile.''',
    "help": '''
Displays help messages for some of the Open Sauce commands.''',
    "hud-messages": "",
    "import-device-defaults": '''unknown''',
    "import-structure-lightmap-uvs": '''
Replaces the lightmap UVs of a bsp with custom ones loaded from an obj file.
The obj file must have lightmaps grouped by object and have the group index
appending the group name (lightmap_0). Best way to ensure this is to export
a fresh lightmaps obj using Aether, import it into your modelling program
then ONLY edit the UV's to ensure the model matches the bsp.
    (filepath)  obj-file
        Location of the source obj, relative to the data directory.

    (filepath)  structure-bsp
        Location of the target bsp, relative to the tags directory.''',
    #"lightmaps": "",
    #"merge-scenery": "",
    #"model": "",
    #"physics": "",
    #"process-sounds": ""'''unknown''',
    "remove-os-tag-data": '''
Removes OS tag data that would prevent loading in the stock tools.
Back up your tags before hand to be safe.
    (filepath)  tag-name
        Name of the tag to clean.

    (string)    tag-type
        Type of the tag (the tags file extension)

    (boolean)   recursive
        Whether to also process all tags referred to by the given tag.''',
    "runtime-cache-view": '''
Allows you to view the contents of the tag cache in an executing
instance of Halo CE. See the tools own help for more details.''',
    #"sounds": "",
    "sounds_by_type": '''unknown''',
    #"strings": "",
    #"structure": "",
    #"structure-breakable-surfaces": "",
    #"structure-lens-flares": "",
    "tag-load-test": '''
Validates a tag and ALL of its children can be loaded without error
Optionally prints additional diagnostic information
    (string)    tag-name
        Root tag's path.

    (string)    group
        Root tag's group name.

    (boolean)   prompt-to-continue
        Prompt to continue for each child tag.

    (boolean)   prompt-to-fix-unresolved
        NOT YET IMPLEMENTED

    (boolean)   load-non-resolving-refs
        Load all tag_references, even if they're non-resolving.

    (boolean)   print-size
        Print the total size of the tag hierarchy as well as the tag_group memory.

    (boolean)   verbose
        Outputs progress/extra information as it processes the tags.''',
    #"unicode-strings": "",
    #"windows-font": "",
    "zoners_model_upgrade": '''unknown''',
    })


class HekPoolHelpWindow(tk.Toplevel):
    pass
