#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-05-04 ROwen
2011-05-05 ROwen    Grid the collimator widgets in the status widget to improve widget alignment.
2011-05-09 ROwen    Added commented-out QuickLook button.
2011-05-16 SBeland  Added calbox support.
2011-08-16 ROwen    Added a state tracker.
2011-08-31 ROwen    Added cold shutter support.
"""
import Tkinter
import opscore.actor
import RO.Constants
import RO.Wdg
import TUI.Models
import CollWdgSet
import CalBoxWdgSet
import ExposeWdg
import ShutterWdgSet
import StatusWdg
import FPIShutterWdg

_EnvWidth = 6 # width of environment value columns
_HelpURL = "Instruments/APOGEEWindow.html"

class APOGEEWdg(Tkinter.Frame):
    RunningExposureStates = set("Exposing READING INTEGRATING PROCESSING UTR".split())
    def __init__(self, master):
        """Create the APOGEE status/control/exposure widget
        """
        Tkinter.Frame.__init__(self, master)

        self.actor = "apogee"
        self.model = TUI.Models.getModel(self.actor)
        self.tuiModel = TUI.Models.getModel("tui")
        self._stateTracker = RO.Wdg.StateTracker(logFunc = self.tuiModel.logFunc)

        self.statusBar = TUI.Base.Wdg.StatusBar(self)

        self.scriptRunner = opscore.actor.ScriptRunner(
            name = "Exposure command script",
            runFunc = self._exposureScriptRun,
            statusBar = self.statusBar,
            dispatcher = self.statusBar.dispatcher,
            stateFunc = self.enableButtons,
        )

        row = 0

        self.statusWdg = StatusWdg.StatusWdg(self, helpURL = _HelpURL)
        self._stateTracker.trackWdg("telemetry", self.statusWdg.telemetryWdgSet.showHideWdg)
        self.statusWdg.grid(row=row, column=0, sticky="w")
        row += 1

        self.shutterWdgSet = ShutterWdgSet.ShutterWdgSet(
            gridder = self.statusWdg.gridder,
            statusBar = self.statusBar,
            helpURL = _HelpURL,
        )
        self._stateTracker.trackWdg("shutter", self.shutterWdgSet.showHideWdg)

        self.calboxWdgSet = CalBoxWdgSet.CalBoxWdgSet(
            gridder = self.statusWdg.gridder,
            statusBar = self.statusBar,
            helpURL = _HelpURL,
        )
        self._stateTracker.trackWdg("calbox", self.calboxWdgSet.showHideWdg)

        self.collWdgSet = CollWdgSet.CollWdgSet(
            gridder = self.statusWdg.gridder,
            statusBar = self.statusBar,
            helpURL = _HelpURL,
        )
        self._stateTracker.trackWdg("collimator", self.collWdgSet.showHideWdg)

        self.FPIshutterWdgSet = FPIShutterWdg.FPIShutterWdg(
            gridder = self.statusWdg.gridder,
            statusBar = self.statusBar,
            helpURL = _HelpURL,
        )

        row += 1

        self.exposeWdg = ExposeWdg.ExposeWdg(self, helpURL=_HelpURL)
        self.exposeWdg.grid(row=row, column=0, columnspan=3, sticky="ew")
        row += 1

        self.statusBar.grid(row=row, column=0, sticky="ew")
        row += 1

        buttonFrame = Tkinter.Frame(self)
        self.exposeBtn = RO.Wdg.Button(
            master = buttonFrame,
            text = "Expose",
            command = self.scriptRunner.start,
            helpText = "Set dither and start exposure",
            helpURL = _HelpURL,
        )
        self.exposeBtn.pack(side="left")

        self.stopBtn = RO.Wdg.Button(
            master = buttonFrame,
            text = "Stop",
            command = self.stopExposure,
            helpText = "Stop current exposure",
            helpURL = _HelpURL,
        )
        self.stopBtn.pack(side="left")

        self.cancelBtn = RO.Wdg.Button(
            master = buttonFrame,
            text = "X",
            command = self.scriptRunner.cancel,
            helpText = "Cancel dither command",
            helpURL = _HelpURL,
        )
        self.cancelBtn.pack(side="left")

        buttonFrame.grid(row=row, column=0, sticky="ew")
        row += 1

        self.model.exposureState.addCallback(self.enableButtons)

        self.enableButtons()

    def _doQuickLook(self, *dumArgs):
        """Show QuickLook window
        """
        import TUI.Inst.APOGEEQL.APOGEEQLWindow
        self.tuiModel.tlSet.makeVisible(TUI.Inst.APOGEEQL.APOGEEQLWindow.WindowName)

    def getStateTracker(self):
        """Return the state tracker"""
        return self._stateTracker

    def enableButtons(self, *dumArgs):
        """Enable or disable widgets as appropriate
        """
        isExposing = self.model.exposureState[0] in self.RunningExposureStates
        isRunning = self.scriptRunner.isExecuting
        self.exposeBtn.setEnable(not (isRunning or isExposing))
        self.stopBtn.setEnable(isExposing)
        self.cancelBtn.setEnable(isRunning)

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
        ditherCmd = self.exposeWdg.getDitherCmd()
        exposureCmd = self.exposeWdg.getExposureCmd()
        if ditherCmd:
            yield sr.waitCmd(
                actor = self.actor,
                cmdStr = ditherCmd,
            )
        yield sr.waitCmd(
            actor = self.actor,
            cmdStr = exposureCmd,
        )


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
