'''
Most byteswapping is handeled by supyr_struct by changing the endianness,
but certain chunks of raw data are significantly faster to just write
byteswapping routines for, like raw vertex, triangle, and animation data.
'''

from supyr_struct.field_types import BytearrayRaw
from supyr_struct.defs.block_def import BlockDef

raw_block_def = BlockDef("raw_block",
    BytearrayRaw('data',
        SIZE=lambda node, *a, **kw: 0 if node is None else len(node))
    )


def byteswap_raw_reflexive(refl):
    desc = refl.desc
    struct_size, two_byte_offs, four_byte_offs = desc.get(
        "RAW_REFLEXIVE_INFO", (0, (), ()))
    data = refl.STEPTREE
    refl.STEPTREE = swapped = bytearray(data)

    for refl_off in range(0, refl.size*struct_size, struct_size):
        for tmp_off in two_byte_offs:
            tmp_off += refl_off
            swapped[tmp_off]   = data[tmp_off+1]
            swapped[tmp_off+1] = data[tmp_off]

        for tmp_off in four_byte_offs:
            tmp_off += refl_off
            swapped[tmp_off]   = data[tmp_off+3]
            swapped[tmp_off+1] = data[tmp_off+2]
            swapped[tmp_off+2] = data[tmp_off+1]
            swapped[tmp_off+3] = data[tmp_off]


def byteswap_coll_bsp(bsp):
    for b in bsp:
        byteswap_raw_reflexive(b)


def byteswap_sbsp_meta(meta):
    if len(meta.collision_bsp.STEPTREE):
        for b in meta.collision_bsp.STEPTREE[0]:
            byteswap_raw_reflexive(b)

    for b in (meta.nodes, meta.leaves, meta.leaf_surfaces,
              meta.surface, meta.lens_flare_markers, meta.breakable_surfaces,
              meta.pathfinding_surfaces, meta.pathfinding_edges, meta.markers):
        byteswap_raw_reflexive(b)


def byteswap_uncomp_verts(verts_block):
    raw_block = verts_block.STEPTREE
    raw_data  = raw_block.data

    # replace the verts with the byteswapped and trimmed ones
    raw_block.data = new_raw = bytearray(68*(len(raw_data)//68))
    four_byte_field_offs = (0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44,
                            48, 52, 60, 64)
    # byteswap each of the floats, ints, and shorts
    for i in range(0, len(new_raw), 68):
        # byteswap the position floats and lighting vectors
        for j in four_byte_field_offs:
            j += i
            new_raw[j] = raw_data[j+3]
            new_raw[j+1] = raw_data[j+2]
            new_raw[j+2] = raw_data[j+1]
            new_raw[j+3] = raw_data[j]
        # byteswap the node indices
        new_raw[i+56] = raw_data[i+57]
        new_raw[i+57] = raw_data[i+56]
        new_raw[i+58] = raw_data[i+59]
        new_raw[i+59] = raw_data[i+58]

    # set the size of the reflexive
    verts_block.size = len(new_raw)//68


def byteswap_comp_verts(verts_block):
    raw_block = verts_block.STEPTREE
    raw_data  = raw_block.data

    # replace the verts with the byteswapped and trimmed ones
    raw_block.data = new_raw = bytearray(32*(len(raw_data)//32))
    four_byte_field_offs = (0, 4, 8, 12, 16, 20)
    # byteswap each of the floats, ints, and shorts
    for i in range(0, len(new_raw), 32):
        # byteswap the position floats and lighting vectors
        for j in four_byte_field_offs:
            j += i
            new_raw[j] = raw_data[j+3]
            new_raw[j+1] = raw_data[j+2]
            new_raw[j+2] = raw_data[j+1]
            new_raw[j+3] = raw_data[j]
        # byteswap the texture coordinates
        new_raw[i+24] = raw_data[i+25]
        new_raw[i+25] = raw_data[i+24]
        new_raw[i+26] = raw_data[i+27]
        new_raw[i+27] = raw_data[i+26]
        # copy over the node indices
        new_raw[i+28] = raw_data[i+28]
        new_raw[i+29] = raw_data[i+29]
        # byteswap the node weight
        new_raw[i+30] = raw_data[i+31]
        new_raw[i+31] = raw_data[i+30]

    # set the size of the reflexive
    verts_block.size = len(new_raw)//32


def byteswap_tris(tris_block):
    raw_block = tris_block.STEPTREE
    raw_data  = raw_block.data

    if len(raw_data)%6 == 4:
        raw_data.extend(b'\xff\xff')

    # replace the verts with the byteswapped and trimmed ones
    raw_block.data = new_raw = bytearray(6*(len(raw_data)//6))
    # byteswap each of the shorts
    for i in range(0, len(new_raw), 2):
        new_raw[i] = raw_data[i+1]
        new_raw[i+1] = raw_data[i]

    # set the size of the reflexive
    tris_block.size = len(new_raw)//6


def byteswap_animation(anim):
    frame_info   = anim.frame_info.STEPTREE
    default_data = anim.default_data.STEPTREE
    frame_data   = anim.frame_data.STEPTREE

    frame_count = anim.frame_count
    node_count  = anim.node_count
    uncomp_size = anim.frame_size * frame_count
    trans_flags = anim.trans_flags0 + (anim.trans_flags1<<32)
    rot_flags   = anim.rot_flags0   + (anim.rot_flags1<<32)
    scale_flags = anim.scale_flags0 + (anim.scale_flags1<<32)

    default_data_size = 0
    for n in range(node_count):
        if not rot_flags & (1<<n):
            default_data_size += 8
        if not trans_flags & (1<<n):
            default_data_size += 12
        if not scale_flags & (1<<n):
            default_data_size += 4

    new_frame_info   = bytearray(len(frame_info))
    new_default_data = bytearray(default_data_size)
    new_frame_data   = bytearray(uncomp_size)

    # byteswap the frame info
    for i in range(0, len(frame_info), 4):
        new_frame_info[i]   = frame_info[i+3]
        new_frame_info[i+1] = frame_info[i+2]
        new_frame_info[i+2] = frame_info[i+1]
        new_frame_info[i+3] = frame_info[i]

    if anim.flags.compressed_data:
        anim.offset_to_compressed_data = uncomp_size
        new_frame_data += frame_data
    else:
        i = 0
        swap = new_default_data
        raw = default_data
        # byteswap the default_data
        for n in range(node_count):
            if not rot_flags & (1<<n):
                for j in range(0, 8, 2):
                    swap[i] = raw[i+1]; swap[i+1] = raw[i]
                    i += 2

            if not trans_flags & (1<<n):
                for j in range(0, 12, 4):
                    swap[i] = raw[i+3];   swap[i+1] = raw[i+2]
                    swap[i+2] = raw[i+1]; swap[i+3] = raw[i]
                    i += 4

            if not scale_flags & (1<<n):
                swap[i] = raw[i+3]; swap[i+1] = raw[i+2]
                swap[i+2] = raw[i+1]; swap[i+3] = raw[i]
                i += 4

        i = 0
        swap = new_frame_data
        raw = frame_data
        # byteswap the frame_data
        for f in range(frame_count):
            for n in range(node_count):
                if rot_flags & (1<<n):
                    for j in range(0, 8, 2):
                        swap[i] = raw[i+1]; swap[i+1] = raw[i]
                        i += 2

                if trans_flags & (1<<n):
                    for j in range(0, 12, 4):
                        swap[i] = raw[i+3];   swap[i+1] = raw[i+2]
                        swap[i+2] = raw[i+1]; swap[i+3] = raw[i]
                        i += 4

                if scale_flags & (1<<n):
                    swap[i] = raw[i+3];   swap[i+1] = raw[i+2]
                    swap[i+2] = raw[i+1]; swap[i+3] = raw[i]
                    i += 4

    anim.frame_info.STEPTREE   = new_frame_info
    anim.default_data.STEPTREE = new_default_data
    anim.frame_data.STEPTREE   = new_frame_data
