#!/usr/bin/python
"""genLoadStdModules.py.

Create the python module TUI.LoadStdModules
and function loadAll()
to load all of TUI's standard window modules.

This speeds startup (over searching for modules
at startup) and potentialy simplifies distribution
as prebuilt packages by allowing TUI's python code
to be run from a zip file.

On the down side, one must remember to run this file
and thus regenerate LoadStdModules whenever the list
of TUI's standard windows modules changes.

History:
2005-08-01 ROwen
2005-08-08 ROwen    Modified to use TUI.WindowModuleUtil
2005-09-22 ROwen    Modified to not use TUI.TUIPaths.
"""
import os
import TUI
import TUI.WindowModuleUtil

# get location to look for standard windows
tuiPath = os.path.dirname(TUI.__file__)

modNames = list(TUI.WindowModuleUtil.findWindowsModules(
    path = tuiPath,
    isPackage = True,
    loadFirst="TUIMenu",
))
modFilePath = os.path.join(tuiPath, "LoadStdModules.py")
modFile = file(modFilePath, "w")
try:
    modFile.write("import TUI.TUIModel\n")
    for modName in modNames:
        modFile.write("import %s\n" % modName)

    modFile.write("""
def loadAll():
    tuiModel = TUI.TUIModel.Model()
    tlSet = tuiModel.tlSet
""")
    for modName in modNames:
        modFile.write("    %s.addWindow(tlSet)\n" % modName)
    
finally:
    modFile.close()