/*
Contains definitions for structures associated with the sound_looping tag.
*/
#pragma pack(push, 1)
#pragma once

#include "common.h"
#include "tag_io.h"
#include "sound.h"


typedef struct LsndFlags {
    uint32 deafening_to_ai : 1;
    uint32 not_a_loop      : 1;
    uint32 stops_music     : 1;
} LsndFlags; DUMB_STATIC_ASSERT(sizeof(LsndFlags) == 4);

typedef struct LsndTrackFlags {
    uint32 fade_in_at_start  : 1;
    uint32 fade_out_at_stop  : 1;
    uint32 fade_in_alternate : 1;
} TrackFlags; DUMB_STATIC_ASSERT(sizeof(TrackFlags) == 4);

typedef struct LsndDetailSoundFlags {
    uint32 dont_play_with_alternate    : 1;
    uint32 dont_play_without_alternate : 1;
} DetailSoundFlags; DUMB_STATIC_ASSERT(sizeof(DetailSoundFlags) == 4);


typedef struct {
    TrackFlags flags;
    float gain;
    float fade_in_duration;
    float fade_out_duration;
    SndTag *start;
    SndTag *loop;
    SndTag *end;
    SndTag *alt_loop;
    SndTag *alt_end;
} LoadedTrack;

typedef struct {
    SndTag *sound;
    FromToFloat random_period_bounds;
    float gain;
    DetailSoundFlags flags;
} LoadedDetailSound;


class LsndTag : public HaloTag {
public:
    LsndTag();
    LsndTag(char *data, long data_size, const char *new_filepath, const char *new_tags_dir);
    ~LsndTag();

    void parse();
    void serialize();
    void print();

    bool reset_sound_states();
    bool load_dependencies();
    void unload_dependencies();

    LoadedTrack       *track_sounds;
    LoadedDetailSound *detail_sounds;
    sint32 track_sound_count;
    sint32 detail_sound_count;
};

typedef struct LsndDetailSound {
    Dependency sound;
    FromToFloat random_period_bounds;
    float gain;
    DetailSoundFlags flags;
    pad padding[48];
    FromToFloat yaw_bounds;
    FromToFloat pitch_bounds;
    FromToFloat distance_bounds;
} DetailSound; DUMB_STATIC_ASSERT(sizeof(DetailSound) == 104);

typedef struct LsndTrack {
    TrackFlags flags;
    float gain;
    float fade_in_duration;
    float fade_out_duration;
    pad padding[32];
    Dependency start;
    Dependency loop;
    Dependency end;
    pad padding1[32];
    Dependency alt_loop;
    Dependency alt_end;
} Track; DUMB_STATIC_ASSERT(sizeof(Track) == 160);

typedef struct LsndBody {
    LsndFlags flags;
    float detail_sound_period_at_zero;
    float unknown0;  // defaults to 1.0
    float unknown1;  // defaults to 1.0
    float detail_sound_period_at_one;
    float unknown2;  // defaults to 1.0
    float unknown3;  // defaults to 1.0
    sint32 unknown4; // defaults to -1
    float unknown5;  // defaults to 1.0
    pad padding[8];
    Dependency continuous_damage_effect;
    Reflexive tracks;
    Reflexive detail_sounds;
} LsndBody; DUMB_STATIC_ASSERT(sizeof(LsndBody) == 84);

static void byteswap_lsnd_detail_sound(LsndDetailSound *);
static void byteswap_lsnd_track(LsndTrack *);
static void byteswap_lsnd_body(LsndBody *);

#pragma pack(pop)