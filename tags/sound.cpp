/*
Contains functions for parsing a buffer into a sound tag and
byteswaping the fields in a sound tag.
*/

#include "sound.h"
#include "sound_looping.h"
#include "tag_io.h"
#include <iostream>

using std::cout;

SndTag::SndTag() : HaloTag() {
    this->curr_pitch_range = -1;
    this->max_pitch_range  = -1;
    this->curr_actual_perm = -1;
    this->curr_perm        = -1;
}

SndTag::SndTag(char *data, long data_size, const char *new_filepath, const char *new_tags_dir) : 
               HaloTag(data, data_size, new_filepath, new_tags_dir) {
    this->curr_pitch_range = -1;
    this->max_pitch_range  = -1;
    this->curr_actual_perm = -1;
    this->curr_perm        = -1;
    this->parse();
}

SndTag::~SndTag() {
    HaloTag::~HaloTag();
}

sint16 SndTag::max_actual_perm() {
    if (!this->is_valid()) return -1;

    SndBody *snd_body = (SndBody *)this->tag_data;
    if (this->curr_pitch_range >= snd_body->pitch_ranges.size) return -1;

    PitchRange *p_range = (PitchRange *)snd_body->pitch_ranges.pointer;
    return p_range[this->curr_pitch_range].actual_permutation_count - 1;
}

void SndTag::parse() {
    /*
    Parses a snd tag's buffer to byteswap everything to little endian
    and set pointers to reflexives, rawdata, and dependency paths.
    */
    PitchRange *p_range;
    Permutation *perm;

    char *curr_pos = this->tag_data;
    SndBody *tag_body = (SndBody *)curr_pos;
    byteswap_snd_body(tag_body);

    // skip over the tag body
    curr_pos += sizeof(SndBody);

    // set the pointer to the promotion_sound dependency and skip over it
    curr_pos = parse_dependency(&tag_body->promotion_sound, curr_pos);

    if (tag_body->pitch_ranges.size > 0) {
        curr_pos = parse_reflexive(&tag_body->pitch_ranges, curr_pos,
                                   sizeof(PitchRange));
        p_range = (PitchRange *)tag_body->pitch_ranges.pointer;

        this->curr_pitch_range = 0;
        this->max_pitch_range  = tag_body->pitch_ranges.size - 1;

        for (sint32 i = 0; i < tag_body->pitch_ranges.size; i++, p_range++) {
            byteswap_snd_pitch_range(p_range);

            if (p_range->permutations.size > 0) {

                curr_pos = parse_reflexive(&p_range->permutations, curr_pos,
                                           sizeof(Permutation));
                perm = (Permutation *)p_range->permutations.pointer;

                for (sint32 j = 0; j < p_range->permutations.size; j++, perm++) {
                    byteswap_snd_permutation(perm);
                    curr_pos = parse_rawdata_ref(&perm->samples, curr_pos);
                    curr_pos = parse_rawdata_ref(&perm->mouth_data, curr_pos);
                    curr_pos = parse_rawdata_ref(&perm->subtitle_data, curr_pos);
                }
            }
        }
    }
}

void SndTag::serialize() {
    /*
    Any serializer functions will just be placeholders for now.
    */
    if (!this->is_valid()) return;
}

void SndTag::print() {
    if (!this->is_valid()) {
        cout << "Tag is invalid\n";
        return;
    }

    cout << "tag_path      == " << this->filepath << std::endl;
    cout << "tag_data_size == " << this->tag_data_size << std::endl;
    cout << "is_valid_tag  == " << this->is_valid() << std::endl;
    print_tag_header(*this->tag_header, 0);

    char *indent1 = make_indent_str(1);
    char *indent2 = make_indent_str(2);
    char *indent3 = make_indent_str(3);

    PitchRange *p_range;
    Permutation *perm;
    SndBody *body = (SndBody *)this->tag_data;

    cout << "{ tag_body, ptr == " << (&body) << '\n';
    cout << indent1 << "class            == " << (body->sound_class) << '\n';
    cout << indent1 << "sample_rate      == ";
    switch (body->sample_rate) {
    case SAMPLE_RATE_22KHZ: cout << "22khz"; break;
    case SAMPLE_RATE_44KHZ: cout << "44khz"; break;
    case SAMPLE_RATE_32KHZ: cout << "32khz"; break;
    default:                cout << body->sample_rate; break;
    }
    cout << '\n';

    cout << indent1 << "encoding         == ";
    switch (body->encoding) {
    case ENCODING_MONO:   cout << "mono";   break;
    case ENCODING_STEREO: cout << "stereo"; break;
    default:              cout << body->encoding; break;
    }
    cout << '\n';

    cout << indent1 << "compression      == ";
    switch (body->compression) {
    case COMPRESSION_PCM_LE: cout << "none"; break;
    case COMPRESSION_XBOX:   cout << "xbox_adpcm"; break;
    case COMPRESSION_IMA:    cout << "ima_adpcm"; break;
    case COMPRESSION_OGG:    cout << "ogg"; break;
    default:                 cout << body->compression; break;
    }
    cout << '\n';

    cout << indent1 << "gain_modifier    == " << (body->gain_modifier) << '\n';
    cout << indent1 << "max_bend_per_sec == " <<
        (body->maximum_bend_per_second) << '\n';

    print_dependency(body->promotion_sound, "promotion sound", 1);
    print_reflexive(body->pitch_ranges, "pitch_ranges", 1);

    if (body->pitch_ranges.size > 0) {
        p_range = (PitchRange *)body->pitch_ranges.pointer;

        for (sint32 i = 0; i < body->pitch_ranges.size; i++, p_range++) {
            cout << indent1 << "{ #" << i << " pitch_range, ptr == "
                << (&p_range) << '\n';
            cout << indent2 << "name              == \"" << (p_range->name) << "\"\n";
            cout << indent2 << "bend_bounds_low   == " << (p_range->bend_bounds.from) << '\n';
            cout << indent2 << "bend_bounds_high  == " << (p_range->bend_bounds.to) << '\n';
            cout << indent2 << "natural_pitch     == " << (p_range->natural_pitch) << '\n';
            cout << indent2 << "permutation_count == " << (p_range->actual_permutation_count) << '\n';

            print_reflexive(p_range->permutations, "permutations", 2);
            if (p_range->permutations.size > 0) {
                perm = (Permutation *)p_range->permutations.pointer;
                for (sint32 j = 0; j < p_range->permutations.size; j++, perm++) {
                    cout << indent2 << "{ #" << j << " permutation, ptr == "
                        << (&perm) << '\n';
                    cout << indent3 << "name            == \"" << (perm->name) << "\"\n";
                    cout << indent3 << "skip_fraction   == " << (perm->skip_fraction) << '\n';
                    cout << indent3 << "gain            == " << (perm->gain) << '\n';
                    cout << indent3 << "compression     == " << (perm->compression) << '\n';
                    cout << indent3 << "next_perm_index == " << (perm->next_permutation_index) << '\n';
                    print_rawdata_ref(perm->samples, "samples", 3);
                    print_rawdata_ref(perm->mouth_data, "mouth_data", 3);
                    print_rawdata_ref(perm->subtitle_data, "subtitle_data", 3);
                    cout << indent2 << "}\n";
                }
            }
            cout << indent1 << "}\n";
        }
    }
    cout << "}\n";
}

bool SndTag::set_actual_perm_index(sint16 new_index) {
    if (!this->is_valid()) return true;

    SndBody *body = (SndBody *)this->tag_data;
    if (body == NULL) return true;

    if (body->pitch_ranges.size <= 0 ||
        body->pitch_ranges.size <= this->curr_pitch_range) {
        // no pitch ranges, or an invalid one is selected
        this->curr_pitch_range = -1;
        return true;
    }

    PitchRange *p_range = (PitchRange *)body->pitch_ranges.pointer;
    if (p_range == NULL || this->curr_pitch_range < 0) return true;
    if (new_index < 0) new_index = -1;
    if (new_index >= p_range[this->curr_pitch_range].permutations.size) {
        // trying to set index to a too high value
        this->curr_actual_perm = this->curr_perm = -1;
        return true;
    }

    this->curr_actual_perm = this->curr_perm = new_index;
    return false;
}

bool SndTag::inc_actual_perm_index() {
    if (!this->is_valid()) return true;

    int          loop_count = 0;
    SndBody     *body    = (SndBody *)this->tag_data;
    if (body == NULL) return true;
    PitchRange  *p_range = (PitchRange *)body->pitch_ranges.pointer;
    if (p_range == NULL || this->curr_pitch_range < 0) return true;
    Permutation *perm    = (Permutation *)p_range[this->curr_pitch_range].permutations.pointer;

    sint16 next_actual_perm  = this->curr_actual_perm;
    sint16 actual_perm_count = p_range->actual_permutation_count;
    if (this->curr_actual_perm < 0) {
        // starting getting the permutations for the first time
        this->curr_actual_perm = 0;
        next_actual_perm = -1;
    }

    // loop 7^2 times(since bungie has a thing for the number 7) before we
    // give up and decide to just use the next permutation in the chain.
    while (loop_count < 49) {
        // loop over each actual permutation and roll a random number from
        // 0.0 to 1.0 to determine if the permutation will be selected
        next_actual_perm++;

        if (next_actual_perm == this->curr_actual_perm) loop_count++;

        // resetting to beginning of permutations
        if (next_actual_perm >= actual_perm_count) next_actual_perm = 0;

        // add 1 to make sure 0.0 is never skipped, and 1.0 always is
        float skip_roll = ((float)(rand() + 1) / (RAND_MAX + 1));
        if (perm[next_actual_perm].skip_fraction < skip_roll) break;
    }

    this->curr_actual_perm = this->curr_perm = next_actual_perm;
    return false;
}

bool SndTag::inc_perm_index() {
    if (!this->is_valid()) return true;

    SndBody    *body = (SndBody *)this->tag_data;
    if (body == NULL) return true;
    PitchRange *p_range = (PitchRange *)body->pitch_ranges.pointer;
    if (p_range == NULL || this->curr_pitch_range < 0) return true;
    sint32 perm_count = p_range[this->curr_pitch_range].permutations.size;
    sint16 next_perm;

    if (perm_count <= 0 || this->curr_perm >= perm_count) {
        // something is wrong if curr_perm is somehow too large
        next_perm = -1;
    } else if (this->curr_perm < 0 || this->curr_actual_perm < 0) {
        // starting a new permutations chain from its beginning.
        this->inc_actual_perm_index();
        next_perm = this->curr_perm;
    } else {
        // incrementing to the next permutation piece in the chain
        Permutation *perm = (Permutation *)p_range->permutations.pointer;
        next_perm = perm[this->curr_perm].next_permutation_index;
    }

    if (next_perm < 0 || next_perm >= perm_count) {
        // the permutation chain ended
        next_perm = -1;
    }

    this->curr_perm = next_perm;
    return false;
}


SoundSamples *SndTag::get_curr_samples() {
    if (!this->is_valid()) return NULL;
    SndBody *body = (SndBody *)this->tag_data;
    if (body == NULL) return NULL;

    if (body->pitch_ranges.size == 0 ||
        body->pitch_ranges.size <= this->curr_pitch_range) {
        // either no pitch ranges, or current pitch range is to high.
        this->curr_pitch_range = -1;
        this->curr_actual_perm = this->curr_perm = -1;
        return NULL;
    } 

    // check if no permutations, or if we hit the end of the chain
    if (this->curr_actual_perm == -1 || this->curr_perm == -1) return NULL;

    PitchRange   *p_range = (PitchRange *)body->pitch_ranges.pointer;
    if (p_range == NULL) return NULL;
    Permutation  *perm    = (Permutation *)p_range[this->curr_pitch_range].permutations.pointer;
    if (perm == NULL)    return NULL;

    uint8 bytes_per_sample = sizeof(sint16);
    uint16 rate = 1;

    switch(body->sample_rate) {
    case(SAMPLE_RATE_22KHZ): rate = 22050; break;
    case(SAMPLE_RATE_44KHZ): rate = 44010; break;
    case(SAMPLE_RATE_32KHZ): rate = 32000; break;
    }

    SoundSamples *samples = new SoundSamples(
        &perm[this->curr_perm], (uint8)(body->encoding + 1),
        this->curr_perm, this->curr_actual_perm,
        bytes_per_sample, rate);

    return samples;
}


static void byteswap_snd_permutation(SndPermutation *permutation) {
    byteswap_32((char *)&(permutation->skip_fraction));
    byteswap_32((char *)&(permutation->gain));
    byteswap_16((char *)&(permutation->compression));
    byteswap_16((char *)&(permutation->next_permutation_index));
    byteswap_rawdata_ref(permutation->samples);
    byteswap_rawdata_ref(permutation->mouth_data);
    byteswap_rawdata_ref(permutation->subtitle_data);
}

static void byteswap_snd_pitch_range(SndPitchRange *pitch_range) {
    byteswap_32((char *)&(pitch_range->natural_pitch));
    byteswap_array_32((char *)&(pitch_range->bend_bounds), 2);
    byteswap_16((char *)&(pitch_range->actual_permutation_count));
    byteswap_reflexive(pitch_range->permutations);
}

static void byteswap_snd_body(SndBody *snd_body) {
    byteswap_32((char *)&(snd_body->flags));
    byteswap_16((char *)&(snd_body->sound_class));
    byteswap_16((char *)&(snd_body->sample_rate));
    byteswap_32((char *)&(snd_body->minimum_distance));
    byteswap_32((char *)&(snd_body->maximum_distance));
    byteswap_32((char *)&(snd_body->skip_fraction));
    byteswap_array_32((char *)&(snd_body->random_pitch_bounds), 2);
    byteswap_32((char *)&(snd_body->inner_cone_angle));
    byteswap_32((char *)&(snd_body->outer_cone_angle));
    byteswap_32((char *)&(snd_body->outer_cone_gain));
    byteswap_32((char *)&(snd_body->gain_modifier));
    byteswap_32((char *)&(snd_body->maximum_bend_per_second));

    byteswap_array_32((char *)&(snd_body->when_scale_is_zero), 3);
    byteswap_array_32((char *)&(snd_body->when_scale_is_one) , 3);

    byteswap_16((char *)&(snd_body->encoding));
    byteswap_16((char *)&(snd_body->compression));
    byteswap_16((char *)&(snd_body->promotion_count));

    byteswap_dependency(snd_body->promotion_sound);
    byteswap_reflexive(snd_body->pitch_ranges);
}


SoundSamples::SoundSamples() {
    this->skip_fraction     = 1.0;
    this->gain              = 1.0;
    this->channel_count     = 1;
    this->encoded_format    = COMPRESSION_NONE;
    this->decoded_format    = COMPRESSION_NONE;
    this->sect_type         = LSND_SECTION_TYPE_START;
    this->this_perm_index   = 0;
    this->next_perm_index   = -1;
    this->sample_rate       = 0;
    this->sample_data       = NULL;
    this->sample_data_owner = false;
    this->sample_data_size  = 0;
    this->bytes_per_sample  = 0;

    this->decoded_sample_adjust    = 0;
    this->decoded_sample_data_size = 0;
    this->decode_buffer_size       = 0;

    this->decode_buffer       = NULL;
    this->decoded_sample_data = NULL;
    this->decoding_pos        = NULL;
}

SoundSamples::SoundSamples(SndPermutation *snd_perm, uint8 channel_count,
                           sint16 perm_index, uint16 actual_perm_index,
                           uint8 bytes_per_sample, uint16 sample_rate) : SoundSamples() {
    strncpy(this->name, snd_perm->name, 32);
    this->skip_fraction   = snd_perm->skip_fraction;
    this->gain            = snd_perm->gain;
    this->encoded_format  = snd_perm->compression;
    this->sect_type       = LSND_SECTION_TYPE_START;
    this->next_perm_index = snd_perm->next_permutation_index;

    this->actual_perm_index = actual_perm_index;
    this->this_perm_index   = perm_index;
    this->channel_count     = channel_count;
    this->sample_rate       = sample_rate;
    this->bytes_per_sample  = bytes_per_sample;

    if (snd_perm->samples.pointer != 0) {
        this->sample_data  = (char *)snd_perm->samples.pointer;
        this->decoding_pos = this->sample_data;
        this->sample_data_size = snd_perm->samples.size;
    }
}

SoundSamples::~SoundSamples() {
    if (this->sample_data_owner) {
        this->sample_data_owner = false;
        free(this->sample_data);
    }
    if (this->decoded_buffer_owner) {
        this->decoded_buffer_owner = false;
        free(this->decode_buffer);
    }
    this->sample_data   = NULL;
    this->decode_buffer = this->decoded_sample_data = NULL;
}

bool SoundSamples::is_valid() {
    return (this->sample_rate      != 0 &&
            this->sample_data_size != 0 &&
            this->sample_data      != NULL);
}

bool SoundSamples::setup_decode_buffer(uint32 req_samp_ct) {
    uint32 new_buf_size = req_samp_ct * this->channel_count * this->bytes_per_sample;

    // if the current buffer is large enough we can just use it as is.
    if (this->decode_buffer == NULL || this->decode_buffer_size < new_buf_size) {
        // need to allocate a larger buffer
        if (this->decoded_buffer_owner) {
            this->decoded_buffer_owner = false;
            free(this->decode_buffer);
        }
        this->decode_buffer = (char *)malloc(new_buf_size);
        this->decoded_buffer_owner = true;

        // if the new buffer isnt usable, set its size to 0
        if (this->decode_buffer == NULL) new_buf_size = 0;

        this->decode_buffer_size = new_buf_size;
    }

    // reset these so other objects know there isnt valid data in the buffer yet
    this->decoded_sample_data = this->decode_buffer;
    this->decoded_sample_data_size = 0;
    return (this->decode_buffer == NULL);
}

bool SoundSamples::is_compressed() {
    return !(this->encoded_format == COMPRESSION_PCM_LE ||
             this->encoded_format == COMPRESSION_PCM_BE ||
             this->encoded_format == COMPRESSION_PCM_F);
}

bool SoundSamples::direct_buffer_copy(uint32 req_samp_ct) {
    this->decoded_format = this->encoded_format;

    if (req_samp_ct == 0) req_samp_ct = this->sample_count();

    // already in float format. copy the samples directly and return
    if (this->setup_decode_buffer(req_samp_ct)) return true;

    // set the size of the decoded samples
    this->decoded_sample_data_size = req_samp_ct * this->bytes_per_sample * this->channel_count;

    // copy the samples directly into the decode buffer
    memcpy(this->decode_buffer, this->decoding_pos, this->decoded_sample_data_size);

    // set up the public read position, reset the adjust to 0, and increment the decode pos
    this->decoded_sample_data = this->decode_buffer;
    this->decoding_pos += this->decoded_sample_data_size;
    return false;
}

bool SoundSamples::decode_to_pcm_int16(uint32 req_samp_ct) {
    if (!this->is_valid()) return true;

    if (req_samp_ct == 0) req_samp_ct = this->sample_count();
    req_samp_ct += this->decoded_sample_adjust;

    if (this->encoded_format == COMPRESSION_PCM_LE) {
        this->bytes_per_sample = sizeof(sint16);
        if (direct_buffer_copy(req_samp_ct)) return true;
        this->decoded_sample_adjust = 0;
        return false;
    }

    char  *samp;
    char  *samp_end;
    uint8  temp;

    switch (this->encoded_format) {
    case COMPRESSION_PCM_LE:
    case COMPRESSION_PCM_BE:
        this->bytes_per_sample = sizeof(sint16);
        if (direct_buffer_copy(req_samp_ct)) return true;

        this->decoded_sample_adjust = 0;

        if (this->encoded_format != COMPRESSION_PCM_BE) return false;

        // halo 2
        // byteswap from big endian to little endian.

        samp = this->decoded_sample_data;
        samp_end = this->decoded_sample_data_size + samp;

        for (; samp < samp_end; samp += 2) {
            temp = samp[0];
            samp[0] = samp[1];
            samp[1] = temp;
        }
        this->decoded_format = COMPRESSION_PCM_LE;
        break;
    case COMPRESSION_XBOX:
    case COMPRESSION_IMA:
        // do adpcm decompression
        // TODO: FINISH THIS
        //break;
    case COMPRESSION_OGG:
        // halo 1
        // TODO: FINISH THIS
        //break;
    case COMPRESSION_WMA:
        // halo 2
        // TODO: FINISH THIS
        //break;
    default:
        return true;
    }

    return false;
}

bool SoundSamples::decode_to_pcm_float32(uint32 req_samp_ct) {
    if (!this->is_valid()) return NULL;

    if (req_samp_ct == 0) req_samp_ct = this->sample_count();

    // setup and grab the current buffer so it doesnt get cleared
    // by the function to decode to pcm16 if it doesnt need to be

    switch (this->encoded_format) {
    case COMPRESSION_PCM_F:
        if (direct_buffer_copy(req_samp_ct + this->decoded_sample_adjust)) return true;
        this->decoded_sample_adjust = 0;

        return false;
    case COMPRESSION_IMA:
    case COMPRESSION_XBOX:
    case COMPRESSION_PCM_BE:
    case COMPRESSION_PCM_LE:
    case COMPRESSION_OGG:
    case COMPRESSION_WMA:
        // make sure everything is pcm_16 first
        if (!this->decode_to_pcm_int16(req_samp_ct)) break;
    default:
        // no idea how to decode this format
        return true;
    }

    // get how many samples were actually able to be decoded
    req_samp_ct = this->decoded_sample_count();

    // take ownership of the pcm buffer, set the decode format
    // to pcm float, and make a new float decode buffer.
    char   *pcm16_buffer = this->decode_buffer;
    sint16 *sint16s      = (sint16 *)this->decoded_sample_data;
    this->decode_buffer  = NULL;

    this->bytes_per_sample = sizeof(float);
    this->decoded_format = COMPRESSION_PCM_F;
    if (this->setup_decode_buffer(req_samp_ct)) return true;
    float *floats = (float *)this->decode_buffer;

    // dont need to touch this->decoded_sample_adjust as its
    // being managed by whatever function decoded it to pcm16
    this->decoded_sample_data      = this->decode_buffer = (char *)floats;
    this->decoded_sample_data_size = req_samp_ct * this->bytes_per_sample * this->channel_count;

    for (uint32 i = 0; i < req_samp_ct * this->channel_count; i++) {
        if (sint16s[i] < 0)
            floats[i] = ((float)sint16s[i]) / 32768;
        else
            floats[i] = ((float)sint16s[i]) / 32767;
    }

    // free the pcm16 buffer now that we're done with it
    free(pcm16_buffer);

    return false;
}

double SoundSamples::sample_length() {
    // returns sample length of all encoded samples in milliseconds

    switch (this->encoded_format) {
    case COMPRESSION_IMA:
    case COMPRESSION_XBOX:
    case COMPRESSION_PCM_F:
    case COMPRESSION_PCM_BE:
    case COMPRESSION_PCM_LE:
        return ((double)this->sample_count() * 1000) / this->sample_rate;
    case COMPRESSION_OGG:
    case COMPRESSION_WMA:
    default:
        return -1.0;
    }
}

bool SoundSamples::decoding_finished() {
    return this->decoding_pos >= this->sample_data + this->sample_data_size;
}

uint32 SoundSamples::sample_count() {
    uint32 ct = this->sample_data_size;

    switch (this->encoded_format) {
    case COMPRESSION_IMA:
    case COMPRESSION_XBOX:
        // ima and xbox adpcm are a 4:1 compression scheme
        ct *= 4;
    case COMPRESSION_PCM_F:
    case COMPRESSION_PCM_BE:
    case COMPRESSION_PCM_LE:
        return ct / (this->bytes_per_sample * this->channel_count);
    case COMPRESSION_OGG:
    case COMPRESSION_WMA:
    default:
        return 0;
    }
}

uint32 SoundSamples::decoded_sample_count() {
    switch (this->decoded_format) {
    case COMPRESSION_PCM_F:
    case COMPRESSION_PCM_BE:
    case COMPRESSION_PCM_LE:
        return this->decoded_sample_data_size / (this->bytes_per_sample * this->channel_count);
    default:
        return 0;
    }
}