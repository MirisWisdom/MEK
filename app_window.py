import io
import os
import sys
import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from os.path import basename, exists, isfile, dirname, join, relpath, splitext
from time import time, sleep
from threading import Thread
from tkinter.filedialog import askopenfilenames, askopenfilename,\
     asksaveasfilename, askdirectory
from tkinter.font import Font
from tkinter import messagebox
from traceback import format_exc

from supyr_struct.defs.constants import *
from binilla.util import *
from binilla.widgets import BinillaWidget

from hek_pool.constants import *
from hek_pool.help_window import HekPoolHelpWindow
from hek_pool.config_def import config_def, CFG_DIRS


platform = sys.platform.lower()
if "linux" in platform:
    platform = "linux"


if platform == "win32":
    TEXT_EDITOR_NAME = "notepad"
elif platform == "darwin":
    # I don't actually think this will work since mac seems to require
    # the "open" argument and the -a argument before the application name.
    # leaving this here just in case it somehow works though.
    TEXT_EDITOR_NAME = "TextEdit"
elif platform == "linux":
    TEXT_EDITOR_NAME = "nano"
else:
    # idfk
    TEXT_EDITOR_NAME = "vim"


curr_dir = dirname(__file__)
default_config_path = curr_dir + '%shek_pool.cfg' % PATHDIV
using_console = bool(sys.stdout)
if using_console:
    try:
        using_console |= os.isatty(sys.stdout.fileno())
    except io.UnsupportedOperation:
        using_console = True
    except Exception:
        using_console = False


class HekPool(tk.Tk):
    processes = ()

    _execution_state = 0  # 0 == not executing,  1 == executing
    _stop_processing = False
    _execution_thread = None
    _reset_style_on_click = False

    fixed_font = None

    help_window = None

    open_log = None
    clear_log = None
    proc_limit = None

    last_load_dir = curr_dir
    working_dir = curr_dir
    command_lists_dir = join(curr_dir, "cmd_lists")

    tool_paths = ()

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

        self.app_name = str(kwargs.pop('app_name', self.app_name))
        self.version  = str(kwargs.pop('version', self.version))

        tk.Tk.__init__(self, *args, **kwargs)

        # make the tkinter variables
        self.clear_log = tk.BooleanVar(self)
        self.open_log  = tk.BooleanVar(self, 1)
        self.proc_limit = tk.StringVar(self, 1)

        self.processes = {}

        if type(self).fixed_font is None:
            type(self).fixed_font = Font(family="Terminal", size=10)

        self.title('%s v%s' % (self.app_name, self.version))
        self.minsize(width=400, height=300)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.bind('<Control-s>', lambda e=None: self.save_command_list())
        self.bind('<Control-S>', lambda e=None: self.save_command_list_as())
        self.bind('<Control-Alt-s>', lambda e=None: self.save_command_list_as())
        self.bind('<Control-o>', lambda e=None: self.load_commands_list())

        # make the menubar
        self.main_menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.main_menu, tearoff=0)
        self.settings_menu = tk.Menu(self.main_menu, tearoff=0)
        self.tools_menu = tk.Menu(self.main_menu, tearoff=0,
                                  postcommand=self.generate_tools_menu)
        self.config(menu=self.main_menu)
        self.main_menu.add_cascade(label="File", menu=self.file_menu)
        self.main_menu.add_cascade(label="Settings", menu=self.settings_menu)
        self.main_menu.add_cascade(label="Select Tool", menu=self.tools_menu)
        self.main_menu.add_command(label="Help", command=self.show_help)

        self.file_menu.add_command(label="Add Tool",
                                   command=self.tool_path_browse)
        self.file_menu.add_command(label="Remove Tool",
                                   command=self.remove_tool_path)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Open...",
                                   command=self.load_commands_list)
        self.file_menu.add_command(label="Select command list folder",
                                   command=self.set_command_list_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save",
                                   command=self.save_command_list)
        self.file_menu.add_command(label="Save As...",
                                   command=self.save_command_list_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Edit style",
                                   command=self.edit_style_in_text_editor)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.close)

        self.settings_menu.add("checkbutton", variable=self.clear_log,
                               label="Clear debug.txt's before processing")
        self.settings_menu.add("checkbutton", variable=self.open_log,
                               label="Open debug.txt's after processing")

        ''' LOAD THE CONFIG '''
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

        # make the command text area
        self.commands_frame = tk.LabelFrame(self, text=(
            "Enter directives and Tool commands to process (one per line)\n"
            '    Empty lines mean "Finish everything above before proceeding"'))
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
        self.commands_text.bind('<Control-o>',       self.ignore_keypress)
        self.commands_text.bind('<Any-KeyPress>',    self.event_in_text)
        self.commands_text.bind('<Button-1>',        self.event_in_text)
        self.commands_text.bind('<ButtonRelease-1>', self.event_in_text)
        self.commands_text.bind('<<Paste>>', self.reset_line_style)
        self.commands_text.bind('<Control-z>', self.reset_line_style)
        self.commands_text.bind('<Control-y>', self.reset_line_style)
        self.commands_text.bind('<Button-3>', self.right_click_cmd_text)

        # make the start buttons
        self.buttons_frame = tk.Frame(self.commands_frame)
        self.process_button = tk.Button(
            self.buttons_frame, text="Process selected",
            command=self.execute_selected_commands)
        self.process_all_button = tk.Button(
            self.buttons_frame, text="Process all",
            command=self.execute_commands)
        self.cancel_button = tk.Button(
            self.buttons_frame, text="Cancel",
            command=self.cancel_unprocessed)
        self.proc_limit_frame = tk.LabelFrame(self.buttons_frame,
                                              text="Max parallel processes")
        self.proc_limit_spinbox = tk.Spinbox(
            self.proc_limit_frame, values=tuple(range(1, 65)),
            textvariable=self.proc_limit, state="readonly")

        # pack everything
        self.buttons_frame.pack(fill="both")
        self.commands_frame.pack(fill="both", padx=5, pady=(0, 5), expand=1)

        self.vsb.pack(side="right",  fill='y')
        self.commands_text.pack(side="right", fill="both", expand=True)

        self.hsb.pack(side="bottom", fill='x')
        self.commands_frame_inner.pack(side="bottom", fill="both", expand=True)

        self.proc_limit_frame.pack(side="left", fill="x", padx=5, pady=(0, 9))
        self.proc_limit_spinbox.pack(fill="x")
        for btn in (self.process_button, self.process_all_button,
                    self.cancel_button):
            btn.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        self.apply_style()
        self.apply_config()
        self.load_commands_list(LAST_CMD_LIST_NAME)

    def right_click_cmd_text(self, e):
        cmd_text = self.commands_text
        index = cmd_text.index("@%d,%d" % (e.x, e.y))
        posy, posx = (int(p) for p in index.split('.'))

        raw_cmd_str = self.commands_text.get(
            '%d.0' % posy, '%d.end' % posy).replace('\t', ' ')
        if len(raw_cmd_str.strip(' ').strip('\t')) == 0:
            # empty line. post the menu to select a command
            self.post_templates_menu(e)
            return

        cmd_args, disabled = self.get_command(posy)

        # selecting a command. find out what part of the command
        i, cmd_infos, find_dir = 0, TOOL_COMMANDS, False
        if cmd_args[0] == '#':
            i, cmd_infos, find_dir = 1, DIRECTIVES, True

        is_directive = find_dir

        cmd_type, cmd_args = cmd_args[i], cmd_args[i + 1:]
        cmd_info = cmd_infos.get(cmd_type)
        if not cmd_info:
            return

        arg_index, i, in_str, param_str = -1, 0, False, ""
        for c in raw_cmd_str:
            if i > posx:
                break
            elif find_dir:
                if c == '#' and find_dir == 1:
                    find_dir = 2
                elif c != ' ' and find_dir == 2:
                    find_dir = False
            elif c == ' ' and not in_str:
                if param_str:
                    arg_index += 1
                param_str = ""
            elif c == '"':
                in_str = not in_str
                param_str += c
            else:
                param_str += c
            i += 1

        if arg_index not in range(len(cmd_info)):
            return

        arg_info = cmd_info[arg_index]
        cur_val  = cmd_args[arg_index]
        new_val = None
        name, typ, default = arg_info[:3]
        options = () if len(arg_info) < 4 else arg_info[3]
        if isinstance(typ, (tuple, list)):
            typ, typ_info = typ[0], typ[1:]
        else:
            typ_info = ()

        if typ in ("dir", "file", "file-no-ext"):
            cwd = dirname(self.get_tool_path())
            if not cwd:
                cwd = self.working_dir

            if len(arg_info) >= 4:
                cwd = join(cwd, arg_info[4])

            abs_path = join(cwd, cur_val)
            if not exists(abs_path):
                abs_path = cwd

            if typ == "dir":
                new_val = join(askdirectory(
                    initialdir=cwd, parent=self,
                    title="Select the %s for %s" % (name, cmd_type)), '')
            elif typ in ("file", "file-no-ext"):
                new_val = askopenfilename(
                    initialdir=cwd, parent=self,
                    filetypes=tuple(typ_info) + (("All", "*"), ),
                    title="Select the %s for %s" % (name, cmd_type))
                if typ == "file-no-ext":
                    new_val = splitext(new_val)[0]

                if new_val:
                    new_val = relpath(new_val, cwd)

            if new_val:
                new_val = '"%s"' % new_val.replace('/', '\\')
            else:
                new_val = None

        if new_val is not None:
            cmd_args[arg_index] = new_val
            cmd_args.insert(0, cmd_type)
            if is_directive:
                cmd_args.insert(0, "#")

            new_arg_string = ''.join('%s ' % a for a in cmd_args)[:-1]
            if disabled:
                new_arg_string = ';' + new_arg_string

            self.commands_text.delete('%d.0' % posy, '%d.end' % posy)
            self.commands_text.insert('%d.0' % posy, new_arg_string)
            self.set_line_style(posy, self.get_line_style(posy))

    def post_templates_menu(self, e=None):
        pass

    def ignore_keypress(self, e=None):
        self.commands_text.delete(tk.INSERT)

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

    def edit_style_in_text_editor(self):
        Thread(target=self._edit_style_in_text_editor, daemon=True).start()

    def _edit_style_in_text_editor(self):
        style_path = join(self.working_dir, STYLE_CFG_NAME)
        if not isfile(style_path):
            self.save_style()
            if not isfile(style_path):
                return

        try:
            proc_controller = ProcController()
            self._start_process(None, TEXT_EDITOR_NAME, (style_path, ),
                                proc_controller=proc_controller)

            while proc_controller.returncode is None:
                sleep(0.1)
            self.load_style()
            self.apply_style()
        except Exception:
            print(format_exc())

    def set_command_list_folder(self):
        folder = askdirectory(
            initialdir=self.command_lists_dir, parent=self,
            title="Select the command lists directory")

        if folder:
            self.command_lists_dir = folder

    def get_command_list_names(self):
        if exists(join(self.command_lists_dir, '')):
            return

        list_names = []
        for root, dirs, files in os.walk(self.command_lists_dir):
            for filename in sorted(files):
                list_names.append(relpath(join(root), self.command_lists_dir))

        return list_names

    def load_commands_list(self, list_name=None):
        if self._execution_state:
            return

        if list_name is None:
            filepath = askopenfilename(
                initialdir=self.command_lists_dir, parent=self,
                title="Select a command list to load",
                filetypes=(("Text file", "*.txt"), ("All", "*")),)
        else:
            if not exists(join(self.command_lists_dir, '')):
                return
            filepath = join(self.command_lists_dir, "%s.txt" % list_name)

        if not filepath:
            return

        with open(filepath, 'r') as f:
            data = f.read()

        cmd_list_name = splitext(basename(filepath))[0]
        if cmd_list_name != LAST_CMD_LIST_NAME:
            self.curr_command_list_name = cmd_list_name

        self.commands_text.delete('1.0', tk.END)
        self.commands_text.insert('1.0', data)
        self.commands_text.edit_reset()
        self.reset_line_style()

    def save_command_list_as(self):
        fp = asksaveasfilename(
            initialdir=self.command_lists_dir, parent=self,
            title="Save the command list to where",
            filetypes=(("Text file", "*.txt"), ("All", "*")),)

        if fp:
            path, ext = splitext(sanitize_path(fp))
            if not ext: ext = ".txt"
            self.save_command_list(path + ext)

    def save_command_list(self, filepath=None, directory=None, filename=None):
        if filepath:
            directory = dirname(filepath)
        else:
            if filename is None:
                if self.curr_command_list_name is None:
                    return self.save_command_list_as()

                filename = self.curr_command_list_name
            if directory is None:
                directory = self.command_lists_dir

            filepath = join(directory, filename + '.txt')

        if directory and not exists(directory):
            os.makedirs(directory)

        with open(filepath, 'w') as f:
            data = self.commands_text.get('1.0', tk.END)
            if data[-1] in '\n\r':
                # always seems to be an extra new line. remove that.
                data = data[:-1]
            f.write(data)

        self.curr_command_list_name = splitext(basename(filepath))[0]

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

        self.proc_limit.set(str(max(header.proc_limit, 1)))
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

        header.parse(attr_index='date_modified')
        header.last_tool_index = max(self.curr_tool_index + 1, 0)
        header.proc_limit = max(int(self.proc_limit.get()), 1)
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
                data = ''
                for line in f:
                    if not line.startswith('#'):
                        data += line
                data = data.replace('\n\n', '\n').strip('\n').\
                       replace('\n', ',\n').replace('{,', '{').\
                       replace('{', 'dict(').replace('}', ')')
                new_style = eval("dict(%s)" % data.lower())
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

                for c in set(tuple(colors) + tuple(new_colors)):
                    if c not in new_colors: continue

                    malformed |= not(isinstance(new_colors[c], str))
                    if malformed: break
                    new_color = new_colors[c].lower()
                    malformed |= (len(new_color) != 6 and
                                  set(new_color).issubset("0123456789abcdef"))

                    if not malformed:
                        new_colors[c] = '#' + new_color

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
            f.write(
                """
# These sets of hex values determine the letter(fg) and background(bg) colors
# for the specified type of text. For example, lines being processed use the
# "processed" colors, while commented lines use the "commented" colors.
""")
            for name in sorted(text_tags_colors):
                f.write("\n%s = {\n" % name)
                colors = text_tags_colors[name]
                for color_name in sorted(colors):
                    f.write('    %s = "%s"\n' %
                            (color_name, colors[color_name][1:]))
                f.write("    }\n")

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
        if not using_console:
            kw["stdout"] = kw["stderr"] = kw["stdin"] = None

        new_thread = Thread(
            target=proc_wrapper, daemon=True, kwargs=kw,
            args=(self, cmd_line, exec_path, cmd_args, exec_args))
        if cmd_line is not None:
            self.processes[cmd_line] = dict(
                thread=new_thread, exec_path=exec_path,
                exec_args=exec_args, cmd_args=cmd_args, **kw)
        new_thread.start()

    def reset_line_style(self, e=None):
        for color_to_remove in text_tags_colors:
            self.commands_text.tag_remove(color_to_remove, "1.0", tk.END)
    
        for line in range(1, self.get_command_count()):
            style = self.get_line_style(line)
            if style is None:
                continue
            self.commands_text.tag_add(style, '%d.0' % line, '%d.end' % line)

    def get_line_style(self, line):
        cmd_str, disabled = self.get_command(line)

        style = None
        if not cmd_str:
            pass
        elif disabled:
            style = "commented"
        elif cmd_str[0] in DIRECTIVE_START_STRS:
            style = "directive"

        return style

    def event_in_text(self, e):
        if self._reset_style_on_click:
            self._reset_style_on_click = False
            self.reset_line_style()

        if self.get_text_state() != tk.NORMAL:
            return

        line = int(self.commands_text.index(tk.INSERT).split('.')[0])
        self.set_line_style(line, self.get_line_style(line))
        self.display_edit_widgets(line)

    def set_line_style(self, line=None, style=None):
        if line is None:
            start, end = "1.0", tk.END
        else:
            start, end = "%d.0" % line, "%d.end" % line

        for style_to_remove in text_tags_colors:
            self.commands_text.tag_remove(style_to_remove, start, end)

        if style:
            self.commands_text.tag_add(style, start, end)

    def get_command(self, line):
        cmd_str = self.commands_text.get(
            '%d.0' % line, '%d.end' % line).strip("\n").\
            replace("\t", " ").strip(" ")

        disabled = False
        no_comment_cmd_str = cmd_str
        for c in COMMENT_START_STRS:
            no_comment_cmd_str = no_comment_cmd_str.lstrip(c)

        disabled = len(no_comment_cmd_str) != len(cmd_str)
        cmd_str = no_comment_cmd_str.replace("\t", " ").strip(" ")
        if not cmd_str:
            return "", True

        if ' ' in cmd_str:
            cmd_name, cmd_str = cmd_str.split(' ', 1)
        else:
            cmd_name, cmd_str = cmd_str, ""

        if cmd_name.startswith('#'):
            cmd_name = cmd_name.lstrip('#').strip(" ")
            if cmd_name:
                # directive type is not separated from # by spaces
                cmd_str = "%s %s" % (cmd_name, cmd_str)
            cmd_name = '#'

        cmd_args = [cmd_name]

        in_str, param_str = False, ""
        for c in cmd_str:
            if c == ' ' and not in_str:
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
            self.reset_line_style()
            self.commands_text.config(state=tk.DISABLED)
            time_start = time()
            if start is None: start = 1
            if stop is None:  stop  = self.get_command_count()

            tool_path = self.get_tool_path()
            cwd = dirname(tool_path)
            processes, proc_limit = self.processes, self.proc_limit

            i, curr_max_proc_ct = start, 0
            last_break, blank_ct, direc_ct = 0, 0, 0
            completed, processes, cmd_args_dict = {}, {}, dict(k=False)
            self.processes = processes
            while i <= stop and not self._stop_processing:
                curr_proc_ct = len(processes)

                # FIX THIS!
                #     currently allowing breaking blank line protocol

                print(len(completed), blank_ct, direc_ct, start, last_break)
                if len(completed) + blank_ct + direc_ct + start <= last_break:
                    sleep(0.1)
                    continue
                elif curr_proc_ct >= int(proc_limit.get()):
                    # continually execute processes until the max quota is hit
                    sleep(0.1)
                    continue

                loc_vars["cwd"] = cwd

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
                elif exec_args[0] in DIRECTIVE_START_STRS:
                    # directive to change some variable
                    direc_ct += 1

                    typ  = None if len(exec_args) == 1 else exec_args[1]
                    vals = () if len(exec_args) == 2 else exec_args[2:]
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
                    elif typ == 'k':
                        # need to check if we are running with an interactive
                        # console, since if we are we CANNOT keep the process
                        # open since it will hose up the interpreter forever.
                        if not using_console:
                            cmd_args_dict['k'] = True
                    elif typ == 'c':
                        cmd_args_dict['k'] = False
                    elif typ == "set" and len(vals) >= 2:
                        loc_vars[vals[0]] = vals[1]
                    elif typ == "del" and vals:
                        loc_vars.pop(vals[0], None)
                    elif typ == "run" and vals:
                        exec_name = vals.pop(0).strip('"')
                        self._start_process(
                            i, join(cwd, exec_name), vals, cwd=cwd,
                            completed=completed, processes=processes)

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
        self._reset_style_on_click = True
        self.commands_text.config(state=tk.NORMAL)

        if open_log:
            Thread(target=self.open_logs, daemon=1, args=(log_paths, )).start()

        if error: raise error

    def open_logs(self, log_paths):
        while len(self.processes):
            # wait until all processes finish
            sleep(0.1)

        for log_path in log_paths:
            if not isfile(log_path): continue
            try: self._start_process(None, TEXT_EDITOR_NAME, (log_path, ))
            except Exception: pass

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
        dir_str = ''.join(' %s' % param[2] for param in params)
        index = self.commands_text.index(tk.INSERT).split('.')[0] + '.0'
        self.commands_text.insert(index, dir_type + dir_str + '\n')

    def insert_tool_cmd(self, cmd_type):
        params = TOOL_COMMANDS.get(cmd_type, ())
        cmd_str = ''.join(' %s' % param[2] for param in params)
        index = self.commands_text.index(tk.INSERT).split('.')[0] + '.end'
        self.commands_text.insert(index, cmd_type + cmd_str + '\n')

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
            self.save_command_list(filename=LAST_CMD_LIST_NAME)
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
