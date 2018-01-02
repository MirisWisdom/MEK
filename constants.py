from supyr_struct.defs.frozen_dict import FrozenDict

STYLE_CFG_NAME = "colors.txt"
LAST_CMD_LIST_NAME = ".recent"

BLACK_COLOR = '#%02x%02x%02x' % (0, 0, 0)  # black

COMMENT_START_STRS = (';', '/', )
DIRECTIVE_START_STRS = ('#', )

text_tags_colors = dict(
    default    = dict(
        bg = BLACK_COLOR,
        fg = '#%02x%02x%02x' % (192, 192, 192),  # very light grey
        bg_highlight = '#%02x%02x%02x' % (100, 100, 100)  # light grey
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

DIRECTIVES = FrozenDict({
    "k": (),
    "c": (),
    "cwd": (
        ("directory", '""'),
        ),
    "set": (
        ("var-name", '""'),
        ("var-value", '""'),
        ),
    "del": (
        ("var-name", '""'),
        ),
    })

TOOL_COMMANDS = FrozenDict({
    "animations": (
        ("source-directory", '""'),
        ),
    "bitmap": (
        ("source-file", '""'),
        ),
    "bitmaps": (
        ("source-directory", '""'),
        ),
    "build-cache-file": (
        ("scenario-name", '""'),
        ),
    "build-cache-file-ex": (
        ("mod-name",           '""'),
        ("create-anew",           0),
        ("store-resources",       0),
        ("use-memory-upgrades",   0),
        ("scenario-name",      '""'),
        ),
    "build-cache-file-new": (
        ("create-anew",           0),
        ("store-resources",       0),
        ("use-memory-upgrades",   0),
        ("scenario-name",      '""'),
        ),
    "build-cpp-definition": (
        ("tag-group",         '""'),
        ("add-boost-asserts",    0),
        ),
    "build-packed-file": (
        ("source-directory",    '""'),
        ("output-directory",    '""'),
        ("file-definition-xml", '""'),
        ),
    "collision-geometry": (
        ("source-directory", '""'),
        ),
    #"compile-scripts": (
    #    ("scenario-name", '""'),
    #    ),
    "compile-shader-postprocess": (
        ("shader-directory", '""'),
        ),
    "help": (
        ("os-tool-command", '""', (
            "animations",
            "bitmap",
            "bitmaps",
            "build-cache-file",
            "build-cache-file-ex",
            "build-cache-file-new",
            "build-cpp-definition",
            "build-packed-file",
            "collision-geometry",
            #"compile-scripts",
            "compile-shader-postprocess",
            "help",
            "hud-messages",
            "import-device-defaults",
            "import-structure-lightmap-uvs",
            "lightmaps",
            "merge-scenery",
            "model",
            "physics",
            "process-sounds",
            "remove-os-tag-data",
            "runtime-cache-view",
            "sounds",
            "sounds_by_type",
            "structure",
            "structure-breakable-surfaces",
            "structure-lens-flares",
            "tag-load-test",
            "unicode-strings",
            "windows-font",
            #"zoners_model_upgrade",
            )
         ),
        ),
    "hud-messages": (
        ("path",          '""'),
        ("scenario-name", '""'),
        ),
    "import-device-defaults": (
        ("type",          '""', ("defaults", "profiles")),
        ("savegame-path", '""'),
        ),
    "import-structure-lightmap-uvs": (
        ("structure-bsp", '""'),
        ("obj-file",      '""'),
        ),
    "lightmaps": (
        ("scenario",      '""'),
        ("bsp-name",      '""'),
        ("quality",        0.0),
        ("stop-threshold", 0.5),
        ),
    "merge-scenery": (
        ("source-scenario",      '""'),
        ("destination-scenario", '""'),
        ),
    "model": (
        ("source-directory", '""'),
        ),
    "physics": (
        ("source-file", '""'),
        ),
    "process-sounds": (
        ("root-path", '""'),
        ("substring", '""'),
        ("effect", "gain+",
             ("gain+", "gain-", "gain=", "maximum-distance", "minimum-distance"),
             ),
        ("value", 0.0),
        ),
    "remove-os-tag-data": (
        ("tag-name",       '""'),
        ("tag-type",       '""'),
        ("recursive", 0, (0, 1)),
        ),
    "runtime-cache-view": (),
    "sounds": (
        ("directory-name",            '""'),
        ("platform",                  'xbox', ("ogg", "xbox", "wav")),
        ("use-high-quality(ogg_only)", 1,     (0, 1)),
        ),
    "sounds_by_type": (
        ("directory-name", '""'),
        ("type",           '""'),
        ),
    "strings": (
        ("source-directory", '""'),
        ),
    "structure": (
        ("scenario-directory", '""'),
        ("bsp-name",           '""'),
        ),
    "structure-breakable-surfaces": (
        ("structure-name",   '""'),
        ),
    "structure-lens-flares": (
        ("bsp-name", '""'),
        ),
    "tag-load-test": (
        ("tag-name", '""'),
        ("group",    '""'),
        ("prompt-to-continue",       0, (0, 1)),
        ("load-non-resolving-refs",  0, (0, 1)),
        ("print-size",               0, (0, 1)),
        ("verbose",                  0, (0, 1)),
        ),
    "unicode-strings": (
        ("source-directory", '""'),
        ),
    "windows-font": (),
    #"zoners_model_upgrade": (),
    })
