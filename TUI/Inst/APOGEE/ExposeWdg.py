#!/usr/bin/env python
"""APOGEE Exposure widget

To Do:
- Add support for the collimator

History:
2011-04-26 ROwen    Prerelease test code
2011-04-28 ROwen    Modified for new keyword dictionary.
"""
import Tkinter
import RO.Constants
import opscore.actor
import RO.Wdg
import TUI.Models

_EnvWidth = 6 # width of environment value columns

class ExposeWdg(Tkinter.Frame):
    EnvironCat = "environ"
    RunningExposureStates = set("Exposing READING INTEGRATING PROCESSING UTR".split())
    def __init__(self, master, helpURL=None):
        """Create a status widget
        """
        Tkinter.Frame.__init__(self, master)

        gridder = RO.Wdg.StatusConfigGridder(master=self, sticky="w")

        self.actor = "apogee"
        self.model = TUI.Models.getModel(self.actor)

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
            items = "Object Flat Dark Sky Calib LocalFlat SuperDark SuperFlat".split(),
            defValue = "Object",
            helpText = "Type of exposure",
            helpURL = helpURL,
            autoIsCurrent = True,
            trackDefault = True,
            width = 9
        )
        gridder.gridWdg("Exp Type", self.expTypeWdg)

        self.numReadsWdg = RO.Wdg.IntEntry(
            master = self,
            helpText = "Number of reads",
            defValue = 60,
            minValue = 1,
            helpURL = helpURL,
            autoIsCurrent = True,
            trackDefault = True,
            width = 4
        )
        gridder.gridWdg("Num Reads", self.numReadsWdg)

        self.statusBar = TUI.Base.Wdg.StatusBar(self)
        gridder.gridWdg(False, self.statusBar, sticky="ew", colSpan=3)
        self.grid_columnconfigure(2, weight=1)

        self.scriptRunner = opscore.actor.ScriptRunner(
            name = "Exposure command script",
            runFunc = self._exposureScriptRun,
            statusBar = self.statusBar,
            dispatcher = self.statusBar.dispatcher,
            stateFunc = self.enableButtons,
        )
        
        buttonFrame = Tkinter.Frame(self)
        self.exposeBtn = RO.Wdg.Button(
            master = buttonFrame,
            text = "Expose",
            command = self.scriptRunner.start,
            helpText = "Set dither and start exposure",
            helpURL = helpURL,
        )
        self.exposeBtn.pack(side="left")

        self.stopBtn = RO.Wdg.Button(
            master = buttonFrame,
            text = "Stop",
            command = self.stopExposure,
            helpText = "Stop current exposure",
            helpURL = helpURL,
        )
        self.stopBtn.pack(side="left")

        self.cancelBtn = RO.Wdg.Button(
            master = buttonFrame,
            text = "X",
            command = self.scriptRunner.cancel,
            helpText = "Cancel dither command",
            helpURL = helpURL,
        )
        self.cancelBtn.pack(side="left")
        gridder.gridWdg(False, buttonFrame, sticky="w", colSpan=3)

        master.columnconfigure(2, weight=1)

        self.model.ditherPosition.addCallback(self._ditherPositionCallback)
        self.model.ditherLimits.addCallback(self._ditherLimitsCallback)
        self.model.ditherNamedPositions.addCallback(self._ditherNamedPositionsCallback)
        self.model.exposureState.addCallback(self._exposureStateCallback)
        self.enableButtons()

        gridder.allGridded()

    def _ditherNameWdgCallback(self, wdg):
        """ditherNameWdg callback
        """
        name = wdg.getString()
        if name[0] in ("A", "B"):
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
            "Other",
        )
        self.ditherNameWdg.setItems(valList, checkCurrent=False, checkDef=False)
        self.ditherNameWdg.set(valList[currIndex])
        self._ditherNamedPositionsCallback(self.model.ditherPosition)

    def _exposureStateCallback(self, keyVar):
        """exposureStateCallback keyVar callback
        """
        if keyVar[0] == None:
            return
        self.expTypeWdg.setDefault(keyVar[1])
        self.numReadsWdg.setDefault(keyVar[2])
        self.enableButtons()

    def getDitherCmd(self):
        """Get the dither command, or None if current value is default
        """
        name = self.ditherNameWdg.getString()
        if name[0] in ("A", "B"):
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

    def stopExposure(self):
        """Stop exposure at end of current UTR read
        """
        stopCmdVar = opscore.actor.CmdVar(
            actor = self.actor,
            cmdStr = "expose stop",
        )
        self.statusBar.doCmd(stopCmdVar)

    def _exposureScriptRun(self, sr):
        """Run function for exposure script.
        
        Set dither if not defult, then start exposure.
        """
        ditherCmd = self.getDitherCmd()
        exposureCmd = self.getExposureCmd()
        if ditherCmd:
            yield sr.waitCmd(
                actor = self.actor,
                cmdStr = ditherCmd,
            )
        yield sr.waitCmd(
            actor = self.actor,
            cmdStr = exposureCmd,
        )
    
    def enableButtons(self, *dumArgs):
        isExposing = self.model.exposureState[0] in self.RunningExposureStates
        isRunning = self.scriptRunner.isExecuting
        self.exposeBtn.setEnable(not (isRunning or isExposing))
        self.stopBtn.setEnable(isExposing)
        self.cancelBtn.setEnable(isRunning)
        

if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = ExposeWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand=True)
    
    def printCmds():
        ditherCmd = self.getDitherCmd()
        if ditherCmd:
            print ditherCmd
        print self.getExposureCmd()

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")
    Tkinter.Button(text="Print Cmds", command=printCmds).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
