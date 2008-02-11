#!/usr/bin/env python
"""Status and configuration for NICFPS.

History:
2003-09-02 ROwen
2004-11-15 ROwen    Modified to use RO.Wdg.Checkbutton's improved defaults.
2005-06-03 ROwen    Fixed some irregular indentation (tab-space).
2005-06-14 ROwen    Bug fix: _HelpPrefix was wrong.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2008-01-07 ROwen    Renamed Abort to X to shrink the window.
                    Improved the enabling and disabling of buttons.
"""
import Tkinter
import RO.MathUtil
import RO.KeyVariable
import RO.ScriptRunner
import RO.Wdg
import TUI.PlaySound
import TUI.TUIModel
import StatusConfigInputWdg

_HelpPrefix = "Instruments/NICFPS/NICFPSWin.html#"

class StatusConfigWdg (Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        """Create a new widget to configure the Dual Imaging Spectrograph
        """
        Tkinter.Frame.__init__(self, master, **kargs)

        tuiModel = TUI.TUIModel.getModel()

        self.tlSet = tuiModel.tlSet
        self.configShowing = False

        row = 0

        self.inputWdg = StatusConfigInputWdg.StatusConfigInputWdg(self)
        self.inputWdg.grid(row=row, column=0, sticky="w")
        row += 1
            
        # create and pack status monitor
        self.statusBar = RO.Wdg.StatusBar(
            master = self,
            helpURL = _HelpPrefix + "StatusBar",
            dispatcher = tuiModel.dispatcher,
            prefs = tuiModel.prefs,
            summaryLen = 20,
        )
        self.statusBar.grid(row=row, column=0, sticky="ew")
        row += 1

        # create and pack the buttons
        buttonFrame = Tkinter.Frame(self)
        
        bfCol=0

        self.exposeButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Expose...",
            command = self.showExpose,
            helpText = "open the NICFPS Expose window",
            helpURL = _HelpPrefix + "Expose",
        )
        self.exposeButton.grid(row=0, column=bfCol, sticky="w")
        bfCol += 1

        self.showConfigWdg = RO.Wdg.Checkbutton(
            master = buttonFrame,
            onvalue = "Hide Config",
            offvalue = "Show Config",
            callFunc = self._showConfigCallback,
            showValue = True,
            helpText = "show/hide config. controls",
            helpURL = _HelpPrefix + "ShowConfig",
        )
        self.showConfigWdg.grid(row=0, column=bfCol)
        buttonFrame.columnconfigure(bfCol, weight=1)
        bfCol += 1

        self.applyButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Apply",
            command = self.doApply,
            helpText = "apply the config. changes",
            helpURL = _HelpPrefix + "Apply",
        )
        self.applyButton.grid(row=0, column=bfCol)
        bfCol += 1
        
        self.cancelButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "X",
            command = self.doCancel,
            helpText = "Cancel remaining config. changes",
            helpURL = _HelpPrefix + "Current",
        )
        self.cancelButton.grid(row=0, column=bfCol)
        bfCol += 1

        self.currentButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Current",
            command = self.doCurrent,
            helpText = "Restore controls to current config.",
            helpURL = _HelpPrefix + "Current",
        )
        self.currentButton.grid(row=0, column=bfCol)
        bfCol += 1

        buttonFrame.grid(row=2, column=0, sticky="w")
        
        self.inputWdg.gridder.addShowHideWdg (
            StatusConfigInputWdg._ConfigCat,
            [self.applyButton, self.cancelButton, self.currentButton],
        )
        self.inputWdg.gridder.addShowHideControl (
            StatusConfigInputWdg._ConfigCat,
            self.showConfigWdg,
        )
        
        self.inputWdg.addCallback(self.enableButtons)

        def doConfig(sr, self=self):
            """Script run function to modify the configuration.
            
            This would be a class method if they could be generators.
            """
            cmdList = self.inputWdg.getStringList()
            
            for cmdStr in cmdList:
                yield sr.waitCmd(
                    actor = "nicfps",
                    cmdStr = cmdStr,
                )

        self.scriptRunner = RO.ScriptRunner.ScriptRunner(
            master = master,
            name = 'NICFPS Config',
            dispatcher = tuiModel.dispatcher,
            runFunc = doConfig,
            statusBar = self.statusBar,
            stateFunc = self.enableButtons,
        )
    
    def doApply(self, btn=None):
        self.scriptRunner.start()
    
    def doCancel(self, btn=None):
        if self.scriptRunner.isExecuting():
            self.scriptRunner.cancel()
        
    def doCurrent(self, btn=None):
        """Restore all input widgets to the current state.
        If no command executing, clear status bar.
        """
        self.inputWdg.restoreDefault()
        if not self.scriptRunner.isExecuting():
            self.statusBar.clear()

    def showExpose(self):
        """Show the expose window.
        """
        self.tlSet.makeVisible("None.NICFPS Expose")
    
    def _showConfigCallback(self, wdg=None):
        """Callback for show/hide config toggle.
        Restores defaults if config newly shown."""
        showConfig = self.showConfigWdg.getBool()
        restoreConfig = showConfig and not self.configShowing
        self.configShowing = showConfig
        if restoreConfig:
            self.inputWdg.restoreDefault()
    
    def enableButtons(self, *args, **kargs):
        if self.scriptRunner.isExecuting():
            self.applyButton.setEnable(False)
            self.cancelButton.setEnable(True)
            self.currentButton.setEnable(False)
        else:
            self.cancelButton.setEnable(False)
            doEnable = not self.inputWdg.inputCont.allDefault()
            self.currentButton.setEnable(doEnable)
            self.applyButton.setEnable(doEnable)


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
            print "Command error:", e
            return
        if cmdList:
            print "Commands:"
            for cmd in cmdList:
                print cmd
        else:
            print "(no commands)"
    
    butFrame = Tkinter.Frame()
    Tkinter.Button(butFrame, text="Cmds", command=printCmds).pack(side="left")
    Tkinter.Button(butFrame, text="Demo", command=TestData.animate).pack(side="left")
    butFrame.pack(side="top")
    root.mainloop()
