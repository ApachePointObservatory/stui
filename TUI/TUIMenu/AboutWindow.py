#!/usr/bin/env python
"""About TUI window

2003-12-17 ROwen
2004-03-08 ROwen    Expanded the text and made it center-justified.
                    Moved the code to a separate class.
                    Added test code.
2004-05-18 ROwen    Stopped obtaining TUI model in addWindow; it was ignored.
                    Thus stopped importing TUI.TUIModel in the main code.
2005-10-24 ROwen    Updated the acknowledgements to include WingIDE.
2006-06-01 ROwen    Updated the acknowledgements to include Fritz Stauffer.
2007-04-17 ROwen    Updated the acknowledgements to add "scripts".
2009-03-31 ROwen    Modified for tuiModel.root -> tuiModel.tkRoot.
"""
import sys
import Image
try:
    import matplotlib
except ImportError:
    pass 
import numpy
import pyfits
import RO.Wdg
import TUI.Version
import TUI.TUIModel

def addWindow(tlSet):
    tlSet.createToplevel(
        name = "TUI.About TUI",
        resizable = False,
        visible = False,
        wdgFunc = AboutWdg,
    )

def getVersionDict():
    tuiModel = TUI.TUIModel.Model()
    res = {}
    res["tui"] = TUI.Version.VersionStr
    res["python"] = sys.version.split()[0]
    res["tcltk"] = tuiModel.tkRoot.call("info", "patchlevel")
    try:
        res["matplotlib"] = matplotlib.__version__
    except NameError:
        res["matplotlib"] = "not installed"
    res["numpy"] = numpy.__version__
    # Image presently uses VERSION but may change to the standard so...
    res["pil"] = getattr(Image, "VERSION", getattr(Image, "__version__", "unknown"))
    res["pyfits"] = pyfits.__version__
    return res

class AboutWdg(RO.Wdg.StrLabel):
    def __init__(self, master):
        versDict = getVersionDict()
        RO.Wdg.StrLabel.__init__(
            self,
            master = master,
            text = u"""APO 3.5m Telescope User Interface
Version %(tui)s
by Russell Owen

Library versions:
Python: %(python)s
Tcl/Tk: %(tcltk)s
matplotlib: %(matplotlib)s
numpy: %(numpy)s
PIL: %(pil)s
pyfits: %(pyfits)s

With special thanks to:
- Craig Loomis and Fritz Stauffer for the APO hub
- Bob Loewenstein for Remark
- Dan Long for the photograph used for the icon
- APO observing specialists and users
  for suggestions, scripts and bug reports
- Wingware for free use of WingIDE
""" % (versDict),
            justify = "left",
            borderwidth = 10,
        )


if __name__ == "__main__":
    import TUI.TUIModel
    root = RO.Wdg.PythonTk()

    tm = TUI.TUIModel.Model(True)
    addWindow(tm.tlSet)
    tm.tlSet.makeVisible('TUI.About TUI')

    root.lower()

    root.mainloop()
