import pandoc
import os

doc = pandoc.Document()
with open('README.MD') as f:
    doc.markdown = f.read()
with open('README.RST','w+') as f:
    f.write(doc.rst)

register_str = "python setup.py register"
os.system(register_str + input(register_str))
os.remove('README.RST')

input("Finished...")
