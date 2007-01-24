#!/usr/bin/env python
"""Status and configuration for NICFPS.

History:
2003-09-02 ROwen
2004-11-15 ROwen    Modified to use RO.Wdg.Checkbutton's improved defaults.
2005-06-03 ROwen    Fixed some irregular indentation (tab-space).
2005-06-14 ROwen    Bug fix: _HelpPrefix was wrong.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
"""
import Tkinter
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
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
            # command is set by ScriptWdg
            helpText = "apply the config. changes",
            helpURL = _HelpPrefix + "Apply",
        )
        self.applyButton.grid(row=0, column=bfCol)
        bfCol += 1
        
        self.cancelButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Cancel",
            # command is set by BasicScriptWdg
            helpText = "cancel remaining config. changes",
            helpURL = _HelpPrefix + "Cancel",
        )
        self.cancelButton.grid(row=0, column=bfCol)
        bfCol += 1

        spacerFrame = Tkinter.Frame(buttonFrame, width=5)
        spacerFrame.grid(row=0, column=5)

        self.currentButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Current",
            command = self.doCurrent,
            helpText = "reset controls to current NICFPS config.",
            helpURL = _HelpPrefix + "Current",
        )
        self.currentButton.grid(row=0, column=bfCol)
        bfCol += 1

        buttonFrame.grid(row=2, column=0, sticky="w")
        
        self.inputWdg.gridder.addShowHideWdg (
            StatusConfigInputWdg._ConfigCat,
            [self.applyButton, self.cancelButton, spacerFrame, self.currentButton],
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

        self.scriptWdg = RO.Wdg.BasicScriptWdg(
            master = master,
            name = 'NICFPS Config',
            dispatcher = tuiModel.dispatcher,
            runFunc = doConfig,
            statusBar = self.statusBar,
            startButton = self.applyButton,
            cancelButton = self.cancelButton,
        )
        
    def doCurrent(self):
        """Restore all input widgets to the current state.
        If no command executing, clear status bar.
        """
        self.inputWdg.restoreDefault()
        if self.scriptWdg.scriptRunner.isDone():
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
