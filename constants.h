/*
Defines the basic data types found in tags, a collection of constants
defining the fourcc's for each tag type and blam engine version, and
other constants, such as the max size a tag can be before it wont be loaded.
*/

#pragma pack(push, 1)
#pragma once
#include <cstdint>

typedef uint8_t  uint8;
typedef uint16_t uint16;
typedef uint32_t uint32;
typedef int8_t   sint8;
typedef int16_t  sint16;
typedef int32_t  sint32;

typedef uint32 pointer32;

typedef uint8 pad;
typedef uint16 pad2;
typedef uint32 pad4;

#define FOURCC(a, b, c, d) (uint32)(((((( a << 8) | b) << 8) | c) << 8) | d)
#define DUMB_STATIC_ASSERT(x) typedef char assertion_on_struct_size[(!!(x))*2-1]

const uint32 MAX_TAG_SIZE    = 1024 * 1024 * 64;  // max of 64Mb tag file
const uint32 MAX_CFG_STR_LEN = 1024 * 4;          // max of 1Kb per string
const uint32 TAG_HEADER_SIZE = 64;  // a tag must be at least the size of its header
const long INDENT_SIZE = 4; // number of spaces to indent when printing

/*
Define the fourcc ints for the tag classes.

TODO: There should be 81 more of these for the basic Halo 1 classes, and
even more if you include open sauce. I dont have time to type them.
*/
enum TagClass : uint32 {
    TAG_CLASS_SND  = FOURCC('s', 'n', 'd', '!'),
    TAG_CLASS_LSND = FOURCC('l', 's', 'n', 'd'),
    TAG_CLASS_NONE = 0xFFFFFFFF,
};

/*
Define the fourcc ints for the blam engine versions.
*/

enum EngineId : uint32 {
    ENGINE_ID_HALO_1 = FOURCC('b', 'l', 'a', 'm'),
    ENGINE_ID_HALO_2 = FOURCC('!', 'm', 'l', 'b'),
};

#pragma pack(pop)  