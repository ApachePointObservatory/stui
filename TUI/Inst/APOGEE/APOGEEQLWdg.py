#!/usr/bin/env python
"""Display APOGEE QuickLook actor

@todo Add a help URL

History:
2011-04-04 ROwen    Very preliminary. Needs current exposure data from APOGEE and controls
2011-04-24 ROwen    Added a help URL
"""
import Tkinter
import RO.Wdg
import TUI.Models
import ExposureTableWdg
import SNRGraphWdg

_Width = 4 # size of graph in inches
_Height = 4 # size of graph in inches
_HelpURL = "Instruments/APOGEEQuickLookWindow.html"

class APOGEEQLWdg(Tkinter.Frame):
    def __init__(self, master, width=40):
        """Create an exposure table
        """
        Tkinter.Frame.__init__(self, master)

        self.expLogWdg = ExposureTableWdg.ExposureTableWdg(master=self, helpURL=_HelpURL)
        self.expLogWdg.grid(row=0, column=0, sticky="ew")
        
        self.snrGraphWdg = SNRGraphWdg.SNRGraphWdg(master=self, width=_Width, height=_Height, helpURL=_HelpURL)
        self.snrGraphWdg.grid(row=1, column=0, sticky="news")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)



if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = APOGEEQLWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
