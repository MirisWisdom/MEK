from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *
from supyr_struct.defs.constants import *

CFG_DIRS = (
    "working_dir",
    "last_load_dir",
    "commands_lists_dir",
    )

def get():
    return config_def


config_header = Struct("header",
    UEnum32("id", ('Pool', 'looP'), DEFAULT='looP'),
    UInt32("version", DEFAULT=1),
    Bool32("flags",
        "open_log",
        "clear_log",
        "smart_assist_on_rclick",
        "supress_tool_beta_errors",
        "null_physics_model_data",
        "install_ogg_dlls",
        DEFAULT=sum([1<<i for i in (2, 3, 4, 5)]),
        ),
    UInt32("max_undos", DEFAULT=1000),
    Pad(24 - 4*4),

    Timestamp32("date_created"),
    Timestamp32("date_modified"),

    UInt16("proc_limit", DEFAULT=1),
    UInt16("last_tool_index"),
    Pad(32 - 2*1),
    SIZE=64
    )

array_counts = Struct("array_counts",
    UInt16("directory_path_count"),
    UInt16("tool_paths_count"),
    SIZE=16,
    )

app_window = Struct("app_window",
    UInt16("app_width", DEFAULT=650),
    UInt16("app_height", DEFAULT=350),
    SInt16("app_offset_x"),
    SInt16("app_offset_y"),
    SIZE=16,
    )

filepath = Container("filepath",
    UInt16("path_len"),
    StrUtf8("path", SIZE=".path_len")
    )

config_def = TagDef("hek_pool_config",
    config_header,
    array_counts,
    app_window,
    Array("directory_paths", SUB_STRUCT=filepath,
        SIZE=".array_counts.directory_path_count", NAME_MAP=CFG_DIRS),
    Array("tool_paths", SUB_STRUCT=filepath,
        SIZE=".array_counts.tool_paths_count"),
    ENDIAN='<', ext=".cfg",
    )
