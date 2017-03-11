import os

upload_str = "python setup.py sdist upload "
os.system(upload_str + input(upload_str))

input("Finished...")
