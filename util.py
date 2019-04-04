import hashlib
import imp
import os
import platform
import shutil
import sys
import subprocess
try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
from io import StringIO

from math import log, ceil
from time import sleep
from supyr_struct.defs.util import *
from traceback import format_exc


POS_INF = float("inf")
NEG_INF = float("-inf")
FLOAT_PREC  = 23*log(2, 10)


def is_main_frozen():
   return (hasattr(sys, "frozen") or hasattr(sys, "importers")
           or imp.is_frozen("__main__"))


def get_cwd(module=None):
   if is_main_frozen():
       return os.path.dirname(sys.executable)
   return os.path.dirname(__file__ if module is None else module)


def float_to_str(f, max_sig_figs=FLOAT_PREC):
    if f == POS_INF:
        return "inf"
    elif f == NEG_INF:
        return "-inf"
    
    sig_figs = -1
    if abs(f) > 0:
        sig_figs = int(round(max_sig_figs - log(abs(f), 10)))

    if sig_figs < 0:
        return ("%f" % f).split(".")[0]
    return (("%" + (".%sf" % sig_figs)) % f).rstrip("0").rstrip(".")


class ProcController():
    kill = False
    abandon = False
    process = None
    returncode = None

    def __init__(self, kill=False, abandon=False,
                 process=None, returncode=None):
        self.kill = kill
        self.abandon = abandon
        self.process = process
        self.returncode = returncode


def do_subprocess(exec_path, cmd_args=(), exec_args=(), **kw):
    result = 1
    proc_controller = kw.pop("proc_controller", ProcController())
    try:

        if platform.system() == "Linux":
            args = (exec_path, ) + exec_args
        else:
            cmd_args  = ''.join((" /%s" % a.lower()) for a in cmd_args)
            cmd_str = '"%s" %s'
            if cmd_args:
                # ALWAYS make sure either /c or /k are explicitely supplied when
                # calling cmd, otherwise default quote handling will be used and
                # putting quotes around everything won't supply parameters right
                if '/k' not in cmd_args:
                    cmd_args += ' /c'
                cmd_str = 'cmd %s "%s"' % (cmd_args, cmd_str)

            exec_args = ''.join(( " %s" % a.lower()) for a in exec_args)
            args = cmd_str % (exec_path, exec_args)

        with subprocess.Popen(args, **kw) as p:
            proc_controller.process = p
            while p.poll() is None:
                if proc_controller.kill:
                    p.kill()
                    p.wait()
                elif proc_controller.abandon:
                    break
                sleep(0.02)

        result = p.returncode
    except Exception:
        print(format_exc())

    proc_controller.returncode = result
    return result


def get_is_executable(filepath):
    if not os.path.isfile(filepath):
        return False

    try:
        with open(filepath, "rb") as f:
            if f.read(2) != b"MZ":
                return False
            f.seek(296)
            if f.read(6) != b"PE\x00\x00\x4c\x01":
                return False
    except Exception:
        return False

    return True


def do_executable_patch(file_path, region_bounds=(), orig_hashes=(),
                        patched_hashes=(), patches=(), backup=True):
    '''Returns True if patch failed.
    Returns False if patch succeeded.
    Returns None if patch is already applied.
    '''
    if not get_is_executable(file_path):
        return True

    assert len(region_bounds) == len(orig_hashes)
    # already_patched will start out True if we have enough hashes
    # to compare, and will only be False if one or more don't match
    already_patched = len(region_bounds) == len(patched_hashes)
    patched_hashes = tuple(patched_hashes) + (
        (None, ) * (len(orig_hashes) - len(patched_hashes)))

    try:
        with open(file_path, "rb") as f:
            for bounds, orig, patched in zip(region_bounds, orig_hashes,
                                             patched_hashes):
                f.seek(bounds[0])
                hasher = hashlib.md5()
                hasher.update(f.read(bounds[1] - bounds[0]))
                area_hash = hasher.hexdigest()
                if area_hash == patched and patched is not None:
                    continue
                elif area_hash != orig:
                    return True
                already_patched = False

        if already_patched:
            return None

        if backup:
            try:
                if not os.path.exists(file_path + ".ORIG"):
                    with open(file_path, "rb") as in_file,\
                         open(file_path + ".ORIG", "wb") as out_file:
                        shutil.copyfileobj(in_file, out_file)
            except Exception:
                pass

        with open(file_path, "rb+") as f:
            for offset, patch in patches:
                f.seek(offset)
                f.write(patch)

    except Exception:
        print(format_exc())
        return True

    return False
