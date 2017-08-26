/*
Implements a Playlist class for controlling the playback of the permutations
in any number of sound_looping tags. The Playlist class contains methods for
serializing itself to a file and loading settings from a file.
*/
#include "playlist.h"
#include "../util/util.h"
#include <iostream>

using std::cout;

bool is_valid_command(Command *cmd) {
    if (cmd == NULL)             return false;
    if (cmd->sig != COMMAND_SIG) return false;
    return true;
}

bool is_valid_command_list(CommandList *cmdl) {
    if (cmdl == NULL)                  return false;
    if (cmdl->sig != COMMAND_LIST_SIG) return false;
    return true;
}

Command *new_command() {
    Command *cmd = (Command *)calloc(1, sizeof(Command));
    if (cmd == NULL) return NULL;

    cmd->sig = COMMAND_SIG;

    return cmd;
}

CommandList *new_command_list() {
    CommandList *cmdl = (CommandList *)calloc(1, sizeof(CommandList));
    if (cmdl == NULL) return NULL;

    cmdl->sig = COMMAND_LIST_SIG;
    cmdl->play_length   = 0;
    cmdl->command_count = 1;
    cmdl->commands      = new_command();
    cmdl->lsnd_path     = strcpycat("blank.sound_looping", "");
    cmdl->lsnd_path_len = strlen(cmdl->lsnd_path);
    cmdl->lsnd_tag      = NULL;

    return cmdl;
}


Playlist::Playlist() {
    // make sure these are null so erase_playlist doesnt free random memory
    this->tags_dir      = NULL;
    this->filepath      = NULL;
    this->command_lists = NULL;
    this->tags_dir_len  = 0;
    this->filepath_len  = 0;
    this->command_list_count = 0;
    this->curr_section = LSND_SECTION_TYPE_NONE;

    this->new_playlist();
}

Playlist::Playlist(char *input_path) : Playlist() {
    this->parse(input_path);
}

Playlist::~Playlist() {
    this->erase_playlist();
}


bool Playlist::set_filepath(const char *new_path) {
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

char *Playlist::get_filepath() { return this->filepath; }

bool Playlist::set_tags_dir(const char *new_tags_dir) {
    char *new_alloc_path = copy_dir_string(new_tags_dir);
    if (new_alloc_path == NULL) return true;

    free(this->tags_dir);
    this->tags_dir_len = strlen(new_alloc_path);
    this->tags_dir = new_alloc_path;

    return false;
}

bool Playlist::set_lsnd_tags_dirs() {
    return this->set_lsnd_tags_dirs(this->get_tags_dir());
}

bool Playlist::set_lsnd_tags_dirs(char *new_tags_dir) {
    LsndTag *lsnd_tag;
    if (new_tags_dir == NULL || this->command_lists == NULL) return true;

    for (uint32 i = 0; i < this->command_list_count; i++) {
        lsnd_tag = this->command_lists[i].lsnd_tag;
        if (lsnd_tag == NULL) continue;
        lsnd_tag->set_tags_dir(new_tags_dir);
    }
    return false;
}

char *Playlist::get_tags_dir() { return this->tags_dir; }

bool Playlist::set_list_filepath(const char *new_path) {
    CommandList *cmdl = this->get_command_list();
    if (!is_valid_command_list(cmdl)) return NULL;

    size_t new_alloc_len = strlen(new_path);
    char *new_alloc_path = (char *)malloc(new_alloc_len + 1);
    if (new_alloc_path == NULL) return true;

    // should probably do some checking to make sure the new_path
    // is a valid filepath before setting it.
    free(cmdl->lsnd_path);
    cmdl->lsnd_path_len = new_alloc_len;
    cmdl->lsnd_path     = new_alloc_path;

    memcpy(new_alloc_path, new_path, new_alloc_len + 1);
    return false;
}

char *Playlist::get_list_filepath() {
    CommandList *cmdl = this->get_command_list();
    if (!is_valid_command_list(cmdl)) return NULL;
    if (cmdl->lsnd_path == NULL)  return NULL;
    return cmdl->lsnd_path;
}


int Playlist::curr_command_list() {
    return this->_curr_command_list;
}

int Playlist::curr_command() {
    return this->_curr_command;
}

sint16 Playlist::curr_perm() {
    SndTag *snd_tag = this->get_snd_tag();
    if (snd_tag == NULL) return true;
    if (snd_tag->curr_actual_perm < 0 || 
        snd_tag->curr_actual_perm > snd_tag->max_actual_perm()) {
        // invalid current permutation
        snd_tag->curr_actual_perm = -1;
    }
    return snd_tag->curr_actual_perm;
}

double Playlist::play_timer() {
    if (this->pause_start <= 0.0)
        return (time_now()    - this->play_start) / 1000.0;
    return (this->pause_start - this->play_start) / 1000.0;
}

void Playlist::pause_timers() {
    if (this->is_paused()) return;
    this->pause_start = time_now();
}

void Playlist::resume_timers() {
    if (!this->is_paused()) return;
    // get the play and fade times
    double p_time = play_timer();
    double f_time = fade_out_timer();

    // unpause
    this->pause_start = -1.0;

    // set the times
    this->play_timer(p_time);
    this->fade_out_timer(f_time);
}

bool Playlist::is_playing() {
    return !this->is_paused() && !this->is_stopped();
}

bool Playlist::is_paused() {
    return this->pause_start > 0.0;
}

bool Playlist::is_stopped() {
    return this->curr_section == LSND_SECTION_TYPE_NONE;
}

void Playlist::play() {
    if (this->is_playing())            return;
    if (this->command_list_count <= 0) return;

    // reset the timers to 0.0
    this->play_timer(0.0);
    this->fade_out_timer(0.0);
    this->resume_timers();

    if (this->is_stopped()) {
        // start playing by selecting a command list and its first command
        if (this->_curr_command_list < 0) {
            // pick a command_list to start playing if none is selected
            this->inc_command_list();
        }
        // reset to the beginning of the commands so we can start playing
        this->select_command(-1);
        this->curr_section = LSND_SECTION_TYPE_STARTING;
    }
}

void Playlist::pause() {
    if (this->is_paused() || this->is_stopped()) return;
    this->pause_timers();
}

void Playlist::stop() {
    LsndTag *lsnd_tag = this->get_lsnd_tag();
    if (lsnd_tag != NULL) {
         lsnd_tag->reset_sound_states();
    }

    // setting to no command selected, which should stop all playback.
    this->curr_section   = LSND_SECTION_TYPE_NONE;
    this->loop_iteration = 0;
    this->_curr_command  = -1;
    this->alt            = false;

    // reset the timers to 0.0
    this->pause();
    this->play_timer(0.0);
    this->fade_out_timer(0.0);
}

double Playlist::play_timer(double initial) {
    if (this->pause_start <= 0.0) {
        this->play_start = time_now() - initial * 1000.0;
    } else {
        this->play_start = this->pause_start - initial * 1000.0;
    }
    return this->play_timer();
}

double Playlist::fade_out_timer() {
    if (this->pause_start <= 0.0)
        return (time_now() - this->fade_out_start) / 1000.0;
    return (this->pause_start - this->fade_out_start) / 1000.0;
}
double Playlist::fade_out_timer(double initial) {
    if (this->pause_start <= 0.0) {
        this->fade_out_start = time_now() - initial * 1000.0;
    } else {
        this->fade_out_start = this->pause_start - initial * 1000.0;
    }
    return this->fade_out_timer();
}

double Playlist::fade_in_end() {
    LsndTag *lsnd_tag = this->get_lsnd_tag();
    if (lsnd_tag == NULL) return 0.0;
    LoadedTrack l_track = lsnd_tag->track_sounds[this->track];
    return max(0.0, (double)l_track.fade_in_duration);
}
double Playlist::fade_out_end() {
    LsndTag *lsnd_tag = this->get_lsnd_tag();
    if (lsnd_tag == NULL) return 0.0;
    LoadedTrack l_track = lsnd_tag->track_sounds[this->track];
    return max(0.0, (double)l_track.fade_out_duration);
}

bool Playlist::fade_in() {
    if (this->curr_section != LSND_SECTION_TYPE_START) return false;
    LsndTag *lsnd_tag = this->get_lsnd_tag();
    if (lsnd_tag == NULL) return false;
    return lsnd_tag->track_sounds[this->track].flags.fade_in_at_start;
}
bool Playlist::fade_out() {
    if (this->curr_section != LSND_SECTION_TYPE_END && 
        this->curr_section != LSND_SECTION_TYPE_ENDED) return false;
    LsndTag *lsnd_tag = this->get_lsnd_tag();
    if (lsnd_tag == NULL) return false;
    return lsnd_tag->track_sounds[this->track].flags.fade_out_at_stop;
}

SoundSamples *Playlist::get_next_samples() {
    if (!this->is_valid())  return NULL;
    if (this->is_paused())  return NULL;
    if (this->is_stopped()) return NULL;

    if (this->curr_section == LSND_SECTION_TYPE_STARTING) {
        this->inc_command();
    }

    LsndTag *lsnd_tag = this->get_lsnd_tag();
    if (lsnd_tag == NULL) return NULL;

    SndTag *snd_tag = this->get_snd_tag();
    if (snd_tag == NULL) return NULL;

    SoundSamples *samples = snd_tag->get_curr_samples();
    if (samples == NULL) return NULL;

    // cant do fading without having a validLsndTag to get the fade times from.
    if (!(lsnd_tag->is_valid())) return NULL;
    if (this->track >= lsnd_tag->track_sound_count) return NULL;

    if (samples->next_perm_index < 0) {
        // hit the end of the permutation chain; choose a new chain
        this->inc_command();
    } else {
        // increment permutation chain to the next link
        snd_tag->inc_perm_index();
    }

    samples->sect_type = this->curr_section;
    return samples;
}

SndTag *Playlist::get_snd_tag() {
    return this->get_snd_tag(this->curr_section, this->alt);
}
SndTag *Playlist::get_snd_tag(LsndSectionType section, bool use_alt) {
    LsndTag *lsnd_tag = this->get_lsnd_tag();
    if (lsnd_tag == NULL) return NULL;
    if (lsnd_tag->track_sounds == NULL || lsnd_tag->track_sound_count == 0) return NULL;
    LoadedTrack l_track = lsnd_tag->track_sounds[this->track];

    // the order and lack of breaks is correct. if there is no dedicated
    // start or end sound, we default to using the loop sound
    switch (section) {
    case LSND_SECTION_TYPE_STARTING:
    case LSND_SECTION_TYPE_START:
        if (l_track.start != NULL)                return l_track.start;
    case LSND_SECTION_TYPE_LOOP:
        if (use_alt  && l_track.alt_loop != NULL) return l_track.alt_loop;
        if (!use_alt && l_track.loop     != NULL) return l_track.loop;
        break;
    case LSND_SECTION_TYPE_END:
        if (use_alt  && l_track.alt_end  != NULL) return l_track.alt_end;
        if (!use_alt && l_track.end      != NULL) return l_track.end;
        if (use_alt  && l_track.alt_loop != NULL) return l_track.alt_loop;
        if (!use_alt && l_track.loop     != NULL) return l_track.loop;
    }
    return NULL;
}

LsndTag *Playlist::get_lsnd_tag() {
    return this->get_lsnd_tag(this->_curr_command_list);
}
LsndTag *Playlist::get_lsnd_tag(int list_index) {
    CommandList *cmdl = this->get_command_list(list_index);
    if (cmdl == NULL) return NULL;

    return cmdl->lsnd_tag;
}

CommandList *Playlist::get_command_list() {
    return this->get_command_list(this->_curr_command_list);
}
CommandList *Playlist::get_command_list(int list_index) {
    if (!this->is_valid()) return NULL;
    if (list_index < 0)         return NULL;

    if (this->command_list_count == 0 || this->command_lists == NULL) return NULL;
    if (list_index >= this->command_list_count) return NULL;

    // make sure the command_list array is actually valid
    CommandList *cmdl = this->command_lists + list_index;
    if (!is_valid_command_list(cmdl)) return NULL;

    return cmdl;
}

bool Playlist::inc_command_list() {
    if (!this->is_valid()) return true;

    CommandList *new_cmdl;
    sint32 new_command_list = this->_curr_command_list;
    uint32 tries = this->command_list_count;

    do {
        if (this->shuffle) {
            // choose a random command_list
           new_command_list = ((rand() + (rand() << 16)) %
                                (sint32)(this->command_list_count));
        } else if (this->command_list_count < 0) {
            // starting playlist from reset state
            new_command_list = 0;
        } else if (new_command_list < this->command_list_count - 1) {
            // increment to the next command_list
            new_command_list = new_command_list++;
        } else if (this->loop && this->command_list_count > 0) {
            // looping back to the first playlist
            new_command_list = 0;
        } else {
            // not looping back. set to invalid play state
            new_command_list = -1;
            break;
        }
        if (tries-- <= 0) break;

        new_cmdl = this->get_command_list(new_command_list);
        if (!is_valid_command_list(new_cmdl)) continue;  // bad track; loop again
        else if (new_cmdl->lsnd_tag != NULL)  break;
    } while (true);

    return this->select_command_list(new_command_list);
}

bool Playlist::select_command_list(int list_index) {
    CommandList   *cmdl = this->get_command_list(list_index);
    LsndTag *c_lsnd_tag = this->get_lsnd_tag();
    LsndTag   *lsnd_tag = this->get_lsnd_tag(list_index);

    if (c_lsnd_tag != NULL && c_lsnd_tag != lsnd_tag) {
        // make sure the old lsnd_tag's dependencies are unloaded
        c_lsnd_tag->unload_dependencies();
    }

    this->stop();
    if ((!is_valid_command_list(cmdl)) || lsnd_tag == NULL) {
        // invalid command_list or sound_looping tag
        this->_curr_command_list = -1;
        return true;
    } else {
        // increment to the first command in the command_list
        this->_curr_command_list = list_index;
        return this->inc_command();
    }
}

bool Playlist::add_command_list() {
    return this->insert_command_list(this->command_list_count);
}
bool Playlist::add_command_list(LsndTag *lsnd_tag) {
    return this->insert_command_list(this->command_list_count, lsnd_tag);
}

bool Playlist::insert_command_list(int list_index) {
    if (list_index < 0) return true;
    if (list_index > this->command_list_count) return true;

    // make a new command_list and a new buffer large enough to hold everything
    CommandList *new_cmdl = new_command_list();
    if (new_cmdl == NULL) return true;

    // if the current command_list doesnt exist we just use the new one as it
    if (this->command_lists == NULL || this->command_list_count == 0) {
        free(this->get_command_list());
        this->command_lists      = new_cmdl;
        this->command_list_count = 1;
        return false;
    }

    // use realloc so when delete_command is called and the buffer isnt
    // actually shrunk, it should decide to not reallocate the memory
    CommandList *new_cmdls = (CommandList *)realloc(
        this->command_lists, (this->command_list_count + 1) * COMMAND_LIST_SIZE);
    if (new_cmdls == NULL) {
        // couldn't allocate memory for the larger command_lists array.
        // free the new_cmdl and its commands and its lsnd_path.
        free(new_cmdl->lsnd_path);
        free(new_cmdl->commands);
        free(new_cmdl);
        return true;
    }

    size_t u_half_size = COMMAND_LIST_SIZE * (this->command_list_count - list_index);
    if (u_half_size > 0) {
        // move the upper half of the array up 1 entry
        memmove(new_cmdls + list_index + 1,
                new_cmdls + list_index,
                u_half_size);
    }
    memcpy(new_cmdls + list_index, new_cmdl, COMMAND_LIST_SIZE);
    free(new_cmdl);

    this->command_lists = new_cmdls;
    this->command_list_count++;

    return false;
}
bool Playlist::insert_command_list(int list_index, LsndTag *lsnd_tag) {
    if (list_index < 0)                return true;
    if (lsnd_tag == NULL)         return true;
    if (!lsnd_tag->is_valid())    return true;
    if (this->insert_command_list(list_index)) return true;

    // populate the new list with data from the lsnd_tag
    CommandList *cmdl = this->get_command_list(list_index);
    Command     *command;
    if (cmdl == NULL)           return true;
    if (cmdl->commands == NULL) return true;

    if (lsnd_tag->get_filepath() != NULL) {
        cmdl->lsnd_path     = strcpycat(&lsnd_tag->get_filepath()[lsnd_tag->tags_dir_len], "");
        cmdl->lsnd_path_len = strlen(cmdl->lsnd_path);
        uint32 i;
        for (i = cmdl->lsnd_path_len; i >= 0 && cmdl->lsnd_path[i] != '.'; i--) {
            if (i == 0 || cmdl->lsnd_path[i] == '/' || cmdl->lsnd_path[i] == '\\') {
                i = cmdl->lsnd_path_len;
                break;
            }
        }
        cmdl->lsnd_path_len = i;
        cmdl->lsnd_path[i]  = 0;
    }
    // blank the commands(1 created by default) so we can make them manually
    free(cmdl->commands);
    cmdl->play_length = 3 * 60;  // default to 3 minutes of play
    cmdl->command_count = 0;
    cmdl->commands = NULL;
    cmdl->lsnd_tag = lsnd_tag;

    bool unload = false;
    if (lsnd_tag->track_sounds == NULL) {
        lsnd_tag->load_dependencies();
        unload = true;
    }

    if (lsnd_tag->track_sounds != NULL) {
        // create commands for each of the sound_looping tags tracks
        for (sint32 i = 0; i < lsnd_tag->track_sound_count; i++) {
            // make sure the track_sounds are actually valid
            bool has_loops     = lsnd_tag->track_sounds[i].loop     != NULL;
            bool has_alt_loops = lsnd_tag->track_sounds[i].alt_loop != NULL;
            if (has_loops)     has_loops     &= lsnd_tag->track_sounds[i].loop->tag_data     != NULL;
            if (has_alt_loops) has_alt_loops &= lsnd_tag->track_sounds[i].alt_loop->tag_data != NULL;

            if (!has_loops && !has_alt_loops) {
                if (!this->add_command(list_index)) {
                    command = this->get_command(cmdl->command_count - 1, list_index);
                    command->ordered = true;
                    continue;
                }
            }

            if (has_loops) {
                if (!this->add_command(list_index)) {
                    command = this->get_command(cmdl->command_count - 1, list_index);
                    command->ordered = true;
                    if (has_alt_loops) {
                        command->loop_count = 9;  // default to 10 regular loops
                                                  // before going into any alt loops
                    } else {
                        command->endless_loop = true;
                    }
                }
            }
            if (has_alt_loops) {
                if (!this->add_command(list_index)) {
                    command = this->get_command(cmdl->command_count - 1, list_index);
                    command->ordered = true;
                    command->alt = true;
                    command->endless_loop = true;
                }
            }
        }
    }
    if (unload) lsnd_tag->unload_dependencies();

    if (cmdl->commands == NULL || cmdl->command_count == 0) {
        // no commands were added to the command_list, meaning the
        // sound_looping tag was blank and cant be played.
        this->remove_command_list(list_index);
        delete cmdl->lsnd_tag;
        return true;
    }

    return false;
}

bool Playlist::remove_command_list() {
    return this->remove_command_list(this->_curr_command_list);
}
bool Playlist::remove_command_list(int list_index) {
    if (list_index < 0) return true;
    // make sure the current command_list is actually valid
    CommandList *c_cmdl = this->get_command_list(list_index);
    if (c_cmdl == NULL) return true;

    // free the command_list's commands
    free(c_cmdl->commands);
    free(c_cmdl->lsnd_path);
    delete c_cmdl->lsnd_tag;

    // if there is only one command_list and we are removing it, set them to null
    if (this->command_list_count == 1) {
        free(this->command_lists);
        this->command_lists      = NULL;
        this->command_list_count = 0;
        this->_curr_command = -1;
        this->_curr_command_list = -1;
        return false;
    }

    // shift the upper command_lists in the array down by 1
    size_t l_half_size = list_index;
    size_t u_half_size = (this->command_list_count - list_index - 1);
    if (u_half_size != 0) {
        memmove(this->command_lists + l_half_size,
                this->command_lists + l_half_size + 1,
                COMMAND_LIST_SIZE * u_half_size);
    }
    // fix the current command_list
    this->command_list_count--;
    if (this->_curr_command_list > list_index)  this->_curr_command_list--;
    else if (this->_curr_command_list == list_index) this->select_command_list(-1);

    return false;
}

bool Playlist::move_command_list(int target, int src) {
    if (target < 0 || src < 0) return true;
    if (target == src) return false;

    // make sure the command_lists are actually valid
    CommandList *plists = this->command_lists;
    if (plists == NULL) return true;
    if (target < 0 || target >= this->command_list_count) return true;
    if (src    < 0 || src    >= this->command_list_count) return true;

    int chunk_size = target - src;
    if (chunk_size < 0) chunk_size *= -1;
    chunk_size *= sizeof(CommandList);

    CommandList *tmp = (CommandList *)alloca(sizeof(CommandList));
    // temporarily store the source command_list on the stack
    memcpy(tmp, plists + src, sizeof(CommandList));

    // shift the structs between the src and target up or down
    if (src < target) {
        memmove(plists + src,        
                plists + src + 1, 
                chunk_size);
    } else {
        memmove(plists + target + 1,
                plists + target,
                chunk_size);
    }
    // copy the source command_list to its target location
    memcpy(plists + target, tmp, sizeof(CommandList));

    // change the current list if it needs to be shifted
    if (this->_curr_command_list < 0) {
        ;// current list is invalid; dont change it.
    } else if (this->_curr_command_list == src) {
        // change this->_curr_command_list to the new target
        this->_curr_command_list = target;
    } else if (target > src && this->_curr_command_list > src && this->_curr_command_list <= target) {
        // need to shift this->_curr_command_list DOWN if it is
        // above the src and below or equal to the target
        this->_curr_command_list--;
    } else if (target < src && this->_curr_command_list < src && this->_curr_command_list >= target) {
        // need to shift this->_curr_command_list UP if it is
        // below the src and above or equal to the target
        this->_curr_command_list++;
    }

    return false;
}


Command *Playlist::get_command() {
    return this->get_command(this->_curr_command, this->_curr_command_list);
}
Command *Playlist::get_command(int index) {
    return this->get_command(index, this->_curr_command_list);
}
Command *Playlist::get_command(int index, int list_index) {
    if (index < 0) return NULL;
    CommandList *cmdl = this->get_command_list(list_index);
    // make sure the current command_list is actually valid
    if (!is_valid_command_list(cmdl)) return NULL;
    if (index >= cmdl->command_count) return NULL;

    return cmdl->commands + index;
}

bool Playlist::inc_command() {
    if (!this->is_valid()) return true;

    // the new_command may the the same one due to certain loop
    // conditions, so we use this->_curr_command until we know.
    sint32 new_command  = this->_curr_command;
    CommandList *c_cmdl = this->get_command_list();
    LsndTag *lsnd_tag   = this->get_lsnd_tag();
    SndTag  *snd_tag;

    if (lsnd_tag == NULL)      return true;
    if (!lsnd_tag->is_valid()) return true;
    if (!is_valid_command_list(c_cmdl)) {
        // current command list is invalid.
        // place it in a reset state.
        this->select_command_list(-1);
        return true;
    }

    // determine if the lsnd_tag has its sounds loaded
    bool load_failed = lsnd_tag->load_dependencies();

    // increment the current section type if necessary
    switch (this->curr_section) {
    case LSND_SECTION_TYPE_STARTING:
        // make sure sounds are loaded and their permutation states are reset
        if (load_failed || lsnd_tag->reset_sound_states()) {
            // couldnt load/reset sounds.
            // reset to playing nothing and pause timers.
            this->stop();
            return true;
        }

        new_command = -1;
        this->curr_section = LSND_SECTION_TYPE_START;

        // skip this section if there isnt a start sound
        snd_tag = lsnd_tag->track_sounds[this->track].start;
        if (snd_tag != NULL) {
            snd_tag->set_actual_perm_index(0);
            break;
        }

    case LSND_SECTION_TYPE_START:
        if (this->play_timer() >= this->fade_in_end()) {
            this->curr_section = LSND_SECTION_TYPE_LOOP;
            // skip this section if there isnt a loop sound
            snd_tag = this->get_snd_tag();
            if (snd_tag != NULL) {
                snd_tag->set_actual_perm_index(0);
                break;
            }
        } else {
            break;
        }

    case LSND_SECTION_TYPE_LOOP:
        if (c_cmdl->play_length > 0.0 &&
            this->play_timer() > 0.5 &&
            this->play_timer() >= (double)c_cmdl->play_length) {
            // play time up. start ending this sound_looping tag's playback
            this->curr_section = LSND_SECTION_TYPE_END;
            this->fade_out_timer(0.0);
        }
        // skip this section if there isnt an end sound
        snd_tag = this->get_snd_tag();
        if (snd_tag != NULL) {
            if (this->curr_section == LSND_SECTION_TYPE_END) {
                // make sure a permutation is selected for the end sound
                snd_tag->set_actual_perm_index(0);

                // only break if the end is to be faded out or
                // there is a specific end sound to play.
                if (this->fade_out()) break;
                else if (!this->alt && lsnd_tag->track_sounds[this->track].end != NULL)     break;
                else if (this->alt  && lsnd_tag->track_sounds[this->track].alt_end != NULL) break;
            } else {
                break;
            }
        }

    case LSND_SECTION_TYPE_END:
    case LSND_SECTION_TYPE_ENDED:
        this->curr_section = LSND_SECTION_TYPE_ENDED;
        break;

    default:
        // currently in an invalid section state
        this->curr_section = LSND_SECTION_TYPE_NONE;
        break;
    }

    Command *curr_cmd = this->get_command();
    Command *next_cmd;
    bool     skip = false;
    bool     reset_counter = false;
    sint32   can_skip = c_cmdl->command_count;

    if (is_valid_command(curr_cmd) && this->curr_section == LSND_SECTION_TYPE_END) {
        // playback ending. to simplify things the command wont get incremented.
        // this prevents accidentally calling select_command when the end sound
        // is selected, and allows us to know which permutation was being played
        // when the track started to end.
        return false;
    } else if (this->curr_section == LSND_SECTION_TYPE_ENDED) {
        return false;
    }

    // decide which command to increment to
    do {
        if (this->curr_section == LSND_SECTION_TYPE_NONE ||
            this->curr_section == LSND_SECTION_TYPE_ENDED) {
            // not playing anything. set new_command to -1 to stop playing.
            new_command = -1;
            break;
        }

        if (new_command + 1 < c_cmdl->command_count) {
            // increment to the next command index
            new_command++;
        } else {
            // hit the end, so restart to the first command
            new_command = 0;
        }

        next_cmd = this->get_command(new_command);
        if (!is_valid_command(next_cmd)) {
            // next command is invalid. set new_command to -1 to stop playing.
            new_command = -1;
            break;
        }

        if (is_valid_command(curr_cmd)) {
            // check if the current command needs to be repeated
            if (!curr_cmd->skip && curr_cmd->endless_loop) {
                // nothing needs to be done, looping forever
                new_command = this->_curr_command;
                break;
            } else if (!curr_cmd->skip && this->loop_iteration < curr_cmd->loop_count) {
                // need to play this loop more times. increment the loop count
                new_command = this->_curr_command;
                this->loop_iteration++;
                break;
            } else {
                // finished looping. reset loop counter
                reset_counter = true;
            }
        }
        skip = next_cmd->skip && (can_skip > 0);

        can_skip--;
    } while (skip);

    next_cmd = this->get_command(new_command);
    if (!is_valid_command(next_cmd) && new_command >= 0) return true;
    if (reset_counter) this->loop_iteration = 0;

    return this->select_command(new_command);
}

bool Playlist::select_command(int index) {
    if (!this->is_valid()) return true;
    if (index < 0) {
        this->stop();
        return false;
    }

    CommandList *c_cmdl  = this->get_command_list();
    Command     *c_cmd   = this->get_command(index);
    if (!is_valid_command_list(c_cmdl)) return true;
    if (!is_valid_command(c_cmd))       return true;

    // backup the current alt state
    bool curr_alt = this->alt;

    switch (this->curr_section) {
    case LSND_SECTION_TYPE_LOOP:
        this->alt = c_cmd->alt;
    case LSND_SECTION_TYPE_END:
        break;  // leave it unchanged from what it last was
    default:
        this->alt = false;
    }

    SndTag *snd_tag = this->get_snd_tag();
    if (snd_tag == NULL) {
        this->alt = curr_alt;
        return true;
    }

    this->_curr_command = index;

    if (c_cmd->ordered) {
        // sound tag will increment itself in order using each
        // perms skip_factor to determine whether to play or skip.
        snd_tag->inc_actual_perm_index();
    } else {
        // playlist will determine which permutation to play.
        sint16 new_perm_index = snd_tag->max_actual_perm();

        if (c_cmd->any && (new_perm_index > 0)) {
            // choose a random permutation
            new_perm_index = rand() % (sint16)(new_perm_index + 1);
        } else if (c_cmd->perm_index <= new_perm_index) {
            // choose the perm specified by the command
            new_perm_index = c_cmd->perm_index;
        }

        snd_tag->set_actual_perm_index(new_perm_index);
    }

    return false;
}

bool Playlist::add_command() {
    return this->insert_command(this->_curr_command, this->_curr_command_list);
}
bool Playlist::add_command(int list_index) {
    CommandList *cmdl = this->get_command_list(list_index);
    if (cmdl == NULL) return true;

    return this->insert_command(cmdl->command_count, list_index);
}

bool Playlist::insert_command(int index) {
    return this->insert_command(index, this->_curr_command_list);
}
bool Playlist::insert_command(int index, int list_index) {
    if (index < 0 || list_index < 0) return true;
    CommandList *c_cmdl = this->get_command_list(list_index);
    if (!is_valid_command_list(c_cmdl)) return true;
    if (index > c_cmdl->command_count) return true;

    // make a new command and a new buffer large enough to hold everything
    Command *new_cmd = new_command();
    if (new_cmd == NULL) return true;

    // if the current command_list doesnt have any commands we will fix
    // this broken state by setting it to the newly made command.
    if (c_cmdl->commands == NULL || c_cmdl->command_count == 0) {
        free(c_cmdl->commands);
        c_cmdl->commands = new_cmd;
        c_cmdl->command_count = 1;
        return false;
    }

    // use realloc so when delete_command is called and the buffer isnt
    // actually shrunk, it should decide to not reallocate the memory
    Command *new_cmds = (Command *)realloc(
        c_cmdl->commands, (c_cmdl->command_count + 1) * COMMAND_SIZE);
    if (new_cmds == NULL) {
        free(new_cmd);
        return true;
    }

    size_t u_half_size = COMMAND_SIZE * (c_cmdl->command_count - index);
    if (u_half_size > 0) {
        // move the upper half of the array up 1 entry
        memmove(new_cmds + index + 1,
                new_cmds + index,
                u_half_size);
    }
    memcpy(new_cmds + index, new_cmd, COMMAND_SIZE);
    free(new_cmd);

    c_cmdl->commands = new_cmds;
    c_cmdl->command_count++;

    return false;
}

bool Playlist::remove_command() {
    return this->remove_command(this->_curr_command, this->_curr_command_list);
}
bool Playlist::remove_command(int index) {
    return this->remove_command(index, this->_curr_command_list);
}
bool Playlist::remove_command(int index, int list_index) {
    if (index < 0 || list_index < 0) return true;
    // make sure the current command_list is actually valid
    CommandList *cmdl = this->get_command_list(list_index);
    if (cmdl == NULL) return true;

    if (cmdl->command_count <= 1) {
        // command_lists cannot be empty. they MUST have an entry
        return true;
    }

    // shift the upper commands in the array down by 1
    size_t l_half_size = index;
    size_t u_half_size = (cmdl->command_count - index - 1);
    if (u_half_size != 0) {
        memmove(cmdl->commands + l_half_size,
                cmdl->commands + l_half_size + 1,
                COMMAND_SIZE * u_half_size);
    }
    cmdl->command_count--;
    if (list_index == this->_curr_command_list) {
        // fix the current command_list command if editing the active list
        if (this->_curr_command > index)  this->_curr_command--;
        else if (this->_curr_command == index) this->select_command(-1);
    }

    return false;
}

bool Playlist::move_command(int target, int src) {
    return this->move_command(target, src, this->_curr_command_list);
}
bool Playlist::move_command(int target, int src, int list_index) {
    if (src < 0 || target < 0 || list_index < 0) return true;
    if (target == src) return false;

    // make sure the current command_list is actually valid
    CommandList *cmdl = this->get_command_list(list_index);
    if (cmdl == NULL) return true;
    if (target < 0 || target >= cmdl->command_count) return true;
    if (src    < 0 || src    >= cmdl->command_count) return true;

    int chunk_size = target - src;
    if (chunk_size < 0) chunk_size *= -1;
    chunk_size *= sizeof(Command);

    Command *tmp = (Command *)alloca(sizeof(Command));
    // temporarily store the source command_list on the stack
    memcpy(tmp, cmdl->commands + src, sizeof(Command));

    // shift the structs between the src and target up or down
    if (src < target) {
        memmove(cmdl->commands + src,
                cmdl->commands + src + 1,
                chunk_size);
    } else {
        memmove(cmdl->commands + target + 1, 
                cmdl->commands + target, 
                chunk_size);
    }
    // copy the source command_list to its target location
    memcpy(cmdl->commands + target, tmp, sizeof(Command));

    // change the current command if it needs to be shifted
    if (this->_curr_command < 0) {
        ;// current command is invalid; dont change it.
    } else if (this->_curr_command == src) {
        // change this->_curr_command to the new target
        this->_curr_command = target;
    } else if (target > src && this->_curr_command > src && this->_curr_command <= target) {
        // need to shift this->_curr_command DOWN if it is
        // above the src and below or equal to the target
        this->_curr_command--;
    } else if (target < src && this->_curr_command < src && this->_curr_command >= target) {
        // need to shift this->_curr_command UP if it is
        // below the src and above or equal to the target
        this->_curr_command++;
    }

    return false;
}

void Playlist::parse(char *input_path) {
    if (input_path == NULL) return;
    FILE *in_file = fopen(input_path, "rb");
    long length = 0;

    if (!in_file) {
        // couldn't load the playlist for some reason
        cout << "Could not load playlist: " << input_path << '\n';
        return;
    }

    fseek(in_file, 0, SEEK_END);
    length = ftell(in_file);
    fseek(in_file, 0, SEEK_SET);

    if (length < (PLAYLIST_HEADER_SIZE + COMMAND_LIST_SIZE +  COMMAND_SIZE)) {
        // not even enough data to read the header, a command_list, and a command
        fclose(in_file);
        return;
    }

    // copy the header into memory
    CommandList    *cmdl;
    PlaylistHeader *head = (PlaylistHeader *)malloc(PLAYLIST_HEADER_SIZE);
    if (head == NULL) {
        fclose(in_file);
        return;
    }

    fread(head, PLAYLIST_HEADER_SIZE, 1, in_file);
    if (head->tags_dir_len > MAX_CFG_STR_LEN) {
        // max string size exceeded
        free(head);
        fclose(in_file);
        return;
    }

    // read the tags_dir and last_tag into memory
    head->tags_dir = (char *)malloc(head->tags_dir_len + 1);
    if (head->tags_dir == NULL) {
        free(head);
        fclose(in_file);
        return;
    }
    fread(head->tags_dir, head->tags_dir_len + 1, 1, in_file);

    // read the command_lists into memory
    head->command_lists = (CommandList *)calloc(
        head->command_list_count, PLAYLIST_HEADER_SIZE);
    if (head->command_lists == NULL) {
        // couldnt allocate for the command_lists. free the allocated memory
        free(head->tags_dir);
        free(head);
        fclose(in_file);
        return;
    }
    fread(head->command_lists, PLAYLIST_HEADER_SIZE, head->command_list_count, in_file);

    // load each command_lists lsnd path and commands
    bool bad_load = false;
    for (sint32 i = 0; i < head->command_list_count; i++) {
        cmdl = &head->command_lists[i];
        if (cmdl->sig != COMMAND_LIST_SIG || bad_load) {
            cmdl->lsnd_path = NULL;
            cmdl->commands  = NULL;
            cmdl->lsnd_tag  = NULL;
            bad_load = true;
            continue;
        }

        cmdl->lsnd_path = (char *)malloc(cmdl->lsnd_path_len + 1);
        cmdl->commands = (Command *)calloc(
            cmdl->command_count, COMMAND_SIZE);

        if (cmdl->lsnd_path == NULL || cmdl->commands == NULL) {
            // couldnt allocate memory. start setting every pointer to NULL
            bad_load = true;
            continue;
        }
        fread(cmdl->lsnd_path, cmdl->lsnd_path_len + 1, 1, in_file);
        fread(cmdl->commands, COMMAND_SIZE, cmdl->command_count, in_file);

        cmdl->lsnd_tag = (LsndTag *)load_tag_at_path(
            strcpycat(head->tags_dir,
                strcpycat(cmdl->lsnd_path, ".sound_looping"), 0, 1), head->tags_dir);
    }

    fclose(in_file);

    if (bad_load) {
        // couldnt load command_lists. gotta free all allocated memory
        for (sint32 i = 0; i < this->command_list_count; i++) {
            cmdl = &head->command_lists[i];
            // free the command_list's commands and its tag path
            free(cmdl->lsnd_path);
            free(cmdl->commands);
            free(cmdl->lsnd_tag);
        }
        free(head->tags_dir);
        free(head->command_lists);
        free(head);
        return;
    }

    // erase the old playlist data and update it with the loaded data
    this->erase_playlist();

    // populate this playlist with the loaded one
    this->command_lists      = head->command_lists;
    this->command_list_count = head->command_list_count;
    this->tags_dir     = head->tags_dir;
    this->tags_dir_len = head->tags_dir_len;
    this->shuffle = head->shuffle;
    this->loop    = head->shuffle || head->loop;
    this->loop_iteration = 0;
    this->pause_start = -1.0;
    this->play_timer(0.0);
    this->fade_out_timer(0.0);

    this->_curr_command = -1;
    this->_curr_command_list = -1;

    this->set_filepath(input_path);

    if (!this->is_valid()) {
        // playlist wasn't properly formed. make a default blank one
        this->new_playlist();
    }
}

size_t Playlist::serialize() {
    if (!this->is_valid()) return 0;

    FILE *out = fopen(this->filepath, "wb");

    if (!out) return 0;

    CommandList    *c_cmdl;
    PlaylistHeader *head = (PlaylistHeader *)
        calloc(1, sizeof(PlaylistHeader));

    // make sure ALL the command_lists are valid
    for (sint32 i = 0; i < this->command_list_count &&
        0 < this->command_list_count; i++) {
        if (!is_valid_command_list(&this->command_lists[i])) {
            this->command_list_count--;
            this->remove_command_list(i);
            i--;
        }
    }

    // populate the header
    head->sig = PLAYLIST_HEADER_SIG;
    head->command_lists      = this->command_lists;
    head->command_list_count = this->command_list_count;
    head->tags_dir     = this->tags_dir;
    head->tags_dir_len = this->tags_dir_len;
    head->shuffle = this->shuffle;
    head->loop    = this->shuffle || this->loop;

    // write the playlist header
    fwrite(head, PLAYLIST_HEADER_SIZE, 1, out);

    // write the tags dir
    fwrite(head->tags_dir, head->tags_dir_len + 1, 1, out);

    // write the command_lists
    fwrite(this->command_lists, sizeof(CommandList),
           head->command_list_count, out);

    // write each command_list's lsnd tag path and commands
    for (sint32 i = 0; i < head->command_list_count; i++) {
        c_cmdl = &this->command_lists[i];
        fwrite(c_cmdl->lsnd_path, 1,
               c_cmdl->lsnd_path_len, out);
        // make sure the string is null terminated
        fwrite("", 1, 1, out);
        fwrite(c_cmdl->commands, sizeof(Command),
               c_cmdl->command_count, out);
    }

    fseek(out, 0, SEEK_END);
    long length = ftell(out);
    fclose(out);

    return length;
}


void Playlist::new_playlist() {
    this->erase_playlist();
    this->filepath = strcpycat(get_working_dir(), "new_playlist.play", 1, 0);
    this->tags_dir = strcpycat(get_working_dir(), "tags\\", 1, 0);
    this->filepath_len = strlen(this->filepath);
    this->tags_dir_len = strlen(this->tags_dir);

    this->pause_start = -1.0;
    this->pause_timers();
    this->_curr_command      = -1;
    this->_curr_command_list = -1;
    this->loop_iteration = 0;
    this->play_timer(0.0);
    this->fade_out_timer(0.0);
    this->track   = 0;
    this->shuffle = false;
    this->loop    = false;

    this->command_lists = NULL;
    this->command_list_count = 0;
}

void Playlist::erase_playlist() {
    CommandList *plists;

    if (this->command_lists != NULL) {
        // might need to free command_lists
        plists = this->command_lists;

        for (sint32 i = 0; i < this->command_list_count; i++) {
            // free the command_list's commands and its tag path
            if (plists[i].lsnd_tag  != NULL) delete plists[i].lsnd_tag;
            if (plists[i].lsnd_path != NULL) free(plists[i].lsnd_path);
            if (plists[i].commands  != NULL) free(plists[i].commands);
        }
    }

    free(this->tags_dir);
    free(this->command_lists);
    free(this->filepath);
    this->tags_dir      = NULL;
    this->command_lists = NULL;
    this->filepath      = NULL;
    this->tags_dir_len       = 0;
    this->command_list_count = 0;
    this->filepath_len       = 0;
}

bool Playlist::is_valid() {
    if (this->tags_dir == NULL || this->filepath == NULL) {
        return false;
    }
    return true;

}