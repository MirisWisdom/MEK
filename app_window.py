import os
import sys
import threadsafe_tkinter as tk

from os.path import exists, isfile, dirname, join
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
from hek_pool.config_def import config_def, CFG_DIRS


curr_dir = dirname(__file__)
default_config_path = curr_dir + '%shek_pool.cfg' % PATHDIV


class HekPool(tk.Tk):
    processes = ()

    _execution_state = 0  # 0 == not executing,  1 == executing
    _stop_processing = False
    _execution_thread = None

    fixed_font = None

    help_window = None

    open_log = None
    clear_log = None
    proc_limit = None

    last_load_dir = curr_dir
    working_dir = curr_dir
    command_lists_dir = join(curr_dir, "cmd_lists")

    tool_paths = ()
    command_lists = ()

    curr_tool_index = -1
    curr_command_list_name = None
    
    '''Window location and size'''
    app_width = 400
    app_height = 300
    app_offset_x = 0
    app_offset_y = 0

    '''Config properties'''
    # holds all the config settings for this application
    config_def = config_def
    config_file = None
    config_version = 1
    config_path = default_config_path

    '''Miscellaneous properties'''
    app_name = "Pool"  # the name of the app(used in window title)
    version = '1.0.0'
    log_filename = 'hek_pool.log'
    max_undos = 1000

    def __init__(self, *args, **kwargs):
        for i in range(20):
            print("DONT FORGET TO FIX THE HIDDEN TITLE INDENT BUG")


        for s in ('working_dir', 'config_version',
                  'app_width', 'app_height', 'app_offset_x', 'app_offset_y'):
            if s in kwargs:
                object.__setattr__(self, s, kwargs.pop(s))

        tk.Tk.__init__(self, *args, **kwargs)

        # make the tkinter variables
        self.clear_log = tk.BooleanVar(self)
        self.open_log  = tk.BooleanVar(self, 1)
        self.proc_limit = tk.IntVar(self, 1)

        self.processes = {}
        self.command_lists = {}

        if type(self).fixed_font is None:
            type(self).fixed_font = Font(family="Terminal", size=10)

        self.title('%s v%s' % (self.app_name, self.version))
        self.minsize(width=400, height=300)

        # make the menubar
        self.main_menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.main_menu, tearoff=0)
        self.tools_menu = tk.Menu(self.main_menu, tearoff=0,
                                  postcommand=self.generate_tools_menu)
        self.config(menu=self.main_menu)
        self.main_menu.add_cascade(label="File", menu=self.file_menu)
        self.main_menu.add_command(label="Help", command=self.show_help)
        self.main_menu.add_cascade(label="Select Tool", menu=self.tools_menu)

        self.file_menu.add_command(label="Add Tool filepath",
                                   command=self.tool_path_browse)
        self.file_menu.add_command(label="Remove Tool filepath",
                                   command=self.remove_tool_path)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Edit style in notepad",
                                   command=self.edit_style_in_notepad)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.close)


        if self.config_file is not None:
            pass
        elif isfile(self.config_path):
            # load the config file
            try:
                self.load_config()
            except Exception:
                print(format_exc())
                self.make_config()
        else:
            # make a config file
            self.make_config()

        if not exists(self.working_dir):
            try:
                dirs = self.config_file.data.directory_paths
                dirs.working_dir.path = dirs.last_load_dir.path =\
                                        self.working_dir = curr_dir
            except Exception:
                print(format_exc())
            
        try:
            self.load_style()
        except Exception:
            print(format_exc())

        self.app_name = kwargs.pop('app_name', self.app_name)
        self.app_name = str(kwargs.pop('version', self.app_name))

        self.protocol("WM_DELETE_WINDOW", self.close)

        # make the main controls area
        self.controls_frame = tk.Frame(self)

        # make the command text area
        self.commands_frame = tk.LabelFrame(
            self, text="Enter directives and Tool commands to process (one per line)")
        self.commands_frame_inner = tk.Frame(self.commands_frame)
        self.commands_text = tk.Text(
            self.commands_frame_inner, font=self.fixed_font,
            maxundo=self.max_undos, undo=True, wrap=tk.NONE)
        self.vsb = tk.Scrollbar(self.commands_frame_inner, orient='vertical',
                                command=self.commands_text.yview)
        self.hsb = tk.Scrollbar(self.commands_frame, orient='horizontal',
                                command=self.commands_text.xview)
        self.commands_text.config(yscrollcommand=self.vsb.set,
                                  xscrollcommand=self.hsb.set)

        self.commands_text.tag_add("all", "1.0", tk.END)
        bindtags = list(self.commands_text.bindtags())
        bindtags[0], bindtags[1] = bindtags[1], bindtags[0]
        self.commands_text.bindtags(bindtags)
        self.commands_text.bind('<Any-KeyPress>',    self.event_in_text)
        self.commands_text.bind('<Button-1>',        self.event_in_text)
        self.commands_text.bind('<ButtonRelease-1>', self.event_in_text)
        self.commands_text.bind('<<Paste>>', self.reset_line_style)
        self.commands_text.bind('<Control-z>', self.reset_line_style)
        self.commands_text.bind('<Control-y>', self.reset_line_style)

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
        for frame in (self.controls_frame, self.buttons_frame):
            frame.pack(fill="both", padx=5, pady=5)

        self.vsb.pack(side="right",  fill='y')
        self.hsb.pack(side="bottom", fill='x')
        self.commands_text.pack(side="right", fill="both", expand=True)

        self.commands_frame.pack(side="bottom", fill="both",
                                 padx=5, pady=5, expand=True)
        self.commands_frame_inner.pack(fill="both", expand=True)

        for btn in (self.process_button, self.process_all_button,
                    self.cancel_button):
            btn.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        self.apply_style()
        self.apply_config()
        self.load_cmd_lists()

    def get_text_state(self):
        return self.commands_text.config()['state'][-1]

    def get_command_count(self):
        return int(self.commands_text.index(tk.END).split('.')[0])

    def apply_style(self):
        color = text_tags_colors['default']
        self.commands_text.config(fg=color['fg'], bg=color['bg'],
                                  insertbackground=color['fg'],
                                  selectbackground=color['bg_highlight'])

        self.commands_text.tag_config("all")
        self.commands_text.tag_config(
            "processing",
            background=text_tags_colors['processing']['bg'],
            foreground=text_tags_colors['processing']['fg'])
        self.commands_text.tag_config(
            "processed",
            background=text_tags_colors['processed']['bg'],
            foreground=text_tags_colors['processed']['fg'])
        self.commands_text.tag_config(
            "commented",
            #background=text_tags_colors['commented']['bg'],
            foreground=text_tags_colors['commented']['fg'])
        self.commands_text.tag_config(
            "directive",
            #background=text_tags_colors['directive']['bg'],
            foreground=text_tags_colors['directive']['fg'])

    def edit_style_in_notepad(self):
        Thread(target=self._edit_style_in_notepad, daemon=True).start()

    def _edit_style_in_notepad(self):
        style_path = join(self.working_dir, STYLE_CFG_NAME)
        if not isfile(style_path):
            return

        try:
            proc_controller = ProcController()
            self._start_process(None, "notepad.exe", (style_path, ),
                                proc_controller=proc_controller)

            while proc_controller.returncode is None:
                sleep(0.1)
            self.load_style()
            self.apply_style()
        except Exception:
            print(format_exc())

    def save_current_command_list(self, filename=None):
        with open(join(self.command_lists_dir, filename), 'w') as f:
            f.write(self.commands_text.get('1.0', tk.END))

    def apply_config(self):
        if not self.config_file:
            return

        config_data = self.config_file.data
        header = config_data.header
        app_window = config_data.app_window
        dir_paths = config_data.directory_paths

        __osa__ = object.__setattr__
        __tsa__ = type.__setattr__
        for s in app_window.NAME_MAP.keys():
            try: __osa__(self, s, app_window[s])
            except IndexError: pass

        for s in ('max_undos', ):
            try: __osa__(self, s, header[s])
            except IndexError: pass

        for s in CFG_DIRS[:len(dir_paths)]:
            try: __osa__(self, s, dir_paths[s].path)
            except IndexError: pass

        self.tool_paths = [b.path for b in config_data.tool_paths]
        self.curr_tool_index = header.last_tool_index - 1
        self.select_tool_path(self.curr_tool_index)

        self.proc_limit.set(max(header.proc_limit, 1))
        self.open_log.set(header.flags.open_log)
        self.clear_log.set(header.flags.clear_log)

        self.geometry("%sx%s+%s+%s" %
                      (self.app_width,    self.app_height,
                       self.app_offset_x, self.app_offset_y))
        self.update()

    def update_config(self, config_file=None):
        if config_file is None:
            config_file = self.config_file
        config_data = config_file.data

        header = config_data.header
        dir_paths = config_data.directory_paths
        app_window = config_data.app_window

        header.version = self.config_version
        __oga__ = object.__getattribute__

        self.app_width = self.winfo_width()
        self.app_height = self.winfo_height()
        self.app_offset_x = self.winfo_x()
        self.app_offset_y = self.winfo_y()

        header.last_tool_index = max(self.curr_tool_index + 1, 0)
        header.proc_limit = max(self.proc_limit.get(), 1)
        header.flags.open_log = self.open_log.get()
        header.flags.clear_log = self.clear_log.get()

        for s in app_window.NAME_MAP.keys():
            try: app_window[s] = __oga__(self, s)
            except IndexError: pass

        # make sure there are enough tagsdir entries in the directory_paths
        if len(CFG_DIRS) > len(dir_paths):
            dir_paths.extend(len(CFG_DIRS) - len(dir_paths))

        for s in ('max_undos', ):
            try: header[s] = __oga__(self, s)
            except IndexError: pass

        for s in CFG_DIRS:
            try: dir_paths[s].path = __oga__(self, s)
            except IndexError: pass

        del config_data.tool_paths[:]
        for path in self.tool_paths:
            config_data.tool_paths.append()
            config_data.tool_paths[-1].path = path

    def load_config(self, filepath=None):
        if filepath is None:
            filepath = self.config_path
        assert exists(filepath)

        # load the config file
        self.config_file = self.config_def.build(filepath=filepath)
        if self.config_file.data.header.version != self.config_version:
            raise ValueError(
                "Config version is not what this application is expecting.")

        self.apply_config()

    def load_style(self):
        try:
            with open(join(self.working_dir, STYLE_CFG_NAME), 'r') as f:
                data = f.read().replace('\n\n', '\n').strip('\n').\
                       replace('\n', ',\n').replace('{,', '{').\
                       replace('{', 'dict(').replace('}', ')')
                new_style = eval("dict(%s)" % data)
            malformed = False
        except Exception:
            malformed = True
            new_style = None

        malformed |= not isinstance(new_style, dict)
        if not malformed:
            for k in text_tags_colors:
                if k not in new_style: continue

                malformed |= not(isinstance(new_style[k], dict))
                if malformed: break
                colors = text_tags_colors[k]
                new_colors = new_style[k]

                for c in colors:
                    if c not in new_colors: continue

                    malformed |= not(isinstance(new_colors[c], str))
                    if malformed: break
                    new_color = new_colors[c].lower()
                    malformed |= (len(new_color) != 6 and
                                  set(new_color).issubset("0123456789abcdef"))

                    if not malformed:
                        new_colors[c] = '#' + new_colors[c] 

        if malformed:
            print("Could not load %s as it is malformed." % STYLE_CFG_NAME)
        else:
            text_tags_colors.update(new_style)

    def make_config(self, filepath=None):
        if filepath is None:
            filepath = self.config_path

        # create the config file from scratch
        self.config_file = self.config_def.build()
        self.config_file.filepath = filepath

        data = self.config_file.data
        data.directory_paths.extend(len(data.directory_paths.NAME_MAP))
        self.update_config()

    def save_config(self):
        self.config_file.serialize(temp=0, backup=0, calc_pointers=0)

    def save_style(self):
        with open(join(self.working_dir, STYLE_CFG_NAME), 'w') as f:
            for name in sorted(text_tags_colors):
                f.write("\n%s = {\n" % name)
                colors = text_tags_colors[name]
                for color_name in sorted(colors):
                    f.write('    %s = "%s"\n' %
                            (color_name, colors[color_name][1:]))
                f.write("    }\n")

    def load_cmd_lists(self):
        if (not exists(self.command_lists_dir) or
                isfile(self.command_lists_dir)):
            return

        cmd_lists = self.command_lists
        for root, dirs, files in os.walk(self.command_lists_dir):
            for filename in files:
                with open(join(root, filename), 'r') as f:
                    data = f.read()

                if filename == LAST_CMD_LIST_NAME:
                    self.commands_text.delete('1.0', tk.END)
                    self.commands_text.insert('1.0', data)
                    self.reset_line_style()
                else:
                    cmd_lists[filename] = data

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

        if "proc_controller" not in kw:
            kw.update(proc_controller=ProcController())

        new_thread = Thread(
            target=proc_wrapper, daemon=True, kwargs=kw,
            args=(self, cmd_line, exec_path, cmd_args, exec_args))
        if cmd_line is not None:
            self.processes[cmd_line] = dict(
                thread=new_thread, exec_path=exec_path,
                exec_args=exec_args, cmd_args=cmd_args, **kw)
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

        for color_to_remove in text_tags_colors:
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

    def get_can_execute_command(self, cmd_args):
        # TODO
        return True

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
        log_paths, loc_vars = set(), dict()
        open_log, clear_log = self.open_log.get(), self.clear_log.get()
        try:
            self.commands_text.config(state=tk.DISABLED)
            time_start = time()
            if start is None: start = 1
            if stop is None:  stop  = self.get_command_count()

            tool_path = self.get_tool_path()
            cwd = self.get_tool_cwd()
            processes, proc_limit = self.processes, self.proc_limit

            i, curr_max_proc_ct = start, 0
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
                elif curr_max_proc_ct and curr_proc_ct == curr_max_proc_ct:
                    # same number of processes as last checked. don't
                    # need to check self.get_can_execute_command again
                    continue
                elif not self.get_can_execute_command(exec_args):
                    curr_max_proc_ct = curr_proc_ct
                    continue
                elif exec_args[0] and exec_args[0][0] in DIRECTIVE_START_STRS:
                    # directive to change some variable
                    direc_ct += 1
                    j = 0
                    if not exec_args[j].lstrip('#').strip(' ').lower():
                        # directive type is separated from # by spaces
                        j += 1

                    typ  = None if len(exec_args) == j else exec_args[j]
                    vals = () if len(exec_args) == j + 1 else exec_args[j + 1:]

                    if typ is None:
                        # malformed directive
                        i += 1
                        continue

                    if loc_vars:
                        new_vals = []
                        for v in vals:
                            for var, repl in loc_vars.items():
                                v = v.replace("<%s>" % var, repl.strip('"'))
                            new_vals.append(v)
                        vals = new_vals

                    typ = typ.lstrip('#').strip(' ').lower()
                    if typ == 'cwd' and vals:
                        # if spaces are in the filepath, put them back in.
                        # also, strip parenthese since cmd doesn't know how.
                        cwd = ''.join("%s " % s for s in vals)[:-1].strip('"')
                    elif typ in ('k'):
                        # need to check if we are running with an interactive
                        # console, since if we are we CANNOT keep the process
                        # open since it will hose up the interpreter forever.
                        if not(sys.stdout and os.isatty(sys.stdout.fileno())):
                            cmd_args_dict['k'] = True
                    elif typ in ('c'):
                        cmd_args_dict['k'] = False
                    elif typ == "set" and len(vals) >= 2:
                        loc_vars[vals[0]] = vals[1]
                    elif typ == "del" and vals:
                        loc_vars.pop(vals[0], None)

                    self.set_line_style(i, "processed")
                else:
                    # this is a command we can actually execute!
                    curr_max_proc_ct = 0

                    log_path = join(cwd, 'debug.txt')
                    if log_path not in log_paths:
                        if clear_log:
                            try:
                                with open(log_path, "w") as f:
                                    f.truncate()
                            except Exception:
                                pass
                        log_paths.add(log_path)

                    if loc_vars:
                        new_exec_args = []
                        for a in exec_args:
                            for var, repl in loc_vars.items():
                                a = a.replace("<%s>" % var, repl.strip('"'))
                            new_exec_args.append(a)
                        exec_args = new_exec_args

                    print('\n\n"%s"' % tool_path,
                          ''.join(" %s" % a for a in exec_args))

                    # start the command
                    cmd_args = (a for a in cmd_args_dict if cmd_args_dict[a])
                    self._start_process(
                        i, tool_path, exec_args, cmd_args, cwd=cwd,
                        completed=completed, processes=processes)

                    # set the command's text to the 'processing' color
                    self.set_line_style(i, "processing")
                    self.commands_text.see("%s.0" % i)

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
                if not isfile(log_path): continue
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
            self.main_menu.entryconfig(3, label="Select Tool")
        else:
            self.select_tool_path(self.curr_tool_index)

    def select_tool_path(self, index):
        assert isinstance(index, int)
        if index < 0:
            if hasattr(self, "main_menu"):
                self.main_menu.entryconfig(3, label="Select Tool")
            self.curr_tool_index = -1
            return

        assert index in range(len(self.tool_paths))
        if self._execution_state or not len(self.tool_paths):
            return

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

    def insert_directive(self, dir_type):
        params = DIRECTIVES.get(dir_type, ())
        dir_type = "# %s" % dir_type
        dir_str = ''.join(' %s' % param[1] for param in params)
        index = self.commands_text.index(tk.INSERT).split('.')[0] + '.0'
        self.commands_text.insert(index, dir_type + dir_str + '\n')

    def insert_tool_cmd(self, cmd_type):
        params = TOOL_COMMANDS.get(cmd_type, ())
        cmd_str = ''.join(' %s' % param[1] for param in params)
        index = self.commands_text.index(tk.INSERT).split('.')[0] + '.end'
        self.commands_text.insert(index, cmd_type + cmd_str + '\n')

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
        elif not messagebox.askyesno(
                "Not all commands have been started/finished!",
                "Some Tool processes have not yet been started.\n"
                "Do you wish to cancel the ones still waiting and exit?",
                icon='warning', parent=self):
            return

        try:
            self.save_current_command_list(LAST_CMD_LIST_NAME)
        except Exception:
            print(format_exc())

        try:
            self.save_style()
        except Exception:
            print(format_exc())

        try:
            # need to save before destroying the
            # windows or bindings wont be saved
            self.update_config()
            self.save_config()
        except Exception:
            print(format_exc())

        tk.Tk.destroy(self)
        self._stop_processing = True
