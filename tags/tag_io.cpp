#include "common.h"
#include "tag_io.h"
#include <iostream>
#include <stdio.h>

#include "sound.h"
#include "sound_looping.h"
#include "../util/util.h"

using std::cout;

HaloTag::HaloTag() {
    this->tag_header = NULL;
    this->tag_data   = NULL;
    this->filepath   = NULL;
    this->tags_dir   = NULL;
    this->tag_data_size = 0;
    this->filepath_len = 0;
    this->tags_dir_len = 0;
}

HaloTag::HaloTag(char *data, long data_size, const char *new_filepath, const char *new_tags_dir) : HaloTag() {
    if ((data == NULL) || (new_filepath == NULL)) return;

    this->tag_header = (TagHeader*)data;
    this->tag_data   = data + TAG_HEADER_SIZE;
    this->tag_data_size = data_size - TAG_HEADER_SIZE;

    this->set_filepath(new_filepath);
    this->set_tags_dir(new_tags_dir);

    this->tag_class = this->tag_header->tag_class;
}

HaloTag::~HaloTag() {
    free(tag_header);
    // dont need to free tag_data as it is in the same buffer as tag_header
    free(this->filepath);
    free(this->tags_dir);
    this->tag_header = NULL;
    this->tag_data = NULL;
    this->filepath = NULL;
    this->tags_dir = NULL;
}

bool HaloTag::set_filepath(const char *new_path) {
    size_t new_alloc_len = strlen(new_path);
    char *new_alloc_path = (char *)malloc(new_alloc_len + 1);
    if (new_alloc_path == NULL) return true;

    // should probably do some checking to make sure the new_path
    // is a valid filepath before setting it.
    free(this->filepath);
    this->filepath_len = new_alloc_len;
    this->filepath = new_alloc_path;

    memcpy(this->filepath, new_path, new_alloc_len + 1);
    return false;
}

char *HaloTag::get_filepath() {
    if (!this->is_valid()) return NULL;

    return this->filepath;
}

bool HaloTag::set_tags_dir(const char *new_tags_dir) {
    char *new_alloc_path = copy_dir_string(new_tags_dir);
    if (new_alloc_path == NULL) return true;

    free(this->tags_dir);
    this->tags_dir_len = strlen(new_alloc_path);
    this->tags_dir = new_alloc_path;

    return false;
}

char *HaloTag::get_tags_dir() {
    if (!this->is_valid()) return NULL;

    return this->tags_dir;
}


bool HaloTag::is_valid() {
    return (this->tag_data != NULL &&
            this->filepath != NULL &&
            this->tags_dir != NULL &&
            this->tag_header != NULL);
}

HaloTag *load_tag_at_path(const char *path, const char *tags_dir) {
    if (path     == NULL) return NULL;
    if (tags_dir == NULL) return NULL;

    cout << "loading: " << path << '\n';
    if (!file_exists(path)) {
        // file doesnt exist
        return NULL;
    }

    FILE *tag_file = fopen(path, "rb");
    if (!tag_file) {
        // couldn't load the tag for some reason
        cout << "Could not load tag\n";
        return NULL;
    }

    fseek(tag_file, 0, SEEK_END);
    long length = ftell(tag_file);
    fseek(tag_file, 0, SEEK_SET);

    if (length > MAX_TAG_SIZE) {
        // max tag size exceeded
        cout << "Max size exceeded\n";
        fclose(tag_file);
        return NULL;
    } else if (length < TAG_HEADER_SIZE) {
        // tag isn't even large enough to parse its header
        cout << "Tag too small\n";
        fclose(tag_file);
        return NULL;
    }

    // copy the tag file into memory
    char *tag_buffer = (char *)malloc(length);
    fread(tag_buffer, length, 1, tag_file);
    fclose(tag_file);

    // byteswap the header and read it to determine the tag type
    TagHeader *tag_header = (TagHeader *)tag_buffer;
    byteswap_tag_header(*tag_header);

    if (tag_header->engine_id != ENGINE_ID_HALO_1) {
        // incorrect version for the engine. free the buffer we just made
        cout << "Engine ID does not match: \n";
        cout << tag_header->engine_id << " != " << ENGINE_ID_HALO_1 << '\n';
        free(tag_buffer);
        return NULL;
    }

    HaloTag *halo_tag;
    if (tag_header->tag_class == TAG_CLASS_SND) {
        halo_tag = new SndTag(tag_buffer, length, path, tags_dir);
    } else if (tag_header->tag_class == TAG_CLASS_LSND) {
        halo_tag = new LsndTag(tag_buffer, length, path, tags_dir);
    } else {
        halo_tag = new HaloTag(tag_buffer, length, path, tags_dir);
    }

    return halo_tag;
}