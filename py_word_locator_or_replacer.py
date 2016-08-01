import os
import re
from traceback import format_exc

curr_dir = os.path.abspath(os.curdir).replace('/', '\\')
word_map = {'set_data':0}
flags = None
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
            print(in_p)
            try:
                if self.mode.lower() == "replace":
                    with open(in_p, "r") as in_f, open(out_p, "w") as out_f:
                        modified_string = in_f.read()

                        for old_word in self.word_map:
                            new_word = self.word_map[old_word]
                            modified_string = re.sub(r'\b%s\b' % old_word,
                                                     new_word, modified_string)

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
                        print("COULDNT RENAME THIS FILE TO BACKUP\n", in_p)

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
                                print("    %s Occurances of:%s" %
                                      (len(match), word))

            except:
                print(in_p)
                print(format_exc())

if __name__ == "__main__":
    program = python_word_locator_replacer()
    program.run(flags)
    print("Done")
    input()
