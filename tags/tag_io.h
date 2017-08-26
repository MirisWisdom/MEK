/*
Not sure if this will need to include anything other than function prototypes.
*/
#pragma once

#include "common.h"

class HaloTag {
public:
    HaloTag::HaloTag();
    HaloTag(char *data, long data_size, const char *new_filepath, const char *new_tags_dir);
    ~HaloTag();

    TagHeader *tag_header;
    TagClass   tag_class;
    size_t     tag_data_size;
    char      *tag_data;

    size_t     filepath_len;
    char      *filepath;

    size_t     tags_dir_len;
    char      *tags_dir;

    bool  is_valid();
    bool  set_filepath(const char *new_path);
    char *get_filepath();

    bool  set_tags_dir(const char *new_tags_dir);
    char *get_tags_dir();
};

HaloTag *load_tag_at_path(const char *path, const char *tags_dir);