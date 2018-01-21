import os
import traceback
try:
    # make sure the build directory is clean
    os.system("rmdir /S /Q dist")

    # build the wheel
    os.system("python setup.py sdist --formats=zip")

    # find the filename of the newly built module
    zip_filename = None
    for _, __, files in os.walk(os.path.join(os.curdir, "dist")):
        for filename in sorted(files):
            if filename.lower().endswith(".zip"):
                zip_filename = filename

    input("\nPress enter to upload module with twine.")

    # upload the module with twine
    os.system("twine upload %s" % os.path.join("dist", zip_filename))

except Exception:
    print(traceback.format_exc())

input("Finished...")
