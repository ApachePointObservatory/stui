#!/usr/bin/env python
"""Status/config window for enclosure

History:
2004-12-23 ROwen
2005-10-13 ROwen    Removed extra import of RO.Wdg.
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
        wdgFunc = EnclosureWdg,
        visible = (__name__ == "__main__"),
    )

class EnclosureWdg(Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        """Create a new widget to configure the enclosure
        """
        Tkinter.Frame.__init__(self, master=master, **kargs)
        
        tuiModel = TUI.TUIModel.getModel()

        self.statusBar = RO.Wdg.StatusBar(
            master = self,
            helpURL = _HelpURL,
            dispatcher = tuiModel.dispatcher,
            prefs = tuiModel.prefs,
            summaryLen = 10,
        )

        self.inputWdg = StatusCommandWdg.StatusCommandWdg(
            master = self,
            statusBar = self.statusBar,
        )

        row = 0

        self.inputWdg.grid(row=row, column=0, sticky="news")
        row += 1
            
        self.statusBar.grid(row=row, column=0, sticky="ew")
        row += 1

if __name__ == "__main__":
    root = RO.Wdg.PythonTk()
    root.resizable(width=0, height=0)

    import TestData
    
    tlSet = TestData.tuiModel.tlSet

    addWindow(tlSet)
    
    TestData.run()
    
    root.mainloop()
