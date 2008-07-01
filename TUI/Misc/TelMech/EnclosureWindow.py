#!/usr/bin/env python
"""Status/config window for enclosure

History:
2004-12-23 ROwen
2005-10-13 ROwen    Removed extra import of RO.Wdg.
2007-06-22 ROwen    Added Eyelids.
2007-07-27 ROwen    Modified to pay command-completed sounds.
2008-07-01 ROwen    Fixed test code to make window visible.
                    Modified for new StatusCommandWdg argument list.
"""
import Tkinter
import RO.Wdg
import StatusCommandWdg
import TUI.TUIModel

_HelpURL = "Misc/EnclosureWin.html"

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "Misc.Enclosure",
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = StatusCommandWdg.StatusCommandWdg,
        visible = (__name__ == "__main__"),
    )


if __name__ == "__main__":
    root = RO.Wdg.PythonTk()
    root.resizable(width=0, height=0)

    import TestData
    
    tlSet = TestData.tuiModel.tlSet

    addWindow(tlSet)
    
    tlSet.makeVisible("Misc.Enclosure")
    
    TestData.run()
    
    root.mainloop()
