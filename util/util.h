#pragma once
#include <windows.h>
#include <sys/stat.h>

#ifdef UNICODE
#define PATHSTR_TYPE LPWSTR
const int PATHSTR_SIZE = sizeof(wchar_t);
const PATHSTR_TYPE PATH_DELIMS = L"\\/";
#else
#define PATHSTR_TYPE LPSTR
const int PATHSTR_SIZE = sizeof(char);
const PATHSTR_TYPE PATH_DELIMS = "\\/";
#endif // !UNICODE

inline int gcd(int x, int y);
double time_now();
char *strcpycat(char *left, char *right);
char *strcpycat(char *left, char *right, bool l_free, bool r_free);
bool file_exists(const char *name);
char *dirname(const char *path);
char *get_working_dir();
char *copy_dir_string(const char *dir_path);