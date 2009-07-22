#!/usr/bin/env python
"""Status/config window for enclosure

History:
2009-04-03 ROwen
"""
import Tkinter
import RO.Wdg
import MCPWdg
import TUI.Models.TUIModel

_HelpURL = "Misc.MCPWin.html"

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "Misc.MCP",
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = MCPWdg.MCPWdg,
        visible = (__name__ == "__main__"),
    )


if __name__ == "__main__":
    root = RO.Wdg.PythonTk()
    root.resizable(width=0, height=0)

    import TestData
    
    tlSet = TestData.tuiModel.tlSet

    addWindow(tlSet)
    
    tlSet.makeVisible("Misc.MCP")
    
    TestData.run()
    
    root.mainloop()
