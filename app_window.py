import os
import sys
import threadsafe_tkinter as tk

from os.path import dirname, join, splitext, relpath
from time import time, sleep
from threading import Thread
from tkinter.filedialog import askopenfilenames
from tkinter.font import Font
from tkinter import messagebox
from traceback import format_exc

from supyr_struct.defs.constants import *
from binilla.util import *
from binilla.widgets import BinillaWidget

from hek_pool.constants import *
from hek_pool.help_window import HekPoolHelpWindow


curr_dir = dirname(__file__)


class HekPool(tk.Tk, BinillaWidget):
    config_file = None
    processes = ()

    _execution_state = 0  # 0 == not executing,  1 == executing
    _stop_processing = False
    _execution_thread = None

    fixed_font = None

    help_window = None

    open_log = None
    clear_log = None
    proc_limit = None

    tool_paths = ()
    command_lists = ()

    curr_tool_index = -1
    curr_command_list_name = None

    '''Miscellaneous properties'''
    _initialized = False
    app_name = "Pool"  # the name of the app(used in window title)
    version = '1.0.0'
    log_filename = 'hek_pool.log'

    def __init__(self, *args, **kwargs):
        self.last_load_dir = curr_dir
        self.processes = {}
        self.tool_paths = []
        self.command_lists = {}

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
        self.clear_log = tk.BooleanVar(self)
        self.open_log = tk.BooleanVar(self, 1)
        self.proc_limit = tk.IntVar(self, 5)

        # make the menubar
        self.main_menu = tk.Menu(self)
        self.tools_menu = tk.Menu(self.main_menu, tearoff=0,
                                  postcommand=self.generate_tools_menu)
        self.config(menu=self.main_menu)
        self.main_menu.add_command(label="Tool help",
                                   command=self.show_help)
        self.main_menu.add_command(label="Add Tool",
                                   command=self.tool_path_browse)
        self.main_menu.add_command(label="Remove Tool",
                                   command=self.remove_tool_path)
        self.main_menu.add_cascade(label="Select Tool",
                                   menu=self.tools_menu)

        # make the main controls area
        self.controls_frame = tk.LabelFrame(
            self, text="")

        # make the command text area
        self.commands_frame = tk.LabelFrame(
            self, text="Enter Tool commands to batch process (one per line)")
        self.commands_text = tk.Text(
            self.commands_frame, font=self.fixed_font,
            maxundo=1000, undo=True, wrap=tk.NONE)
        self.vsb = tk.Scrollbar(self.commands_frame, orient='vertical',
                                command=self.commands_text.yview)
        self.hsb = tk.Scrollbar(self.commands_frame, orient='horizontal',
                                command=self.commands_text.xview)
        self.commands_text.config(yscrollcommand=self.vsb.set,
                                  xscrollcommand=self.hsb.set)

        self.commands_text.tag_config("all")
        self.commands_text.tag_config("processing",
                                      background=TEXT_TAGS['processing'][0],
                                      foreground=TEXT_TAGS['processing'][1])
        self.commands_text.tag_config("processed",
                                      background=TEXT_TAGS['processed'][0],
                                      foreground=TEXT_TAGS['processed'][1])
        self.commands_text.tag_config("commented", overstrike=1)
        self.commands_text.tag_config("directive", underline=1)

        self.commands_text.tag_add("all", "1.0", tk.END)
        bindtags = list(self.commands_text.bindtags())
        bindtags[0], bindtags[1] = bindtags[1], bindtags[0]
        self.commands_text.bindtags(bindtags)
        self.commands_text.bind('<Any-KeyPress>',    self.event_in_text)
        self.commands_text.bind('<Button-1>',        self.event_in_text)
        self.commands_text.bind('<ButtonRelease-1>', self.event_in_text)
        self.commands_text.bind('<<Paste>>', self.reset_line_style)

        # make the start buttons
        self.buttons_frame = tk.Frame(self)
        self.process_button = tk.Button(
            self.buttons_frame, text="Process selected",
            command=self.execute_selected_commands)
        self.process_all_button = tk.Button(
            self.buttons_frame, text="Process all",
            command=self.execute_commands)
        self.cancel_button = tk.Button(
            self.buttons_frame, text="Cancel",
            command=self.cancel_unprocessed)

        # pack everything
        for frame in (self.controls_frame, self.buttons_frame,
                      self.commands_frame):
            frame.pack(fill="both", padx=5, pady=5)

        for btn in (self.process_button, self.process_all_button,
                    self.cancel_button):
            btn.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        self.hsb.pack(side="bottom", fill='x', expand=True)
        self.vsb.pack(side="right",  fill='y', expand=True)
        self.commands_text.pack(side='left', fill='both', expand=True)

        self.apply_config()
        self.apply_style()

    def get_text_state(self):
        return self.commands_text.config()['state'][-1]

    def get_command_count(self):
        return int(self.commands_text.index(tk.END).split('.')[0])

    def apply_style(self):
        for w in (self, self.buttons_frame):
            w.config(bg=self.default_bg_color)

        for w in (self.controls_frame, self.commands_frame):
            w.config(fg=self.text_normal_color, bg=self.default_bg_color)

        self.commands_text.config(fg=self.io_fg_color, bg=self.io_bg_color,
                                  insertbackground=self.io_fg_color)

        for w in (self.process_button, self.process_all_button,
                  self.cancel_button):
            w.config(bg=self.button_color, activebackground=self.button_color,
                     fg=self.text_normal_color, bd=self.button_depth,
                     disabledforeground=self.text_disabled_color)

    def apply_config(self):
        config_file = self.config_file
        if not config_file:
            return

        self.tool_paths = [b.path for b in config_file.tool_paths]
        self.command_lists = {}
        for block in config_file.tool_commands:
            self.command_lists[b.name] = b.commands

        self.curr_tool_index = config_file.last_tool_path - 1
        self.select_tool_path(self.curr_tool_index)

    def display_edit_widgets(self, line=None):
        # TODO
        pass

    def _start_process(self, cmd_line, exec_path,
                       exec_args=(), cmd_args=(), **kw):
        if cmd_line is None:
            # if this is a tool command, make sure it's not currently running
            self.processes.setdefault(cmd_line, cmd_line)
            assert self.processes[cmd_line] is cmd_line

        def proc_wrapper(app, line, *args, **kwargs):
            try:
                processes = kwargs.pop("processes", {})
                completed = kwargs.pop("completed", {})
                do_subprocess(*args, **kwargs)
            except Exception:
                print(format_exc())

            if line is None:
                return

            completed[line] = processes.pop(line, None)
            if not app or processes is not app.processes:
                return

            # set the command's text to the 'processed' color
            if app._execution_state:
                app.set_line_style(line, "processed")

        proc_controller = ProcController()
        kw.update(proc_controller=proc_controller)
        new_thread = Thread(
            target=proc_wrapper, daemon=True, kwargs=kw,
            args=(self, cmd_line, exec_path, cmd_args, exec_args))
        if cmd_line is not None:
            self.processes[cmd_line] = dict(
                thread=new_thread, proc_controller=proc_controller,
                exec_path=exec_path, exec_args=exec_args, cmd_args=cmd_args)
        new_thread.start()

    def reset_line_style(self, e=None):
        for line in range(1, self.get_command_count()):
            self.update_line_style("%d.0" % line)

    def update_line_style(self, index):
        pos = index.split('.')
        posy, posx = int(pos[0]), int(pos[1])
        cmd_str = self.commands_text.get(
            '%d.0' % posy, '%d.end' % posy).strip(" ")

        line_color = None
        if not cmd_str:
            pass
        elif cmd_str[0] in COMMENT_START_STRS:
            line_color = "commented"
        elif cmd_str[0] in DIRECTIVE_START_STRS:
            line_color = "directive"

        self.set_line_style(posy, line_color)

    def event_in_text(self, e):
        if self.get_text_state() != tk.NORMAL:
            return

        index = self.commands_text.index(tk.INSERT)
        self.update_line_style(index)
        self.display_edit_widgets(int(index.split('.')[0]))

    def set_line_style(self, line=None, color=None):
        if line is None:
            start, end = "1.0", tk.END
        else:
            start, end = "%d.0" % line, "%d.end" % line

        remove_all = color in ("commented", "directive")

        for color_to_remove in TEXT_TAGS:
            if color is None or remove_all or color_to_remove not in(
                    "commented", "directive"):
                self.commands_text.tag_remove(color_to_remove, start, end)

        if color:
            self.commands_text.tag_add(color, start, end)

    def get_command(self, line):
        cmd_str = self.commands_text.get(
            '%d.0' % line, '%d.end' % line).strip("\n").strip(" ")

        disabled = False
        no_comment_cmd_str = cmd_str
        for c in COMMENT_START_STRS:
            no_comment_cmd_str = no_comment_cmd_str.lstrip(c)

        disabled = len(no_comment_cmd_str) != len(cmd_str)
        cmd_str = no_comment_cmd_str.strip(" ")
        if not cmd_str:
            return "", True

        if ' ' in cmd_str:
            cmd_name, cmd_str = cmd_str.split(' ', 1)
        else:
            cmd_name, cmd_str = cmd_str, ""
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
            else:
                param_str += c

        if param_str:
            if in_str:
                param_str += '"'
            cmd_args.append(param_str)

        disabled |= not cmd_args
        return cmd_args, disabled

    def cancel_unprocessed(self):
        self._stop_processing = True

    def execute_commands(self, start=None, stop=None):
        if not self._execution_thread:
            pass
        elif self._execution_thread.is_alive():
            return
        self._execution_thread = Thread(target=self._execute_commands, daemon=1,
                                        kwargs=dict(start=start, stop=stop))
        self._execution_thread.start()

    def execute_selected_commands(self):
        try:
            start = tuple(self.commands_text.index(tk.SEL_FIRST).split('.'))
            stop  = tuple(self.commands_text.index(tk.SEL_LAST).split('.'))
        except tk.TclError:
            return

        start_y, start_x = int(start[0]), int(start[1])
        stop_y,  stop_x  = int(stop[0]),  int(stop[1])
        if start_x and self.commands_text.get("%s.%s" % start) in ('\n', '\r'):
            start_y += 1
        if stop_x and self.commands_text.get("%s.%s" % stop) in ('\n', '\r'):
            stop_y += 1
        self.execute_commands(start_y, stop_y)

    def get_tool_path(self):
        if self.curr_tool_index not in range(len(self.tool_paths)):
            return ""
        return self.tool_paths[self.curr_tool_index]

    def get_tool_cwd(self):
        if self.curr_tool_index not in range(len(self.tool_paths)):
            return ""
        return dirname(self.tool_paths[self.curr_tool_index])

    def _execute_commands(self, start=None, stop=None):
        tool_path = self.get_tool_path()
        if self._execution_state:
            return
        elif not tool_path:
            print("No Tool selected to process commands")
            return
        self._execution_state = True

        error = None
        log_paths = set()
        open_log, clear_log = self.open_log.get(), self.clear_log.get()
        try:
            self.commands_text.config(state=tk.DISABLED)
            time_start = time()
            if start is None: start = 1
            if stop is None:  stop  = self.get_command_count()

            tool_path = self.get_tool_path()
            cwd = self.get_tool_cwd()
            processes, proc_limit = self.processes, self.proc_limit

            i = start
            last_break, blank_ct, direc_ct = 0, 0, 0
            completed, processes, cmd_args_dict = {}, {}, dict(k=False)
            self.processes = processes
            while i <= stop and not self._stop_processing:
                curr_proc_ct = len(processes)

                if len(completed) + blank_ct + direc_ct + start <= last_break:
                    sleep(0.1)
                    continue
                elif curr_proc_ct >= proc_limit.get():
                    # continually execute processes until the max quota is hit
                    sleep(0.1)
                    continue

                exec_args, disabled = self.get_command(i)
                if not exec_args:
                    # ignore empty lines
                    last_break = i
                    blank_ct += 1
                elif disabled:
                    # ignore commented commands
                    blank_ct += 1
                elif exec_args[0] and exec_args[0][0] in DIRECTIVE_START_STRS:
                    # directive to change some variable
                    direc_ct += 1
                    j = 0
                    if not exec_args[j].lstrip('#').strip(' ').lower():
                        # directive type is separated from # by spaces
                        j += 1

                    typ = None if len(exec_args) == j     else exec_args[j]
                    val = None if len(exec_args) == j + 1 else exec_args[j + 1]

                    if typ is None:
                        # malformed directive
                        i += 1
                        continue

                    typ = typ.lstrip('#').strip(' ').lower()
                    if typ == 'cwd' and val:
                        # if spaces are in the filepath, put them back in.
                        # also, strip parenthese since cmd doesn't know how.
                        cwd = ''.join("%s " % s for s in
                                      exec_args[j + 1:])[:-1].strip('"')
                    elif typ in ('k', 'keep', 'keep_window'):
                        # need to check if we are running with an interactive
                        # console, since if we are we CANNOT keep the process
                        # open since it will hose up the interpreter forever.
                        if not(sys.stdout and os.isatty(sys.stdout.fileno())):
                            cmd_args_dict['k'] = True
                    elif typ in ('c', 'close', 'close_window'):
                        cmd_args_dict['k'] = False

                    self.set_line_style(i, "processed")
                else:
                    # this is a command we can actually execute!

                    print('"%s"' % tool_path,
                          ''.join(" %s" % a for a in exec_args))

                    log_path = join(cwd, 'debug.txt')
                    if log_path not in log_paths:
                        if clear_log:
                            try:
                                with open(log_path, "w") as f:
                                    f.truncate()
                            except Exception:
                                pass
                        log_paths.add(log_path)

                    # start the command
                    cmd_args = (a for a in cmd_args_dict if cmd_args_dict[a])
                    self._start_process(
                        i, tool_path, exec_args, cmd_args, cwd=cwd,
                        completed=completed, processes=processes)

                    # set the command's text to the 'processing' color
                    self.set_line_style(i, "processing")

                i += 1

            if not self._stop_processing:
                while len(processes):
                    # wait until all processes finish
                    sleep(0.1)

            self._stop_processing = False
        except Exception as e:
            error = e

        self._execution_state = False
        print("Finished executing Tool commands. " +
              "Took %s seconds" % (time() - time_start))
        print('-'*79)
        print()
        if open_log:
            for log_path in log_paths:
                try: self._start_process(None, "notepad.exe", (log_path, ))
                except Exception: pass
        self.commands_text.config(state=tk.NORMAL)
        self.reset_line_style()

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
            self.main_menu.entryconfig(4, label="Select Tool")
        else:
            self.select_tool_path(self.curr_tool_index)

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

        self.main_menu.entryconfig(4, label=trimmed_path)

    def tool_path_browse(self):
        for fp in askopenfilenames(
                initialdir=self.last_load_dir, parent=self,
                title="Select Tool executables",
                filetypes=(("Tool", "*.exe"), ("All", "*")),):
            fp = sanitize_path(fp)
            self.last_load_dir = dirname(fp)
            self.insert_tool_path(fp)

    def insert_tool_cmd(self, cmd_type):
        params = TOOL_COMMANDS.get(cmd_type, ())
        cmd_str = ''.join(' %s' % param[1] for param in params)
        self.commands_text.insert(tk.END, cmd_type + cmd_str + '\n')

    def add_tool_cmd_list(self):
        # ask to name the command
        pass

    def remove_tool_cmd_list(self):
        # ask to remove the command
        pass

    def change_tool_cmd_list(self, cmd_name):
        if self._execution_state or cmd_name not in self.command_lists:
            return

        curr_state = self.get_text_state()
        if curr_state != tk.NORMAL:
            self.commands_text.config(state=tk.NORMAL)

        self.commands_text.insert("1.0", self.command_lists[cmd_name])
        self.commands_text.edit_reset()

        if curr_state != tk.NORMAL:
            self.commands_text.config(state=curr_state)

    def show_help(self):
        if self.help_window is None:
            self.help_window = HekPoolHelpWindow(self)
            self.help_window.protocol("WM_DELETE_WINDOW", self.close_help)

    def close_help(self):
        self.help_window.destroy()
        self.help_window = None

    def close(self):
        if not self._execution_state:
            pass
        elif not messagebox.askyesnocancel(
                "Not all commands have been started/finished!",
                "Some Tool processes have not yet been started.\n"
                "Do you wish to cancel the ones still waiting and exit?",
                icon='warning', parent=self):
            return
        tk.Tk.destroy(self)
        self._stop_processing = True
