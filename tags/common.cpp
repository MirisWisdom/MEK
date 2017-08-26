/*
Contains functions for byteswapping individual fields in tag files.
*/
#include "common.h"
#include <iostream>

using std::cout;

char *parse_dependency(Dependency *dependency, char *curr_pos) {
    if (dependency->path_length == 0) {
        dependency->path_pointer = NULL;
    } else {
        dependency->path_pointer = (pointer32)curr_pos;
        curr_pos += dependency->path_length + 1;
    }
    return curr_pos;
}

char *parse_reflexive(Reflexive *reflexive, char *curr_pos, size_t struct_size) {
    if (reflexive->size == 0) {
        reflexive->pointer = NULL;
    } else {
        reflexive->pointer = (pointer32)curr_pos;
        curr_pos += reflexive->size * struct_size;
    }
    return curr_pos;
}

char *parse_rawdata_ref(RawdataRef *rawdata_ref, char *curr_pos) {
    if (rawdata_ref->size == 0) {
        rawdata_ref->pointer = NULL;
    } else {
        rawdata_ref->pointer = (pointer32)curr_pos;
        curr_pos += rawdata_ref->size;
    }
    return curr_pos;
}

void byteswap_tag_header(TagHeader &tag_header) {
    byteswap_32((char *)&(tag_header.tag_class));
    byteswap_32((char *)&(tag_header.checksum));
    byteswap_32((char *)&(tag_header.header_size));
    byteswap_16((char *)&(tag_header.version));
    byteswap_32((char *)&(tag_header.engine_id));
}

void byteswap_rawdata_ref(RawdataRef &rawdata_ref) {
    byteswap_array_32((char *)&rawdata_ref, 5);
}

void byteswap_dependency(Dependency &dependency) {
    byteswap_array_32((char *)&dependency, 4);
}

void byteswap_reflexive(Reflexive &reflexive) {
    byteswap_array_32((char *)&reflexive, 3);
}

inline void byteswap_16(char *val) {
    char temp = val[0];
    val[0] = val[1];
    val[1] = temp;
}

inline void byteswap_32(char *val) {
    char temp = val[0];
    val[0] = val[3];
    val[3] = temp;

    temp = val[1];
    val[1] = val[2];
    val[2] = temp;
}

inline void byteswap_array_16(char *data, unsigned int size) {
    for (unsigned int i = 0; i < size; i++) {
        byteswap_16(data + i * 2);
    }
}
inline void byteswap_array_32(char *data, unsigned int size) {
    for (unsigned int i = 0; i < size; i++) {
        byteswap_32(data + i * 4);
    }
}

char *make_indent_str(int indent) {
    char *new_str = (char *)malloc(indent * INDENT_SIZE + 1);
    for (int i = 0; i < indent * INDENT_SIZE; i++) {
        new_str[i] = ' ';
    }
    new_str[indent * INDENT_SIZE] = 0;
    return new_str;
}

void print_tag_header(TagHeader &header, int indent) {
    char *indent0 = make_indent_str(indent);
    char *indent1 = make_indent_str(indent + 1);
    cout << indent0 << "{ tag_header, ptr == " << (&header) << '\n';
    cout << indent1 << "tag_class   == " << (header.tag_class) << '\n';
    cout << indent1 << "checksum    == " << (header.checksum) << '\n';
    cout << indent1 << "header_size == " << (header.header_size) << '\n';
    cout << indent1 << "version     == " << (header.version) << '\n';
    cout << indent1 << "integ0      == " << ((uint32)header.integ0) << '\n';
    cout << indent1 << "integ1      == " << ((uint32)header.integ1) << '\n';
    cout << indent1 << "engine_id   == " << (header.engine_id) << '\n';
    cout << indent0 << "}\n";
}
void print_rawdata_ref(RawdataRef &rawdata_ref, char *name, int indent) {
    char *indent0 = make_indent_str(indent);
    char *indent1 = make_indent_str(indent + 1);
    cout << indent0 << "{ " << name << ", ptr == " << (&rawdata_ref) << '\n';
    cout << indent1 << "size        == " << (rawdata_ref.size) << '\n';
    cout << indent1 << "flags       == " << (rawdata_ref.flags) << '\n';
    cout << indent1 << "raw_pointer == " << (rawdata_ref.raw_pointer) << '\n';
    cout << indent1 << "pointer     == " << (rawdata_ref.pointer) << '\n';
    cout << indent1 << "id          == " << (rawdata_ref.id) << '\n';
    cout << indent0 << "}\n";
}
void print_dependency(Dependency &dependency, char *name, int indent) {
    char *indent0 = make_indent_str(indent);
    char *indent1 = make_indent_str(indent + 1);
    cout << indent0 << "{ " << name << ", ptr == " << (&dependency) << '\n';
    cout << indent1 << "tag_class    == " << (dependency.tag_class) << '\n';
    cout << indent1 << "path_length  == " << (dependency.path_length) << '\n';
    cout << indent1 << "path_pointer == " << (dependency.path_pointer) << '\n';
    cout << indent1 << "id           == " << (dependency.id) << '\n';
    if (dependency.path_length) {
        cout << indent1 << "path == \"" << ((char *)dependency.path_pointer) << "\"\n";
    } else {
        cout << indent1 << "path == \"\"\n";
    }
    cout << indent0 << "}\n";
}
void print_reflexive(Reflexive &reflexive, char *name, int indent) {
    char *indent0 = make_indent_str(indent);
    char *indent1 = make_indent_str(indent + 1);
    cout << indent0 << "{ " << name << ", ptr == " << (&reflexive) << '\n';
    cout << indent1 << "size        == " << (reflexive.size) << '\n';
    cout << indent1 << "pointer     == " << (reflexive.pointer) << '\n';
    cout << indent1 << "id          == " << (reflexive.id) << '\n';
    cout << indent0 << "}\n";
}