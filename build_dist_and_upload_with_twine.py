import os
import traceback
try:
    # make sure the build directory is clean
    os.system("rmdir /S /Q build")
    os.system("rmdir /S /Q dist")

    # build the egg
    os.system("python setup.py sdist bdist_egg")

    print('\n')

    # build the wheel
    os.system("python setup.py sdist bdist_wheel")

    # find the filename of the newly built module
    egg_filename = None
    wheel_filename = None
    for _, __, files in os.walk(os.path.join(os.curdir, "dist")):
        for filename in sorted(files):
            if filename.lower().endswith(".egg"):
                egg_filename = filename
            elif filename.lower().endswith(".wheel"):
                wheel_filename = filename

    input("\nPress enter to upload module with twine.")

    # upload the module with twine
    os.system("twine upload dist\\%s" % egg_filename)
    # os.system("twine upload dist\\%s" % wheel_filename)

except Exception:
    print(traceback.format_exc())

input("Finished...")
