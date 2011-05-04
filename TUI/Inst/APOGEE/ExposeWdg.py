#!/usr/bin/env python
"""APOGEE Exposure widget

History:
2011-04-26 ROwen    Prerelease test code
2011-04-28 ROwen    Modified for new keyword dictionary.
2011-05-03 ROwen    Added estimated exposure time.
2011-05-04 ROwen    Removed controls, script runner and status bar to make it easy to use in a script.
                    Add support for new keyword exposureTypeList.
                    Renamed Dither option Other to Any; this should be less confusing
                    when the pixel value happens to be the position of A or B.
"""
import Tkinter
import RO.Constants
import opscore.actor
import RO.Wdg
import TUI.Models
import CollWdgSet

_EnvWidth = 6 # width of environment value columns

class ExposeWdg(Tkinter.Frame):
    def __init__(self,
        master,
        helpURL=None,
    ):
        """Create a status widget
        """
        Tkinter.Frame.__init__(self, master)

        gridder = RO.Wdg.Gridder(master=self, sticky="w")
        self.gridder = gridder

        self.actor = "apogee"
        self.model = TUI.Models.getModel(self.actor)

        self.ditherLabelWdg = RO.Wdg.StrLabel(
            master = self,
            text = "Dither",
        )
        self.ditherFrame = Tkinter.Frame(self)

        self.ditherNameWdg = RO.Wdg.OptionMenu(
            master = self.ditherFrame,
            items = ("A", "B", "Any"),
            autoIsCurrent = True,
            trackDefault = True,
            callFunc = self._ditherNameWdgCallback,
        )
        self.ditherNameWdg.grid(row=0, column=0)
        self.ditherPosWdg = RO.Wdg.FloatEntry(
            master = self.ditherFrame,
            helpText = "Desired dither position (A, B or # of pixels)",
            helpURL = helpURL,
            autoIsCurrent = True,
            trackDefault = True,
            width = 4
        )
        self.ditherPosWdg.grid(row=0, column=1)
        self.ditherUnitsWdg = RO.Wdg.StrLabel(
            master = self.ditherFrame,
            text = "pixels",
        )
        self.ditherUnitsWdg.grid(row=0, column=2)
        self.ditherFrame.grid(row=0, column=1)
        gridder.gridWdg(self.ditherLabelWdg, self.ditherFrame, colSpan=2)
        
        self.expTypeWdg = RO.Wdg.OptionMenu(
            master = self,
            items = ("Object", "Dark"), # initial list to use until exposureTypeList is seen
            defValue = "Object",
            helpText = "Type of exposure",
            helpURL = helpURL,
            autoIsCurrent = True,
            trackDefault = True,
            width = 9
        )
        gridder.gridWdg("Exp Type", self.expTypeWdg)

        numReadsFrame = Tkinter.Frame(self)
        self.numReadsWdg = RO.Wdg.IntEntry(
            master = numReadsFrame,
            helpText = "Number of reads",
            defValue = 60,
            minValue = 1,
            helpURL = helpURL,
            callFunc = self._numReadsWdgCallback,
            autoIsCurrent = True,
            trackDefault = True,
            width = 4
        )
        self.numReadsWdg.pack(side="left")
        self.estReadTimeWdg = RO.Wdg.StrLabel(
            master = numReadsFrame,
            helpText = "Estimated exposure time",
            helpURL = helpURL,
        )
        self.estReadTimeWdg.pack(side="left")
        gridder.gridWdg("Num Reads", numReadsFrame)

        self.model.ditherPosition.addCallback(self._ditherPositionCallback)
        self.model.ditherLimits.addCallback(self._ditherLimitsCallback)
        self.model.ditherNamedPositions.addCallback(self._ditherNamedPositionsCallback)
        self.model.exposureTypeList.addCallback(self._exposureTypeListCallback)
        self.model.exposureState.addCallback(self._exposureStateCallback)
        self.model.utrReadTime.addCallback(self._numReadsWdgCallback)

        gridder.allGridded()

    def _numReadsWdgCallback(self, *dumArgs):
        """numReadsWdg callback; set estReadTimeWdg to match
        """
        numReads = self.numReadsWdg.getNumOrNone()
        if numReads == None:
            self.estReadTimeWdg.set("", isCurrent=True)
            return

        timePerRead = self.model.utrReadTime[0]
        if timePerRead == None:
            self.estReadTimeWdg.set(" ? sec", isCurrent=False)
            return

        estReadTime = numReads * timePerRead
        self.estReadTimeWdg.set(" %0.0f sec" % (estReadTime,), isCurrent=self.model.utrReadTime.isCurrent)
        
    def _ditherNameWdgCallback(self, wdg):
        """ditherNameWdg callback
        """
        name = wdg.getString()
        if name[1] == " ":
            self.ditherPosWdg.grid_remove()
            self.ditherUnitsWdg.grid_remove()
        else:
            self.ditherPosWdg.grid()
            self.ditherUnitsWdg.grid()

    def _ditherPositionCallback(self, keyVar):
        """ditherPosition keyVar callback
        """
        self.ditherPosWdg.setDefault(keyVar[0], isCurrent=keyVar.isCurrent)
        ditherInd = {"A": 0, "B": 1}.get(keyVar[1], 2)
        self.ditherNameWdg.setDefault(self.ditherNameWdg._items[ditherInd], isCurrent=keyVar.isCurrent)

    def _ditherLimitsCallback(self, keyVar):
        """ditherLimits keyVar callback
        """
        if None in keyVar:
            return
        self.ditherPosWdg.setRange(float(keyVar[0]), float(keyVar[1]))

    def _ditherNamedPositionsCallback(self, keyVar):
        """ditherNamedPositions keyVar callback
        """
        if None in keyVar:
            return
        currIndex = self.ditherNameWdg.getIndex()
        valList = (
            "A  %0.1f pixels" % (keyVar[0],),
            "B  %0.1f pixels" % (keyVar[1],),
            "Any",
        )
        self.ditherNameWdg.setItems(valList, checkCurrent=False, checkDef=False)
        self.ditherNameWdg.set(valList[currIndex])
        self._ditherNamedPositionsCallback(self.model.ditherPosition)

    def _exposureTypeListCallback(self, keyVar):
        """exposureTypeListCallback keyVar callback
        """
        if keyVar[0] == None:
            return
        self.expTypeWdg.setItems(keyVar[:])

    def _exposureStateCallback(self, keyVar):
        """exposureStateCallback keyVar callback
        """
        if keyVar[0] == None:
            return
        self.expTypeWdg.setDefault(keyVar[1])
        self.numReadsWdg.setDefault(keyVar[2])

    def getDitherCmd(self):
        """Get the dither command, or None if current value is default
        """
        name = self.ditherNameWdg.getString()
        if name[1] == " ":
            if self.ditherNameWdg.isDefault():
                return None
            return "dither namedpos=%s" % (name[0],)

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
    
    def showDither(self, doShow):
        """Show or hide all the dither widgets. Useful for scripts.
        """
        if doShow:
            self.ditherLabelWdg.grid()
            self.ditherFrame.grid()
        else:
            self.ditherLabelWdg.grid_remove()
            self.ditherFrame.grid_remove()


if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = ExposeWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand=True)
    statusBar = TUI.Base.Wdg.StatusBar(root)
    statusBar.pack(side="top", fill="x", expand=True)
    
    def printCmds():
        ditherCmd = testFrame.getDitherCmd()
        if ditherCmd:
            print ditherCmd
        print testFrame.getExposureCmd()

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")
    Tkinter.Button(text="Print Cmds", command=printCmds).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
