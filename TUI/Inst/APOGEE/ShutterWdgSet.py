#!/usr/bin/env python
"""APOGEE cold shutter control and status

History:
2011-08-30 ROwen
"""
import Tkinter
import RO.Constants
import RO.Wdg
import RO.TkUtil
import RO.StringUtil
import TUI.Models
import opscore.actor.keyvar
import TUI.Base.Wdg
import LimitParser

class ShutterWdgSet(object):
    _ShutterCat = "shutter"
    _NumLEDs = 4
    def __init__(self, gridder, statusBar, colSpan=3, helpURL=None):
        """Create a ShutterWdgSet for the APOGEE cold shutter and calibration LEDs

        Inputs:
        - gridder: an instance of RO.Wdg.Gridder;
            the widgets are gridded starting at the next row and default column
        - statusBar: status bar (to send commands)
        - colSpan: the number of columns to span
        - helpURL: path to an HTML help file or None

        Note: you may wish to call master.columnconfigure(n, weight=1)
        where n is the last column of this widget set
        so that the environment widget panel can fill available space
        without resizing the columns of other widgets.
        """
        self.statusBar = statusBar
        self.helpURL = helpURL

        self.gridder = gridder
        master = self.gridder._master

        self.model = TUI.Models.getModel("apogee")

        self.showHideWdg = RO.Wdg.Checkbutton(
            master = master,
            text = "Shutter",
            indicatoron = False,
            callFunc = self._doShowHide,
            helpText = "Show/hide cold shutter controls.",
            helpURL = helpURL,
        )

        self.summaryWdg = RO.Wdg.StrLabel(
            master = master,
            anchor = "w",
            helpText = "Shutter status",
            helpURL = helpURL,
        )
        gridder.gridWdg(self.showHideWdg, self.summaryWdg, sticky="w", colSpan=colSpan-1)

        # hidable frame showing the controls

        self.detailWdg = Tkinter.Frame(
            master = master,
            borderwidth = 1,
            relief = "solid",
        )
        self.gridder.gridWdg(False, self.detailWdg, colSpan=colSpan, sticky="w", cat=self._ShutterCat)
        detailGridder = RO.Wdg.Gridder(self.detailWdg, sticky="w")

        self.shutterWdg = _ShutterWdg(
            master = self.detailWdg,
            statusBar = self.statusBar,
            helpURL = helpURL,
        )
        detailGridder.gridWdg("Shutter", self.shutterWdg)

        self.ledWdg = _LEDWdg(
            master = self.detailWdg,
            statusBar = self.statusBar,
            numLEDs = self._NumLEDs,
            helpURL = helpURL,
        )
        detailGridder.gridWdg("LEDs", self.ledWdg)

        self.model = TUI.Models.getModel("apogee")
        self.model.shutterIndexer.addCallback(self._updSummary)
        self.model.shutterLimitSwitch.addCallback(self._updSummary)
        self.model.shutterLED.addCallback(self._updSummary)

        self.showHideWdg.addCallback(self._doShowHide, callNow = True)

    def _doShowHide(self, wdg=None):
        argDict = {
            self._ShutterCat: self.showHideWdg.getBool(),
        }
        self.gridder.showHideWdg(**argDict)

    def _updSummary(self, *dumArgs):
        """Update collimator summary label
        """
        severity = RO.Constants.sevNormal
        sumStr = "OK"
        isCurrent = self.model.shutterIndexer.isCurrent

        if self.model.shutterIndexer[0] == False:
            sumStr = "Off"
            severity = RO.Constants.sevError
        else:
            shutterStr, shutterSeverity = self.shutterWdg.getSummary()

            ledStr, ledSeverity = self.ledWdg.getSummary()

            sumStr = "%s; %s" % (shutterStr, ledStr)
            severity = max(shutterSeverity, ledSeverity)

        self.summaryWdg.set(sumStr, isCurrent=isCurrent, severity=severity)


class _ShutterWdg(Tkinter.Frame):
    """A widget to open or close the cold shutter
    """
    actor = "apogee"
    def __init__(self, master, statusBar, helpURL=None):
        Tkinter.Frame.__init__(self, master)
        self.statusBar = statusBar

        self.currCmd = None
        self.settingStatus = False

        self.shutterWdg = RO.Wdg.Checkbutton(
            master = self,
            onvalue = "Open",
            offvalue = "Closed",
            autoIsCurrent = True,
            showValue = True,
            callFunc = self.doShutter,
            helpText = "Open or close cold shutter",
            helpURL = helpURL,
        )
        self.shutterWdg.pack(side="left")

        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "X",
            callFunc = self.doCancel,
            helpText = "Cancel cold shutter command",
            helpURL = helpURL,
        )
        self.cancelBtn.pack(side="left")

        self.model = TUI.Models.getModel(self.actor)
        self.model.shutterLimitSwitch.addCallback(self._shutterLimitSwitchCallback)

    def isRunning(self):
        """Return True if running a command
        """
        return self.currCmd and not self.currCmd.isDone

    def doCancel(self, wdg=None):
        """Cancel the current command, if any
        """
        if self.isRunning():
            self.currCmd.abort()

    def doShutter(self, wdg=None):
        """Send a command to open or close the shutter
        """
        if self.settingStatus:
            return
        doOpen = self.shutterWdg.getBool()
        if doOpen:
            cmdStr = "shutter open"
        else:
            cmdStr = "shutter close"
        self.currCmd = opscore.actor.keyvar.CmdVar(
            actor = self.actor,
            cmdStr = cmdStr,
            callFunc = self._cmdCallback,
        )
        self.statusBar.doCmd(self.currCmd)
        self.enableButtons()

    def _cmdCallback(self, cmdVar):
        """Command callback

        If the command was aborted or failed then restore the current state.
        Update button state.
        """
        if cmdVar.didFail:
            self._shutterLimitSwitchCallback()
        self.enableButtons()

    def enableButtons(self, dumCmd=None):
        """Enable or disable widgets, as appropriate
        """
        isRunning = self.isRunning()
        self.shutterWdg.setEnable(not isRunning)
        self.cancelBtn.setEnable(isRunning)

    def getSummary(self):
        """Return a string and severity summarizing the current state
        """
        shutterLimits = tuple(self.model.shutterLimitSwitch[0:2])
        return {
            (False, False): ("?", RO.Constants.sevWarning),
            (False, True): ("Closed", RO.Constants.sevNormal),
            (True, False): ("Open", RO.Constants.sevNormal),
            (True, True): ("Bad", RO.Constants.sevError),
        }.get(shutterLimits, ("?", RO.Constants.sevError))

    def _shutterLimitSwitchCallback(self, keyVar=None):
        """shutterLimitSwitch keyword callback
        """
        keyVar = self.model.shutterLimitSwitch
        isCurrent = keyVar.isCurrent
        isOpen, isClosed = keyVar[0:2]

        try:
            self.settingStatus = True
            if None in (isOpen, isClosed):
                self.shutterWdg.setIsCurrent(isCurrent)
                return

            if isOpen and not isClosed:
                self.shutterWdg.setDefault(True)
                self.shutterWdg.set(True, isCurrent=isCurrent)
            elif isClosed and not isOpen:
                self.shutterWdg.setDefault(False)
                self.shutterWdg.set(False, isCurrent=isCurrent)
            else:
                self.shutterWdg.setIsCurrent(False)
        finally:
            self.settingStatus = False


class _LEDWdg(Tkinter.Frame):
    actor = "apogee"
    def __init__(self, master, statusBar, numLEDs, helpURL=None):
        Tkinter.Frame.__init__(self, master)
        self.statusBar = statusBar
        self.numLEDs = int(numLEDs)
        self.allOnMask = (1 << self.numLEDs) - 1

        self.currCmd = None
        self.settingStatus = False

        self.ledWdgSet = []
        for ledInd in range(self.numLEDs):
            ledWdg = RO.Wdg.Checkbutton(
                master = self,
                text = "",
                callFunc = self.toggleOne,
                autoIsCurrent = True,
                helpText = "Turn LED %d on or off" % (ledInd + 1,),
                helpURL = helpURL,
            )
            ledWdg.pack(side="left")
            self.ledWdgSet.append(ledWdg)

        self.allOffBtn = RO.Wdg.Button(
            master = self,
            text = "All Off",
            callFunc = self.turnAllOff,
            helpText = "Turn all LEDs off",
            helpURL = helpURL,
        )
        self.allOffBtn.pack(side="left")

        self.allOnBtn = RO.Wdg.Button(
            master = self,
            text = "All On",
            callFunc = self.turnAllOn,
            helpText = "Turn all LEDs on",
            helpURL = helpURL,
        )
        self.allOnBtn.pack(side="left")

        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "X",
            callFunc = self.doCancel,
            helpText = "Cancel LED command",
            helpURL = helpURL,
        )
        self.cancelBtn.pack(side="left")

        self.model = TUI.Models.getModel(self.actor)
        self.model.shutterLED.addCallback(self._shutterLEDCallback)

    def isRunning(self):
        """Return True if running a command
        """
        return self.currCmd and not self.currCmd.isDone

    def doCancel(self, wdg=None):
        """Cancel the current command, if any
        """
        if self.isRunning():
            self.currCmd.abort()

    def setLEDs(self, ledMask, setWdg):
        """Send a command to turn on and off the specified LEDs

        Inputs:
        - ledMask: a bit mask of which LEDs should be on (0=all off)
        - setWdg: it True then set the widgets;
            set True for buttons that control multiple widgets;
            set False if the user has toggled the button manually
        """
        cmdStr = "shutter ledControl=%d" % (ledMask,)
        self.currCmd = opscore.actor.keyvar.CmdVar(
            actor = self.actor,
            cmdStr = cmdStr,
            callFunc = self._cmdCallback,
        )
        self.statusBar.doCmd(self.currCmd)
        self.enableButtons()
        if setWdg:
            self._setLEDWdg(ledMask)

    def _cmdCallback(self, cmdVar):
        """Command callback

        If the command was aborted or failed then restore the current state.
        Update button state.
        """
        if cmdVar.didFail:
            self._shutterLEDCallback()
        self.enableButtons()

    def enableButtons(self, dumCmd=None):
        """Enable or disable widgets, as appropriate
        """
        isRunning = self.isRunning()
        self.cancelBtn.setEnable(isRunning)
        for wdg in self.ledWdgSet:
            wdg.setEnable(not isRunning)
        self.allOffBtn.setEnable(not isRunning)
        self.allOnBtn.setEnable(not isRunning)

    def turnAllOff(self, wdg=None):
        """Turn all LEDs off
        """
        self.setLEDs(0, setWdg=True)

    def turnAllOn(self, wdg=None):
        """Turn all LEDs on
        """
        self.setLEDs(self.allOnMask, setWdg=True)

    def toggleOne(self, wdg=None):
        """Toggle one LED on or off
        """
        if self.settingStatus:
            return

        ledMask = 0
        for ind, wdg in enumerate(self.ledWdgSet):
            if wdg.getBool():
                ledMask += 1 << ind
        self.setLEDs(ledMask, setWdg=False)

    def getSummary(self):
        """Return a summary string and associated severity
        """
        ledMask = self.model.shutterLED[0]
        if ledMask == None:
            return "LEDs ?", RO.Constants.sevWarning
        if ledMask == 0:
            return "LEDs all off", RO.Constants.sevNormal
        if ledMask == self.allOnMask:
            return "LEDs ALL ON", RO.Constants.sevWarning

        onList = [str(ind+1) for ind in range(self.numLEDs) if ledMask & (1 << ind) != 0]
        if len(onList) == 1:
            pfx = "LED"
        else:
            pfx = "LEDs"
        sumStr = "%s %s ON" % (pfx, " ".join(onList))
        return sumStr, RO.Constants.sevWarning

    def _shutterLEDCallback(self, keyVar=None):
        """shutterLED keyword callback
        """
        keyVar = self.model.shutterLED
        isCurrent = keyVar.isCurrent
        ledMask = keyVar[0]
        if ledMask == None:
            for wdg in self.ledWdgSet:
                wdg.setIsCurrent(isCurrent)
            return

        try:
            self.settingStatus = True

            for ind, wdg in enumerate(self.ledWdgSet):
                isOn = ledMask & (1 << ind) != 0
                wdg.setDefault(isOn)
                wdg.setBool(isOn, isCurrent=isCurrent)
        finally:
            self.settingStatus = False

    def _setLEDWdg(self, ledMask):
        """Set LED widgets to a particular state
        """
        try:
            self.settingStatus = True

            for ind, wdg in enumerate(self.ledWdgSet):
                isOn = ledMask & (1 << ind) != 0
                wdg.setBool(isOn)
        finally:
            self.settingStatus = False


if __name__ == "__main__":
    import TestData
    import TUI.Base.Wdg

    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot

    statusBar = TUI.Base.Wdg.StatusBar(root)

    testFrame = Tkinter.Frame(root)
    gridder = RO.Wdg.Gridder(testFrame)
    shutterWdgSet = ShutterWdgSet(gridder, statusBar)
    testFrame.pack(side="top", expand=True)
    testFrame.columnconfigure(2, weight=1)

    statusBar.pack(side="top", expand=True, fill="x")

    TestData.start()

    tuiModel.reactor.run()
