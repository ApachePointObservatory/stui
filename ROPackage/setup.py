#!/usr/bin/env python
from distutils.core import setup
import sys
import os

if not hasattr(sys, 'version_info') or sys.version_info[0:2] < (2,3):
    raise SystemExit("Python 2.3 or later required for RO package.")

PkgName = "RO"
PkgDir = "RO"
UPSArg = "--ups"

Debug = True

roDir = os.path.join(PkgDir, PkgName)
sys.path.insert(0, PkgDir)
import Version

def getPackages():
    packages = [PkgName]
    dataList = []
    for dirPath, dirNames, fileNames in os.walk(PkgDir):
        if ".svn" in dirNames:
            dirNames.remove(".svn")
        dirName = os.path.basename(dirPath)
        
        tryInit = os.path.join(dirPath, "__init__.py")
        if os.path.exists(os.path.join(dirPath, "__init__.py")):
            pkgName = dirPath.replace("/", ".")
            packages.append(pkgName)
        else:
            # package data
            # need to strip initial component of dir
            dataPath = dirPath.split("/", 1)[1]
            dataList += [os.path.join(dataPath, fileName) for fileName in fileNames
                if not fileName.startswith(".")]
            
    return packages, {PkgName: dataList}
packages, package_data = getPackages()

if Debug:
    print "packages:"
    for pkg in packages:
        print "    %s" % (pkg,)
    print "package_data:"
    for pkgName, dataList in package_data.iteritems():
        print "    %s:" % (pkgName,)
        for data in dataList:
            print "       ", data

dataFiles = []
if UPSArg in sys.argv and "install" in sys.argv:
    # create data file for the Fermi/Princeton UPS runtime loader
    upsFileName = "ups/%s.table" % (PkgName,)
    sys.argv.pop(sys.argv.index(UPSArg))
    sitePkgDir = distutils.sysconfig.get_python_lib(prefix="")
    if not os.path.exists("ups"):
        os.mkdir("ups")
    upsFile = file(upsFileName, "w")
    try:
        upsFile.write("""File=Table
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
        upsFile.close()
    dataFiles.append(["ups", [upsFileName]])

setup(
    name = PkgName,
    version = Version.__version__,
    description = "Utility package including astronomical transforms and Tkinter widgets",
    author = "Russell Owen",
    url = "http://www.astro.washington.edu/rowen/",
    package_dir = {'RO': PkgDir},
    packages = packages,
    package_data = package_data,
#    data_files = dataFiles,
    scripts = [],
)
