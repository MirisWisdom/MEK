
from array import array
from os.path import splitext

from ...field_types import *
from ..defs.objs.bitm import *

from reclaimer.resources.arbytmap import arbytmap as ab
from reclaimer.resources import p8_palette


"""##################"""
### CHANNEL MAPPINGS ###
"""##################"""


"""These channel mappings are for swapping MULTIPURPOSE channels from
pc to xbox format and vice versa from 4 channel source to 4 channel target"""
#                      (A, R, G, B)
PC_ARGB_TO_XBOX_ARGB = (1, 3, 2, 0)
XBOX_ARGB_TO_PC_ARGB = (3, 0, 2, 1)

AY_COMBO_TO_AY   = ( 0, 0 )
AY_COMBO_TO_ARGB = ( 0,  0,  0,  0)

FORMAT_NAME_MAP = {
    -1:None,
    0:"A8", 1:"Y8", 2:"AY8", 3:"A8Y8",
    4:"UNUSED1",5:"UNUSED2",
    6:"R5G6B5", 7:"UNUSED3", 8:"A1R5G5B5", 9:"A4R4G4B4",
    10:"X8R8G8B8", 11:"A8R8G8B8",
    12:"UNUSED4", 13:"UNUSED5",
    14:"DXT1", 15:"DXT3", 16:"DXT5", 17:"P8-BUMP"}

I_FORMAT_NAME_MAP = {
    "A8":0, "Y8":1, "AY8":2, "A8Y8":3,
    "UNUSED1":4, "UNUSED2":5,
    "R5G6B5":6, "UNUSED3":7, "A1R5G5B5":8, "A4R4G4B4":9,
    "X8R8G8B8":10, "A8R8G8B8":11,
    "UNUSED4":12, "UNUSED5":13,
    "DXT1":14, "DXT3":15, "DXT5":16, "P8-BUMP":17}

TYPE_NAME_MAP = ["2D", "3D", "CUBE"]

global tex_infos
tex_infos = []


#load the palette for p-8 bump maps
P8_PALETTE = p8_palette.load_palette()

ab.FORMAT_P8 = "P8-BUMP"

"""ADD THE P8 FORMAT TO THE BITMAP CONVERTER"""
ab.define_format(
    format_id=ab.FORMAT_P8, raw_format=True, channel_count=4,
    depths=(8,8,8,8), offsets=(24,16,8,0),
    masks=(4278190080, 16711680, 65280, 255))

'''Constants that determine which index
each of the flags are in per tag'''
DONT_REPROCESS = 0
RENAME_OLD = 1
READ_ONLY = 2
WRITE_LOG = 3
PLATFORM = 4
SWIZZLED = 5
DOWNRES = 6
MULTI_SWAP = 7
CUTOFF_BIAS = 8
P8_MODE = 9
MONO_KEEP = 10
MONO_SWAP = 11
CK_TRANS = 12
NEW_FORMAT = 13
MIP_GEN = 14
GAMMA = 15
EXTRACT_TO = 16

def process_bitmap_tag(tag):
    '''this function will return whether or not the conversion
    routine below should be run on a bitmap based on its format,
    type, etc and how they compare to the conversion variablers'''
    
    flags = tag.tag_conversion_settings
    
    #check if the bitmap has already been processed, or
    #is a PC bitmap or if we are just creating a debug log
    if tag.processed_by_reclaimer or not(tag.is_xbox_bitmap):
        format = tag.bitmap_format()

        #if all these are true we skip the tag
        if ( flags[DOWNRES]=='0' and flags[MULTI_SWAP] == 0 and
             flags[NEW_FORMAT] == FORMAT_NONE and flags[MIP_GEN]== False and
             tag.is_xbox_bitmap == flags[PLATFORM] and
             (flags[MONO_SWAP] == False or format!= FORMAT_A8Y8) and
             (tag.swizzled() == flags[SWIZZLED] or
              FORMAT_NAME_MAP[format] in ab.DDS_FORMATS) ):
            return False
    return True


def extracting_texture(tag):
    '''determines if a texture extraction is to take place'''
    return tag.tag_conversion_settings[EXTRACT_TO] != " "


def convert_bitmap_tag(tag, **kwargs):
    '''tons of possibilities here. not gonna try to name
    them. Basically this is the main conversion routine'''
    del tex_infos[:]

    conversion_flags = tag.tag_conversion_settings
    tagsdir = tag.handler.tagsdir

    root_window = kwargs.get("root_window",None)
    tagpath = kwargs.get("tagpath",tag.filepath.split(tagsdir)[-1])
    conversion_report = kwargs.get("conversion_report",{})
    reprocess = kwargs.get("reprocess", False)
    
    '''if ANY of the bitmaps does not have a power of 2
    dimensions height/width/depth then we need to break
    out of this since we can't work with it properly'''
    for i in range(tag.bitmap_count()):
        if not(tag.is_power_of_2_bitmap(i)):
            conversion_report[tagpath] = False
            return False
    

    """GET THE FLAGS FOR THE CONVERSION SETTINGS
    THAT DON'T DEPEND ON BITMAP FORMAT OR TYPE"""
    save_as_xbox = conversion_flags[PLATFORM]
    swizzle_mode = conversion_flags[SWIZZLED]
    downres_amount = int(conversion_flags[DOWNRES])
    alpha_cutoff_bias = int(conversion_flags[CUTOFF_BIAS])
    p8_mode = conversion_flags[P8_MODE]
    channel_to_keep = conversion_flags[MONO_KEEP]
    ck_transparency = conversion_flags[CK_TRANS]
    new_format = FORMAT_NAME_MAP[conversion_flags[NEW_FORMAT]]
    multi_swap = conversion_flags[MULTI_SWAP]
    mono_swap = conversion_flags[MONO_SWAP]
    gamma = conversion_flags[GAMMA]
    generate_mipmaps = conversion_flags[MIP_GEN]
    export_format = conversion_flags[EXTRACT_TO]

    processing = process_bitmap_tag(tag)

    """CREATE THE BITMAP CONVERTER MODULE"""
    bm = ab.Arbytmap()

    '''BEFORE WE TRY TO LOAD THE PIXEL DATA WE NEED TO
    MAKE SURE THE DESCRIPTION OF EACH BITMAP IS WORKABLE'''
    bad_bitmaps = fix_mipmap_counts(tag)

    if len(bad_bitmaps) > 0:
        print("WARNING: BAD BITMAP BLOCK INFORMATION ENCOUNTERED "+
              "WHILE PROCESSING THIS TAG:\n", tagpath, "\n",
              "THE INDEXES THAT WERE BAD ARE AS FOLLOWS:", bad_bitmaps,
              "\nCannot process bitmap until you manually fix this.\n")
        load_status = False
    else:
        '''CONVERT THE RAW PIXEL DATA INTO ORGANIZED ARRAYS OF PIXELS'''
        load_status = parse_bitmap_blocks(tag)

    #If an error was encountered during the load
    #attempt or the conversion was cancelled we quit
    if root_window and (not load_status or root_window.conversion_cancelled):
        conversion_report[tagpath] = False
        return False
        
    """LOOP THROUGH ALL THE BITMAPS, FIGURE OUT
    HOW THEY'RE BEING CONVERTED AND CONVERT THEM"""
    for i in range(tag.bitmap_count()):
        format = FORMAT_NAME_MAP[tag.bitmap_format(i)]
        type   = TYPE_NAME_MAP[tag.bitmap_type(i)]
        target_format = new_format

        #get the texture block to be loaded
        tex_block = list(tag.data.tagdata.processed_pixel_data.data[i])
        tex_info = tex_infos[i]

        """MAKE SOME CHECKS TO FIGURE OUT WHICH FORMAT WE ARE
        REALLY CONVERTING TO (IT'S NOT STRAIGHTFORWARD)"""
        if target_format == ab.FORMAT_P8:
            #since this button is shared between
            #p-8 and 32 bit we make another check
            #also make sure this ISN'T a cubemap
            if (format in (ab.FORMAT_R5G6B5, ab.FORMAT_A1R5G5B5,
                           ab.FORMAT_A4R4G4B4, ab.FORMAT_X8R8G8B8,
                           ab.FORMAT_A8R8G8B8) and type != ab.TYPE_CUBEMAP):
                target_format = ab.FORMAT_P8
            elif format == ab.FORMAT_Y8:
                target_format = ab.FORMAT_X8R8G8B8
            else:
                target_format = ab.FORMAT_A8R8G8B8
                
        elif target_format not in ab.VALID_FORMATS:
            target_format = format
        else:
            if target_format in ab.DDS_FORMATS and type == "3D":
                target_format = format
                print("CANNOT CONVERT 3D TEXTURES TO DXT FORMAT.")
                
            if not(channel_to_keep) and target_format == ab.FORMAT_A8:
                target_format = ab.FORMAT_Y8
                
            """ SINCE THESE THREE FORMATS CAN BE EASILY INTERCHANGED JUST
            BY CHANGING THE FORMAT IDENTIFIER, THAT'S WHAT WE'LL DO"""
            if (format in (ab.FORMAT_A8, ab.FORMAT_Y8, ab.FORMAT_AY8) and
                target_format in (ab.FORMAT_A8, ab.FORMAT_Y8, ab.FORMAT_AY8)):
                tex_info["format"] = format = target_format


        """CHOOSE WHICH CHANNEL MAPPINGS TO USE
        AND DO EXTRA TARGET FORMAT CHECKS"""
        channel_mapping, channel_merge_mapping, target_format = \
                         get_channel_mappings(format, mono_swap, target_format,
                                              multi_swap, channel_to_keep)
        palette_picker = None
        palettize = True
        
        """IF WE ARE CONVERTING TO P8 THIS IS
        WHERE WE SELECT THE SPECIFIC SETTINGS"""
        if format == ab.FORMAT_P8:
            palette_picker = P8_PALETTE.argb_array_to_p8_array_auto
        elif target_format != ab.FORMAT_P8:
            palettize = False
        elif ab.FORMAT_CHANNEL_COUNTS[format] != 4:
            pass
        elif ck_transparency and format not in (ab.FORMAT_X8R8G8B8,
                                                ab.FORMAT_R5G6B5):
            #auto-bias
            if p8_mode == 0:
                palette_picker = P8_PALETTE.argb_array_to_p8_array_auto_alpha
            else:#average-bias
                palette_picker = P8_PALETTE.argb_array_to_p8_array_average_alpha
        elif p8_mode == 0:
            #auto-bias
            palette_picker = P8_PALETTE.argb_array_to_p8_array_auto
        else:
            #average-bias
            palette_picker = P8_PALETTE.argb_array_to_p8_array_average

        #we want to preserve the color key transparency of
        #the original image if converting to the same format
        if (format == target_format and
            target_format in (ab.FORMAT_P8, ab.FORMAT_DXT1)):
            ck_transparency = True

        """LOAD THE TEXTURE INTO THE BITMAP CONVERTER"""
        bm.load_new_texture(texture_block = tex_block,
                            texture_info = tex_info)
        
        #build the initial conversion settings list from the above settings
        conv_settings = dict(
            swizzle_mode=swizzle_mode, one_bit_bias=alpha_cutoff_bias,
            downres_amount=downres_amount, palettize=palettize,
            color_key_transparency=ck_transparency,
            gamma=gamma, generate_mipmaps=generate_mipmaps)


        #add the variable settings into the conversion settings list
        conv_settings["target_format"] = target_format
        if channel_mapping is not None:
            conv_settings["channel_mapping"] = channel_mapping
        if channel_merge_mapping is not None:
            conv_settings["channel_merge_mapping"] = channel_merge_mapping
        if palette_picker is not None:
            conv_settings["palette_picker"] = palette_picker

        if conv_settings["target_format"] != ab.FORMAT_P8:
            conv_settings["palettize"] = False

        """LOAD THE CONVERSION SETTINGS INTO THE BITMAP CONVERTER"""
        bm.load_new_conversion_settings(**conv_settings)

        """RUN THE CONVERSION ROUTINE ON THE BITMAP CONVERTOR"""
        status = True
        if processing:
            status = bm.convert_texture()
        if export_format != " ":
            path = bm.filepath
            if tag.bitmap_count() > 1:
                path += ("_"+str(i))
            bm.save_to_file(output_path=path, ext=export_format)
                

        """IF THE CONVERSION WAS SUCCESSFUL WE UPDATE THE
        TAG'S DATA TO THE NEW FORMAT AND SWIZZLE MODE.
        IF WE WERE ONLY EXTRACTING THE TEXTURE WE DON'T RESAVE THE TAG"""
        if status and (processing or reprocess):
            tex_root = tag.data.tagdata.processed_pixel_data.data[i]

            #set the data block to the newly converted one
            tex_root.parse(initdata=bm.texture_block)

            #set the flag showing that the bitmap
            #is either swizzled or not swizzled
            tag.swizzled(bm.swizzled, i)

            #change the bitmap format to the new format
            tag.bitmap_format(i, I_FORMAT_NAME_MAP[target_format])
        elif not extracting_texture(tag):
            print("Error occurred while attempting to convert the tag:")
            print(tagpath+"\n")
            conversion_report[tagpath] = False
            return False
        
    if processing or reprocess:
        """RECALCULATE THE BITMAP HEADER AND FOOTER
        DATA AFTER POSSIBLY CHANGING IT ABOVE"""
        bitmap_sanitize(tag)
        
        #SET THE TAG'S CHARACTERISTICS TO XBOX OR PC FORMAT
        tag.set_platform(save_as_xbox)

        #SET THE "PROCESSED BY RECLAIMER" FLAG
        tag.processed_by_reclaimer(True)
        
        #IF THE FORMAT IS P8 OR PLATFORM IS XBOX WE NEED TO ADD PADDING
        add_bitmap_padding(tag, save_as_xbox)
        """FINISH BY RESAVING THE TAG"""
        try:
            save_status = tag.serialize()
            conversion_report[tagpath] = True
        except Exception:
            print(format_exc())
            conversion_report[tagpath] = save_status = False
        return save_status
    elif export_format == " ":
        conversion_report[tagpath] = False
        return False
    
    conversion_report[tagpath] = None
    return None


def parse_bitmap_blocks(tag):
    '''converts the raw pixel data into arrays of pixel
    data and replaces the raw data in the tag with them'''
    
    pixel_data = tag.data.tagdata.processed_pixel_data
    rawdata = pixel_data.data

    tagsdir = tag.handler.tagsdir
    datadir = tag.handler.datadir
    
    #this is the block that will hold all of the bitmap blocks
    root_tex_block = tag.definition.subdefs['pixel_root'].build()

    is_xbox = tag.is_xbox_bitmap
    get_mip_dims = ab.get_mipmap_dimensions
    bytes_to_array = ab.bitmap_io.bitmap_bytes_to_array
    
    #Read the pixel data blocks for each bitmap
    for i in range(tag.bitmap_count()):
        #since we need this information to read the bitmap we extract it
        mw, mh, md, = tag.bitmap_width_height_depth(i)
        type         = tag.bitmap_type(i)
        format       = FORMAT_NAME_MAP[tag.bitmap_format(i)]
        mipmap_count = tag.bitmap_mipmaps_count(i) + 1
        sub_bitmap_count = ab.SUB_BITMAP_COUNTS[TYPE_NAME_MAP[type]]

        #Get the offset of the pixel data for
        #this bitmap within the raw pixel data
        off = tag.bitmap_data_offset(i)

        #this texture info is used in manipulating the texture data
        tex_infos.append(dict(
            width=mw, height=mh, depth=md, format=format,
            mipmap_count=(mipmap_count-1), sub_bitmap_count=sub_bitmap_count,
            swizzled=tag.swizzled(), texture_type=TYPE_NAME_MAP[type],
            filepath=splitext(tag.filepath.replace(tagsdir,datadir))[0]))
        
        """IF THE TEXTURE IS IN P-8 FORMAT THEN WE NEED TO
        PROVIDE THE PALETTE AND SOME INFORMATION ABOUT IT"""
        if format == ab.FORMAT_P8:
            tex_infos[-1]["palette"] = [
                P8_PALETTE.p8_palette_32bit_packed[0]]*mipmap_count

            # set it to packed since if we need to drop channels
            # then it needs to be unpacked with channels dropped
            tex_infos[-1]["palette_packed"] = True
            tex_infos[-1]["indexing_size"] = 8
        
        '''this is the block that will hold each mipmap,
        texture slice, and cube face of the bitmap'''
        root_tex_block.append()
        tex_block = root_tex_block[-1]

        # xbox bitmaps are stored all mip level faces first, then
        # the next mip level, whereas pc is the other way. Xbox
        # bitmaps also have padding between each mipmap and bitmap.
        dim0 = sub_bitmap_count if is_xbox else mipmap_count
        dim1 = mipmap_count if is_xbox else sub_bitmap_count
        for j in range(dim0):
            if not is_xbox: w, h, d = get_mip_dims(mw, mh, md, j, format)

            for k in range(dim1):
                if is_xbox: w, h, d = get_mip_dims(mw, mh, md, k, format)

                if format == ab.FORMAT_P8:
                    pixel_count = w*h
                    tex_block.append(array('B', rawdata[off: off+pixel_count]))
                    off += pixel_count
                    continue

                off = bytes_to_array(rawdata, off, tex_block, format, w, h, d)
            
            # skip the xbox alignment padding to get to the next texture
            if is_xbox:
                tex_pad, sub_tex_pad = calc_padding_size(tag, i)
                off += sub_tex_pad
                if j + 1 == dim0:
                    off += tex_pad

    pixel_data.data = root_tex_block
    '''now that we've successfully built the bitmap
    blocks from the raw data we replace the raw data'''
    if is_xbox:
        '''it's easier to work with bitmaps in one format so
        we'll switch the mipmaps from XBOX to PC ordering'''
        tag.change_sub_bitmap_ordering(False)

    return True



def fix_mipmap_counts(tag):
    '''Some original xbox bitmaps have fudged up mipmap counts and cause issues.
    This function will scan through all a bitmap's bitmaps and check that they
    fit within their calculated pixel data bounds. This is done by checking if
    a bitmap's calculated size is both within the side of the total pixel data
    and less than the next bitmap's pixel data start'''
    
    bad_bitmap_index_list = []
    bitmap_count = tag.bitmap_count()
    
    for i in range(bitmap_count):

        #if this is the last bitmap
        if i + 1 == bitmap_count:
            #this is how many bytes of texture data there is total
            max_size = tag.pixel_data_bytes_size()
        else:
            #this is the start of the next bitmap's pixel data
            max_size = tag.bitmap_data_offset(i+1)
        
        while True:
            mipmap_count = tag.bitmap_mipmaps_count(i)
            curr_size = calc_bitmap_size(tag, i) + tag.bitmap_data_offset(i)

            if curr_size <= max_size:
                break

            tag.bitmap_mipmaps_count(i, mipmap_count - 1)

            #the mipmap count is zero and the bitmap still will
            #not fit within the space provided. Something's wrong
            if mipmap_count == 0:
                bad_bitmap_index_list.append(i)
                break

    return bad_bitmap_index_list


def add_bitmap_padding(tag, save_as_xbox):
    '''Given a tag, this function will create and apply padding to
    each of the bitmaps in it to make it XBOX compatible. This function
    will also add the number of bytes of padding to the internal offsets'''

    """The offset of each bitmap's pixel data needs to be increased by
    the padding of all the bitmaps before it. This variable will be
    used for knowing the total amount of padding before each bitmap.

    DO NOT RUN IF A BITMAP ALREADY HAS PADDING."""
    total_data_size = 0

    for i in range(tag.bitmap_count()):
        sub_bitmap_count = 1
        if tag.bitmap_type(i) == TYPE_CUBEMAP:
            sub_bitmap_count = 6
            
        pixel_data_block = tag.data.tagdata.processed_pixel_data.data[i]

        """BECAUSE THESE OFFSETS ARE THE BEGINNING OF THE PIXEL
        DATA WE ADD THE NUMBER OF BYTES OF PIXEL DATA BEFORE
        WE CALCULATE THE NUMBER OF BYTES OF THIS ONE"""
        #apply the offset to the tag
        tag.bitmap_data_offset(i, total_data_size)

        """ONLY ADD PADDING IF THE BITMAP IS P8 FORMAT OR GOING ON XBOX"""
        if save_as_xbox or tag.bitmap_format(i) == ab.FORMAT_P8:
            #calculate how much padding to add to the xbox bitmaps
            bitmap_pad, cubemap_pad = calc_padding_size(tag, i)
            
            #add the number of bytes of padding to the total
            total_data_size += bitmap_pad + cubemap_pad*sub_bitmap_count

            #if this bitmap has padding on each of the sub-bitmaps
            if cubemap_pad:
                mipmap_count = tag.bitmap_mipmaps_count(i) + 1
                for j in range(0, 6*(mipmap_count + 1), mipmap_count + 1):
                    pad = bytearray(cubemap_pad)
                    if isinstance(pixel_data_block[0], array):
                        pad = array('B', pad)
                    pixel_data_block.insert(j + mipmap_count, pad)
                    
            #add the main padding to the end of the bitmap block
            pad = bytearray(bitmap_pad)
            if isinstance(pixel_data_block[0], array):
                pad = array('B', pad)
            pixel_data_block.append(pad)

        #add the number of bytes this bitmap is to the
        #total bytes so far(multiple by sub-bitmap count)
        total_data_size += calc_bitmap_size(tag, i)*sub_bitmap_count

    #update the total number of bytes of pixel data
    #in the tag by all the padding that was added
    tag.pixel_data_bytes_size(total_data_size)


def calc_bitmap_size(tag, b_index):
    '''Given a bitmap index and a tag, this function
    will calculate how many bytes the data takes up.
    THIS FUNCTION WILL NOT TAKE INTO ACCOUNT THE NUMBER OF SUB-BITMAPS'''

    #since we need this information to read the bitmap we extract it
    mw, mh, md, = tag.bitmap_width_height_depth(b_index)
    format = FORMAT_NAME_MAP[tag.bitmap_format(b_index)]

    #this is used to hold how many pixels in
    #total all this bitmaps mipmaps add up to
    pixel_count = 0
    
    for mipmap in range(tag.bitmap_mipmaps_count(b_index) + 1):
        w, h, d = ab.get_mipmap_dimensions(mw, mh, md, mipmap, format)
        pixel_count += w*h*d

    bytes_count = pixel_count
    #based on the format, each pixel takes up a different amount of bytes
    if format != ab.FORMAT_P8:
        bytes_count = (bytes_count * ab.BITS_PER_PIXEL[format])//8

    return bytes_count
            


def calc_padding_size(tag, b_index):
    '''Calculates how many bytes of padding need to be added
    to a bitmap to properly align it in the texture cache'''

    #first we need to know how many bytes the bitmap data takes up
    bytes_count = calc_bitmap_size(tag, b_index)
    cubemap_pad = 0

    #if there are sub-bitmaps we calculate the amount of padding for them
    if tag.bitmap_type(b_index) == TYPE_CUBEMAP:
        cubemap_pad = ((CUBEMAP_PADDING - (bytes_count % CUBEMAP_PADDING))
                       % CUBEMAP_PADDING)
        bytes_count = (bytes_count + cubemap_pad) * 6

    bitmap_pad = (BITMAP_PADDING - (bytes_count%BITMAP_PADDING))%BITMAP_PADDING
    
    return (bitmap_pad, cubemap_pad)


def bitmap_sanitize(tag):
    '''after we've edited with the bitmap in whatever ways we did this will
    tie up all the loose ends and recalculate all the offsets and stuff'''
    
    #Prune the original TIFF data from the tag
    tag.data.tagdata.compressed_color_plate_data.data = bytearray()

    #Read the pixel data blocks for each bitmap
    for i in range(tag.bitmap_count()):
        format = FORMAT_NAME_MAP[tag.bitmap_format(i)]
        flags = tag.bitmap_flags(i)
        old_w, old_h, _ = tag.bitmap_width_height_depth(i)
        
        reg_point_x, reg_point_y = tag.registration_point_xy(i)
        texinfo = tex_infos[i]
        
        #set the flags to the new value
        flags.palletized = (format == ab.FORMAT_P8)
        flags.compressed = (format in ab.COMPRESSED_FORMATS)
        
        tag.bitmap_width_height_depth(
            i, (texinfo["width"], texinfo["height"], texinfo["depth"]))
        tag.bitmap_mipmaps_count(i, texinfo["mipmap_count"])
        tag.registration_point_xy(i, (texinfo["width"]*reg_point_x//old_w,
                                      texinfo["height"]*reg_point_y//old_h))


def get_channel_mappings(format, mono_swap, target_format,
                         multi_swap, channel_to_keep):
    """Goes through a ton of checks to figure out which channel
    mapping to use for converting(and returns it). Also checks a
    few exception cases where converting to that format would
    be bad and instead resets the target format to the source format"""
    
    channel_count = ab.FORMAT_CHANNEL_COUNTS[format]
    target_channel_count = ab.FORMAT_CHANNEL_COUNTS[target_format]
    channel_mapping = None
    channel_merge_mapping = None
    if channel_count == 4:
        if target_channel_count == 4:
            """THIS TAKES CARE OF ALL THE MULTIPURPOSE CHANNEL SWAPPING"""
            if multi_swap == 1:
                #SWAP CHANNELS FROM PC TO XBOX
                channel_mapping = PC_ARGB_TO_XBOX_ARGB

            elif multi_swap == 2:
                #SWAP CHANNELS FROM XBOX TO PC
                channel_mapping = XBOX_ARGB_TO_PC_ARGB

        elif target_format in (ab.FORMAT_A8, ab.FORMAT_Y8,
                             ab.FORMAT_AY8, ab.FORMAT_P8):
            """THIS AND THE NEXT ONE TAKE CARE OF CONVERTING
            FROM A 4 CHANNEL FORMAT TO MONOCHROME"""
            if channel_to_keep:
                #keep the alpha channel
                channel_mapping = ab.ANYTHING_TO_A
                if format == ab.FORMAT_P8:
                    channel_merge_mapping = ab.M_ARGB_TO_A
            else:
                #keep the intensity channel
                channel_merge_mapping = ab.M_ARGB_TO_Y

        elif target_format == ab.FORMAT_A8Y8:
            if mono_swap:
                channel_merge_mapping = ab.M_ARGB_TO_YA
            else:
                channel_merge_mapping = ab.M_ARGB_TO_AY

    elif channel_count == 2:
        """THIS TAKES CARE OF CONVERTING FROM A
        2 CHANNEL FORMAT TO OTHER FORMATS"""

        if format == ab.FORMAT_A8Y8:
            if mono_swap:
                if target_format == ab.FORMAT_A8Y8:
                    channel_mapping = ab.AY_TO_YA
                    
                elif target_channel_count == 4:
                    channel_mapping = ab.YA_TO_ARGB
                
            elif target_channel_count == 4:
                channel_mapping = ab.AY_TO_ARGB
                
            elif target_format in (ab.FORMAT_A8, ab.FORMAT_Y8, ab.FORMAT_AY8):
                if channel_to_keep:
                    #keep the alpha channel
                    channel_mapping = ab.ANYTHING_TO_A
                else:
                    #keep the intensity channel
                    channel_mapping = ab.AY_TO_Y
    
    elif channel_count == 1:
        """THIS TAKES CARE OF CONVERTING FROM A
        1 CHANNEL FORMAT TO OTHER FORMATS"""
        if target_channel_count == 4:
            if format == ab.FORMAT_A8:
                channel_mapping = ab.A_TO_ARGB
                    
            elif format == ab.FORMAT_Y8:
                channel_mapping = ab.Y_TO_ARGB
                    
            elif format == ab.FORMAT_AY8:
                channel_mapping = AY_COMBO_TO_ARGB
                
        elif target_channel_count == 2:
            if format == ab.FORMAT_A8:
                channel_mapping = ab.A_TO_AY
                
            elif format == ab.FORMAT_Y8:
                channel_mapping = ab.Y_TO_AY
                
            elif format == ab.FORMAT_AY8:
                channel_mapping = AY_COMBO_TO_AY
                
    return(channel_mapping, channel_merge_mapping, target_format)
