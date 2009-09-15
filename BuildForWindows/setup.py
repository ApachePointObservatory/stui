"""Build TUI for Windows

  python buildtui.py py2exe

Hints on including matplotlib came from the following
(search for libgdk_pixbuf-2.0-0.dll):
<http://sourceforge.net/mailarchive/forum.php?forum_id=40690&max_rows=25&style=nested&viewmonth=200510>

History:
2005-10-07 ROwen
2006-02-28 ROwen    Modified to include matplotlib (note: matplotlib requires
                    a lot of work; you can't just rely on auto-detection).
                    Added getDataFiles.
                    Moved the win32com.shell workaround here from RO.OS.getWinDirs.
                    TUI no longer opens a console window (now that it writes a log file).
2006-03-09 ROwen    Modified to call the executable TUI.exe.
                    Got rid of the console window.
                    Expected python and snack in slightly unusual locations,
                    but now looks in C:\Python24 and C:\Python24\tcl\snacklib.
                    Bug fix: required RO and TUI to be on the python path.
2006-12-14 ROwen    Added wxmsw26uh_vc.dll to dll_excludes to make it compatible
                    with matplotlib 0.87.7 (which includes WxAgg support).
                    Note: to actually use WxAgg support one would have to
                    include that dll, not exclude it.
                    Added TUI to the included packages because py2exe
                    was not including TUI.Base.BaseFocusScript.
2007-01-16 ROwen    Added email.Utils to required modules (needed for Python 2.5).
2007-01-30 ROwen    Overhauled to work with repackaged RO; links are not
                    followed on Windows so I used a different method.
                    Corrected inclusion of the email package from 2007-01-16.
2007-04-24 ROwen    Changed commented-out import of numarray to numpy;
                    whether it builds using numpy is untested.
2007-07-10 ROwen    Fixed for Python 2.5 (was referring to Python 2.4 for the snack directory).
2008-02-21 ROwen    Modified to use direct RO path instead of relying on the symlink
                    (which was not working when trying to build 1.4.5).
"""
from distutils.core import setup
import os
import sys
import matplotlib
import py2exe

# The following code is necessary for py2exe to find win32com.shell.
# Solution from <http://starship.python.net/crew/theller/moin.cgi/WinShell>
import win32com
import py2exe.mf as modulefinder
for pth in win32com.__path__[1:]:
    modulefinder.AddPackagePath("win32com", pth)
for extra in ["win32com.shell"]:
    __import__(extra)
    m = sys.modules[extra]
    for pth in m.__path__[1:]:
        modulefinder.AddPackagePath(extra, pth)

tuiRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
roRoot = os.path.join(tuiRoot, "ROPackage", "python")
sys.path = [tuiRoot, roRoot] + sys.path
import TUI.Version
mainProg = os.path.join(tuiRoot, "runtui.py")

NDataFilesToPrint = 5 # number of data files to print, per directory

def addDataFiles(dataFiles, fromDir, toSubDir=None, inclHiddenDirs=False):
    """Find data files and format data for the data_files argument of setup.
    
    In/Out:
    - dataFiles: a list to which is appended zero or more of these elements:
        [subDir, list of paths to resource files]
    
    Inputs:
    - fromDir: path to root directory of existing resource files
    - toSubDir: relative path to resources in package;
        if omitted then the final dir of fromDir is used
    - inclHiddenDirs: if True, the contents of directories whose names
        start with "." are included
    
    Returns a list of the following elements:
    """
    if not os.path.isdir(fromDir):
        raise RuntimeError("Cannot find directory %r" % (fromDir,))
    lenFromDir = len(fromDir)
    if toSubDir == None:
        toSubDir = os.path.split(fromDir)[1]
    for (dirPath, dirNames, fileNames) in os.walk(fromDir):
        if not inclHiddenDirs:
            numNames = len(dirNames)
            for ii in range(numNames-1, -1, -1):
                if dirNames[ii].startswith("."):
                    del(dirNames[ii])
        if not dirPath.startswith(fromDir):
            raise RuntimeError("Cannot deal with %r files; %s does not start with %r" %\
                (resBase, dirPath, fromDir))
        toPath = os.path.join(toSubDir, dirPath[lenFromDir+1:])
        filePaths = [os.path.join(dirPath, fileName) for fileName in fileNames]
        dataFiles.append((toPath, filePaths))

# Add resources
dataFiles = []
# TUI resources
for resBase in ("Help", "Scripts", "Sounds"):
    toSubDir = os.path.join("TUI", resBase)
    fromDir = os.path.join(tuiRoot, toSubDir)
    addDataFiles(dataFiles, fromDir, toSubDir)
# RO resources
for resBase in ("Bitmaps",):
    toSubDir = os.path.join("RO", resBase)
    fromDir = os.path.join(roRoot, toSubDir)
    addDataFiles(dataFiles, fromDir, toSubDir)
 
# Add tcl snack libraries
pythonDir = os.path.dirname(sys.executable)
snackSubDir = "tcl\\snack2.2"
snackDir = os.path.join(pythonDir, snackSubDir)
addDataFiles(dataFiles, snackDir, snackSubDir)

# Add matplotlib's data files.
matplotlibDataPath = matplotlib.get_data_path()
addDataFiles(dataFiles, matplotlibDataPath, "matplotlibdata")

if NDataFilesToPrint > 0:
    print "\nData files:"
    for pathInfo in dataFiles:
        print pathInfo[0]
        nFiles = len(pathInfo[1])
        for resPath in pathInfo[1][0:NDataFilesToPrint]:
            print "  ", resPath
        if nFiles > NDataFilesToPrint:
            print "  ...and %d more" % (nFiles - NDataFilesToPrint)

versDate = TUI.Version.VersionStr
appVers = versDate.split()[0]
distDir = "TUI_%s_Windows" % (appVers,)

inclModules = [
#    "email.Utils", # needed for Python 2.5.0
]
# packages to include recursively
inclPackages = [
    "TUI",
    "RO",
    "matplotlib",
    "dateutil", # required by matplotlib
    "pytz", # required by matplotlib
#    "matplotlib.backends",
#    "matplotlib.numerix",
#    "encodings",
#    "numpy",
#    "email", # needed for Python 2.5
]

setup(
    options = dict(
        py2exe = dict (
            dll_excludes = [
                # the following are for matplotlib 0.87:
                "libgdk_pixbuf-2.0-0.dll", 
                "libgobject-2.0-0.dll",
                "libgdk-win32-2.0-0.dll",
                "wxmsw26uh_vc.dll",
            ],
            excludes = [ # modules to exclude
                "_gtkagg",
                "_wxagg",
            ],
            #includes = inclModules,
            packages = inclPackages,
        )
    ),
    windows=[ # windows= for no console, console= for console
        dict(
            script = mainProg,
            dest_base = "TUI",
            icon_resources = [(1, "STUI.ico")],
        ),
    ],
    data_files = dataFiles,
)

# rename dist to final directory name
os.rename("dist", distDir)
