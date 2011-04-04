#!/usr/bin/env python
"""Display APOGEE QuickLook actor

@todo Add a help URL

History:
2011-04-04 ROwen    Very preliminary. Needs current exposure data from APOGEE and controls
"""
import Tkinter
import RO.Wdg
import TUI.Models
import ExposureTableWdg
import SNRGraphWdg

class APOGEEWdg(Tkinter.Frame):
    def __init__(self, master, width=40, helpURL=None):
        """Create an exposure table
        """
        Tkinter.Frame.__init__(self, master)

        self.expLogWdg = ExposureTableWdg.ExposureTableWdg(master=self)
        self.expLogWdg.grid(row=0, column=0, sticky="ew")
        
        self.snrGraphWdg = SNRGraphWdg.SNRGraphWdg(master=self, width=4, height=4)
        self.snrGraphWdg.grid(row=1, column=0, sticky="news")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)



if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = APOGEEWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
