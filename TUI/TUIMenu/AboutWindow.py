#!/usr/bin/env python
"""About STUI window

2003-12-17 ROwen
2004-03-08 ROwen    Expanded the text and made it center-justified.
                    Moved the code to a separate class.
                    Added test code.
2004-05-18 ROwen    Stopped obtaining TUI model in addWindow; it was ignored.
                    Thus stopped importing TUI.Models.TUIModel in the main code.
2005-10-24 ROwen    Updated the acknowledgements to include WingIDE.
2006-06-01 ROwen    Updated the acknowledgements to include Fritz Stauffer.
2007-04-17 ROwen    Updated the acknowledgements to add "scripts".
2009-03-31 ROwen    Modified for tuiModel.root -> tuiModel.tkRoot.
2009-11-09 ROwen    Added pygame version; made matplotlib mandatory.
2010-02-18 ROwen    Fixed the test code.
2010-03-12 ROwen    Changed to use Models.getModel.
2010-03-18 ROwen    Added special file paths to the information.
                    Removed Wingware from the acknowledgements.
"""
import os.path
import sys
import Image
import matplotlib
import numpy
import pyfits
import pygame
import RO.Wdg
import TUI.Models
import TUI.Version

WindowName = "%s.About %s" % (TUI.Version.ApplicationName, TUI.Version.ApplicationName)

def addWindow(tlSet):
    tlSet.createToplevel(
        name = WindowName,
        resizable = False,
        visible = False,
        wdgFunc = AboutWdg,
    )

def getInfoDict():
    tuiModel = TUI.Models.getModel("tui")
    res = {}
    res["tui"] = TUI.Version.VersionStr
    res["python"] = sys.version.split()[0]
    res["tcltk"] = tuiModel.tkRoot.call("info", "patchlevel")
    res["matplotlib"] = matplotlib.__version__
    res["numpy"] = numpy.__version__
    # Image presently uses VERSION but may change to the standard so...
    res["pil"] = getattr(Image, "VERSION", getattr(Image, "__version__", "unknown"))
    res["pyfits"] = pyfits.__version__
    res["pygame"] = pygame.__version__
    res["specialFiles"] = getSpecialFileStr()
    return res

def getSpecialFileStr():
    """Return a string describing where the special files are
    """
    def strFromPath(filePath):
        if os.path.exists(filePath):
            return filePath
        return "%s (not found)" % (filePath,)
        
    outStrList = []
    for name, func in (
        ("Preferences", TUI.TUIPaths.getPrefsFile),
        ("Window Geom.", TUI.TUIPaths.getGeomFile),
    ):
        try:
            filePath = func()
            pathStr = strFromPath(filePath)
        except Exception, e:
            pathStr = "?: %s" % (RO.StringUtil.strFromException(e.message),)
        outStrList.append("%s: %s" % (name, pathStr))

    tuiAdditionsDirs = TUI.TUIPaths.getAddPaths(ifExists=False)
    for ind, filePath in enumerate(tuiAdditionsDirs):
        pathStr = strFromPath(filePath)
        outStrList.append("%sAdditions %d: %s" % (TUI.Version.ApplicationName, ind + 1, pathStr))

    outStrList.append("Error Log: %s" % (sys.stderr.name,))

    return "\n".join(outStrList)
    

class AboutWdg(RO.Wdg.StrLabel):
    def __init__(self, master):
        versDict = getInfoDict()
        RO.Wdg.StrLabel.__init__(
            self,
            master = master,
            text = u"""APO SDSS Telescope User Interface
Version %(tui)s
by Russell Owen

Special files:
%(specialFiles)s

Library versions:
Python: %(python)s
Tcl/Tk: %(tcltk)s
matplotlib: %(matplotlib)s
numpy: %(numpy)s
PIL: %(pil)s
pyfits: %(pyfits)s
pygame: %(pygame)s

With special thanks to:
- Craig Loomis for the APO hub
- Dan Long for the photograph used for the icon
- David Kirkby for infrastructure code
""" % (versDict),
            justify = "left",
            borderwidth = 10,
        )


if __name__ == "__main__":
    tuiModel = TUI.Models.TUIModel.Model(True)
    addWindow(tuiModel.tlSet)
    tuiModel.tlSet.makeVisible(WindowName)

    tuiModel.tkRoot.lower()

    tuiModel.reactor.run()
