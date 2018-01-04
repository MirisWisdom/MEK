import os
import traceback
from supyr_struct.defs.frozen_dict import FrozenDict

HELP_NAME = "help.txt"

TOOL_COMMAND_HELP = FrozenDict({
    "animations": (
        "",
        ("source-directory", 'dir',
         ""),
        ),
    "bitmap": (
        "",
        ("source-file", 'file-no-ext',
         ""),
        ),
    "bitmaps": (
        "",
        ("source-directory", 'dir',
         ""),
        ),
    "build-cache-file": (
        'Builds a cache file with no Open Sauce enhancements whatsoever.',
        ("scenario-name", 'file-no-ext',
         'Name of the .scenario to build the mapfile from.'),
        ),
    "build-cache-file-ex": (
        'Builds a cache file with extra Open Sauce arguments.',
        ("mod-name", 'str',
         'The name of the mod this scenario belongs to.\n'
         'This will also be used when naming the new data-files.'),
        ("create-anew", 'bool',
         'Should new data-files be created before building the map?'),
        ("store-resources", 'bool',
         'Store the scenarios bitmaps/sounds/locale data in the data-files?'),
        ("use-memory-upgrades", 'bool',
         'Does the scenario require Open Sauces memory upgrades to run?'),
        ("scenario-name", 'file-no-ext',
         'Name of the .scenario to build the mapfile from.'),
        ),
    "build-cache-file-new": (
        'Builds a cache file with extra Open Sauce arguments.',
        ("create-anew", 'bool',
         'Should new data-files be created before building the map?'),
        ("store-resources", 'bool',
         'Store the scenarios bitmaps/sounds/locale data in the data-files?'),
        ("use-memory-upgrades", 'bool',
         'Does the scenario require Open Sauces memory upgrades to run?'),
        ("scenario-name", 'file-no-ext',
         'Name of the .scenario to build the mapfile from.'),
        ),
    "build-cpp-definition": (
        "",
        ("tag-group", 'str-no-quote',
         ""),
        ("add-boost-asserts", 'bool',
         ""),
        ),
    "build-packed-file": (
        'unknown',
        ("source-directory", 'dir', ''),
        ("output-directory", 'dir', ''),
        ("file-definition-xml", 'file-no-ext', ''),
        ),
    "collision-geometry": (
        "",
        ("source-directory", 'dir',
         ""),
        ),
    "compile-scripts": (
        "",
        ("scenario-name", 'file-no-ext',
         ""),
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
        "",
        ("path", 'dir',
         ""),
        ("scenario-name", 'file-no-ext',
         ""),
        ),
    "import-device-defaults": (
        '', 
        ("type", 'str-no-quote', ''),
        ("savegame-path", 'file', ''),
        ),
    "import-structure-lightmap-uvs": (
        'Replaces the lightmap UVs of a bsp with custom ones loaded from an obj file.\n'
        'The obj file must have lightmaps grouped by object and have the group index\n'
        'appending the group name (lightmap_0). Best way to ensure this is to export\n'
        'a fresh lightmaps obj using Aether, import it into your modelling program,\n'
        'and then ONLY edit the UVs to ensure the model matches the bsp.',
        ("structure-bsp", 'file-no-ext',
         'Location of the target bsp, relative to the tags directory.'),
        ("obj-file", 'file-no-ext',
         'Location of the source obj, relative to the data directory.'),
        ),
    "lightmaps": (
        "",
        ("scenario", 'file-no-ext',
         ""),
        ("bsp-name", 'str',
         ""),
        ("render-high-quality", 'bool',
         ""),
        ("stop-threshold", 'float',
         ""),
        ),
    "merge-scenery": (
        "",
        ("source-scenario", 'file-no-ext',
         ""),
        ("destination-scenario", 'file-no-ext',
         ""),
        ),
    "model": (
        "",
        ("source-directory", 'dir',
         ""),
        ),
    "physics": (
        "",
        ("source-directory", 'dir',
         ""),
        ),
    "process-sounds": (
        'unknown',
        ("root-path", 'dir', ''),
        ("substring", 'str', ''),
        ("effect", 'str-no-quote', ''),
        ("value", 'float', ''),
        ),
    "remove-os-tag-data": (
        'Removes OS tag data that would prevent loading in the stock tools.\n'
        'Back up your tags before hand to be safe.',
        ("tag-name", 'file-no-ext', 'Name of the tag to clean.'),
        ("tag-type", 'str', 'Type of the tag (the tags file extension).'),
        ("recursive", 'bool',
         'Whether to also process all tags referred to by the given tag.'),
        ),
    "runtime-cache-view": (
        'Allows you to view the contents of the tag cache in an executing\n'
        'instance of Halo CE. See the tools own help for more details.',
        ),
    "sounds": (
        "",
        ("directory-name", 'dir',
         ""),
        ("platform", 'str',
         ""),
        ("use-high-quality(ogg_only)", 'bool',
         ""),
        ),
    "sounds_by_type": (
        'unknown',
        ("directory-name", 'dir', ''),
        ("type", 'str', ''),
        ("round-to-64-samples", 'bool', ''),
        ),
    "strings": (
        "",
        ("source-directory", 'dir',
         ""),
        ),
    "structure": (
        "",
        ("scenario-directory", 'dir',
         ""),
        ("bsp-name", 'str',
         ""),
        ),
    "structure-breakable-surfaces": (
        "",
        ("structure-name", 'str',
         ""),
        ),
    "structure-lens-flares": (
        "",
        ("bsp-name", 'str',
         ""),
        ),
    "tag-load-test": (
        'Validates that a tag and ALL of its children can be loaded without error.\n'
        'Optionally prints additional diagnostic information.',
        ("tag-name", 'file-no-ext', "Root tag's path."),
        ("group", 'str', "Root tag's group name."),
        ("prompt-to-continue", 'bool',
         'Prompt to continue for each child tag.'),
        ("prompt-to-fix-unresolved", 'bool',
         'NOT YET IMPLEMENTED.'),
        ("load-non-resolving-refs", 'bool',
         "Load all tag_references, even if they're non-resolving."),
        ("print-size", 'bool',
         'Print the total size of the tag hierarchy as well as the tag_group memory.'),
        ("verbose", 'bool',
         'Outputs progress/extra information as it processes the tags.'),
        ),
    "unicode-strings": (
        "",
        ("source-directory", 'dir',
         ""),
        ),
    "windows-font": (
        "",
        ),
    "zoners_model_upgrade": (
        'unknown',
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
        ("Changes the current working directory, allowing Tool to operate on\n"
         "folders it isn't inside. This allows you to use one copy of tool for\n"
         "any number of separate tags directories and Halo CE installations."),
        ("directory", "dir",
         "The directory to set as the current working directory.\n"
         "This is an absolute path, meaning it is not relative to anything."),
        ),
    "set": (
        ("Adds a variable to a list that can be used for text replacements.\n"
         "To use the variable, you must put arrow braces around it.\n\n"
         "Example:\n"
         '    # set   dir   "levels\\test\\tutorial\\"\n\n'
         '    structure   <dir>tutorial\n'
         '    lightmaps   <dir>tutorial  tutorial  1  0.000001\n'
         '    build-cache-file   <dir>tutorial'),
        ("var-name", "str-no-quote", "Name of the variable."),
        ("var-value", "str",
         "The string to replace any occurances of <var-name> with."),
        ),
    "del": (
        ("Removes a variable from the list of replacements.\n"
         "See the 'set' directive."),
        ("var-name", "str-no-quote", "Name of the variable to remove."),
        ),
    "run": (
        "Runs the specified file located in the current working directoy.\n"
        "Any additional arguments after <exec-path> are passed along to the\n"
        "executable when it is ran.\n\n"
        "Example:\n"
        "    # run haloce.exe  -console  -devmode",
        ("exec-path", "file",
         "Name of the executable to run."),
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
        help_filepath = os.path.join(os.path.dirname(__file__), HELP_NAME)
        with open(help_filepath, "w") as f:
            f.write(help_text)

    return help_text


if __name__ == "__main__":
    try:
        generate_help(True)
    except Exception:
        print(traceback.format_exc())
