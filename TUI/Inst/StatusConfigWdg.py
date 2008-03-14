#!/usr/bin/env python
"""Generic Status/Configuration widget.

History:
2008-02-11 ROwen    Based on NICFPS StatusConfigWdg
2008-03-14 ROwen    Added getActorForCommand method, since TripleSpec's slit commands
                    are handled by its slitviewer. This is a bit of a hack.
                    Read actor from statusConfigInputClass.Actor, if present.
"""
import Tkinter
import RO.ScriptRunner
import RO.Wdg
import TUI.TUIModel

class StatusConfigWdg (Tkinter.Frame):
    def __init__(self,
        master,
        statusConfigInputClass,
        actor = None,
    **kargs):
        """Create a widget to show the current state of and configure an instrument.
        
        Inputs:
        - master: Tcl master widget
        - statusConfigInputClass: a subclass of RO.Wdg.InputContFrame that defines the status
          and configuration controls and an associated input container for the configuration commands
          (see Requirements below for more information).
        - helpURL: help URL for this instruments's status/configuration window
        - **kargs: optional keyword arguments for statusConfigInputClass.__init__
        
        statusConfigInputClass must:
        - Be a subclass of RO.Wdg.InputContFrame
        - Define __init__(self, master [, ...optional keyword arguments])
        - Grid its configuration controls using an RO.Wdg.StatusConfigGridder
          (so this widget knows how to show and hide them).
        - Contain these class variables:
            - InstName: the name of the instrument in CamelCase.
              Also the expose window must be named "None.<InstName> Expose"
            - Actor (optional): the name of the actor; if omitted then InstName.lower() is used.
            - HelpPrefix: a help URL ending in "#"; use None or "" if no help is available.
                The help URL for the command buttons defined here is HelpPrefix + "CmdButtons".
        """
        self.instName = statusConfigInputClass.InstName
        self.actor = getattr(statusConfigInputClass, "Actor", self.instName.lower())

        Tkinter.Frame.__init__(self, master)

        tuiModel = TUI.TUIModel.getModel()

        self.tlSet = tuiModel.tlSet
        self.configShowing = False

        row = 0

        self.inputWdg = statusConfigInputClass(self, **kargs)
        if self.inputWdg.HelpPrefix:
            helpURL = self.inputWdg.HelpPrefix + "CmdButtons"
        else:
            helpURL = None
        self.inputWdg.grid(row=row, column=0, sticky="w")
        row += 1
            
        # create and pack status monitor
        self.statusBar = RO.Wdg.StatusBar(
            master = self,
            helpURL = helpURL,
            dispatcher = tuiModel.dispatcher,
            prefs = tuiModel.prefs,
            summaryLen = 20,
        )
        self.statusBar.grid(row=row, column=0, sticky="ew")
        row += 1

        # create and grid the buttons
        buttonFrame = Tkinter.Frame(self)
        bfCol=0

        self.exposeButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Expose...",
            command = self.showExpose,
            helpText = "open the %s Expose window" % (self.instName,),
            helpURL = helpURL,
        )
        self.exposeButton.grid(row=0, column=bfCol, sticky="w")
        bfCol += 1

        self.showConfigWdg = RO.Wdg.Checkbutton(
            master = buttonFrame,
            onvalue = "Hide Config",
            offvalue = "Show Config",
            callFunc = self._showConfigCallback,
            showValue = True,
            helpText = "show/hide configuration controls",
            helpURL = helpURL,
        )
        self.showConfigWdg.grid(row=0, column=bfCol)
        buttonFrame.columnconfigure(bfCol, weight=1)
        bfCol += 1

        self.applyButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Apply",
            command = self.doApply,
            helpText = "apply the configuration changes",
            helpURL = helpURL,
        )
        self.applyButton.grid(row=0, column=bfCol)
        bfCol += 1
        
        self.cancelButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "X",
            command = self.doCancel,
            helpText = "cancel remaining configuration changes",
            helpURL = helpURL,
        )
        self.cancelButton.grid(row=0, column=bfCol)
        bfCol += 1

        self.currentButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Current",
            command = self.doCurrent,
            helpText = "restore controls to current configuration",
            helpURL = helpURL,
        )
        self.currentButton.grid(row=0, column=bfCol)
        bfCol += 1

        buttonFrame.grid(row=2, column=0, sticky="w")
        
        self.inputWdg.gridder.addShowHideWdg (
            RO.Wdg.StatusConfigGridder.ConfigCat,
            [self.applyButton, self.cancelButton, self.currentButton],
        )
        self.inputWdg.gridder.addShowHideControl (
            RO.Wdg.StatusConfigGridder.ConfigCat,
            self.showConfigWdg,
        )

        def doConfig(sr, inputWdg=self.inputWdg):
            """Script run function to modify the configuration.
            
            This would be a class method if they could be generators.
            """
            cmdList = inputWdg.getStringList()
            
            for cmdStr in cmdList:
                yield sr.waitCmd(
                    actor = self.getActorForCommand(cmdStr),
                    cmdStr = cmdStr,
                )

        self.scriptRunner = RO.ScriptRunner.ScriptRunner(
            master = master,
            name = "%s Config" % (self.instName,),
            dispatcher = tuiModel.dispatcher,
            runFunc = doConfig,
            statusBar = self.statusBar,
            stateFunc = self.enableButtons,
        )
        
        self.inputWdg.addCallback(self.enableButtons)
    
    def doApply(self, btn=None):
        """Apply desired configuration changes.
        """
        self.scriptRunner.start()
    
    def doCancel(self, btn=None):
        """Cancel any pending configuration changes.
        """
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
        """Enable or disable command buttons as appropriate.
        """
        if self.scriptRunner.isExecuting():
            self.applyButton.setEnable(False)
            self.cancelButton.setEnable(True)
            self.currentButton.setEnable(False)
        else:
            self.cancelButton.setEnable(False)
            doEnable = not self.inputWdg.inputCont.allDefault()
            self.currentButton.setEnable(doEnable)
            self.applyButton.setEnable(doEnable)
    
    def getActorForCommand(self, cmdStr):
        return self.actor

    def showExpose(self):
        """Show the instrument's expose window.
        """
        self.tlSet.makeVisible("None.%s Expose" % (self.instName,))
    
    def _showConfigCallback(self, wdg=None):
        """Callback for show/hide config toggle.
        Restores defaults if config newly shown."""
        showConfig = self.showConfigWdg.getBool()
        restoreConfig = showConfig and not self.configShowing
        self.configShowing = showConfig
        if restoreConfig:
            self.inputWdg.restoreDefault()
