#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-04-04 ROwen    Prerelease test code
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models
import StatusWdg
import ExposeWdg

_EnvWidth = 6 # width of environment value columns
_HelpURL = "Instruments/APOGEEWindow.html"

class APOGEEWdg(Tkinter.Frame):
    EnvironCat = "environ"
    def __init__(self, master):
        """Create the APOGEE status/control/exposure widget
        """
        Tkinter.Frame.__init__(self, master)
        
        self.statusWdg = StatusWdg.StatusWdg(self, helpURL = _HelpURL)
        self.statusWdg.grid(row=0, column=0)

        self.exposeWdg = ExposeWdg.ExposeWdg(self, helpURL=_HelpURL)
        self.exposeWdg.grid(row=1, column=0, sticky="ew")

if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = APOGEEWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand=True)

    Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
