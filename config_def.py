from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *
from .field_widgets import *
from .constants import *


def get():
    return config_def


config_header = Struct("header",
    UEnum32("id", ('Pool', 'looP'), DEFAULT='looP'),
    UInt32("version", DEFAULT=1),
    Bool32("flags",
        "sync_window_movement",
        DEFAULT=sum([1<<i for i in (0, 2, 3)]),
        ),

    Timestamp32("date_created"),
    Timestamp32("date_modified"),
    SIZE=64
    )

array_counts = Struct("array_counts",
    UInt32("directory_path_count"),
    UInt32("tool_paths_count"),
    UInt32("tool_cmd_list_count"),
    SIZE=64,
    )

app_window = Struct("app_window",
    UInt16("app_width", DEFAULT=400),
    UInt16("app_height", DEFAULT=300),
    SInt16("app_offset_x"),
    SInt16("app_offset_y"),
    SIZE=64,
    )

filepath = Container("filepath",
    UInt16("path_len"),
    StrUtf8("path", SIZE=".path_len")
    )

tool_command_list = Container("tool_command_list",
    UInt32("name_len"),
    UInt32("cmd_len"),
    StrUtf8("name",     SIZE=".name_len"),
    StrUtf8("commands", SIZE=".cmd_len"),
    )

config_def = TagDef("hek_pool_config",
    config_header,
    array_counts,
    app_window,
    Array("directory_paths", SUB_STRUCT=filepath,
        SIZE=".array_counts.directory_path_count",
        NAME_MAP=("last_load_dir", "curr_dir", "debug_log_path",)),
    Array("tool_paths", SUB_STRUCT=filepath,
        SIZE=".array_counts.tool_paths_count"),
    Array("tool_commands", SUB_STRUCT=tool_command_list,
        SIZE=".array_counts.tool_cmd_list_count"),
    ENDIAN='<', ext=".cfg",
    )
