#!/usr/bin/env python
"""Install the RO package. Requires setuptools.

To use:
python setup.py install

Alternatively you can copy python/RO to site-packages
"""
from setuptools import setup, find_packages
import sys
import os

if not hasattr(sys, 'version_info') or sys.version_info[0:2] < (2,3):
    raise SystemExit("Python 2.3 or later required for RO package.")

PkgRoot = "python"
PkgName = "RO"
PkgDir = os.path.join(PkgRoot, PkgName)
sys.path.insert(0, PkgDir)
import Version
print "%s version %s" % (PkgName, Version.__version__)

setup(
    name = PkgName,
    version = Version.__version__,
    description = "Utility package including astronomical transforms and Tkinter widgets",
    author = "Russell Owen",
    url = "http://www.astro.washington.edu/rowen/",
    install_requires = ['numpy'],
    package_dir = {PkgName: PkgDir},
    packages = find_packages(PkgRoot),
    include_package_data = True,
    scripts = [],
)
