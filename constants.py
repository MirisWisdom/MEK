from supyr_struct.defs.frozen_dict import FrozenDict

MAX_PROCESS_CT = 64

HELP_NAME = "pool_help.txt"
STYLE_CFG_NAME = "pool_colors.txt"
ACTIONS_CFG_NAME = "pool_actions.txt"
LAST_CMD_LIST_NAME = ".recent"
OGG_DLL_ZIP_NAME = "ogg_v1.1.2_dll_fix.zip"

BLACK_COLOR = '#%02x%02x%02x' % (0, 0, 0)  # black

COMMENT_START_STRS = (';', '/', )
DIRECTIVE_START_STRS = ('#', )

text_tags_colors = dict(
    default    = dict(
        bg = BLACK_COLOR,
        fg = '#%02x%02x%02x' % (192, 192, 192),  # very light grey
        bg_highlight = '#%02x%02x%02x' % (100, 100, 100)  # light grey
        ),
    error  = dict(
        bg = '#%02x%02x%02x' % (220,   0,   0),  # red
        fg = BLACK_COLOR,
        ),
    processing = dict(
        bg = '#%02x%02x%02x' % (255, 180,   0),  # yellow
        fg = BLACK_COLOR
        ),
    processed  = dict(
        bg = '#%02x%02x%02x' % (  0, 200,  50),  # green
        fg = BLACK_COLOR
        ),
    directive = dict(
        #bg = BLACK_COLOR,
        fg = '#%02x%02x%02x' % (220, 130,   0),  # orange
        ),
    commented = dict(
        #bg = BLACK_COLOR,
        fg = '#%02x%02x%02x' % (220,   0,   0),  # red
        ),
    )


ARG_TYPES = set((
    "int",
    "bool",
    "float",
    "str",
    "str-no-quote",
    "dir",
    "file",
    "file-no-ext",
    ))

'''
The descriptions of these commands and directives are set up as:

'command-name': (
    ('parameter-name',
        ('parameter-type',
            parameter-type-info_0,
            parameter-type-info_1,
            parameter-type-info_2,
            ...
            ),
        'default-value-as-string',
        (  # enumeration options
            "option_0",
            "option_1",
            "option_2",
            ...
            ),
        "base-dir-within-cwd"  # the directory this file/folder path is
                               # relative to within the cwd. currently
                               # only used for data and tags directories.
        )
    )
'''

SCNR_MACRO = (
    ("file-no-ext",
        ("scenario", "*.scenario"),
        ),
    '""',
    (),
    "tags"
    )
INT_MACRO   = ("int",   "0")
BOOL_MACRO  = ("bool",  "0")
FLOAT_MACRO = ("float", "0.0")
FILE_MACRO  = ("file",  '""')
DIR_MACRO   = ("dir",   '""')
STR_MACRO   = ("str",   '""')
FILE_NO_EXT_MACRO  = ("file-no-ext",  '""')
STR_NO_PAREN_MACRO = ("str-no-quote", 'XXXX')

DATA_DIR_MACRO = DIR_MACRO + ( (), "data")
TAGS_DIR_MACRO = DIR_MACRO + ( (), "tags")


DIRECTIVES = FrozenDict({
    "k": (),
    "c": (),
    "cwd": (
        ("directory", ) + DIR_MACRO,
        ),
    "set": (
        ("var-name", )  + STR_NO_PAREN_MACRO,
        ("var-value", ) + STR_MACRO,
        ),
    "del": (
        ("var-name", ) + STR_NO_PAREN_MACRO,
        ),
    "run": (
        ("exec-path", ) + FILE_MACRO,
        ),
    "w": (),
    })

TOOL_COMMANDS = FrozenDict({
    "animations": (
        ("source-directory", ) + DATA_DIR_MACRO,
        ),
    "bitmap": (
        ("source-file",
            ("file-no-ext",
                ("TIFF Image", "*.tif")
                ),
            '""',
            (),
            "data"
            ),
        ),
    "bitmaps": (
        ("source-directory", ) + DATA_DIR_MACRO,
        ),
    "build-cache-file": (
        ("scenario-path", ) + SCNR_MACRO,
        ),
    "build-cache-file-ex": (
        ("mod-name",            ) + STR_MACRO,
        ("create-anew",         ) + BOOL_MACRO,
        ("store-resources",     ) + BOOL_MACRO,
        ("use-memory-upgrades", ) + BOOL_MACRO,
        ("scenario-path",       ) + SCNR_MACRO,
        ),
    "build-cache-file-new": (
        ("create-anew",           ) + BOOL_MACRO,
        ("store-resources",       ) + BOOL_MACRO,
        ("use-memory-upgrades",   ) + BOOL_MACRO,
        ("scenario-path",         ) + SCNR_MACRO,
        ),
    "build-cpp-definition": (
        ("tag-group",         ) + STR_NO_PAREN_MACRO,
        ("add-boost-asserts", ) + BOOL_MACRO,
        ),
    "build-packed-file": (
        ("source-directory", ) + DATA_DIR_MACRO,
        ("output-directory", ) + DATA_DIR_MACRO,
        ("file-definition-xml",
            ("file-no-ext",
                ("XML definition", "*.xml")
                ),
            '""'
            ),
        ),
    "collision-geometry": (
        ("source-directory", ) + DATA_DIR_MACRO,
        ),
    "compile-scripts": (
        ("scenario-path", ) + SCNR_MACRO,
        ),
    "compile-shader-postprocess": (
        ("shader-directory", ) + DATA_DIR_MACRO,
        ),
    "help": (
        ("os-tool-command", "str-no-quote", 'help', (
            # these are the only ones the help command will work with
            "build-cache-file",
            "build-cache-file-ex",
            "compile-shader-postprocess",
            "help",
            "import-structure-lightmap-uvs",
            "remove-os-tag-data",
            "runtime-cache-view",
            "sounds_by_type",
            "tag-load-test",
            )
         ),
        ),
    "hud-messages": (
        ("hmt-path",      ) + DATA_DIR_MACRO,
        ("scenario-path", ) + STR_MACRO,
        ),
    "import-device-defaults": (
        ("type",  "str-no-quote",  'defaults', ("defaults", "profiles")),
        ("savegame-path", ) + FILE_MACRO,
        ),
    "import-structure-lightmap-uvs": (
        ("structure-bsp-path",
            ("file-no-ext",
                ("structure scenario bsp", "*.structure_scenario_bsp")
                ),
            '""',
            'tags'
            ),
        ("obj-file-path",
            ("file-no-ext",
                ("OBJ model file", "*.obj")
                ),
            '""',
            'data'
            )
        ),
    "lightmaps": (
        ("scenario-path",        ) + SCNR_MACRO,
        ("bsp-name",             ) + STR_MACRO,
        ("render-high-quality",  ) + BOOL_MACRO,
        ("stop-threshold", "float", "0.1", (float("1e-45"), 1.0)),
        ),
    "merge-scenery": (
        ("source-scenario",      ) + SCNR_MACRO,
        ("destination-scenario", ) + SCNR_MACRO,
        ),
    "model": (
        ("source-directory", ) + DATA_DIR_MACRO,
        ),
    "physics": (
        ("source-directory", ) + DATA_DIR_MACRO,
        ),
    "process-sounds": (
        ("root-path", ) + DIR_MACRO,
        ("substring", ) + STR_MACRO,
        ("effect", "str-no-quote", "gain+",
             ("gain+", "gain-", "gain=",
              "maximum-distance", "minimum-distance"),
             ),
        ("value",     ) + FLOAT_MACRO,
        ),
    "remove-os-tag-data": (
        ("tag-path",  ) + STR_MACRO,
        ("tag-type",  ) + STR_NO_PAREN_MACRO,
        ("recursive", ) + BOOL_MACRO,
        ),
    "runtime-cache-view": (),
    "sounds": (
        ("directory-path",             ) + DATA_DIR_MACRO,
        ("platform", "str-no-quote", 'xbox', ("ogg", "xbox", "wav")),
        ("ogg-quality", "float", "1.0", (-0.09999999, 1.0)),
        ),
    "sounds_by_type": (
        ("directory-path",      ) + DATA_DIR_MACRO,
        ("type",                ) + STR_MACRO,
        ("round-to-64-samples", ) + BOOL_MACRO,
        ),
    "strings": (
        ("source-directory", ) + DATA_DIR_MACRO,
        ),
    "structure": (
        ("scenario-directory", ) + DATA_DIR_MACRO,
        ("bsp-name",           ) + STR_MACRO,
        ),
    "structure-breakable-surfaces": (
        ("structure-path",
            ("file-no-ext",
                ("sbsp", "*.scenario_structure_bsp"),
                ),
            '""',
            (),
            "tags"
            ),
        ),
    "structure-lens-flares": (
        ("structure-path",
            ("file-no-ext",
                ("sbsp", "*.scenario_structure_bsp"),
                ),
            '""',
            (),
            "tags"
            ),
        ),
    "tag-load-test": (
        ("tag-path",                ) + FILE_NO_EXT_MACRO,
        ("group",                   ) + STR_NO_PAREN_MACRO,
        ("prompt-to-continue",      ) + BOOL_MACRO,
        ("load-non-resolving-refs", ) + BOOL_MACRO,
        ("print-size",              ) + BOOL_MACRO,
        ("verbose",                 ) + BOOL_MACRO,
        ),
    "unicode-strings": (
        ("source-directory", ) + DATA_DIR_MACRO,
        ),
    "windows-font": (),
    "zoners_model_upgrade": (),
    })


SPECIAL_ACTIONS_KWDS = FrozenDict({
    "<<cut>>": "Cuts the selected text out and puts it into the clipboard.",
    "<<copy>>": "Copies the selected text into the clipboard.",
    "<<paste>>": "Pastes the text from the clipboard into the text.",
    "<<divider>>": "Inserts a horizontal divider into the menu.",
    })


ACTION_MENU_LAYOUT = [
    "<<cut>>",
    "<<copy>>",
    "<<paste>>",
    "<<divider>>",
    ("Most Useful",
        "animations",
        "bitmap",
        "bitmaps",
        "build-cache-file",
        "build-cache-file-ex",
        "collision-geometry",
        "lightmaps",
        "model",
        "physics",
        "sounds",
        "strings",
        "structure",
        "unicode-strings",
        ),
    ("Objects",
        "animations",
        "bitmap",
        "bitmaps",
        "collision-geometry",
        "model",
        "physics",
        "sounds",
        ),
    ("Map / Scenario",
        "build-cache-file",
        "build-cache-file-ex",
        "import-structure-lightmap-uvs",
        "lightmaps",
        "merge-scenery",
        "structure",
        "structure-breakable-surfaces",
        "structure-lens-flares",
        ),
    ("Strings",
        "hud-messages",
        "strings",
        "unicode-strings",
        ),
    ("Misc",
        "bitmap",
        "bitmaps",
        "build-cpp-definition",
        "compile-shader-postprocess",
        "import-device-defaults",
        "remove-os-tag-data",
        "runtime-cache-view",
        "sounds",
        "tag-load-test",
        "windows-font",
        ),
    "<<divider>>",
    ("All Pool Directives", *(k for k in sorted(DIRECTIVES))),
    ]
