#!/usr/bin/env python
from __future__ import generators
"""Status for Dual Imaging Spectrograph.

To Do:
- make it so changing the turret position doesn't change the window width
- make choice of turret not change spacing of x,y or blue/red items
- add a display to ccd window that shows the current size of the window
  (this will be easier once the widget container stuff is in place)  

History:
2003-03-10 ROwen    Preliminary attempt. Lots to do.
2003-03-11 ROwen    Added mask, filter and turret menus (after overhauling RO.Wdg.OptionMenu)
2003-03-14 ROwen    Added command list retrieval; wired up the lambda widgets correctly.
2003-03-17 ROwen    Improved layout and units labelling; mod. for new keywords.
2003-03-24 ROwen    Modified to use Model.getModel().
2003-30-27 ROwen    Renamed Configure button to Apply.
2003-04-03 ROwen    If command cannot be formatted, print msg to statusBar;
                    improved cancel and clear logic.
2003-04-14 ROwen    New try with ! instead of checkboxes.
2003-04-21 ROwen    Renamed StatusWdg to StatusBar to avoid conflicts.
2003-04-24 ROwen    Added help links to the buttons.
2003-06-09 ROwen    Removed most args from StatusConfiWdg.__init__.
2003-08-11 ROwen    Modified to use enhanced Gridder.
2003-11-17 ROwen    Modified to use TUI.PlaySound.
2003-12-09 ROwen    Use new showValue flag in RO.Wdg.Checkbutton.
2004-06-22 ROwen    Modified for RO.Keyvariable.KeyCommand->CmdVar
2004-09-14 ROwen    Tweaked _cmdCallback to make pychecker happier.
2004-11-15 ROwen    Modified to use RO.Wdg.Checkbutton's improved defaults.
2005-01-05 ROwen    Changed level to severity for RO.Wdg.StatusBar.
2005-04-22 ROwen    Fixed one case of inconsistent indentation.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
import TUI.PlaySound
import TUI.TUIModel
import StatusConfigInputWdg

_HelpPrefix = "Instruments/DIS/DISWin.html#"

class StatusConfigWdg (Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        """Create a new widget to configure the Dual Imaging Spectrograph
        """
        Tkinter.Frame.__init__(self, master, **kargs)

        tuiModel = TUI.TUIModel.getModel()
        self.tlSet = tuiModel.tlSet
        self.cmdList = []
        self.configShowing = False

        self.inputWdg = StatusConfigInputWdg.StatusConfigInputWdg(self)
        self.inputWdg.grid(row=0, column=0)
    
        # create and pack command monitor
        self.statusBar = RO.Wdg.StatusBar(
            master = self,
            helpURL = _HelpPrefix + "StatusBar",
            dispatcher = tuiModel.dispatcher,
            prefs = tuiModel.prefs,
            summaryLen = 10,
        )
        self.statusBar.grid(row=1, column=0, sticky="ew")

        # create and pack the buttons
        buttonFrame = Tkinter.Frame(self)
        
        self.exposeButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Expose...",
            command = self.showExpose,
            helpText = "open the DIS Expose window",
            helpURL = _HelpPrefix + "Expose",
        )
        self.exposeButton.grid(row=0, column=0, sticky="w")

        buttonFrame.columnconfigure(2, weight=1)

        self.showConfigWdg = RO.Wdg.Checkbutton(
            master = buttonFrame,
            onvalue = "Hide Config",
            offvalue = "Show Config",
            callFunc = self._showConfigCallback,
            showValue = True,
            helpText = "show/hide config. controls",
            helpURL = _HelpPrefix + "ShowConfig",
        )
        self.showConfigWdg.grid(row=0, column=2)

        self.applyButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Apply",
            command = self.doApply,
            helpText = "apply the config. changes",
            helpURL = _HelpPrefix + "Apply",
        )
        self.applyButton.grid(row=0, column=3)

        self.cancelButton = RO.Wdg.Button(
            master = buttonFrame,
            text="Cancel",
            command = self.doCancel,
            helpText = "stop pending config. changes",
            helpURL = _HelpPrefix + "Cancel",
        )
        self.cancelButton.grid(row=0, column=4)

        spacerFrame = Tkinter.Frame(buttonFrame, width=5)
        spacerFrame.grid(row=0, column=5)

        self.currentButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Current",
            command = self.doCurrent,
            helpText = "reset controls to current DIS config.",
            helpURL = _HelpPrefix + "Current",
        )
        self.currentButton.grid(row=0, column=6)

        buttonFrame.grid(row=2, column=0, sticky="ew")
        
        self.inputWdg.gridder.addShowHideWdg (
            StatusConfigInputWdg._ConfigCat,
            [self.applyButton, self.cancelButton, spacerFrame, self.currentButton],
        )
        self.inputWdg.gridder.addShowHideControl (
            StatusConfigInputWdg._ConfigCat,
            self.showConfigWdg,
        )

        self._setApplyState(True)
    
    def doApply(self):
        if self.cmdList:
            raise RuntimeError, "cannot issue new commands until the old ones are done"
        try:
            cmdList = self.inputWdg.getStringList()
        except ValueError, e:
            self.statusBar.setMsg(
                e,
                severity = RO.Constants.sevError,
                isTemp = True,
            )
            return
        self.cmdList = cmdList
        self._doNextCmd()
    
    def doCancel(self):
        """Flush the remaining commands (if any),
        clear the status window and re-enable the apply button.
        """
        if self.cmdList:
            # commands are outstanding; only cancel temporary messages
            self.statusBar.clearTempMsg()
        else:
            self.statusBar.clear()
        self.cmdList = []
        self._setApplyState(True)
        
    def doCurrent(self):
        """Disable all input widgets and the status window;
        if no commands are queued then enable the apply button.
        """
        self.inputWdg.restoreDefault()
        if self.cmdList:
            # commands are outstanding; only cancel temporary messages
            self.statusBar.clearTempMsg()
        else:
            self.statusBar.clear()
    
    def _showConfigCallback(self, wdg=None):
        """Callback for show/hide config toggle.
        Restores defaults if config newly shown."""
        showConfig = self.showConfigWdg.getBool()
        restoreConfig = showConfig and not self.configShowing
        self.configShowing = showConfig
        if restoreConfig:
            self.inputWdg.restoreDefault()

    def showExpose(self):
        self.tlSet.makeVisible("None.DIS Expose")
    
    def _cmdCallback(self, msgType, msgDict=None, cmdVar=None):
        """Callback for the currently executing command
        """
        if msgType == ":":
            # current command finished, start the next one (if any)
            self._doNextCmd()
        elif msgType in ("f!"):
            # current command failed; give up on the others
            self.cmdList = []
            self._setApplyState(True)
            TUI.PlaySound.cmdFailed()
    
    def _doNextCmd(self):
        if self.cmdList:
            cmd = self.cmdList.pop(0)
            self._setApplyState(False)
        else:
            # all commands executed
            self._setApplyState(True)
            TUI.PlaySound.cmdDone()
            return
        # print "_doNextCmd: dispatching command %r" % cmd

        if cmd.startswith("motors"):
            timeLim = 80
        else:
            timeLim = 10

        cmdVar = RO.KeyVariable.CmdVar(
            cmdStr = cmd,
            actor = "dis",
            timeLim = timeLim,
            callFunc = self._cmdCallback,
        )
        self.statusBar.doCmd(cmdVar)

    def _setApplyState(self, doEnable):
        """Sets the state of the apply and cancel buttons
        (which are always opposite each other)
        """
        if doEnable:
            self.applyButton["state"] = "normal"
            self.cancelButton["state"] = "disabled"
        else:
            self.applyButton["state"] = "disabled"
            self.cancelButton["state"] = "normal"


if __name__ == "__main__":
    root = RO.Wdg.PythonTk()

    import TestData
        
    testFrame = StatusConfigWdg (root)
    testFrame.pack(side="top")
    
    TestData.dispatch()
    testFrame.doCurrent()
    
    def printCmds():
        try:
            cmdList = testFrame.inputWdg.getStringList()
        except ValueError, e:
            print "Invalid command:", e
            return
        print "Commands:"
        for cmd in cmdList:
            print cmd
    
    butFrame = Tkinter.Frame()
    Tkinter.Button(butFrame, text="Cmds", command=printCmds).pack(side="left")
    Tkinter.Button(butFrame, text="Demo", command=TestData.animate).pack(side="left")
    butFrame.pack(side="top")
    root.mainloop()
