#!/usr/bin/env python
from distutils.core import setup
import sys
import os

if not hasattr(sys, 'version_info') or sys.version_info[0:2] < (2,3):
    raise SystemExit("Python 2.3 or later required for RO package.")

PkgName = "RO"
PkgDir = "RO"
UPSArg = "--ups"

roDir = os.path.join(PkgDir, PkgName)
sys.path.insert(0, PkgDir)
import Version

dataFiles = []
if UPSArg in sys.argv and "install" in sys.argv:
    tableName = "ups/%s.table" % (PkgName,)
    # create data file for the Fermi/Princeton UPS runtime loader
    sys.argv.pop(sys.argv.index(UPSArg))
    sitePkgDir = distutils.sysconfig.get_python_lib(prefix="")
    if not os.path.exists("ups"):
        os.mkdir("ups")
    upsfile = file(tableName, "w")
    try:
        upsfile.write("""File=Table
    Product=%s
    Group:
    Flavor=ANY
    Common:
    Action=setup
    proddir()
    setupenv()
    pathAppend(PATH, ${UPS_PROD_DIR}/bin)
    pathAppend(PYTHONPATH, ${UPS_PROD_DIR}/%s)
    End:
    """ % (PkgName, sitePkgDir,))
    finally:
        upsfile.close()
    dataFiles.append(["ups", [tableName]])

setup(
    name = PkgName,
    version = Version.__version__,
    description = "Utility package including astronomical transforms and Tkinter widgets",
    author = "Russell Owen",
    url = "http://www.astro.washington.edu/rowen/",
    package_dir = {'RO': PkgDir},
    packages = [PkgName],
    data_files = dataFiles,
    scripts = [],
)
