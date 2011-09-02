#!/usr/bin/env python
"""Support for sop bypass command

History:
2010-06-28 ROwen    Removed unused import (thanks to pychecker).
2011-09-02 ROwen    Modified to show bypassed systems in red. This required switching from buttons
                    to checkbuttons due to limitations on MacOS X.
                    Modified to allow canceling unbypass commands.
"""
import contextlib
import Tkinter
import itertools
import opscore.actor
import RO.Wdg
import TUI.Models

class BypassWdg(Tkinter.Frame):
    """Widget for sop bypass command
    """
    MaxSystemsInARow = 4
    def __init__(self, master, statusBar, helpURL=None):
        Tkinter.Frame.__init__(self, master, borderwidth=1, relief="ridge")
        self.statusBar = statusBar
        self.helpURL = helpURL
        
        self._updatingStatus = False

        # dict of system name: cmdVar for unbypass commands
        self.unbypassNameCmdVarDict = dict() 

        self.bypassBtn = RO.Wdg.Button(
            master = self,
            text = "Bypass...",
            command = self.doBypass,
            helpText = "Bypass a system",
            helpURL = self.helpURL,
        )
        self.bypassBtn.grid(row=0, column=0, sticky="w")
        self.bypassWdgFrame = Tkinter.Frame(self)
        self.bypassWdgFrame.grid(row=0, column=1, sticky="ew")
        self.bypassWdgFrame.grid_columnconfigure(self.MaxSystemsInARow, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "X",
            command = self.doCancel,
            helpText = "Cancel unbypass commands",
            helpURL = self.helpURL,
        )
        self.cancelBtn.grid(row=0, column=2)

        # dict of system name: wdg for systems being bypassed
        self.nameWdgDict = dict()
        
        self.sopModel = TUI.Models.getModel("sop")
       
        self.sopModel.bypassed.addCallback(self._bypassedCallback)
        self.sopModel.bypassNames.addCallback(self._bypassNamesCallback)

    def doBypass(self, dumWdg=None):
        """Bypass a system
        """
        d = BypassDialog(master=self, bypassNames=self.bypassNames)
        if d.result == None:
            return
        if not d.result:
            self.statusBar.playCmdFailed()
            self.statusBar.setMsg("No system specified", isTemp=True, severity=RO.Constants.sevError)
            return
        systemName = d.result
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "sop",
            cmdStr = "bypass subSystem=%r" % (systemName,),
        )
        self.statusBar.doCmd(cmdVar)

    def doUnbypass(self, wdg):
        """Stop bypassing a system
        """
        if self.updatingStatus:
            return

        wdg.setEnable(False)
        systemName = wdg["text"]
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "sop",
            cmdStr = "bypass subSystem=%r clear" % (systemName,),
            callFunc = self._unbypassCmdCallback,
        )
        self.unbypassNameCmdVarDict[systemName] = cmdVar
        self.statusBar.doCmd(cmdVar)
        self.enableButtons()
    
    def doCancel(self, dumWdg=None):
        """Cancel running commands
        """
        for cmdVar in self.unbypassNameCmdVarDict.itervalues():
            cmdVar.abort()
        self.unbypassNameCmdVarDict.clear()
    
    def enableButtons(self):
        """Enable buttons
        """
        with self.updateLock():
            for name, wdg in self.nameWdgDict.iteritems():
                cmdVar = self.unbypassNameCmdVarDict.get(name)
                doEnable = (cmdVar == None) or cmdVar.isDone
                wdg.set(not doEnable)
                wdg.setEnable(doEnable)
            self.cancelBtn.setEnable(self.isRunning)

    def gridWdg(self):
        row = 0
        col = 0
        sysNames = sorted(self.nameWdgDict.keys())
        maxCol = self.MaxSystemsInARow - 1
        for sysName in sysNames:
            wdg = self.nameWdgDict[sysName]
            wdg.grid_forget()
            wdg.grid(row=row, column=col)
            if col >= maxCol:
                row += 1
                col = 0
            else:
                col += 1
        self.enableButtons()
    
    @contextlib.contextmanager
    def updateLock(self):
        """Use in a with statement while updating status
        
        This prevents doCmd from executing in reaction to anything done by updateStatus,
        for instance changing Checkbuttons.
        """
        try:
            self._updatingStatus = True
            yield
        finally:
            self._updatingStatus = False

    @property
    def updatingStatus(self):
        """Return True if updating status
        """
        return self._updatingStatus
    
    @property
    def isRunning(self):
        """Return True if an any command is running.
        
        Bypass commands aren't included because we don't have a reason to track those, yet.
        """
        isRunning = False
        for cmdVar in self.unbypassNameCmdVarDict.itervalues():
            if not cmdVar.isDone:
                return True
    
    def _bypassedCallback(self, keyVar):
        """bypassed keyvar callback
        """
        keyVar = self.sopModel.bypassed
        if None in keyVar:
            return
        if len(keyVar) != len(self.bypassNames):
            raise RuntimeError("Number of values in bypassed = %s != %s = number in bypassNames" % \
                (len(keyVar), len(self.bypassNames)))

        newSystems = set(name for name, val in itertools.izip(self.bypassNames, keyVar) if val)
            
        oldSystems = set(self.nameWdgDict.keys())
        if newSystems == oldSystems:
            return

        deletedSystems = oldSystems - newSystems
        addedSystems = newSystems - oldSystems
        for delSys in deletedSystems:
            wdg = self.nameWdgDict.pop(delSys)
            wdg.grid_forget()
        for addSys in addedSystems:
            wdg = RO.Wdg.Checkbutton(
                master = self.bypassWdgFrame,
                text = addSys,
                severity = RO.Constants.sevError,
                callFunc = self.doUnbypass,
                indicatoron = False,
                helpText = "Push to stop bypassing %s" % (addSys,),
                helpURL = self.helpURL,
            )
            self.nameWdgDict[addSys] = wdg
        
        for name, wdg in self.nameWdgDict.iteritems():
            cmdVar = self.unbypassNameCmdVarDict.get(name)
            doEnable = cmdVar == None or cmdVar.isDone
            wdg.setEnable(doEnable)
        self.gridWdg()
    
    def _bypassNamesCallback(self, keyVar):
        """bypassNames keyvar callback
        """
        if None in keyVar:
            return
        self.bypassNames = keyVar[:]
    
    def _unbypassCmdCallback(self, cmdVar):
        """Callback from unbypass command
        
        On success asssume bypassNames will take care of status update,
        but on failure repaint based on current bypassNames.
        """
        if cmdVar.didFail:
            self.enableButtons()

class BypassDialog(RO.Wdg.InputDialog.ModalDialogBase):
    """Ask user for the name of a system to bypass.
    
    self.result = system (or None if cancelled)
    """
    def __init__(self, master, bypassNames):
        self.bypassNames = bypassNames
        RO.Wdg.InputDialog.ModalDialogBase.__init__(self, master, "New Rule")

    def body(self, master):
        gr = RO.Wdg.Gridder(master, sticky="ew")
        
        maxNameLen = 0
        for name in self.bypassNames:
            maxNameLen = max(len(name), maxNameLen)

        self.nameWdg = RO.Wdg.OptionMenu(
            master = master,
            items = self.bypassNames,
            width = maxNameLen,
        )
        gr.gridWdg("System to Bypass", self.nameWdg)
        return self.nameWdg # initial focus

    def setResult(self):
        self.result = self.nameWdg.getString()


if __name__ == "__main__":
    import TUI.Base.Wdg
    import TestData
    
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    statusBar = TUI.Base.Wdg.StatusBar(
        master = root,
        playCmdSounds = True,
    )

    testFrame = BypassWdg(
        master = root,
        statusBar = statusBar,
    )
    testFrame.pack(side="top")
    statusBar.pack(side="top", expand=True, fill="x")

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack(side="top")
    
    TestData.start()

    tuiModel.reactor.run()

