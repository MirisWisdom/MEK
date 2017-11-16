import os
import re
from traceback import format_exc

curr_dir = os.path.abspath(os.curdir).replace('/', '\\')
word_map = {}
flags = 0
mode = "locate"

# flags = re.IGNORECASE

print("READY")
input()


class python_word_locator_replacer():

    def __init__(self, **kwargs):
        self.directory = str(kwargs.get("directory", curr_dir))
        self.word_map = kwargs.get("word_map", word_map)
        self.mode = kwargs.get("mode", mode)
        self.filepaths = kwargs.get("filepaths")

        if self.filepaths is None:
            self.allocate_files()

    def allocate_files(self):
        self.filepaths = []
        for root, directories, files in os.walk(self.directory):
            for filename in files:

                base, ext = os.path.splitext(filename)
                filepath = os.path.join(root, filename)

                if __file__ != filepath:
                    if ext.lower() in (".py", ".pyw"):
                        self.filepaths.append(filepath)

        self.filepaths = sorted(self.filepaths)

    def run(self, search_flags=None):
        for in_p in self.filepaths:
            out_p = in_p + '.tmp'
            backup_path = in_p + ".backup"
            print_str = ""
            try:
                if self.mode.lower() == "replace":
                    with open(in_p, "r") as in_f:
                        orig_string = modified_string = in_f.read()

                        for old_word in self.word_map:
                            new_word = self.word_map[old_word]
                            matches = re.findall(
                                r'\b%s\b' % old_word, orig_string)
                            if not matches:
                                continue

                            print_str += (
                                "    Replaced %s Occurances of '%s' with '%s'\n"
                                % (len(matches), old_word, new_word))
                            modified_string = re.sub(r'\b%s\b' % old_word,
                                                     new_word, modified_string)

                    if not print_str:
                        continue

                    with open(out_p, "w") as out_f:
                        out_f.write(modified_string)

                    # Try to delete old file
                    try:
                        if os.path.isfile(backup_path):
                            # Try to delete old file
                            try:
                                os.remove(in_p)
                            except:
                                pass
                        else:
                            os.rename(in_p, backup_path)
                        # Try to rename the temp tag to the real tag name
                        try:
                            os.rename(out_p, in_p)
                        except:
                            pass
                    except:
                        print_str += (
                            "COULDNT RENAME THIS FILE TO BACKUP\n%s\n", in_p)

                elif self.mode.lower() == "locate":
                    with open(in_p, "r") as in_f:
                        in_string = in_f.read()

                        for word in self.word_map:
                            if search_flags:
                                match = re.findall(r'\b%s\b' % word, in_string,
                                                   search_flags)
                            else:
                                match = re.findall(r'\b%s\b' % word, in_string)

                            if match:
                                print_str += ("    %s Occurances of '%s'\n" %
                                              (len(match), word))

            except:
                print(in_p)
                print(format_exc())
                continue

            if print_str:
                print(in_p)
                print(print_str)

if __name__ == "__main__":
    program = python_word_locator_replacer()
    program.run(flags)
    print("Done")
    input()
