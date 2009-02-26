#!/usr/bin/env python
"""Widget to allow users to specify a target position and initiate a slew.

To Do:
- implement some way to tune up pointing on a nearby star;
  either don't do this if alt too high, or zero calib offset for the next slew
- fix this code so that one cannot hide proper motion information while any is present
- some way to set basic info to current info (e.g. pos, csys, date, rot)
- some way to save basic current info into the catalog or history menu

History:
2002-06-25 ROwen    First version with history.
2002-07-29 ROwen    Slew and Catalog buttons automatically enabled when a valid position
            is entered or modified. Enable button not displayed, as an experiment;
            if this succeeds, just ditch it. Catalog is disabled when pushed.
2002-08-02 ROwen    History menu shows full info, so different slews are always unique.
            Input fields neatened when Slew pushed; thus entries are neat in history menu.
            Focus reset when Slew pushed, so one can tab to start a new entry.
2002-08-08 ROwen    Added callFunc.
2002-11-25 ROwen    Added a preliminary command watcher; I still want a contextual pop-up
            menu for details and to position the widget better.
2002-11-26 ROwen    Added help for the controls (buttons and history menu).
2003-03-07 ROwen    Changed RO.Wdg.StringEntry to RO.Wdg.StrEntry.
2003-03-26 ROwen    Mod. to supply dispatcher to ObjPosWdg.
2003-04-04 ROwen    Mod. to use RO.Wdg.StatusBar instead of RO.CmdMonitor.
2003-04-21 ROwen    Renamed StatusWdg to StatusBar to avoid conflicts.
2003-06-12 ROwen    Added helpText strings.
2003-06-18 ROwen    Overhauled handling of enabling slew button;
                    show button when slew ends or after any change
                    (removed test if position OK, so instead of mysteriously
                    being disabled you get an error msg when you press Slew).
2003-10-21 ROwen    Bug fixes: was not adding items to the history menu;
                    was not disabling slew button after starting a slew;
                    was calling the callback function when starting a slew
                    with the wrong args and the call was not necessary at all.
2003-10-30 ROwen    Removed callFunc arg; now sets userModel.potentialTarget;
                    added addWindow.
2004-02-23 ROwen    Modified to play cmdDone/cmdFailed for commands.
2004-03-11 ROwen    Bug fix: mishandled the callback from the catalog menu.
2004-04-19 ROwen    Bug fix: commands with /PtErr would time out
                    because the time limit was not expecting an integration.
2004-05-18 ROwen    Stopped importing sys since it wasn't used.
                    Eliminated a redundant import in the test code.
2004-06-22 ROwen    Modified for RO.Keyvariable.KeyCommand->CmdVar
2004-09-24 ROwen    Modified to give the user a chance to stop typing
                    before updating the user model potential target.
2004-10-11 ROwen    Made callbacks much more sensible to improve performance.
2004-10-12 ROwen    Modified to take advantage of improvements in RO.InputCont.
2004-12-13 ROwen    Changed doEnable to setEnable to match RO.Wdg widgets.
2005-01-05 ROwen    Changed level to severity for RO.Wdg.StatusBar.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2006-04-14 ROwen    The Stop button now sends "track/stop" instead of "axis stop".
2007-08-09 ROwen    Changed Catalog callback function to InputCont.setStar.
2009-02-05 ROwen    Hid Stop button at request of APO; the button will be restored
                    when we have the new axis controllers.
"""
import Tkinter
import RO.KeyVariable
import RO.StringUtil
import RO.Wdg
import TUI.TUIModel
import TUI.PlaySound
import TUI.TCC.Catalog
import TUI.TCC.TelTarget
import TUI.TCC.UserModel
import InputWdg

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = "TCC.Slew",
        resizable = False,
        defGeom = "+0+280",
        wdgFunc = SlewWdg,
    )

_HelpPrefix = "Telescope/SlewWin/index.html#"

class SlewWdg (Tkinter.Frame):
    def __init__ (self,
        master=None,
    ):
        """creates a new widget for specifying object positions

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master=master)
        
        self.tuiModel = TUI.TUIModel.getModel()
        
        self.userModel = TUI.TCC.UserModel.getModel()
        
        # create input widgets, including internal callback
        self.inputWdg = InputWdg.InputWdg(
            master=self,
        )
        self.inputCont = self.inputWdg.inputCont
        
        self.enableInputCallback = True

        # register local callback function
        self.inputWdg.addCallback(self.inputChanged)

        # set up the status bar
        self.statusBar = RO.Wdg.StatusBar(
            master = self,
            dispatcher = self.tuiModel.dispatcher,
            prefs = self.tuiModel.prefs,
            playCmdSounds = True,
            helpURL = _HelpPrefix + "StatusBar",
        )

        # command buttons
        self.buttonFrame = Tkinter.Frame(master=self)
        self.slewButton = RO.Wdg.Button(
            master=self.buttonFrame,
            text="Slew",
            command=self.doSlew,
            helpText = "Start the slew",
            helpURL=_HelpPrefix + "SlewWdg",
        )

        self.slewButton.pack(side="left")
        self.enableButton = RO.Wdg.Button(
            master=self.buttonFrame,
            text="Enable",
            command=self.setEnable,
        )
# don't display the enable button and see if users actually miss it; if not, ditch it!
#       self.enableButton.pack(side="left")

        self.defaultButton = RO.Wdg.Button(
            master = self.buttonFrame,
            text = "Default",
            command = self.restoreDefault,
            helpText = "Clear entries and restore controls to their defaults",
            helpURL=_HelpPrefix + "DefaultWdg",
        )
        self.defaultButton.pack(side="left")

        self.catMenu = TUI.TCC.Catalog.CatalogMenuWdg(
            master = self.buttonFrame,
            callFunc = self.inputWdg.setStar,
            helpText = "Catalog of your objects",
            helpURL = _HelpPrefix + "CatalogWdg",
            statusBar = self.statusBar,
        )
        self.catMenu.pack(side="left")

        self.historyMenu = RO.Wdg.HistoryMenu(
            master = self.buttonFrame,
            callFunc = self.setObjData,
            removeAllDup = True,
            helpText = "A list of past slews; select one to set it up again",
            helpURL = _HelpPrefix + "HistoryWdg",
        )
        self.historyMenu.pack(side="left")

        self.stopButton = RO.Wdg.Button(
            master = self.buttonFrame,
            text = "Stop",
            command = self.doStop,
            helpText = "Stop the telescope",
            helpURL = _HelpPrefix + "StopWdg",
        )
#        self.stopButton.pack(side="left")
    
        # pack the principal frames     
        self.inputWdg.pack(side=Tkinter.TOP, anchor=Tkinter.NW)
        self.statusBar.pack(side=Tkinter.TOP, anchor=Tkinter.NW, expand="yes", fill="x")
        self.buttonFrame.pack(side=Tkinter.TOP, anchor=Tkinter.NW)

        # set up callback for changes to the potential target
        self.userModel.potentialTarget.addCallback(self._updTelPotential)

    def addCmdToHistory(self, cmdStr, valueDict):
        """Add the current object to the history menu.
        
        Note: I'd like a better format for the objects -- in RA, Dec
        and with the name first, but this crude code is a start.
        """
        name, pos1, pos2, csys = self.inputWdg.objPosWdg.getSummary()
        # find first / after /Name (if present)
        qualIndex = cmdStr.find("/Name")
        qualIndex = cmdStr.find("/", qualIndex+1)
        if qualIndex >= 0:
            cmdQuals = cmdStr[qualIndex:]
        else:
            cmdQuals = ""
        if name:
            summaryStr = "%r %s, %s %s %s" % (name, pos1, pos2, csys, cmdQuals)
        else:
            summaryStr = "%s, %s %s %s" % (pos1, pos2, csys, cmdQuals)
        self.historyMenu.addItem(summaryStr, valueDict)
    
    def doCommand(self, cmdStr, timeLim=10, timeLimKeyword=None, callFunc=None):
        """Execute a command."""
        cmdVar = RO.KeyVariable.CmdVar (
            actor = "tcc",
            cmdStr = cmdStr,
            timeLim = timeLim,
            timeLimKeyword=timeLimKeyword,
            isRefresh = False,
            callFunc = callFunc,
        )
        self.statusBar.doCmd(cmdVar)
        
    def setEnable(self):
        """Enable the slew button.
        Also toggle the Enable button's text appropriately.     
        """
        currText = self.enableButton["text"]
        doEnable = (currText == "Enable")
        self._slewEnable(doEnable)
    
    def setObjData(self, name, valueDict):
        """Set the currently displayed info from a value dictionary.
        Note: the name input is ignored, but is present because
        this function is used as a callback.
        """
#       print "SlewWdg.setObjData"
        self.inputWdg.setValueDict(valueDict)
    
    def doSlew(self):
        """Slew the telescope to the currently displayed position.
        """
        self.neatenDisplay()
        valueDict = self.inputWdg.getValueDict()
        self._slewEnable(False)
        try:
            cmdStr = self.inputWdg.getString()
        except ValueError, e:
            self.statusBar.setMsg(
                "Rejected: %s" % (e,),
                severity = RO.Constants.sevError,
                isTemp = True,
            )
            TUI.PlaySound.cmdFailed()
            return

        def slewEnableShim(*args, **kargs):
            self._slewEnable(True)
        
        if "/pter" in cmdStr.lower():
            # leave time for a guider integration
            timeLim = 60
        else:
            timeLim = 15

        self.doCommand(cmdStr,
            timeLim=timeLim,
            timeLimKeyword="SlewDuration",
            callFunc = slewEnableShim,
        )
        self.addCmdToHistory(cmdStr, valueDict)
    
    def doStop(self):
        """Halt the telescope.
        """
        self.doCommand("track/stop")

    def _slewEnable(self, doEnable=True):
        """Set the state of the Slew button and possibly others
        """
        if doEnable:
            self.slewButton["state"] = "normal"
            self.enableButton["text"] = "Disable"
        else:
            self.slewButton["state"] = "disabled"
            self.enableButton["text"] = "Enable"
    
    def _updTelPotential(self, telPotential):
        """Called when some other code updates telPotential.
        """
#       print "SlewWdg._updTelPotential"
        try:
            self.enableInputCallback = False
            telPotential = self.userModel.potentialTarget.get()
            if telPotential:
                valueDict = telPotential.getValueDict()
                self.inputWdg.setValueDict(valueDict)
        finally:
            self.enableInputCallback = True

    def inputChanged(self, inputCont=None):
        """Called whenever the user changes any input.
        """
#       print "SlewWdg.inputChanged"
        self._slewEnable(True)

        if not self.enableInputCallback:
            return
        
        try:
            self.inputWdg.getString()
        except ValueError:
            telPotential = None
        else:
            valueDict = self.inputWdg.getValueDict()
#           print "valueDict=", valueDict
            telPotential = TUI.TCC.TelTarget.TelTarget(valueDict)

        self.userModel.potentialTarget.set(telPotential)

    def neatenDisplay(self):
        """Makes sure all input fields are neatened up.
        """
        self.inputWdg.neatenDisplay()
        self.focus_set()

    def restoreDefault(self):
        self.inputWdg.restoreDefault()

if __name__ == "__main__":
    import TestData

    root = RO.Wdg.PythonTk()
    root.resizable(width=0, height=0)
    
    tuiModel = TUI.TUIModel.getModel(True)
    TestData.setModel(tuiModel)
    
    def printDict():
        print testFrame.inputWdg.getValueDict()

    testFrame = SlewWdg(master=root)
    testFrame.pack()
    
    debugFrame = Tkinter.Frame(root)
    Tkinter.Label(debugFrame, text="Debug:").pack(side="left", anchor="w")
    Tkinter.Button(debugFrame, text="PrintValueDict", command=printDict).pack(side="left", anchor="w")
    debugFrame.pack(anchor="w")
    Tkinter.Button(debugFrame, text="RotAvail", command=TestData.setDIS).pack(side="left", anchor="w")
    Tkinter.Button(debugFrame, text="RotNotAvail", command=TestData.setEchelle).pack(side="left", anchor="w")

    TestData.setDIS()

    root.mainloop()
