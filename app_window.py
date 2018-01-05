import ctypes
import gc
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
from binilla.util import float_to_str

from hek_pool.constants import *
from hek_pool.help_text import INTRODUCTION_TEXT, HELP_NAME,\
     TOOL_COMMAND_HELP, DIRECTIVES_HELP, generate_help
from hek_pool.config_def import config_def, CFG_DIRS


platform = sys.platform.lower()
if "linux" in platform:
    platform = "linux"


SetFileAttributesW = None
if platform == "win32":
    TEXT_EDITOR_NAME = "notepad"
    SetFileAttributesW = ctypes.windll.kernel32.SetFileAttributesW
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
    _template_opt_cache = None
    _reset_style_on_click = False
    _intro_mode = False
    _pre_intro_text = ""

    fixed_font = None

    open_log = None
    clear_log = None
    smart_assist_on_rclick = None
    supress_tool_beta_errors = None
    proc_limit = None

    last_load_dir = curr_dir
    working_dir = curr_dir
    commands_lists_dir = join(curr_dir, "cmd_lists")

    tool_paths = ()

    curr_tool_index = -1
    curr_commands_list_name = None
    
    '''Window location and size'''
    app_width = 630
    app_height = 330
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
    version = '0.9.0'
    log_filename = 'hek_pool.log'
    max_undos = 1000

    def __init__(self, *args, **kwargs):
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
        self.smart_assist_on_rclick = tk.BooleanVar(self, 1)
        self.supress_tool_beta_errors = tk.BooleanVar(self, 1)
        self.proc_limit = tk.StringVar(self, 1)

        self.processes = {}

        if type(self).fixed_font is None:
            type(self).fixed_font = Font(family="Terminal", size=10)

        self.title('%s v%s' % (self.app_name, self.version))
        self.minsize(width=450, height=150)
        self.geometry("%sx%s" % (630, 330))
        self.update()
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.bind('<Control-o>', lambda e=None: self.load_commands_list())
        self.bind('<Control-s>', lambda e=None: self.save_commands_list())
        self.bind('<Control-S>',     lambda e=None: self.save_commands_list_as())
        self.bind('<Control-Alt-s>', lambda e=None: self.save_commands_list_as())

        # make the menubar
        self.main_menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.main_menu, tearoff=0)
        self.templates_menu = tk.Menu(self.main_menu, tearoff=0,
                                      postcommand=self.generate_templates_menu)
        self.settings_menu = tk.Menu(self.main_menu, tearoff=0)
        self.tools_menu = tk.Menu(self.main_menu, tearoff=0,
                                  postcommand=self.generate_tools_menu)
        self.help_menu = tk.Menu(self.main_menu, tearoff=0)
        self.config(menu=self.main_menu)
        self.main_menu.add_cascade(label="File", menu=self.file_menu)
        self.main_menu.add_cascade(label="Settings", menu=self.settings_menu)
        self.main_menu.add_cascade(label="Templates", menu=self.templates_menu)
        self.main_menu.add_cascade(label="Select Tool", menu=self.tools_menu)
        self.main_menu.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Commands and Directives",
                                   command=self.show_help_in_text_editor)
        self.help_menu.add_command(label="Introduction",
                                   command=self.start_introduction)



        self.file_menu.add_command(label="Open...",
                                   command=self.load_commands_list)
        self.file_menu.add_command(label="Select command list folder",
                                   command=self.set_commands_list_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save",
                                   command=self.save_commands_list)
        self.file_menu.add_command(label="Save As...",
                                   command=self.save_commands_list_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Add Tool",
                                   command=self.tool_path_browse)
        self.file_menu.add_command(label="Remove Tool",
                                   command=self.remove_tool_path)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Edit colors",
                                   command=self.edit_style_in_text_editor)
        self.file_menu.add_command(label="Edit right-click menu",
                                   command=self.edit_templates_in_text_editor)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.close)

        self.settings_menu.add("checkbutton", variable=self.clear_log,
                               label="Clear debug.txt's before processing")
        self.settings_menu.add("checkbutton", variable=self.open_log,
                               label="Open debug.txt's after processing")
        self.settings_menu.add("checkbutton",
                               variable=self.smart_assist_on_rclick,
                               label="Enable smart-assist when right-clicking")
        self.settings_menu.add("checkbutton",
                               variable=self.supress_tool_beta_errors,
                               label="Fix toolbeta.map error")

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
            "Enter directives and Tool commands to process (one per line)"))
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
        self.commands_text.tag_config("all")

        # make the start buttons
        self.buttons_frame = tk.Frame(self.commands_frame)
        self.process_button = tk.Button(
            self.buttons_frame, text="Process selected",
            command=self.execute_selected_pressed)
        self.process_all_button = tk.Button(
            self.buttons_frame, text="Process all",
            command=self.execute_pressed)
        self.cancel_button = tk.Button(
            self.buttons_frame, text="Cancel",
            command=self.cancel_pressed)
        self.proc_limit_frame = tk.LabelFrame(self.buttons_frame,
                                              text="Max parallel processes")
        self.proc_limit_spinbox = tk.Spinbox(
            self.proc_limit_frame, values=tuple(range(1, MAX_PROCESS_CT + 1)),
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
        self.load_templates()

        if isfile(join(self.commands_lists_dir, LAST_CMD_LIST_NAME + '.txt')):
            self.load_commands_list(LAST_CMD_LIST_NAME)
        else:
            self.start_introduction()

        try:
            generate_help(True)
        except Exception:
            print(traceback.format_exc())

        if using_console:
            messagebox.showerror(
                "Currently using python with a console!",
                "It is recommended to run Pool without a python console open if "
                "possible. The console will prevent tool windows from appearing "
                "as a separate window, preventing the use of the #k directive. "
                "This will also redirect all tool output to the console, which "
                "is very hard to read with 3+ tool commands going all at once.",
                parent=self.commands_text)

    def start_introduction(self):
        if self._execution_state or self._intro_mode:
            return

        self._intro_mode = True
        self.title('%s v%s [INTRODUCTION MODE]' % (self.app_name, self.version))
        self._pre_intro_text = self.commands_text.get('1.0', tk.END)
        self.commands_text.config(state=tk.NORMAL)
        self.commands_text.delete('1.0', tk.END)
        self.commands_text.insert('1.0', INTRODUCTION_TEXT)
        self.reset_line_style()

    def right_click_cmd_text(self, e):
        try:
            return self._right_click_cmd_text(e)
        except Exception:
            print(format_exc())

    def _right_click_cmd_text(self, e):
        cmd_text = self.commands_text
        index = cmd_text.index("@%d,%d" % (e.x, e.y))
        posy, posx = (int(p) for p in index.split('.'))
        cmd_text.mark_set(tk.INSERT, index)

        raw_cmd_str = self.commands_text.get(
            '%d.0' % posy, '%d.end' % posy).replace('\t', ' ')
        if (not self.smart_assist_on_rclick.get() or self.check_can_copy() or
                len(raw_cmd_str.strip(' ').strip('\t')) == 0):
            # empty line. post the menu to select a command
            self.post_templates_menu(e)
            return

        cmd_args, disabled = self.get_command(posy)

        # selecting a command. find out what part of the command
        i, start_char = 0, ';' if disabled else ' '
        cmd_infos, help_infos = TOOL_COMMANDS, TOOL_COMMAND_HELP
        if cmd_args[0] == '#':
            i, start_char = 1, '#'
            cmd_infos, help_infos = DIRECTIVES, DIRECTIVES_HELP

        # do we need to worry about there possibly being or not being
        # a space between the type char(; or #) and the command type?
        find_start = start_char in ';#'

        cmd_type, cmd_args = cmd_args[i], cmd_args[i + 1:]
        cmd_info  = cmd_infos.get(cmd_type)
        help_info = help_infos.get(cmd_type, ())
        if cmd_info is None:
            self.post_templates_menu(e)
            return

        # locate which argument in the command string we are hovering over
        arg_index, i, in_str, param_str = -1, 0, False, ""
        for c in raw_cmd_str:
            if i > posx:
                break
            elif find_start:
                if c == start_char and find_start == 1:
                    find_start = 2
                elif c != ' ' and find_start == 2:
                    find_start = False
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

        if arg_index == -1 or self._execution_state:
            # clicked the command name. show info about that command
            if help_info:
                message = help_info[0]
                if not message:
                    message = (
                        "Sorry, no help text for the %s command just yet!" %
                        cmd_type)

                if len(help_info) == 1:
                    message += "\n\nThis command accepts no arguments."
                else:
                    message += "\n\nArguments:"

                    for arg_help in help_info[1:]:
                        if len(arg_help[1]) >= 8:
                            message += "\n    (%s)\t<%s>" % (arg_help[1],
                                                             arg_help[0])
                        else:
                            message += "\n    (%s)\t\t<%s>" % (arg_help[1],
                                                               arg_help[0])
                    
                messagebox.showinfo(cmd_type, message,
                                    parent=self.commands_text)
            return
        elif arg_index not in range(len(cmd_info)):
            self.post_templates_menu(e)
            return

        cwd = dirname(self.get_tool_path())
        if not cwd:
            cwd = self.working_dir

        # Simulate the processing of the commands to modify macros and cwd
        loc_vars = dict(cwd=cwd)
        upper_cmds = [self.get_command(l) for l in range(posy)]
        for cmd, dis in upper_cmds:
            if dis or len(cmd) < 3 or cmd[0] != '#': continue
            typ, vals, new_vals = cmd[1], cmd[2:], []
            for v in vals:
                for var, repl in loc_vars.items():
                    if '<' not in v: break
                    v = v.replace("<%s>" % var, repl.strip('"'))
                new_vals.append(v)

            vals = new_vals
            if typ == 'cwd':
                loc_vars['cwd'] = ''.join(
                    "%s " % s for s in vals)[:-1].strip('"')
            elif typ == "set" and len(vals) >= 2:
                loc_vars[vals[0]] = vals[1]
            elif typ == "del" and vals[0] != 'cwd':
                loc_vars.pop(vals[0], None)

        # inject the replacement arguments into this string(if any)
        new_cmd_args = []
        for a in cmd_args:
            for var, repl in loc_vars.items():
                if '<' not in a: break
                a = a.replace("<%s>" % var, repl.strip('"'))
            new_cmd_args.append(a)
        cmd_args = new_cmd_args

        cmd_args.extend([""]*(arg_index - len(cmd_args) + 1))

        # Get informataion on the type of command so we can
        # see if we need to generate a browse widget for it
        arg_info = cmd_info[arg_index]
        cur_val  = cmd_args[arg_index].strip('"')
        new_val = None
        name, typ, default = arg_info[:3]
        options = () if len(arg_info) < 4 else arg_info[3]
        if isinstance(typ, (tuple, list)):
            typ, typ_info = typ[0], typ[1:]
        else:
            typ_info = ()

        cwd = loc_vars['cwd']
        # Create the widget for a more hand-holdey editing interface
        if typ in ("dir", "file", "file-no-ext"):
            if len(arg_info) >= 4:
                cwd = join(cwd, arg_info[4])

            start_dir = dirname(join(cwd, cur_val))
            if not exists(start_dir):
                start_dir = cwd

            start_dir = start_dir.replace('/', '\\')

            if typ == "dir":
                new_val = join(askdirectory(
                    initialdir=start_dir, parent=self.commands_text,
                    title="Select <%s> for %s" % (name, cmd_type)), '')
            elif typ in ("file", "file-no-ext"):
                new_val = askopenfilename(
                    initialdir=start_dir, parent=self.commands_text,
                    filetypes=tuple(typ_info) + (("All", "*"), ),
                    title="Select <%s> for %s" % (name, cmd_type))
                if typ == "file-no-ext":
                    new_val = splitext(new_val)[0]

            if new_val:
                new_val = '"%s"' % relpath(new_val.replace('/', '\\'), start_dir)
            else:
                new_val = None
        elif typ == 'bool':
            message = None
            if arg_index + 1 < len(help_info):
                param_help = help_info[arg_index + 1]
                if len(param_help) > 2:
                    message = param_help[2]

            if not message:
                message = "Sorry, no help text for <%s> just yet!" % name

            new_val = messagebox.askyesnocancel(name, message,
                                                parent=self.commands_text)
            if new_val is not None:
                new_val = str(int(new_val))
        else:
            message = None
            if arg_index + 1 < len(help_info):
                param_help = help_info[arg_index + 1]
                if len(param_help) > 2:
                    message = param_help[2]

            if not message:
                message = "Sorry, no help text for <%s> just yet!" % name

            opts = ()
            if typ in ("str", "str-no-quote", "float") and len(arg_info) >= 4:
                opts = tuple(arg_info[3])

            if opts:
                message += '\n\nValid values for this argument are:\n'
                if typ == "float":
                    message += "    Numbers that are >= %s and <= %s" % (
                        float_to_str(opts[0]), float_to_str(opts[1]))
                else:
                    for opt in opts:
                        message += "    %s\n" % opt
                
            messagebox.showinfo(name, message, parent=self.commands_text)

        # Apply the new value
        if new_val is not None:
            cmd_args[arg_index] = new_val
            cmd_args.insert(0, cmd_type)
            if start_char == '#':
                cmd_args.insert(0, "#")

            # DO NOT strip the last space off the end. This allows quickly
            # right clicking the end of the line to add the next argument
            new_arg_string = ''.join('%s ' % a for a in cmd_args)
            if disabled:
                new_arg_string = ';' + new_arg_string

            self.commands_text.delete('%d.0' % posy, '%d.end' % posy)
            self.commands_text.insert('%d.0' % posy, new_arg_string)
            self.set_line_style(posy, self.get_line_style(posy))

    def post_templates_menu(self, e):
        self.templates_menu.post(e.x_root, e.y_root)

    def ignore_keypress(self, e=None):
        self.commands_text.delete(tk.INSERT)

    def get_text_state(self):
        return self.commands_text.config()['state'][-1]

    def get_command_count(self):
        return int(self.commands_text.index(tk.END).split('.')[0])

    def apply_style(self):
        def_color = text_tags_colors['default']

        for style_name, style_vals in text_tags_colors.items():
            if style_name == "default":
                continue
            kw = {}
            if 'bg' in style_vals:
                kw['background'] = style_vals['bg']
            if 'fg' in style_vals:
                kw['foreground'] = style_vals['fg']
            self.commands_text.tag_config(style_name, **kw)

        kw = dict()
        if 'bg' in def_color:
            kw['bg'] = def_color['bg']
        if 'fg' in def_color:
            kw['fg'] = kw['insertbackground'] = def_color['fg']
        if 'insert_bg' in def_color:
            kw['insertbackground'] = def_color['insert_bg']
        if 'bg_highlight' in def_color:
            kw['selectbackground'] = def_color['bg_highlight']
        if 'fg_highlight' in def_color:
            kw['selectforeground'] = def_color['fg_highlight']

        self.commands_text.config(**kw)

    def show_help_in_text_editor(self):
        Thread(target=self._show_help_in_text_editor, daemon=True).start()

    def _show_help_in_text_editor(self):
        try:
            help_path = join(self.working_dir, HELP_NAME)
            if not isfile(help_path):
                generate_help(True)
                if not isfile(help_path):
                    return

            proc_controller = ProcController(abandon=True)
            self._start_process(None, TEXT_EDITOR_NAME, (help_path, ),
                                proc_controller=proc_controller)
        except Exception:
            print(format_exc())
            print("Could not open %s" % HELP_NAME)

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
            print("Could not open %s" % STYLE_CFG_NAME)

    def edit_templates_in_text_editor(self):
        Thread(target=self._edit_templates_in_text_editor, daemon=True).start()

    def _edit_templates_in_text_editor(self):
        templates_path = join(self.working_dir, TEMPLATES_CFG_NAME)
        if not isfile(templates_path):
            self.save_templates()
            if not isfile(templates_path):
                return

        try:
            proc_controller = ProcController()
            self._start_process(None, TEXT_EDITOR_NAME, (templates_path, ),
                                proc_controller=proc_controller)

            while proc_controller.returncode is None:
                sleep(0.1)
            self.load_templates()
        except Exception:
            print(format_exc())
            print("Could not open %s" % TEMPLATES_CFG_NAME)

    def load_templates(self):
        try:
            templates_path = join(self.working_dir, TEMPLATES_CFG_NAME)
            if not isfile(templates_path):
                return

            with open(templates_path, 'r') as f:
                data = ''
                for line in f:
                    line = line.replace('\t', ' ').replace('\r', '\n').\
                           strip(' ')
                    if not line or line.startswith(';'):
                        continue

                    new_line, old_line = line.replace('  ', ' '), line
                    while new_line != old_line:
                        old_line = new_line
                        new_line = old_line.replace('  ', ' ')

                    if len(line) > 1 and line[-2] not in '({[,':
                        if line.endswith(')\n'):
                            line = line.replace('\n', ',\n')
                        else:
                            line = line.replace('\n', '",\n')

                    if line.lstrip(' ')[0] not in '({[\n]})':
                        line = '"' + line

                    data += line
                data = data.strip('\n').replace('{', '(').replace('}', ')').\
                       replace('[', '(').replace(']', ')').replace('(', '("')

                new_templates = eval("list((%s))" % data)
            malformed = False
        except Exception:
            malformed = True
            new_templates = ()

        sanitized_new_templates = []
        valid_items = set(tuple(SPECIAL_TEMPLATES_KWDS) +
                          tuple(TOOL_COMMANDS) + tuple(DIRECTIVES))
        for item in new_templates:
            if isinstance(item, str):
                if item in valid_items:
                    sanitized_new_templates.append(item)
                continue

            malformed |= not(hasattr(item, '__len__') and len(item))
            if malformed: break

            casc_name, sanitized_items = str(item[0]).strip(' '), []
            for name in item[1:]:
                if name in valid_items:
                    sanitized_items.append(name)

            sanitized_new_templates.append([casc_name] + sanitized_items)

        if malformed:
            print("Could not load %s as it is malformed." % TEMPLATES_CFG_NAME)
        else:
            del TEMPLATE_MENU_LAYOUT[:]
            TEMPLATE_MENU_LAYOUT.extend(sanitized_new_templates)

    def save_templates(self):
        with open(join(self.working_dir, TEMPLATES_CFG_NAME), 'w') as f:
            f.write("""
; This file controls what shows up in the templates menu when you
; right-click an empty line or access it through the menu bar.
; You can make Tool commands and Pool directives appear either
; directly in the menu, or inside a cascade in the menu.
;
; Look at the bottom of this file for a list of all available Tool
; commands, Pool directives, and special keywords. You must type them
; in EXACTLY as they appear(they are case sensitive). If the command
; doesn't appear in the menu when you right-click, it was misspelled.
;
; The cut, copy, and paste keywords cannot be used inside a cascade.
;
; If the templates fail to load at all, make sure:
;    * You don't have any missing starting or ending parenthese
;    * You have only one command/cascade defined per line
;    * You do not have a cascade inside a cascade(not allowed)
;    * Lines have ONLY spaces or tabs before open/close parenthese
;    * ONLY spaces/tabs are on lines containing CLOSING parenthese

""")
            for item in TEMPLATE_MENU_LAYOUT:
                if isinstance(item, str):
                    f.write('\n%s\n' % item)
                    continue

                casc_name, temp_names = item[0], item[1:]
                f.write('\n( %s\n' % casc_name)
                for name in temp_names:
                    f.write('    %s\n' % name)
                f.write("    )\n")

            f.write("\n\n; All Tool commands:\n;\n")
            for cmd_name in sorted(TOOL_COMMANDS):
                f.write(";     %s\n" % cmd_name)

            f.write("\n\n; All Pool directives:\n;\n")
            for dir_name in sorted(DIRECTIVES):
                f.write(";     %s\n" % dir_name)

            f.write("\n\n; All special template keywords:\n;\n")
            for name in sorted(SPECIAL_TEMPLATES_KWDS):
                f.write(";     %s\n" % name)
                f.write(";         %s\n" % SPECIAL_TEMPLATES_KWDS[name])

    def do_clipboard_action(self, event_type):
        cmd_text = self.commands_text
        if event_type == "Cut":
            cmd_text.event_generate("<<Cut>>")
        elif event_type == "Copy":
            if cmd_text.tag_ranges(tk.SEL):
                cmd_text.event_generate("<<Copy>>")
        elif event_type == "Paste":
            if self._execution_state:
                return

            # if the insertion cursor is not inside the selection range,
            # then we can deselect it since we aren't pasting into it.
            insy, insx = cmd_text.index(tk.INSERT).split('.')
            insy, insx = int(insy), int(insx)
            sel_range = cmd_text.tag_ranges(tk.SEL)
            if sel_range:
                starty, startx = cmd_text.index(sel_range[0]).split('.')
                stopy,  stopx  = cmd_text.index(sel_range[1]).split('.')
                starty, startx = int(insy),  int(insx)
                stopy,  stopx  = int(stopy), int(stopx)
                if starty > stopy:
                    starty, stopy = stopy, starty
                    startx, stopx = stopx, startx
                elif startx > stopx:
                    startx, stopx = stopx, startx

                if (insy in range(starty, stopy + 1) and
                    insx in range(startx, stopx + 1)):
                    # pasting into selection. keep the selection so
                    # the contents of the selection are overwritten
                    pass
                else:
                    # not pasting into selection. remove selection
                    cmd_text.tag_remove(tk.SEL, "1.0", tk.END)

            cmd_text.event_generate("<<Paste>>")
            cmd_text.see(tk.INSERT)

    def set_commands_list_folder(self):
        folder = askdirectory(
            initialdir=self.commands_lists_dir, parent=self,
            title="Select the folder to save command lists")

        if folder:
            self.commands_lists_dir = folder

    def get_commands_list_names(self):
        if exists(join(self.commands_lists_dir, '')):
            return

        list_names = []
        for root, dirs, files in os.walk(self.commands_lists_dir):
            for filename in sorted(files):
                list_names.append(relpath(join(root), self.commands_lists_dir))

        return list_names

    def load_commands_list(self, list_name=None):
        if self._execution_state:
            return

        if list_name is None:
            filepath = askopenfilename(
                initialdir=self.commands_lists_dir, parent=self,
                title="Select a command list to load",
                filetypes=(("Text file", "*.txt"), ("All", "*")),)
        else:
            if not exists(join(self.commands_lists_dir, '')):
                return
            filepath = join(self.commands_lists_dir, "%s.txt" % list_name)

        if not isfile(filepath):
            return

        with open(filepath, 'r') as f:
            data = f.read()

        if self._intro_mode:
            self.cancel_pressed()

        cmd_list_name = splitext(basename(filepath))[0]
        if cmd_list_name != LAST_CMD_LIST_NAME:
            self.curr_commands_list_name = cmd_list_name

        self.commands_text.delete('1.0', tk.END)
        self.commands_text.insert('1.0', data)
        self.commands_text.edit_reset()
        self.reset_line_style()

    def save_commands_list_as(self):
        fp = asksaveasfilename(
            initialdir=self.commands_lists_dir, parent=self,
            title="Save the command list to where",
            filetypes=(("Text file", "*.txt"), ("All", "*")),)

        if fp:
            path, ext = splitext(sanitize_path(fp))
            if not ext: ext = ".txt"
            self.save_commands_list(path + ext)

    def save_commands_list(self, filepath=None, directory=None, filename=None):
        if filepath:
            directory = dirname(filepath)
        else:
            if filename is None:
                if self.curr_commands_list_name is None:
                    return self.save_commands_list_as()

                filename = self.curr_commands_list_name
            if directory is None:
                directory = self.commands_lists_dir

            filepath = join(directory, filename + '.txt')

        if directory and not exists(directory):
            os.makedirs(directory)

        with open(filepath, 'w') as f:
            data = self.commands_text.get('1.0', tk.END)
            if data[-1] in '\n\r':
                # always seems to be an extra new line. remove that.
                data = data[:-1]
            f.write(data)

        if filename == LAST_CMD_LIST_NAME:
            try:
                # make it hidden
                SetFileAttributesW(filepath, 2)
            except Exception:
                pass

        self.curr_commands_list_name = splitext(basename(filepath))[0]

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
        self.smart_assist_on_rclick.set(header.flags.smart_assist_on_rclick)
        self.supress_tool_beta_errors.set(header.flags.supress_tool_beta_errors)
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
        header.flags.smart_assist_on_rclick = self.smart_assist_on_rclick.get()
        header.flags.supress_tool_beta_errors = self.supress_tool_beta_errors.get()
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
            style_path = join(self.working_dir, STYLE_CFG_NAME)
            if not isfile(style_path):
                return

            with open(style_path, 'r') as f:
                data = ''
                for line in f:
                    line = line.replace('\t', ' ').replace('\r', '\n').\
                           strip(' ')
                    if not line or line.startswith(';'):
                        continue

                    new_line, old_line = line.replace('  ', ' '), line
                    while new_line != old_line:
                        old_line = new_line
                        new_line = old_line.replace('  ', ' ')

                    if len(line) > 1 and line[-2] not in '({[,':
                        line = line.replace('\n', ',\n')

                    data += line
                data = data.strip('\n').replace('(,', '{').replace('(', 'dict(')
                new_style = eval("dict(%s)" % data.lower())
            malformed = False
        except Exception:
            malformed = True
            new_style = ()

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

    def save_style(self):
        with open(join(self.working_dir, STYLE_CFG_NAME), 'w') as f:
            f.write(
                """
; These sets of hex values determine the letter(fg) and background(bg) colors
; for the specified type of text. For example, lines being processed use the
; "processed" colors, while commented lines use the "commented" colors.
""")
            for name in sorted(text_tags_colors):
                f.write("\n%s = (\n" % name)
                colors = text_tags_colors[name]
                for color_name in sorted(colors):
                    f.write('    %s = "%s"\n' %
                            (color_name, colors[color_name][1:]))
                f.write("    )\n")

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
                proc_c = kwargs.get("proc_controller")
                processes = kwargs.pop("processes", {})
                completed = kwargs.pop("completed", {})
                do_subprocess(*args, **kwargs)
            except Exception:
                print(format_exc())

            if line is None:
                return

            completed[line] = kw = processes.pop(line, {})
            if not app or processes is not app.processes:
                return

            # set the command's text to the 'processed' or 'error' status
            if app._execution_state or app._reset_style_on_click:
                if ("k" not in kw.get('cmd_args', ()) and
                        proc_c and proc_c.returncode):
                    # we HAVE to close windows manually with "k" as an
                    # argument, so they will always return an error code.
                    # in this case we ignore any error code they return.
                    self.set_line_style(line, "error")
                else:
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
            return [""], True

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

    def cancel_pressed(self):
        self._stop_processing = True
        if self._intro_mode:
            self._intro_mode = False
            self.title('%s v%s' % (self.app_name, self.version))
            self.commands_text.delete('1.0', tk.END)
            self.commands_text.insert('1.0', self._pre_intro_text)
            self.reset_line_style()

    def execute_pressed(self, start=None, stop=None):
        if not self._execution_thread:
            pass
        elif self._execution_thread.is_alive():
            return
        self._execution_thread = Thread(target=self._execute_commands, daemon=1,
                                        kwargs=dict(start=start, stop=stop))
        self._execution_thread.start()

    def execute_selected_pressed(self):
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
        self.execute_pressed(start_y, stop_y)

    def get_can_execute_command(self, cmd_args, loc_vars):
        cmd_type = cmd_args[0]
        is_directive = False
        if cmd_type in DIRECTIVE_START_STRS:
            is_directive = True
            cmd_type = None if len(cmd_args) == 1 else cmd_args[1]

        cwd = join(loc_vars.get('cwd', '').lower(), '')

        if len(cmd_args) - is_directive < 2:
            # no arguments for the command, so nothing to compare
            pass
        elif cmd_type in (
                "build-cache-file", "build-cache-file-ex", "lightmaps",
                "build-cache-file-new", "import-structure-lightmap-uvs",
                "structure", "structure-breakable-surfaces", "merge-scenery"):
            # doing something involving scenarios and/or bsp's

            scnr_path = join(cmd_args[1].lower(), '')
            for proc_i, proc_info in tuple(self.processes.items()):
                if not proc_info: continue
                # make sure not trying to do any tag creation in the same
                # folder at the same time we're trying to build a map in it
                proc_args = proc_info['exec_args']
                proc_type = proc_args[0]
                if join(proc_info.get('cwd', '').lower(), '') != cwd:
                    # not the same cwd. safe to run.
                    pass
                elif proc_type in (
                        "import-structure-lightmap-uvs", "lightmaps",
                        "structure", "structure-breakable-surfaces"):
                    if proc_type == "structure" and cmd_type == "structure":
                        # since tool creates specifically named temp files
                        # for compiling bsps, I don't believe you can compile
                        # multiple bsps in the same working directory at once.
                        return False

                    proc_scnr_path = '' if len(proc_args) == 1 else proc_args[1]

                    if scnr_path == join(proc_scnr_path, ''):
                        # edits the same scenario or bsp as the one
                        # currently being processed. NOT safe to run!
                        return False
                elif proc_type == "merge-scenery":
                    pass
                elif proc_type not in (
                        "build-cpp-definition", "build-packed-file", "help",
                        "runtime-cache-view", "windows-font"):
                    # a command that edits tags. NOT safe to run!
                    return False
        elif cmd_type in ("bitmap", "import-device-defaults"):
            path_arg_i = 1
            if cmd_type == "import-device-defaults":
                path_arg_i = 2

            if len(cmd_args) < path_arg_i + 1:
                # not enough args to check
                return True
            
            path_arg = join(cmd_args[path_arg_i].lower(), '')
            for proc_i, proc_info in self.processes.items():
                if not proc_info: continue
                proc_args = proc_info['exec_args']
                proc_type = proc_args[0]

                if (join(proc_info.get('cwd', '').lower(), '') != cwd or
                        proc_type != cmd_type or len(proc_args) <= path_arg_i):
                    # not the same cwd, a different command, or not enough args.
                    # safe to run(i think).
                    pass
                elif join(proc_args[path_arg_i].lower(), '') == path_arg:
                    # same cwd, command type, and directory. NOT safe to run!
                    return False
        elif cmd_type in ("animations", "bitmaps", "compile-shader-postprocess",
                          "hud-messages", "model", "physics", "sounds",
                          "strings", "unicode-strings"):
            dir_arg = join(cmd_args[1].lower(), '')
            for proc_i, proc_info in self.processes.items():
                if not proc_info: continue
                proc_type, proc_args = proc_info['exec_args'][0],\
                                           proc_info['exec_args'][1:]
                if (join(proc_info.get('cwd', '').lower(), '') != cwd or
                        proc_type != cmd_type or not proc_args):
                    # not the same cwd, a different command, or no args.
                    # safe to run(i think).
                    pass
                elif join(proc_args[0].lower(), '') == dir_arg:
                    # same cwd, command type, and directory. NOT safe to run!
                    return False


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
            messagebox.showerror(
                "No Tool.exe!",
                "No tool.exe is selected to process commands.\n"
                'Go to "File->Add Tool" and select the copy of\n'
                "tool.exe you wish to use.")
            return
        self._execution_state = True
        self._stop_processing = False

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
            loc_vars["cwd"] = dirname(tool_path)
            processes, proc_limit = self.processes, self.proc_limit

            i, curr_max_proc_ct = start, 0
            wait_on_cmds, cmds_started, skip_ct, direc_ct = False, 0, 0, 0
            completed, processes, cmd_args_dict = {}, {}, dict(k=False)
            self.processes = processes
            while i <= stop and not self._stop_processing:
                curr_proc_ct = len(processes)
                cwd = loc_vars["cwd"]
                wait_on_cmds &= cmds_started > len(completed)

                if wait_on_cmds:
                    sleep(0.1)
                    continue
                elif curr_proc_ct >= int(proc_limit.get()):
                    # continually execute processes until the max quota is hit
                    sleep(0.1)
                    continue

                exec_args, disabled = self.get_command(i)
                if not exec_args[0]:
                    # ignore empty lines
                    skip_ct += 1
                elif disabled:
                    # ignore commented commands
                    skip_ct += 1
                elif curr_max_proc_ct and curr_proc_ct == curr_max_proc_ct:
                    # same number of processes as last checked. don't
                    # need to check self.get_can_execute_command again
                    continue
                elif exec_args[0] in DIRECTIVE_START_STRS:
                    # directive to change some variable
                    self.commands_text.see("%s.0" % i)
                    direc_ct += 1

                    typ  = None if len(exec_args) == 1 else exec_args[1]
                    vals = () if len(exec_args) == 2 else exec_args[2:]
                    if typ not in DIRECTIVES:
                        # malformed directive
                        self.set_line_style(i, "error")
                        i += 1
                        continue

                    if loc_vars:
                        new_vals = []
                        for v in vals:
                            for var, repl in loc_vars.items():
                                if '<' not in v: break
                                v = v.replace("<%s>" % var, repl.strip('"'))
                            new_vals.append(v)
                        vals = new_vals

                    self.set_line_style(i, "processed")
                    if typ == 'cwd':
                        if vals:
                            # if spaces are in the filepath, put them back in.
                            # also, strip parenthese since cmd doesn't know how.
                            loc_vars["cwd"] = (
                                ''.join("%s " % s for s in vals)[:-1].strip('"'))
                        else:
                            self.set_line_style(i, "error")
                    elif typ == 'k':
                        # need to check if we are running with an interactive
                        # console, since if we are we CANNOT keep the process
                        # open since it will hose up the interpreter forever.
                        if not using_console:
                            cmd_args_dict['k'] = True
                    elif typ == 'c':
                        cmd_args_dict['k'] = False
                    elif typ == "set":
                        if len(vals) >= 2:
                            loc_vars[vals[0]] = vals[1]
                        else:
                            self.set_line_style(i, "error")
                    elif typ == "del":
                        if vals and vals[0] != 'cwd':
                            loc_vars.pop(vals[0], None)
                        else:
                            self.set_line_style(i, "error")
                    elif typ == "run":
                        if self._intro_mode or self._stop_processing:
                            completed[i] = dict()
                            self.set_line_style(i, "processed")
                        else:
                            self.set_line_style(i, "processing")
                            self._start_process(
                                i, join(cwd, vals.pop(0).strip('"')), vals,
                                cwd=cwd, completed=completed,
                                processes=processes)
                        cmds_started += 1
                    elif typ == 'w':
                        wait_on_cmds = True
                    else:
                        self.set_line_style(i, "error")
                else:
                    # this is a command we can actually execute!

                    log_path = join(cwd, 'debug.txt')
                    if log_path not in log_paths:
                        if clear_log and not self._intro_mode:
                            try:
                                with open(log_path, "w") as f:
                                    f.truncate()
                            except Exception:
                                pass
                        log_paths.add(log_path)

                    if loc_vars:
                        cmd_type, new_exec_args = exec_args[0], []
                        for a in exec_args[1:]:
                            for var, repl in loc_vars.items():
                                if '<' not in a: break
                                a = a.replace("<%s>" % var, repl.strip('"'))
                            new_exec_args.append(a)
                        exec_args = [cmd_type] + new_exec_args

                    req_arg_ct = -1
                    if cmd_type in TOOL_COMMANDS:
                        req_arg_ct = len(TOOL_COMMANDS[cmd_type])

                    if len(exec_args) - 1 == req_arg_ct:
                        if not self.get_can_execute_command(exec_args, loc_vars):
                            # can't execute this command just yet.
                            curr_max_proc_ct = curr_proc_ct
                            continue

                        print('\n\n"%s"' % tool_path,
                              ''.join(" %s" % a for a in exec_args))
                        self.commands_text.see("%s.0" % i)
                        curr_max_proc_ct = 0

                        # start the command
                        cmd_args = tuple(a for a in cmd_args_dict if cmd_args_dict[a])
                        if self._intro_mode or self._stop_processing:
                            completed[i] = {}
                            self.set_line_style(i, "processed")
                        else:
                            if self.supress_tool_beta_errors.get():
                                toolbeta_path = join(cwd, "toolbeta.map")
                                try:
                                    if not isfile(toolbeta_path):
                                        with open(toolbeta_path, 'w') as f:
                                            f.write("I shouldn't have had to do this...")
                                        if SetFileAttributesW:
                                            SetFileAttributesW(toolbeta_path, 2)
                                except Exception:
                                    pass
                            self._start_process(
                                i, tool_path, exec_args, cmd_args, cwd=cwd,
                                completed=completed, processes=processes,
                                shell=using_console)

                            # set the command's text to the 'processing' color
                            self.set_line_style(i, "processing")

                        cmds_started += 1
                    else:
                        self.set_line_style(i, "error")

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

    def generate_templates_menu(self):
        if self._template_opt_cache == TEMPLATE_MENU_LAYOUT:
            for i in range(len(TEMPLATE_MENU_LAYOUT)):
                item, state = TEMPLATE_MENU_LAYOUT[i], tk.DISABLED
                if item not in ("<<cut>>", "<<copy>>", "<<paste>>"):
                    continue
                elif ((item == "<<paste>>" and self.check_can_paste()) or
                      (item != "<<paste>>" and self.check_can_copy())):
                    state = tk.NORMAL

                self.templates_menu.entryconfigure(i, state=state)

            return
            
        self.templates_menu.delete(0, "end")
        self._template_opt_cache = list(TEMPLATE_MENU_LAYOUT)

        # generate the options for templates_menu
        for item in TEMPLATE_MENU_LAYOUT:
            if isinstance(item, str):
                if item == "<<divider>>":
                    self.templates_menu.add_separator()
                elif item in ("<<cut>>", "<<copy>>", "<<paste>>"):
                    item = item.strip('<').strip('>').capitalize()
                    state = self.check_can_paste if item == 'Paste' else\
                            self.check_can_copy

                    self.templates_menu.add_command(
                        state=tk.NORMAL if state() else tk.DISABLED, label=item,
                        command=lambda i=item: self.do_clipboard_action(i))
                else:
                    self.templates_menu.add_command(
                        label=item, command=lambda n=item:
                        self.insert_template(n))
                continue

            casc_name, temp_names = item[0], item[1:]
            new_menu = tk.Menu(self.templates_menu, tearoff=0)
            self.templates_menu.add_cascade(label=casc_name, menu=new_menu)
            for name in temp_names:
                if name == "<<divider>>":
                    new_menu.add_separator()
                    continue
                new_menu.add_command(label=name, command=lambda n=name:
                                     self.insert_template(n))

        gc.collect()

    def check_can_copy(self):
        try:
            return bool(self.commands_text.index(tk.SEL_FIRST))
        except tk.TclError:
            return False

    def check_can_paste(self):
        try:
            return bool(self.commands_text.tk.call(
                'tk::GetSelection', self.commands_text, 'CLIPBOARD'))
        except tk.TclError:
            return False

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
        if index < 0:
            if hasattr(self, "main_menu"):
                self.main_menu.entryconfig(4, label="Select Tool")
            self.curr_tool_index = -1
            return

        assert index in range(len(self.tool_paths))
        if self._execution_state or not len(self.tool_paths):
            return

        self.curr_tool_index = max(index, 0)
        tool_path = self.tool_paths[index]
        if self.config_file:
            try:
                self.config_file.last_tool_path = self.curr_tool_index + 1
            except Exception:
                pass

        path_parts = tool_path.replace('/', '\\').split('\\')
        if len(path_parts) > 2:
            trimmed_path = "[  %s\\...\\%s\\%s  ]" % (
                path_parts[0], path_parts[-2], path_parts[-1])
        else:
            trimmed_path = tool_path

        self.main_menu.entryconfig(4, label=trimmed_path)

    def tool_path_browse(self):
        for fp in askopenfilenames(
                initialdir=self.last_load_dir, parent=self,
                title="Select Tool executables",
                filetypes=(("Tool", "*.exe"), ("All", "*")),):
            fp = sanitize_path(fp)
            self.last_load_dir = dirname(fp)
            self.insert_tool_path(fp)

    def insert_template(self, temp_type):
        if temp_type in TOOL_COMMANDS:
            params = TOOL_COMMANDS.get(temp_type, ())
        elif temp_type in DIRECTIVES:
            params = DIRECTIVES.get(temp_type, ())
            temp_type = "# " + temp_type
        else:
            return

        dir_str = ''.join(' %s' % param[2] for param in params)
        posy = int(self.commands_text.index(tk.INSERT).split('.')[0])
        self.commands_text.insert('%d.0' % posy, temp_type + dir_str + '\n')
        self.set_line_style(posy, self.get_line_style(posy))

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
            if not self._intro_mode and (self.commands_text.get('1.0', tk.END).\
                                         replace('\n', '').replace(' ', '')):
                self.save_commands_list(filename=LAST_CMD_LIST_NAME)
        except Exception:
            print(format_exc())

        try:
            self.save_style()
            self.save_templates()
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
