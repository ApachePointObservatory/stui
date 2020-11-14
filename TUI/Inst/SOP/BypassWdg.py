#!/usr/bin/env python
"""Support for sop bypass command

History:
2010-06-28 ROwen    Removed unused import (thanks to pychecker).
2011-09-02 ROwen    Modified to show bypassed systems in red. This required switching from buttons
                    to checkbuttons due to limitations on MacOS X.
                    Modified to allow canceling unbypass commands.
2012-11-15 ROwen    Stop using Checkbutton indicatoron=False; it is no longer supported on MacOS X.
                    Fixed a bug that caused the bypass X button to be enabled when it should not be.
2012-12-06 ROwen    Bug fix: button enable terminated early with a traceback if a system was bypassed
                    that was not in unbypassNameCmdVarDict. This could leave buttons disabled
                    if an unbypass command failed.
2014-06-17 ROwen    Cosmetic fix: BypassWdg.isRunning returned None instead of False if not running.
2014-07-10 ROwen    Modified to use new bypassedNames keyVar.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import contextlib
import Tkinter
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

        # dict of system name: cmdVar for unbypass commands issued by this user
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

        # dict of system name: wdg for systems being bypassed;
        # the widgets are buttons that send the unbypass commend;
        # contents are controlled by keyword "bypassed"
        self.nameWdgDict = dict()
        
        # list of systems that may be bypassed; set by keyword bypassNames
        self.bypassNames = []
        
        self.sopModel = TUI.Models.getModel("sop")
       
        self.sopModel.bypassedNames.addCallback(self._bypassedNamesCallback)
        # use a callback for bypassNames because the startup value of the keyVar is (None,)
        self.sopModel.bypassNames.addCallback(self._bypassNamesCallback)
        self.enableButtons()

    def doBypass(self, dumWdg=None):
        """Bypass a system
        """
        d = BypassDialog(master=self, bypassNames=self.bypassNames)
        if d.result is None:
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
            callFunc = self.enableButtons,
        )
        self.unbypassNameCmdVarDict[systemName] = cmdVar
        self.statusBar.doCmd(cmdVar)
        self.enableButtons()
    
    def doCancel(self, dumWdg=None):
        """Cancel running commands
        """
        for cmdVar in self.unbypassNameCmdVarDict.values():
            cmdVar.abort()
        self.unbypassNameCmdVarDict.clear()
    
    def enableButtons(self, dumArg=None):
        """Enable buttons
        """
#         print "enableButtons()"
        with self.updateLock():
            for name, wdg in self.nameWdgDict.items():
                cmdVar = self.unbypassNameCmdVarDict.get(name)
                doEnable = cmdVar is None or cmdVar.isDone
                wdg.setEnable(doEnable)
            self.cancelBtn.setEnable(self.isRunning)

    def gridWdg(self):
        """Grid unbypass buttons"""
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
        for cmdVar in self.unbypassNameCmdVarDict.values():
            if not cmdVar.isDone:
                return True
        return False
    
    def _bypassedNamesCallback(self, keyVar):
        """bypassedNames keyvar callback
        """
#         print "_bypassedNamesCallback(keyVar=%s)" % (keyVar,)
        keyVar = self.sopModel.bypassedNames
        if None in keyVar:
            return

        newSystems = set(keyVar)
            
        oldSystems = set(self.nameWdgDict.keys())
        if newSystems == oldSystems:
            return

        deletedSystems = oldSystems - newSystems
        addedSystems = newSystems - oldSystems
        for delSys in deletedSystems:
            wdg = self.nameWdgDict.pop(delSys)
            wdg.grid_forget()
        for addSys in addedSystems:
            wdg = RO.Wdg.Button(
                master = self.bypassWdgFrame,
                text = addSys,
                severity = RO.Constants.sevError,
                callFunc = self.doUnbypass,
                helpText = "Push to stop bypassing %s" % (addSys,),
                helpURL = self.helpURL,
            )
            self.nameWdgDict[addSys] = wdg
        
        self.gridWdg()
    
    def _bypassNamesCallback(self, keyVar):
        """bypassNames keyvar callback
        """
#         print "_bypassNamesCallback(keyVar=%s)" % (keyVar,)
        if None in keyVar:
            return
        self.bypassNames = keyVar[:]


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
    from . import TestData
    
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

