import os
import threadsafe_tkinter as tk

from os.path import dirname, join, splitext, relpath
from time import time
from threading import Thread
from tkinter.filedialog import askopenfilenames
from tkinter.font import Font
from tkinter import messagebox
from traceback import format_exc

from supyr_struct.defs.constants import *
from binilla.util import *
from binilla.widgets import BinillaWidget

curr_dir = dirname(__file__)

text_tags = dict(
    processing = '#%02x%02x%02x' % (255, 180,   0),  # yellow
    processed  = '#%02x%02x%02x' % (  0, 200,  50),  # green
    )

COMMENT_START_STRS = ["#", ";", "/"]

tool_command_help = {
    "animations": "",
    "bitmap": "",
    "bitmaps": "",
    "build-cache-file": "",
    "build-cache-file-ex": "",
    "build-cache-file-new": "",
    "build-cpp-definition": "",
    "build-packed-file": "",
    "collision-geometry": "",
    "compile-scripts": "",
    "compile-shader-postprocess": "",
    "help": "",
    "hud-messages": "",
    "import-device-defaults": "",
    "import-structure-lightmap-uvs": "",
    "lightmaps": "",
    "merge-scenery": "",
    "model": "",
    "physics": "",
    "process-sounds": "",
    "remove-os-tag-data": "",
    "runtime-cache-view": "",
    "sounds": "",
    "sounds_by_type": "",
    "strings": "",
    "structure": "",
    "structure-breakable-surfaces": "",
    "structure-lens-flares": "",
    "tag-load-test": "",
    "unicode-strings": "",
    "windows-font": "",
    "zoners_model_upgrade": "",
    }


tool_commands = {
    "animations": (
        ("source-directory", ""),
        ),
    "bitmap": (
        ("source-file", ""),
        ),
    "bitmaps": (
        ("source-directory", ""),
        ),
    "build-cache-file": (
        ("scenario-name", ""),
        ),
    "build-cache-file-ex": (
        ("mod-name",           ""),
        ("create-anew",         0),
        ("store-resources",     0),
        ("use-memory-upgrades", 0),
        ("scenario-name",      ""),
        ),
    "build-cache-file-new": (
        ("create-anew",         0),
        ("store-resources",     0),
        ("use-memory-upgrades", 0),
        ("scenario-name",      ""),
        ),
    "build-cpp-definition": (
        ("tag-group",         ""),
        ("add-boost-asserts",  0),
        ),
    "build-packed-file": (
        ("source-directory",    ""),
        ("output-directory",    ""),
        ("file-definition-xml", ""),
        ),
    "collision-geometry": (
        ("source-directory", ""),
        ),
    "compile-scripts": (
        ("scenario-name", ""),
        ),
    "compile-shader-postprocess": (
        ("shader-directory", ""),
        ),
    "help": (
        ("os-tool-command", "", (
            "animations",
            "bitmap",
            "bitmaps",
            "build-cache-file",
            "build-cache-file-ex",
            "build-cache-file-new",
            "build-cpp-definition",
            "build-packed-file",
            "collision-geometry",
            "compile-scripts",
            "compile-shader-postprocess",
            "hud-messages",
            "import-device-defaults",
            "import-structure-lightmap-uvs",
            "lightmaps",
            "merge-scenery",
            "model",
            "physics",
            "process-sounds",
            "remove-os-tag-data",
            "runtime-cache-view",
            "sounds",
            #"sounds_by_type",
            "structure",
            "structure-breakable-surfaces",
            "structure-lens-flares",
            "tag-load-test",
            "unicode-strings",
            "windows-font",
            #"zoners_model_upgrade",
            )
         ),
        ),
    "hud-messages": (
        ("path",          ""),
        ("scenario-name", ""),
        ),
    "import-device-defaults": (
        ("type",          "", ("defaults", "profiles")),
        ("savegame-path", ""),
        ),
    "import-structure-lightmap-uvs": (
        ("structure-bsp", ""),
        ("obj-file",      ""),
        ),
    "lightmaps": (
        ("scenario",        ""),
        ("bsp-name",        ""),
        ("quality",        0.0),
        ("stop-threshold", 0.5),
        ),
    "merge-scenery": (
        ("source-scenario",      ""),
        ("destination-scenario", ""),
        ),
    "model": (
        ("source-directory", ""),
        ),
    "physics": (
        ("source-file", ""),
        ),
    "process-sounds": (
        ("root-path", ""),
        ("substring", ""),
        ("effect", "gain+",
             ("gain+", "gain-", "gain=",
              "maximum-distance", "minimum-distance"),
             ),
        ("value", 0.0),
        ),
    "remove-os-tag-data": (
        ("tag-name",         ""),
        ("tag-type",         ""),
        ("recursive", 0, (0, 1)),
        ),
    "runtime-cache-view": (),
    "sounds": (
        ("directory-name",            ""),
        ("platform",                  "", ("ogg", "xbox", "wav")),
        ("use-high-quality(ogg_only)", 1,  (0, 1)),
        ),
    #"sounds_by_type": (
    #    ("directory-name", ""),
    #    ("type",           ""),
    #    ),
    "strings": (
        ("source-directory", ""),
        ),
    "structure": (
        ("scenario-directory", ""),
        ("bsp-name",           ""),
        ),
    "structure-breakable-surfaces": (
        ("structure-name",   ""),
        ),
    "structure-lens-flares": (
        ("bsp-name", ""),
        ),
    "tag-load-test": (
        ("tag-name", ""),
        ("group",    ""),
        ("prompt-to-continue",       0, (0, 1)),
        ("load-non-resolving-refs",  0, (0, 1)),
        ("print-size",               0, (0, 1)),
        ("verbose",                  0, (0, 1)),
        ),
    "unicode-strings": (
        ("source-directory", ""),
        ),
    "windows-font": (),
    #"zoners_model_upgrade": (),
    }


class HekPool(tk.Tk, BinillaWidget):
    config_file = None
    processes = ()

    _execution_state = 0  # 0 == not executing,  1 == executing
    _stop_processing = False
    _execution_thread = None

    fixed_font = None

    open_log = None
    clear_log = None
    proc_limit = None

    tool_paths = ()
    command_lists = ()
    command_lists_flags = ()

    curr_tool_index = -1
    curr_command_list_name = None

    '''Miscellaneous properties'''
    _initialized = False
    app_name = "Pool"  # the name of the app(used in window title)
    version = '1.0.0'
    log_filename = 'hek_pool.log'
    debug = 0
    debug_mode = False

    def __init__(self, *args, **kwargs):
        self.last_load_dir = curr_dir
        self.processes = {}
        self.tool_paths = []
        self.command_lists = {}
        self.command_lists_flags = {}

        self.app_name = kwargs.pop('app_name', self.app_name)
        self.app_name = str(kwargs.pop('version', self.app_name))

        for i in range(20):
            print("DONT FORGET TO FIX THE HIDDEN TITLE INDENT BUG")

        tk.Tk.__init__(self, *args, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self.close)

        if type(self).fixed_font is None:
            type(self).fixed_font = Font(family="Terminal", size=10)

        self.title('%s v%s' % (self.app_name, self.version))
        self.minsize(width=400, height=300)

        # make the tkinter variables
        self.open_log = tk.BooleanVar(self)
        self.clear_log = tk.BooleanVar(self)
        self.proc_limit = tk.IntVar(self, 5)

        # make the menubar
        self.main_menu = tk.Menu(self)
        self.tools_menu = tk.Menu(self.main_menu, tearoff=0,
                                  postcommand=self.generate_tools_menu)
        self.config(menu=self.main_menu)
        self.main_menu.add_command(label="Add Tool",
                                   command=self.tool_path_browse)
        self.main_menu.add_command(label="Remove Tool",
                                   command=self.remove_tool_path)
        self.main_menu.add_cascade(label="Select Tool",
                                   menu=self.tools_menu)

        self.commands_text = tk.Text(self, font=self.fixed_font)
        self.commands_text.tag_config(
            "processing", background=text_tags['processing'])
        self.commands_text.tag_config(
            "processed", background=text_tags['processed'])

        # make the frames
        '''
        self.directory_frame = tk.LabelFrame(self, text="Directory to scan")
        self.def_ids_frame = tk.LabelFrame(
            self, text="Select which tag types to scan")
        self.button_frame = tk.Frame(self.def_ids_frame)

        self.def_ids_scrollbar = tk.Scrollbar(
            self.def_ids_frame, orient="vertical")
        self.def_ids_listbox = tk.Listbox(
            self.def_ids_frame, selectmode='multiple', highlightthickness=0,
            yscrollcommand=self.def_ids_scrollbar.set)
        self.def_ids_scrollbar.config(command=self.def_ids_listbox.yview)

        for w in (self.directory_entry, ):
            w.pack(padx=(4, 0), pady=2, side='left', expand=True, fill='x')

        for w in (self.dir_browse_button, ):
            w.pack(padx=(0, 4), pady=2, side='left')

        for w in (self.scan_button, self.cancel_button):
            w.pack(padx=4, pady=2)

        self.def_ids_scrollbar.pack(side='left', fill="y")
        self.directory_frame.pack(fill='x', padx=1)'''
        self.commands_text.pack(fill='both', expand=True)
        self.apply_config()
        self.apply_style()

    @property
    def remaining_commands(self):
        pass

    def apply_style(self):
        self.config(bg=self.default_bg_color)
        for w in():#self.directory_frame, ):
            w.config(fg=self.text_normal_color, bg=self.default_bg_color)

        self.commands_text.config(fg=self.io_fg_color, bg=self.io_bg_color)
        #self.button_frame.config(bg=self.default_bg_color)

        for w in ():#self.dir_browse_button, ):
            w.config(bg=self.button_color, activebackground=self.button_color,
                     fg=self.text_normal_color, bd=self.button_depth,
                     disabledforeground=self.text_disabled_color)

        for w in ():#self.directory_entry, ):
            w.config(bd=self.entry_depth,
                bg=self.entry_normal_color, fg=self.text_normal_color,
                disabledbackground=self.entry_disabled_color,
                disabledforeground=self.text_disabled_color,
                selectbackground=self.entry_highlighted_color,
                selectforeground=self.text_highlighted_color)

    def apply_config(self):
        config_file = self.config_file
        if not config_file:
            return

        self.tool_paths = [b.path for b in config_file.tool_paths]
        self.command_lists = {}
        self.command_lists_flags = {}
        for block in config_file.tool_commands:
            self.command_lists[b.name] = b.commands
            self.command_lists_flags[b.name] = b.command_flags

        self.curr_tool_index = config_file.last_tool_path - 1
        self.select_tool_path(self.curr_tool_index)

    def _start_process(self, cmd_line, exec_path, exec_args, cmd_args):
        self.processes.setdefault(cmd_line, cmd_line)  # make sure this one is
        assert self.processes[cmd_line] is cmd_line    # not currently in use.

        def proc_wrapper(app, line, *args, **kwargs):
            try:
                do_subprocess(*args, **kw)
            except Exception:
                print(format_exc())

            if app is None:
                return
            app.processes.pop(tid, None)

            if len(app.processes) == 0:
                app._execution_state = 0

            # set the command's text to the 'processed' color
            # maybe do this with tagged regions
            app.set_line_color(line, "processed")

        proc_controller = ProcController()
        kwargs.update(proc_controller=proc_controller)
        new_thread = Thread(
            target=proc_wrapper, daemon=True,
            args=(self, cmd_line, exec_path, exec_args, cmd_args))
        self.processes[cmd_line] = dict(
            thread=new_thread, proc_controller=proc_controller,
            exec_path=exec_path, exec_args=exec_args, cmd_args=cmd_args)
        new_thread.start()

    def set_line_color(self, line=None, color=None):
        if line is None:
            start, end = "1.0", tk.END
        else:
            start, end = "%d.0" % line, "%d.end" % line

        if color is None:
            for color in text_tags:
                self.commands_text.tag_remove(color, start, end)
        else:
            self.commands_text.tag_add(color, start, end)

    def get_command(self, line):
        cmd_str = self.commands_text.get(
            '%d.0' % line, '%d.end' % line).strip("\n").strip(" ")
        disabled = False
        no_comment_cmd_str = cmd_str
        for c in COMMENT_START_STRS:
            no_comment_cmd_str = no_comment_cmd_str.lstrip(c)

        disabled = len(no_comment_cmd_str) == len(cmd_str)
        cmd_str = no_comment_cmd_str.lstrip(" ")

        cmd_name, cmd_str = cmd_str.split(' ', 1)
        cmd_args = [cmd_name]

        in_str, param_str = False, ""
        for c in cmd_str:
            if c == " " and not in_str:
                if param_str:
                    cmd_args.append(param_str)
                param_str = ""
            elif c == '"':
                in_str = not in_str
                param_str += c

        if param_str:
            if in_str:
                param_str += '"'
            cmd_args.append(param_str)

        return cmd_args, disabled

    def set_flag(self, flag_name, var):
        name, all_flags = self.curr_command_list_name, self.command_lists_flags
        if name in all_flags:
            all_flags[name].set_to(flag_name, bool(var.get()))
        else:
            print("No set of flags named '%s'" % name)

    def get_command_flags(self, line):
        exec_args = []
        if self.curr_command_list_name not in self.command_lists_flags:
            return exec_args

        flags = self.command_lists_flags[self.curr_command_list_name]
        if flags.keep_window_open:
            exec_args.append('k')
        else:
            exec_args.append('c')

        return exec_args

    def get_can_execute_command(self, cmd_args):
        # TODO
        return True

    def execute_commands(self, e=None):
        if not self._execution_thread:
            pass
        elif self._execution_thread.is_alive():
            return
        self._execution_thread = Thread(target=self._execute_commands, daemon=1)
        self._execution_thread.start()

    def _execute_commands(self):
        if self._execution_state:
            return
        self._execution_state = True

        log_path = ""
        open_log, clear_log = self.open_log.get(), self.clear_log.get()
        try:
            self.commands_text.config(state=tk.DISABLED)
            start = time()
            exec_path = self.get_tag_path()
            log_path = join(dirname(exec_path), 'debug.txt')
            command_count, i = self.remaining_commands, 0
            processes, proc_limit = self.processes, self.tk_proc_limit
            if clear_log:
                try:
                    f = open(log_path, "w+b")
                    f.close()
                except Exception:
                    pass

            curr_max_proc_ct = 0
            while i < command_count and not self._stop_processing:
                curr_proc_ct = len(processes)

                # continually execute processes until the max quota is hit
                if curr_proc_ct >= proc_limit.get():
                    sleep(0.1)
                    continue

                exec_args, disabled = self.get_command(i)
                cmd_args  = self.get_command_flags(i)
                i += 1
                if disabled or not exec_args:
                    # ignore commented and empty commands
                    continue
                elif curr_max_proc_ct and curr_proc_ct == curr_max_proc_ct:
                    # same number of processes as last checked. don't
                    # need to check self.get_can_execute_command again
                    continue
                elif not self.get_can_execute_command(cmd_args):
                    curr_max_proc_ct = curr_proc_ct
                    continue

                curr_max_proc_ct = 0

                # start the command
                self._start_process(i - 1, exec_path, exec_args, cmd_args)

                # set the command's text to the 'processing' color
                # maybe do this with tagged regions
                self.set_line_color(line, "processing")

            while not len(processes):
                # wait until all processes finish
                sleep(0.1)

            error = None
        except Exception as error:
            pass

        self._execution_state = False
        print("Finished executing Tool commands. " +
              "Took %s seconds" % (time() - start))
        if open_log:
            try: do_subprocess(log_path, cmd_args=("c",))
            except Exception: pass
        self.commands_text.config(state=tk.NORMAL)
        self.set_line_color()

        if error: raise error

    def generate_tools_menu(self):
        self.tools_menu.delete(0, "end")
        i = 0

        for tool_path in self.tool_paths:
            try:
                self.tools_menu.add_command(
                    label=tool_path, command=lambda index=i:
                    self.select_tool_path(index))
                i += 1
            except Exception:
                print(format_exc())

    def insert_tool_path(self, path, index=None):
        if index is None:
            index = len(self.tool_paths)

        self.tool_paths.insert(index, path)
        if self.config_file:
            try:
                paths = self.config_file.tool_paths
                paths.insert(index)
                paths[index].path = path
            except Exception:
                pass

        if self.curr_tool_index not in range(len(self.tool_paths)):
            self.select_tool_path(len(self.tool_paths) - 1)

    def remove_tool_path(self, index=None):
        if self._execution_state or not len(self.tool_paths):
            return
        elif index is None:
            index = self.curr_tool_index

        self.tool_paths.pop(index)
        if self.config_file:
            try:
                self.config_file.tool_paths.pop(index)
            except Exception:
                pass

        if self.curr_tool_index not in range(len(self.tool_paths)):
            self.curr_tool_index = len(self.tool_paths) - 1

        if not len(self.tool_paths):
            self.main_menu.entryconfig(3, label="Select Tool")

    def select_tool_path(self, index):
        assert isinstance(index, int)
        assert index in range(len(self.tool_paths))
        self.curr_tool_index = max(index, 0)
        tag_path = self.tool_paths[index]
        if self.config_file:
            try:
                self.config_file.last_tool_path = self.curr_tool_index + 1
            except Exception:
                pass

        path_parts = tag_path.replace('/', '\\').split('\\')
        if len(path_parts) > 2:
            trimmed_path = "%s\\...\\%s\\%s" % (
                path_parts[0], path_parts[-2], path_parts[-1])
        else:
            trimmed_path = tag_path

        self.main_menu.entryconfig(3, label=trimmed_path)

    def tool_path_browse(self):
        for fp in askopenfilenames(
                initialdir=self.last_load_dir, parent=self,
                title="Select Tool executables",
                filetypes=(("Tool", "*.exe"), ("All", "*")),):
            fp = sanitize_path(fp)
            self.last_load_dir = dirname(fp)
            self.insert_tool_path(fp)

    def add_tool_cmd(self):
        # ask to name the command
        pass

        # add entry to command_lists_flags as well

    def remove_tool_cmd(self):
        # ask to remove the command
        pass

        # remove entry from command_lists_flags as well

    def change_tool_cmd(self, cmd_name):
        if self._execution_state or cmd_name not in self.command_lists:
            return

        curr_state = self.commands_text.config()['state']
        if curr_state != tk.NORMAL:
            self.commands_text.config(state=tk.NORMAL)

        self.commands_text.insert("1.0", self.command_lists[cmd_name])
        self.commands_text.edit_reset()

        if curr_state != tk.NORMAL:
            self.commands_text.config(state=curr_state)

    def close(self):
        if not self._execution_state:
            pass
        elif not messagebox.askyesnocancel(
                "Not all Tool commands have been started/finished!",
                ("Currently running %s Tool processes with %s waiting to start.\n"
                 "Do you wish to cancel the ones waiting and close this window?") %
                (len(self.processes), self.remaining_commands),
                icon='warning', parent=self):
            return
        tk.Toplevel.destroy(self)
        self._stop_processing = True
