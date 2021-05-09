#!/usr/bin/env python
"""Display APOGEE QuickLook actor

@todo Add a help URL

History:
2011-04-04 ROwen    Very preliminary. Needs current exposure data from APOGEE and controls
2011-04-24 ROwen    Added a help URL
2011-05-06 ROwen    Added table for current exposure.
"""
import Tkinter
import RO.Wdg
import TUI.Base.Wdg
import TUI.Models
import ExposureTableWdg
import ReadStatusWdg
import SNRGraphWdg

_Width = 4 # size of graph in inches
_Height = 4 # size of graph in inches
_HelpURL = "Instruments/APOGEEQuickLookWindow.html"

class APOGEEQLWdg(Tkinter.Frame):
    def __init__(self, master, width=40):
        """Create an exposure table
        """
        Tkinter.Frame.__init__(self, master)

        row = 0
        self.readStatusWdg = ReadStatusWdg.ReadStatusWdg(master=self, helpURL=_HelpURL)
        self.readStatusWdg.grid(row=row, column=0, sticky="nw")

        sepFrame = Tkinter.Frame(self, bg="gray")
        sepFrame.grid(row=row, column=1, padx=2, sticky="ns")

        self.expLogWdg = ExposureTableWdg.ExposureTableWdg(master=self, helpURL=_HelpURL)
        self.expLogWdg.grid(row=row, column=2, sticky="news")
        row += 1

        self.statusBar = TUI.Base.Wdg.StatusBar(master=self)
        self.statusBar.grid(row=row, column=0, columnspan=3, sticky="ew")
        row += 1

        # self.snrGraphWdg = SNRGraphWdg.SNRGraphWdg(master=self, width=_Width, height=_Height, helpURL=_HelpURL)
        # self.snrGraphWdg.grid(row=row, column=0, columnspan=3, sticky="news")
        self.grid_rowconfigure(row, weight=1)
        self.grid_columnconfigure(2, weight=1)
        row += 1


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = APOGEEQLWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
