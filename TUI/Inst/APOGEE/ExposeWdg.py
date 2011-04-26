#!/usr/bin/env python
"""APOGEE Exposure widget

TO DO:
- Set dither limits based on keyword data (after confirming it's valid and in pixels)
- Set dither name default based on current value, after it's output
- Set number of reads default based on whatever keyword is appropriate
- Set exposure type based on whatever keyword is appropriate

History:
2011-04-04 ROwen    Prerelease test code
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models

_EnvWidth = 6 # width of environment value columns

class ExposeWdg(Tkinter.Frame):
    EnvironCat = "environ"
    def __init__(self, master, helpURL=None):
        """Create a status widget
        """
        Tkinter.Frame.__init__(self, master)

        gridder = RO.Wdg.StatusConfigGridder(master=self, sticky="w")

        self.model = TUI.Models.getModel("apogee")
        self.tuiModel = TUI.Models.getModel("tui")

        ditherFrame = Tkinter.Frame(self)

        self.ditherNameWdg = RO.Wdg.OptionMenu(
            master = ditherFrame,
            items = ("A", "B", "Other"),
            autoIsCurrent = True,
            trackDefault = True,
            callFunc = self._ditherNameWdgCallback,
        )
        self.ditherNameWdg.grid(row=0, column=0)
        self.ditherPosWdg = RO.Wdg.FloatEntry(
            master = ditherFrame,
            helpText = "Desired dither position (A, B or # of pixels)",
            helpURL = helpURL,
            autoIsCurrent = True,
            trackDefault = True,
            width = 4
        )
        self.ditherPosWdg.grid(row=0, column=1)
        self.ditherUnitsWdg = RO.Wdg.StrLabel(
            master = ditherFrame,
            text = "pixels",
        )
        self.ditherUnitsWdg.grid(row=0, column=2)
        ditherFrame.grid(row=0, column=1)
        gridder.gridWdg("Dither", ditherFrame, colSpan=2)
        
        self.expTypeWdg = RO.Wdg.OptionMenu(
            master = self,
            items = "object flat dark sky calib localflat superdark superflat".split(),
            defValue = "object",
            helpText = "Type of exposure",
            helpURL = helpURL,
            autoIsCurrent = True,
            trackDefault = True,
            width = 4
        )
        gridder.gridWdg("Exp Type", self.expTypeWdg)

        self.numReadsWdg = RO.Wdg.IntEntry(
            master = self,
            helpText = "Number of reads",
            defValue = 60,
            helpURL = helpURL,
            autoIsCurrent = True,
            trackDefault = True,
            width = 4
        )
        gridder.gridWdg("Num Reads", self.numReadsWdg)

        self.statusBar = TUI.Base.Wdg.StatusBar(self)
        gridder.gridWdg(False, self.statusBar, sticky="ew", colSpan=3)


        self.model.ditherPosition.addCallback(self._ditherPositionCallback)

        master.columnconfigure(2, weight=1)

        gridder.allGridded()

    def _ditherNameWdgCallback(self, wdg):
        """ditherNameWdg callback
        """
        name = wdg.getString()
        if name in ("A", "B"):
            self.ditherPosWdg.grid_remove()
            self.ditherUnitsWdg.grid_remove()
        else:
            self.ditherPosWdg.grid()
            self.ditherUnitsWdg.grid()

    def _ditherPositionCallback(self, keyVar):
        """ditherPosition keyVar callback
        """
        self.ditherPosWdg.setDefault(keyVar[0])

    def getDitherCmd(self):
        """Get the dither command, or None if current value is default
        """
        name = self.ditherNameWdg.getString()
        if name in ("A", "B"):
            if self.ditherNameWdg.isDefault():
                return None
            return "dither namedpos=%s" % (name,)

        if self.ditherPosWdg.isDefault():
            return None
        pos = self.ditherPosWdg.getNumOrNone()
        if pos == None:
            return None
        return "dither pixelpos=%0.2f" % (pos,)
    
    def getExposureCmd(self):
        """Get the exposure command
        """
        numReads = self.numReadsWdg.getNum()
        if not numReads:
            raise RuntimeError("Must specify number of reads")
        expType = self.expTypeWdg.getString()
        return "expose nreads=%d; object=%s" % (numReads, expType)

    def getCmdList(self):
        """Get dither and exposure commands
        """
        ditherCmd = self.getDitherCmd()
        exposureCmd = self.getExposureCmd()
        if ditherCmd:
            return [ditherCmd, exposureCmd]
        else:
            return [exposureCmd]

if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = ExposeWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand=True)
    
    def printCmds():
        cmdList = testFrame.getCmdList()
        for cmd in cmdList:
            print cmd

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")
    Tkinter.Button(text="Print Cmds", command=printCmds).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
