#!/usr/bin/env python
"""Status/config window for enclosure

History:
2009-04-03 ROwen
2010-03-12 ROwen    Removed unused import.
"""
import tkinter
import RO.Wdg
from . import MCPWdg

_HelpURL = "Misc.MCPWin.html"
_WindowTitle = "Misc.MCP"

def addWindow(tlSet):
    tlSet.createToplevel (
        name = _WindowTitle,
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = MCPWdg.MCPWdg,
        visible = (__name__ == "__main__"),
    )


if __name__ == "__main__":
    import tkinter
    from . import TestData
    
    tlSet = TestData.tuiModel.tlSet
    addWindow(tlSet)
    tlSet.makeVisible(_WindowTitle)
    tkinter.Button(TestData.tuiModel.tkRoot, text="Demo", command=TestData.animate).pack()
    TestData.start()
    TestData.tuiModel.reactor.run()
