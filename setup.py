#!/usr/bin/env python
from os.path import dirname, join
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

curr_dir = dirname(__file__)

import hek_pool


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
    version='%s.%s.%s' % hek_pool.__version__,
    url='http://bitbucket.org/moses_of_egypt/hek_pool',
    author='Devin Bobadilla',
    author_email='MosesBobadilla@gmail.com',
    license='MIT',
    packages=[
        'hek_pool',
        ],
    package_data={
        '': ['*.txt', '*.md', '*.rst', '*.pyw', '*.ico', '*.png'],
        'hek_pool': ['cmd_lists/*.txt', 'ogg_v1.1.2_dll_fix.zip'],
        },
    platforms=["POSIX", "Windows"],
    #keywords="",
    install_requires=['supyr_struct', 'threadsafe_tkinter'],
    requires=['supyr_struct', 'threadsafe_tkinter'],
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
