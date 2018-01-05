#!/usr/bin/env python
from os.path import dirname, join
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

curr_dir = dirname(__file__)

#               YYYY.MM.DD
release_date = "2018.01.04"
version = (0, 9, 0)  # DONT FORGET TO UPDATE THE VERSION IN app_window.py

try:
    try:
        long_desc = open(join(curr_dir, "readme.rst")).read()
    except Exception:
        long_desc = open(join(curr_dir, "readme.md")).read()
except Exception:
    long_desc = 'Could not read long description from readme.'

setup(
    name='hek_pool',
    #description='',
    long_description=long_desc,
    version='%s.%s.%s' % version,
    url='http://bitbucket.org/moses_of_egypt/hek_pool',
    author='Devin Bobadilla',
    author_email='MosesBobadilla@gmail.com',
    license='MIT',
    packages=[
        'hek_pool',
        ],
    package_data={
        '': ['*.txt', '*.md', '*.rst', '*.pyw'],
        'cmd_lists': ['*.txt'],
        },
    platforms=["POSIX", "Windows"],
    #keywords="",
    install_requires=['supyr_struct', 'binilla'],
    requires=['supyr_struct', 'binilla'],
    provides=['hek_pool'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        ],
    zip_safe=False,
    )
