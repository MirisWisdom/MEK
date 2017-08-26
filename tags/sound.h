/*
Contains definitions for structures associated with the sound tag.
*/
#pragma pack(push, 1)
#pragma once

#include "common.h"
#include "tag_io.h"
#include <stdio.h>

// JUCE asks for samples in 1ms blocks, which at 48Khz means 480 samples.
// 1024 samples should be enough to handle most decoding requirements.
const uint32 DEF_DECODE_BUFFER_SIZE = 1024;

typedef struct SndFlags {
    uint32 fit_to_adpcm_blocksize             : 1;
    uint32 split_long_sound_into_permutations : 1;
} SndFlags; DUMB_STATIC_ASSERT(sizeof(SndFlags) == 4);

enum SoundClasses : sint16 {
    projectile_impact     = 0,
    projectile_detonation = 1,

    weapon_fire     = 4,
    weapon_ready    = 5,
    weapon_reload   = 6,
    weapon_empty    = 7,
    weapon_charge   = 8,
    weapon_overheat = 9,
    weapon_idle     = 10,

    object_impacts        = 13,
    particle_impacts      = 14,
    slow_particle_impacts = 15,

    unit_footsteps = 18,
    unit_dialog    = 19,

    vehicle_collision = 22,
    vehicle_engine    = 23,

    device_door        = 26,
    device_force_field = 27,
    device_machinery   = 28,
    device_nature      = 29,
    device_computers   = 30,

    music             = 32,
    ambient_nature    = 33,
    ambient_machinery = 34,
    ambient_computers = 35,

    first_person_damage = 39,

    scripted_dialog_player = 44,
    scripted_effect        = 45,
    scripted_dialog_other  = 46,
    scripted_dialog_force_unspatialized = 47,

    game_event = 50
};

enum SampleRate : sint16 {
    SAMPLE_RATE_22KHZ,
    SAMPLE_RATE_44KHZ,
    SAMPLE_RATE_32KHZ  // halo 2 only
};

enum Encoding : sint16 {
    ENCODING_MONO,
    ENCODING_STEREO
};

enum Compression : sint16 {
    COMPRESSION_PCM_LE,  // 16-bit int
    COMPRESSION_XBOX,
    COMPRESSION_IMA,
    COMPRESSION_OGG,  // for halo 2 this is PCM little endian
    COMPRESSION_WMA,
    COMPRESSION_PCM_BE,  // 16-bit int
    COMPRESSION_PCM_F,   // 32-bit float
    COMPRESSION_NONE = 0x7fff
};
// these compression enums are actually wrong. Since halo 1 and halo 2 have some
// incompatible compression types, the above will be used to unify both enums.
// tags will have their compression changed when they are loaded.

enum H1Compression : sint16 {
    H1_COMPRESSION_NONE,
    H1_COMPRESSION_XBOX,
    H1_COMPRESSION_IMA,
    H1_COMPRESSION_OGG,
};

enum H2Compression : sint16 {
    H2_COMPRESSION_PCM_BE,
    H2_COMPRESSION_XBOX,
    H2_COMPRESSION_IMA,
    H2_COMPRESSION_PCM_LE,
    H2_COMPRESSION_WMA
};

enum LsndSectionType : sint16 {
    LSND_SECTION_TYPE_NONE,      // not playing anything and not expected to be/have been.
    LSND_SECTION_TYPE_STARTING,  // starting playback, but nothing played yet.
    LSND_SECTION_TYPE_START,     // playback has started, but not entered the loops yet.
    LSND_SECTION_TYPE_LOOP,      // loops playing and will continue to until end is triggered.
    LSND_SECTION_TYPE_END,       // playing end sound.
    LSND_SECTION_TYPE_ENDED,     // end sound finished playing. nothing should be playing.
                                 // this state means its safe to switch to a new track.
};

typedef struct SndPermutation {
    ASCIIZ32(name);
    float skip_fraction;
    float gain;
    Compression compression;
    sint16 next_permutation_index;
    pad padding[20];
    RawdataRef samples;
    RawdataRef mouth_data;
    RawdataRef subtitle_data;
} Permutation; DUMB_STATIC_ASSERT(sizeof(Permutation) == 124);

typedef struct SndPitchRange {
    ASCIIZ32(name);
    float natural_pitch;
    FromToFloat bend_bounds;
    sint16 actual_permutation_count;
    pad padding[14];
    Reflexive permutations;
} PitchRange; DUMB_STATIC_ASSERT(sizeof(PitchRange) == 72);

typedef struct SndScaleModifiers {
    float skip_fraction;
    float gain;
    float pitch;
} ScaleModifiers;

typedef struct SndBody {
    SndFlags flags;
    SoundClasses sound_class;
    SampleRate sample_rate;
    float minimum_distance;
    float maximum_distance;
    float skip_fraction;
    FromToFloat random_pitch_bounds;
    float inner_cone_angle;
    float outer_cone_angle;
    float outer_cone_gain;
    float gain_modifier;
    float maximum_bend_per_second;
    pad padding0[12];

    ScaleModifiers when_scale_is_zero;
    pad padding1[12];

    ScaleModifiers when_scale_is_one;
    pad padding2[12];

    Encoding encoding;
    Compression compression;
    Dependency promotion_sound;
    sint16 promotion_count;
    pad padding3[22];

    Reflexive pitch_ranges;
} SndBody; DUMB_STATIC_ASSERT(sizeof(SndBody) == 164);

static void byteswap_snd_permutation(Permutation *);
static void byteswap_snd_pitch_range(PitchRange *);
static void byteswap_snd_body(SndBody *);

class SoundSamples {
public:
    SoundSamples();
    SoundSamples(SndPermutation *snd_perm, uint8 channel_count,
                 sint16 perm_index, uint16 actual_perm_index,
                 uint8 bytes_per_sample, uint16 sample_rate);
    ~SoundSamples();

    bool is_valid();
    bool is_compressed();
    bool decoding_finished();
    uint32 sample_count();
    uint32 decoded_sample_count();
    double sample_length();

    bool direct_buffer_copy(uint32 req_samp_ct = 0);
    bool decode_to_pcm_int16(uint32 req_samp_ct = 0);
    bool decode_to_pcm_float32(uint32 req_samp_ct = 0);
    bool setup_decode_buffer(uint32 buf_size = DEF_DECODE_BUFFER_SIZE);
    bool make_owner();

    ASCIIZ32(name);
    // flags
    uint32          sample_data_owner : 1;  // whether or not this class instance owns and
                                            // must take care of the sample_data buffer.
    uint32          decoded_buffer_owner : 1;  // whether or not this class instance owns and
                                               // must take care of the decode_buffer.

    float           skip_fraction;
    float           gain;
    uint8           channel_count;
    pad             padding;
    Compression     encoded_format;
    Compression     decoded_format;
    LsndSectionType sect_type;  // used to know what kinda of section of a
                                // sound_looping tag these samples belong to.
    uint8       bytes_per_sample;  // number of bytes per decoded sample
    pad         pad;

    sint16      actual_perm_index;  // the index into the permutations reflexive
                                    // where this chain of permutations starts.
    sint16      this_perm_index;    // the index into the permutations reflexive
                                    // that this permutation is located at.
    sint16      next_perm_index;    // the index into the permutations reflexive
                                    // that the permutation after this is located at.
                                    // if this is -1 it means this is the last block.

    uint16      sample_rate;
    uint32      sample_data_size;
    char       *sample_data;       // compressed sample data

    uint32      decoded_sample_adjust;  // when decoding samples, this is how many initial
                                        // samples to discard before getting to the desired ones.

    uint32      decoded_sample_data_size;  // number of bytes of decoded sample data.
    char       *decoded_sample_data;   // sample data after it was decoded.

private:
    char       *decoding_pos;   // the last point in the stream that samples were being decoded
    char       *decode_buffer;  // the start of the decoded samples.
                                // used to free them when they need to be deleted.
    uint32      decode_buffer_size;  // the number of bytes allocated to the buffer for decoding
};


class SndTag : public HaloTag {
public:
    SndTag();
    SndTag(char *data, long data_size, const char *new_filepath, const char *new_tags_dir);
    ~SndTag();

    void parse();
    void serialize();

    void          print();
    bool          set_actual_perm_index(sint16 new_index);
    bool          inc_actual_perm_index();
    bool          inc_perm_index();
    SoundSamples *get_curr_samples();
    sint16        max_actual_perm();


    sint32   curr_pitch_range;  // the pitch range that permutations are being
                                // parsed from. Should be 0 for any music.
                                // will be -1 if no pitch_ranges are in the tag.

    sint32   max_pitch_range;   // should be 0 for any music.
                                // will be -1 if no pitch_ranges are in the tag.

    sint16   curr_actual_perm;  // the current actual permutation being played.
                                // should be [0, actual_perm_count) where
                                // actual_perm_count is the number of actual
                                // permutations in the current pitch range.

protected:
    sint16   curr_perm;         // the index of the last permutation samples
                                // returned from this->get_next_samples.
                                // keeps track of what permutation should be
                                // returned from this->get_next_samples.
};

#pragma pack(pop)