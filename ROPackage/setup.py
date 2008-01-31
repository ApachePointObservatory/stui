#!/usr/bin/env python
"""Install the RO package. Requires setuptools.

To use:
python setup.py install

Alternatively you can copy python/RO to site-packages
"""

long_description = """\
Includes:

* Alg: various useful algorithms including OrderedDict (a dictionary that remembers the order in which items are added) and MultiDict (a dictionary whose values are lists).
* Astro: astronomical calculations including conversion between various coordinate systems and time functions. Note that this library is based on an extensive body of work by Pat Wallace and as such requires payment for commercial use.
* Comm: network communications based on tcl sockets (to mesh nicely with Tkinter applications).
* DS9: interface to SAO's ds9 image viewer. Images can be loaded from numpy arrays, binary files or fits files.
* OS: additions to the standard "os" module (especially os.path). Includes getPrefsDir (find the standard preferences directory on Mac, Windows or unix), findFiles (recursively search for files whose names match specified patterns and don't match others), and removeDupPaths (remove duplicates from a list of paths).
* Prefs: a complete Tkinter-based preferences implementation.
* ScriptRunner: execute user-written scripts that wait for something to happen without halting the main Tkinter event loop. Based on generators.
* SeqUtil: sequence utilities, such as isSequence (returns True if the argument is a sequence), asList (converts one item or a sequence of items to a list), etc.
* StringUtil: string utilities including conversion of sexagesimal (dd:mm:ss and hh:mm:ss) strings to and from numbers.
* Wdg: extensions of the standard Tkinter widgets and useful additional widgets. The widgets support hot help strings (automatically displayed in an RO.Wdg.StatusBar), linking to html help and a contextual menu.
"""

classifiers = """\
Development Status :: 5 - Production/Stable
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
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
    description = "Collection of utilities including general algorithms, astronomical transformations and Tkinter widgets",
    long_description = long_description,
    author = "Russell Owen",
    author_email = "rowen@u.washington.edu",
    url = "http://www.astro.washington.edu/rowen/",
    license = "GPL except RO.Astro which has more restrictions for commercial use",
    classifiers = filter(None, classifiers.split("\n")),
    platforms = ["MacOS X", "unix", "Windows"],
    install_requires = ['numpy'],
    package_dir = {PkgName: PkgDir},
    packages = find_packages(PkgRoot),
    include_package_data = True,
    scripts = [],
)
