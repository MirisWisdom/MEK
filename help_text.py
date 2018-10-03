import os
import tempfile
import traceback
from hek_pool.util import get_cwd
from hek_pool import constants

README_TEXT = ''';                         WHAT IS POOL
; So first off, what is Pool and why should I use it? Pool is a wrapper
; for tool.exe that allows you to batch process tool commands, run up to
; 64 tool commands in parallel, run tool on directories other than the
; one it resides in, and more. Pool also allows you to save the list of
; commands you've typed in to text files and load them up for later use.
; Pool will load up whatever commands were typed in when it was closed.
; Pool can do more, but it is basically an ease-of-use upgrade for tool.


;                       GETTING STARTED
; To use Pool at all, you first need to select the tool.exe to use.
; Pool will try to detect your copies of tool when it loads if none
; have been added. To add one, go to "File->Add Tool" and browse to
; the tool.exe you want to use. To switch tools, click the menu to
; the left of "Help". It will show you all tools it knows about.

; Now you're all set, and you can just type commands into this text
; box like you would normally when running tool in the command line.
; A couple useful examples can be viewed by going to "File->Open"
; and opening one of the text files in the command lists folder.


;                       HOW TO USE POOL
; Just enter commands like you would for running Tool in command line.
; Once you've typed them in, hit "Process all" or "Process selected".
; Lines starting with a ; or a / are considered disabled(they are
; basically comments), and are ignored when processing. Lines that
; begin with a # are considered directives and do special things.
; For example, #cwd allows you to set the current working directory,
; #k and #c make cmd windows stay open or close(respectively) when
; the command finishes processing, and #w tells Pool to wait until
; all commands currently processing are finished before continuing.
; Combine #k with #w and you can pause processing at certain spots.

; Commands currently processing will be surrounded in yellow, failed
; commands will be surrounded in red, and finished ones in green.
; Because Tool doesn't actually report any error information when it
; returns, the only failures Pool can detect are mis-typed commands.
; Go to "Help->Commands and Directives" to view an explaination of
; each command, each directive, and each of their arguments.
;     (NOTE: As of right now, most of the help is blank. Sorry!)


;                        SMART-ASSIST
; I personally prefer to type commands and parameters in rather than
; using a GUI(like a file browser) to do it for me. There are others
; like me, but there are also people who want/need the help. To make
; everyone happy, I've come up with a smart-assist system that works
; through the use of right-clicking. Right-click an empty line and a
; menu will pop up that allows you to paste in a template for any
; command or directive. Right-click a command to get a description
; of it and what its arguments are. Right-click an argument to view
; a description of the argument and/or bring up a GUI to edit it.
; Smart-assist can be turned off at any time in the Settings menu.
; Example:
;     Right-click the <scenario> argument of build-cache-file and a
;     browser will appear, letting you select the scenario to use.


;           THESE COLORS HURT AND I HATE THE ACTION MENUS!!!
; If you don't like the text color scheme or the commands that appear
; in the right-click menu, you can change them through the File menu.
; The color scheme and menu options will be opened in notepad, and
; will both be applied as soon as you save and close the text files.


;              WAS IT REALLY NECESSARY TO CREATE THIS?
; No, not at all lmao. I was REALLY bored and decided that it'd be
; fun to add another tool(lul) to the MEK that sort-of replaces one
; of Bungie's original hek programs. I'm not insane enough to write
; an actual REPLACEMENT for tool.exe, so this is good enough for me.
'''


TOOL_COMMAND_HELP = constants.FrozenDict({
    "animations": (
        "Compiles a folder of jma/jmm/jmo/jmr/jmt/jmw/jmz animations in "
        "the data folder into a model_animations tag. The directory you "
        'specify must contain these files in a folder named "animations". '
        'Do NOT type the "animations" part of the path; it is implied.\n'
        "\n"
        "Each jm* type compiles to a different type of animation. dx/dy/dz "
        "means the animation will permanently move the object in the world "
        "on that/those axis, while dyaw means it will permanently rotate "
        "the object. These are typically used for movement and turning.\n"
        "\n"
        "base\n"
        "       (replaces the current animation on all nodes)\n"
        "       jmm:\tnone\n"
        "       jmw:\tnone (completely world relative)\n"
        "       jma:\tdx/dy\n"
        "       jmt:\tdx/dy/dyaw\n"
        "       jmz:\tdx/dy/dz/dyaw\n"
        "\n"
        "overlay:\n"
        "       (applied over the current base {aiming, talking, etc})\n"
        "       jmo:\tnone\n"
        "\n"
        "replacement\n"
        "       (animates only specific nodes {throw, melee, etc})\n"
        "       jmr:\tdx/dy\n"
        "\n"
        "Replacement animations are special, as they can be played over base "
        "animations partially. Any nodes the replacement animation doesnt "
        "animate, are animated by the current base. This allows replacement "
        "animations to animate the upper body when throwing a grenade, but "
        "have the animation for the characters leg movement handled by the "
        "base(walking, standing, crouching, etc).",
        ("source-directory", 'dir',
         'The directory containing the "animations" folder to be compiled.'),
        ),
    "bitmap": (
        "Compiles the .tif image specified into a bitmap tag. Name the "
        "file with a .tif extension, not .tiff(tool only looks for .tif "
        "files). Once the bitmap is compiled, you may edit it in Guerilla "
        "or Mozzarilla to change how tool processes and compiles it. "
        "When you are done, run this command again to process it with "
        "those setting applied.",
        ("source-file", 'file-no-ext',
         "The filepath of the bitmap to be compiled."),
        ),
    "bitmaps": (
        "Compiles a folder of .tif images in the data folder into bitmap "
        "tags. Name them with a .tif extension, not .tiff(tool only looks "
        "for .tif files). Once the tags are compiled, you may edit them in "
        "Guerilla or Mozzarilla to change how tool processes and compiles "
        "them. When you are done, run this command again to process them "
        "with those setting applied.",
        ("source-directory", 'dir',
         'The directory containing the bitmaps to be compiled.'),
        ),
    "build-cache-file": (
        'Builds a cache file(a .map file) with no Open Sauce enhancements.',
        ("scenario-path", 'file-no-ext',
         'Filepath of the scenario tag to build the map cache file from.'),
        ),
    "build-cache-file-ex": (
        'Builds a cache file(a .map file) with extra Open Sauce arguments.',
        ("mod-name", 'str',
         'The name of the mod this scenario belongs to. '
         'This will also be used when naming the new data-files.'),
        ("create-anew", 'bool',
         'Should new data-files be created before building the map?'),
        ("store-resources", 'bool',
         'Store the scenarios bitmaps/sounds/locale data in the data-files?'),
        ("use-memory-upgrades", 'bool',
         'Does the scenario require Open Sauces memory upgrades to run?'),
        ("scenario-path", 'file-no-ext',
         'Filepath of the scenario tag to build the map cache file from.'),
        ),
    "build-cache-file-new": (
        'Builds a cache file(a .map file) with extra Open Sauce arguments.',
        ("create-anew", 'bool',
         'Should new data-files be created before building the map?'),
        ("store-resources", 'bool',
         'Store the scenarios bitmaps/sounds/locale data in the data-files?'),
        ("use-memory-upgrades", 'bool',
         'Does the scenario require Open Sauces memory upgrades to run?'),
        ("scenario-path", 'file-no-ext',
         'Filepath of the scenario tag to build the map cache file from.'),
        ),
    "build-cpp-definition": (
        "Builds a C++ definition for the tag-group specified and writes it to "
        "the current working directory(typically the folder tool.exe is in). ",
        ("tag-group", 'str-no-quote',
         "The four character code designated for this tag type. For example, "
         "'bitm' is for bitmap, 'matg' is globals, and 'snd!' is sound."),
        ("add-boost-asserts", 'bool',
         "Add assertions to the C++ definition to help make sure the "
         "structures are the correct size if you modify them?"),
        ),
    "build-packed-file": (
        "Something to do with compiling open-sauce shaders. Not useful to map makers.",
        ("source-directory", 'dir', ''),
        ("output-directory", 'dir', ''),
        ("file-definition-xml", 'file-no-ext', ''),
        ),
    "collision-geometry": (
        "Compiles a directory of .jms models in the data folder into a "
        "model_collision_geometry tag. The directory you specify must contain "
        'these files in a folder named "physics". Do NOT type the "physics" '
        "part of the path; it is implied.\n"
        "\n"
        'The name of each jms file in the "physics" folder must be the '
        "permutation name that jms file contains. Here are most of the "
        "special permutation names as well as when they are used:\n"
        "       __base\t\t(the default model)\n"
        "       ~blur\t\t(vehicle tires are spinning fast)\n"
        "       ~primary-blur\t(weapon primary trigger is firing fast)\n"
        "       ~secondary-blur\t(weapon secondary trigger is firing fast)\n"
        "       ~damaged\t(health of a region hit zero and died)\n"
        "\n"
        'If there is a "physics.jms" file in the "physics" folder, make sure '
        "it either has no vertices and triangles, or you have Pool's "
        '"Fix physics.jms" setting checked. The command might fail otherwise.',
        ("source-directory", 'dir',
         'The directory containing the "physics" folder to be compiled.'),
        ),
    "compile-scripts": (
        "NOT YET IMPLEMENTED",
        ("scenario-path", 'file-no-ext',
         'Filepath of the scenario tag whose scripts to compile.'),
        ),
    "compile-shader-postprocess": (
        'Creates shader_postprocess_generic tags from HLSL .fx shaders in the data directory.',
        ("shader-directory", 'dir',
         'Directory that contains the shaders to compile'),
        ),
    "help": (
        'Displays help messages for some of the Open Sauce commands.',
        ),
    "hud-messages": (
        'Compiles a "hud messages.hmt" file in the specified folder into a '
        "hud_message_text tag. The .hmt file must be saved in Unicode 16Bit "
        "encoding(not ANSI/ASCI/UTF8). Each line in the .hmt file must have "
        'the format "X=Y" where X is the message name, and Y is the message.\n'
        "\n"
        "The message name must be 31 characters or less. The entire message "
        'must be on the same line as the "X=" part. If you need to put a line '
        "break in the message, type |n instead. You can also specify a "
        "button/weapon icon to appear in part of the message using special "
        "characters. Here is a list of the icon names:\n"
        "       %a-button, %b-button, %x-button, %y-button\n"
        "       %black-button, %white-button, %left-trigger, %right-trigger\n"
        "       %dpad-up, %dpad-down, %dpad-left, %dpad-right\n"
        "       %start-button, %back-button, %integrated-light, %jump\n"
        "       %left-thumb, %right-thumb, %left-stick, %right-stick\n"
        "       %action, %throw-grenade, %primary-trigger\n"
        "       %use-equipment, %rotate-weapons, %rotate-grenades\n"
        "       %zoom, %crouch, %accept, %back, %move, %look\n"
        "       %custom-1, %custom-2, %custom-3, %custom-4\n"
        "       %custom-5, %custom-6, %custom-7, %custom-8\n\n"
        "Example:\n"
        "       pickup=Press %action to swap|n%custom-1|nfor|n%custom-2",
        ("hmt-path", 'dir',
         'The directory containing the "hud messages.hmt" file.'),
        ("scenario-name", 'str',
         "After the hud_messages_text tag is compiled, this is the name of "
         "the scenario to put a reference to it in. This scenario must be in "
         "the same folder as where the hud_message_text tag will compile to."),
        ),
    "import-device-defaults": (
        "My guess is that this creates a device_defaults tag from your own "
        "savegame preferences. I doubt this has realistically ever been "
        "useful to anyone other than Gearbox Software and Bungie.", 
        ("type", 'str-no-quote', ''),
        ("savegame-path", 'file', ''),
        ),
    "import-structure-lightmap-uvs": (
        'Replaces the lightmap UVs of a bsp with custom ones loaded from an obj file. '
        'The obj file must have lightmaps grouped by object and have the group index '
        'appending the group name (lightmap_0). Best way to ensure this is to export '
        'a fresh lightmaps obj using Aether, import it into your modelling program, '
        'and then ONLY edit the UVs to ensure the model matches the bsp.',
        ("structure-bsp-path", 'file-no-ext',
         'Location of the target bsp, relative to the tags directory.'),
        ("obj-file-path", 'file-no-ext',
         'Location of the source obj, relative to the data directory.'),
        ),
    "lightmaps": (
        "Runs radiosity on the specified bsp to calculate static lighting. "
        "This process can typically take a long time at highest quality, so "
        "only run it when you have time to spare.\n"
        "\n"
        "Quick and dirty lightmaps can be calculated to allow you to quickly "
        "test changes to the level geometry. Use this command if you dont "
        "know what good testing values for your bsp are:\n"
        "       lightmaps   <scenario>  <bsp-name>  0  0.1\n"
        "\n"
        "Best quality lightmaps would use these settings:\n"
        "       lightmaps   <scenario>  <bsp-name>  1  0.0000001",
        ("scenario-path", 'file-no-ext',
         "Filepath to the scenario that uses the bsp you want to light."),
        ("bsp-name", 'str',
         "The name of the bsp to run radiosity on. This is the name of the "
         "structure_scenario_bsp tag you are running this on."),
        ("render-high-quality", 'bool',
         "Use highest quality radiosity settings?"),
        ("stop-threshold", 'float',
         "The amount of light remaining to stop calculating at. Light is "
         "cast in multiple passes from each surface, getting progressively "
         "finer with each pass. Each pass also reduces the total amount of "
         "light to be cast from each surface. When the amount of light "
         "remaining hits this value, radiosity will stop."),
        ),
    "merge-scenery": (
        "Merges scenery instances from the source-scenario into the "
        "destination-scenario.",
        ("source-scenario", 'file-no-ext',
         "The filepath of the scenario to copy the scenery from."),
        ("destination-scenario", 'file-no-ext',
         "The filepath of the scenario to paste the scenery into."),
        ),
    "model": (
        "Compiles a directory of .jms models in the data folder into a "
        "gbxmodel tag. The directory you specify must contain these "
        'files in a folder named "models". Do NOT type the "models" '
        "part of the path; it is implied.\n"
        "\n"
        'The name of each jms file in the "models" folder must be the '
        "permutation name that jms file contains. Here are most of the "
        "special permutation names as well as when they are used:\n"
        "       __base\t\t(the default model)\n"
        "       ~blur\t\t(vehicle tires are spinning fast)\n"
        "       ~primary-blur\t(weapon primary trigger is firing fast)\n"
        "       ~secondary-blur\t(weapon secondary trigger is firing fast)\n"
        "       ~damaged\t(health of a region hit zero and died)",
        ("source-directory", 'dir',
         'The directory containing the "models" folder to be compiled.'),
        ),
    "physics": (
        'Compiles a "physics.jms" model in the data folder into a physics tag. '
        'The directory you specify must contain a folder named "physics" with '
        '"physics.jms" INSIDE that "physics" folder. Do NOT type the '
        '"physics\\physics" part of the path; it is implied.',
        ("source-directory", 'dir',
         'The directory containing the "physics" folder to be compiled. '
         'The "physics" folder must contain the physics.jms file to be compiled.'),
        ),
    "process-sounds": (
        "Unknown",
        ("root-path", 'dir', ''),
        ("substring", 'str', ''),
        ("effect", 'str-no-quote', ''),
        ("value", 'float', ''),
        ),
    "remove-os-tag-data": (
        'Removes OS tag data that would prevent loading in the stock tools. '
        'Back up your tags before hand to be safe.',
        ("tag-path", 'file-no-ext', 'Filepath to the tag to clean.'),
        ("tag-type", 'str', 'Type of the tag (the tags file extension).'),
        ("recursive", 'bool',
         'Process all tags referred to by the given tag?'),
        ),
    "runtime-cache-view": (
        'Allows you to view the contents of the tag cache in an executing '
        'instance of Halo CE. See the tools own help for more details.',
        ),
    "sounds": (
        "Compiles a directory of folders of .wav files in the data folder "
        "into sound tags. Each folder in the directory specified will be "
        "compiled into a sound tag. Any sub-folders within these are treated "
        "as pitch ranges. Any .wav files inside these pitch range folders are "
        "permutations within that pitch range. If you do not need to use "
        "pitch ranges, just put each .wav permutation file directly "
        "inside each sounds folder.\n\n"
        "For example, to compile the tag:\n"
        "       vehicles\\sophia\\sounds\\cannon_fire.sound\n\n"
        "you would create this audio perumtation:\n"
        "       vehicles\\sophia\\sounds\\cannon_fire\\default.wav\n\n"
        "and then run the command:\n"
        "       sounds  vehicles\\sophia\\sounds  ogg  1\n"
        "\n"
        "NOTE: All .wav data files MUST be saved with 16bit signed, little "
        "endian, PCM encoding. This is the only format that tool can read.",
        ("directory-name", 'dir',
         'The directory containing the sounds to be compiled.'),
        ("platform", 'str',
         "The format to compile the sounds to. The xbox and wav formats are "
         "basically the same, and are the only ones that will work on an Xbox. "
         "Ogg can only be used PC, and has higher quality than the others. "
         "If you have a choice, choose xbox for short quick sounds, and ogg "
         "for music or dialog."),
        ("ogg-quality", 'float',
         "The relative quality of ogg compressed audio. Higher values create "
         "higher quality audio, but also higher filesize. Valid values are "
         "(-0.1, 1]. The value -0.1 is itself not a valid value, so -0.09999999 "
         "is the closest you can get to it.\n"
         "\n"
         "-0.1 = ~48 kbit/s\n"
         " 0.0 = ~64 kbit/s\n"
         " 0.2 = ~96 kbit/s\n"
         " 0.4 = ~128 kbit/s\n"
         " 0.6 = ~192 kbit/s\n"
         " 0.8 = ~256 kbit/s\n"
         " 1.0 = ~500 kbit/s"),
        ),
    "sounds_by_type": (
        "Unknown",
        ("directory-name", 'dir', ''),
        ("type", 'str', ''),
        ("round-to-64-samples", 'bool', ''),
        ),
    "strings": (
        "Compiles a folder of .txt files into string_list tags. Each .txt file "
        "must be saved in ANSI or ASCII encoding.\n"
        "\n"
        "NOTE: After each separate string in the text file you must put "
        "###END-STRING### on the next line. This is how it should look:\n\n"
        "       Here is my first string\n"
        "       ###END-STRING###\n"
        "       Here is my second string\n"
        "       ###END-STRING###\n"
        "       Here is my last string\n"
        "       ###END-STRING###",
        ("source-directory", 'dir',
         "The folder containing the .txt files to turn into string_list tags."),
        ),
    "structure": (
        "Compiles a .jms model in the data folder into a scenario_structure"
        "_bsp (sbsp) tag. The directory you specify must contain this .jms "
        'file in a folder named "models". Do NOT type the "models" part of '
        "the path; it is implied.\n"
        "\n"
        'The name of the jms file in the "models" folder is the name the bsp '
        "it compiles to will be given. This is typically the same name as "
        "the scenario, but large levels may utilize multiple bsps.\n"
        "\n"
        "If a scenario tag doesn't already exist in the folder this sbsp tag "
        "will be compiled into, one referencing the new bsp will be created.",
        ("scenario-directory", 'dir',
         'The directory containing the "models" folder that contains the '
         ".jms file you are compiling."),
        ("bsp-name", 'str',
         "The name of the .jms file to compile, as well as the name "
         "to give the scenario_structure_bsp tag you are compiling."),
        ),
    "structure-breakable-surfaces": (
        "Creates breakable surfaces structures in the specified structure_"
        "scenario_bsp (sbsp) tag. Each surface has a flag to specify if it "
        "is breakable. When the sbsp tag is compiled from a .jms file, the "
        "shaders determine whether to set these flags for each surface. "
        "This command will generate breakable-surface structures for each "
        "surface flagged as breakable. Surfaces will not actually break if "
        "these structures are not generated after compiling the sbsp tag.",
        ("structure-path", 'file-no-ext',
         "The scenario-structure-bsp tag to generate breakable surfaces for."),
        ),
    "structure-lens-flares": (
        "Calculates and inserts lens flare markers and dependencies into the "
        "specified scenario_structure_bsp (sbsp) tag. The lens_flares as well "
        "as how far apart to place them are pulled from the sbsp's shaders.\n"
        "The only shaders tags that can reference lens_flare tags are these:\n"
        "       shader_environment\n"
        "       shader_transparent_generic\n"
        "       shader_transparent_chicago\n"
        "       shader_transparent_chicago_extended",
        ("structure-path", 'file-no-ext',
         "The scenario-structure-bsp tag to calculate lens flares markers "
         "and dependencies for."),
        ),
    "tag-load-test": (
        'Validates that a tag and ALL of its children can be loaded without error. '
        'Optionally prints additional diagnostic information.',
        ("tag-name", 'file-no-ext', "Root tag's path."),
        ("group", 'str', "Root tag's group name."),
        ("prompt-to-continue", 'bool',
         'Prompt to continue for each child tag?'),
        ("prompt-to-fix-unresolved", 'bool',
         'NOT YET IMPLEMENTED.'),
        ("load-non-resolving-refs", 'bool',
         "Load all tag_references, even if they're non-resolving?"),
        ("print-size", 'bool',
         'Print the total size of the tag hierarchy as well as the tag_group memory?'),
        ("verbose", 'bool',
         'Output progress/extra information as the tag(s) is/are processesd?'),
        ),
    "unicode-strings": (
        "Compiles a folder of .txt files into unicode_string_list tags. Each "
        ".txt file must be saved in Unicode 16Bit encoding. Big/little endian "
        "byteorder does not matter, just do not save as ANSI, ASCII, or UTF8, "
        "only UTF16.\n"
        "\n"
        "NOTE: After each separate string in the text file you must put "
        "###END-STRING### on the next line. This is how it should look:\n\n"
        "       Here is my first string\n"
        "       ###END-STRING###\n"
        "       Here is my second string\n"
        "       ###END-STRING###\n"
        "       Here is my last string\n"
        "       ###END-STRING###",
        ("source-directory", 'dir',
         "The folder containing the .txt files to turn into unicode_string_list tags."),
        ),
    "windows-font": (
        "Displays a prompt which allows you to select an installed Windows "
        "font you wish to compile into a font tag.",
        ),
    "zoners_model_upgrade": (
        "Unknown",
        ),
    })


DIRECTIVES_HELP = {
    "k": (
        "Tells Pool to keep Tool instances open, even after they finish processing.",
        ),
    "c": (
        "Tells Pool to close Tool instances as soon as they finish processing.",
        ),
    "cwd": (
        "Changes the current working directory, allowing Tool to operate on "
        "folders it isn't inside. This allows you to use one copy of tool for "
        "any number of separate tags directories and Halo CE installations.",
        ("directory", "dir",
         "The directory to set as the current working directory.\n"
         "This is an absolute path, meaning it is not relative to anything."),
        ),
    "set": (
        "Adds a variable to a list that can be used for text replacements. "
        "To use the variable, you must put arrow braces around it.\n"
        "\n"
        "Example:\n"
        '    # set\t\tdir   "levels\\test\\tutorial"\n'
        '    structure\t<dir>\\tutorial\n'
        '    lightmaps\t<dir>\\tutorial  tutorial  1  0.000001\n'
        '    build-cache-file\t<dir>\\tutorial',
        ("var-name", "str-no-quote", "Name of the variable."),
        ("var-value", "str",
         "The string to replace any occurances of <var-name> with."),
        ),
    "del": (
        "Removes a variable from the list of replacements. "
        "See the 'set' directive for more information on variables.",
        ("var-name", "str-no-quote", "Name of the variable to remove."),
        ),
    "run": (
        "Runs the specified file located in the current working directoy. "
        "Any additional arguments after <exec-path> are passed along to the "
        "executable when it is ran.\n"
        "\n"
        "Example:\n"
        "    # run haloce.exe  -console  -devmode",
        ("exec-path", "file",
         "Name of the executable to run."),
        ),
    "w": (
        "Tells Pool to wait until all currently running Tool instances "
        "are closed before continuing executing commands and directives.",
        ),
    }


def generate_help(save_to_file=False):
    help_text = '''
This is a small help-file to explain what each Tool command and
Pool directive does, how to use it, and what its arguments are.
To use a directive in, type a # before it(ex:  # cwd  or  #cwd).

The argument types are as follows:

    bool:   A true or false value. 0 for false, 1 for true.

    float:  A number that can have a decimal(ex: 1.337).

    int:    An integer number(cannot have a decimal point).

    str:    A string of characters such as "letters". If the
        string contains spaces, enclose the string in quotes.
        (ex: "this is a string")

    dir:    A path to a directory. Except for the cwd directive,
        any command or directive asking for a directory will need
        it to be relative to the current working directory(cwd).
        Do NOT use / to separate folders. Tool doesnt recognize
        this as a separator. Use \\ instead.

    file:   A path to a file. Any command or directive asking for
        a filepath will need it to be relative to the current
        working directory(cwd). Do NOT use / to separate folders.
        Tool doesnt recognize this as a separator. Use \\ instead.

    str-no-quote: Same as str, except it cannot be enclosed
        in quotes, and as a result cannot contain spaces.

    file-no-ext:  Same as file, except you do not provide the
        file extension. Tool will either know the extension
        already or will be able to guess it.
'''
    for info, typ in ((DIRECTIVES_HELP,   "DIRECTIVES"),
                      (TOOL_COMMAND_HELP, "TOOL COMMANDS")):
        help_text += "\n\n"
        help_text += "#  %s\n" % typ
        help_text += "#" * (len(typ) + 3) + '\n\n'

        for cmd_name in sorted(info):
            help_text += "  %s\n" % cmd_name
            
            cmd_help, params_help = info[cmd_name][0], info[cmd_name][1:]

            indent = " "*4
            if cmd_help:
                for line in cmd_help.split('\n'):
                    help_text += indent + line + '\n'
                help_text += '\n'

            help_text += "%s#  ARGUMENTS\n" % indent
            help_text += "%s############\n" % indent
            if not params_help:
                help_text += "%sNone\n\n\n" % indent
                continue

            for param_help in params_help:
                arg_name, arg_type, arg_help = param_help[:3]
                help_text += "%s<%s>  (%s)\n" % ((" "*4), arg_name, arg_type)
                if arg_help:
                    for line in arg_help.split('\n'):
                        help_text += (" "*8) + line + '\n'
                help_text += '\n'
            help_text += '\n'

    if save_to_file:
        try:
            try:
                fp = os.path.join(get_cwd(__file__), constants.HELP_NAME)
                with open(fp, "w") as f:
                    f.write(help_text)
            except Exception:
                fp = os.path.join(tempfile.gettempdir(), constants.HELP_NAME)
                with open(fp, "w") as f:
                    f.write(help_text)

            return fp
        except Exception:
            print(traceback.format_exc())

        return help_text


if __name__ == "__main__":
    try:
        generate_help(True)
    except Exception:
        print(traceback.format_exc())
