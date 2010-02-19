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
"""
import sys
import Image
import matplotlib
import numpy
import pyfits
import pygame
import RO.Wdg
import TUI.Version
import TUI.Models.TUIModel

WindowName = "STUI.About STUI"

def addWindow(tlSet):
    tlSet.createToplevel(
        name = WindowName,
        resizable = False,
        visible = False,
        wdgFunc = AboutWdg,
    )

def getVersionDict():
    tuiModel = TUI.Models.TUIModel.Model()
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
    return res

class AboutWdg(RO.Wdg.StrLabel):
    def __init__(self, master):
        versDict = getVersionDict()
        RO.Wdg.StrLabel.__init__(
            self,
            master = master,
            text = u"""APO SDSS Telescope User Interface
Version %(tui)s
by Russell Owen

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
