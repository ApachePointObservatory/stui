#!/usr/bin/env python
"""Status for Echelle Spectrograph.

Note: a Cancel button is implemented (due to copying DIS)
but is not shown because it's not likely to be useful
(the only slow command is move: and it's sent last.)

History:
2003-12-09 ROwen
2004-09-14 ROwen    Tweaked _cmdCallback to make pychecker happier.
2004-11-15 ROwen    Modified to use RO.Wdg.Checkbutton's improved defaults.
2005-05-24 ROwen    Fixed anomalous indentation (<tab><space>-><tab>)
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2008-02-11 ROwen    Use ScriptRunner to sequence the configuration commands (like NICFPS).
                    Properly enable and disable the buttons (like NICFPS).
                    Renamed the Cancel button to X (like NICFPS).
"""
import Tkinter
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
import RO.ScriptRunner
import TUI.TUIModel
import TUI.PlaySound
import StatusConfigInputWdg

_HelpPrefix = "Instruments/Echelle/EchelleWin.html#"

class StatusConfigWdg (Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)

        tuiModel = TUI.TUIModel.getModel()
        self.tlSet = tuiModel.tlSet
        self.configShowing = False

        self.inputWdg = StatusConfigInputWdg.StatusConfigInputWdg(self)
        self.inputWdg.grid(row=0, column=0, sticky="w")
    
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
            helpText = "open the Echelle Expose window",
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
            text="X",
            command = self.doCancel,
            helpText = "stop pending config. changes",
            helpURL = _HelpPrefix + "Cancel",
        )
        self.cancelButton.grid(row=0, column=4)

        self.currentButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Current",
            command = self.doCurrent,
            helpText = "reset controls to current Echelle config.",
            helpURL = _HelpPrefix + "Current",
        )
        self.currentButton.grid(row=0, column=6)

        buttonFrame.grid(row=2, column=0, sticky="ew")
        
        self.inputWdg.gridder.addShowHideWdg (
            StatusConfigInputWdg._ConfigCat,
            [self.applyButton, self.cancelButton, self.currentButton],
        )
        self.inputWdg.gridder.addShowHideControl (
            StatusConfigInputWdg._ConfigCat,
            self.showConfigWdg,
        )

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
        
        self.inputWdg.addCallback(self.enableButtons)
    
    def doApply(self, btn=None):
        """Apply desired configuration changes"""
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
    
    def enableButtons(self, *args, **kargs):
        """Enable or disable command buttons as appropriate"""
        if self.scriptRunner.isExecuting():
            self.applyButton.setEnable(False)
            self.cancelButton.setEnable(True)
            self.currentButton.setEnable(False)
        else:
            self.cancelButton.setEnable(False)
            doEnable = not self.inputWdg.inputCont.allDefault()
            self.currentButton.setEnable(doEnable)
            self.applyButton.setEnable(doEnable)

    def showExpose(self):
        self.tlSet.makeVisible("None.Echelle Expose")
    
    def _showConfigCallback(self, wdg=None):
        """Callback for show/hide config toggle.
        Restores defaults if config newly shown."""
        showConfig = self.showConfigWdg.getBool()
        restoreConfig = showConfig and not self.configShowing
        self.configShowing = showConfig
        if restoreConfig:
            self.inputWdg.restoreDefault()


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
