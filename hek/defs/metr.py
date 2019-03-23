from ...common_descs import *
from .objs.tag import HekTag
from supyr_struct.defs.tag_def import TagDef


meter_body = Struct("tagdata",
    Pad(4),
    dependency("stencil bitmap", "bitm"),
    dependency("source bitmap",  "bitm"),

    SInt16("stencil sequence index"),
    SInt16("source sequence index"),
    Pad(20),
    SEnum16("interpolate colors",
        "linearly",
        "faster near empty",
        "faster near full",
        "through random noise"
        ),
    SEnum16("anchor colors" ,
        "at both ends",
        "at empty",
        "at full"
        ),
    Pad(8),
    QStruct("empty color", INCLUDE=argb_float),
    QStruct("full color",  INCLUDE=argb_float),
    Pad(20),
    Float("unmask distance", SIDETIP="meter units"),
    Float("mask distance", SIDETIP="meter units"),
    Pad(12),
    FlUInt16("screen x pos", SIDETIP="pixels"),
    FlUInt16("screen y pos", SIDETIP="pixels"),
    FlUInt16("width", SIDETIP="pixels"),
    FlUInt16("height", SIDETIP="pixels"),

    rawdata_ref("meter data", max_size=65536),
    SIZE=172, WIDGET=MeterImageFrame
    )

def get():
    return metr_def

metr_def = TagDef("metr",
    blam_header('metr'),
    meter_body,
    ext=".meter", endian=">", tag_cls=HekTag
    )
