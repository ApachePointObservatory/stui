"""Support for sop bypass command

TO DO:
- Configure a column to grow (one past any that I'd use == thus MaxSystemsInARow + 1 or similar
- Add a dialog box to support the bypass command; it needs a menu of choices
  see the alerts widget for a model of how to do this
"""
import Tkinter
import itertools
import opscore.actor
import RO.Wdg
import TUI.Models
import pdb

class BypassWdg(Tkinter.Frame):
    """Widget for sop bypass command
    """
    MaxSystemsInARow = 4
    def __init__(self, master, statusBar, helpURL=None):
        Tkinter.Frame.__init__(self, master, borderwidth=1, relief="ridge")
        self.statusBar = statusBar
        self.helpURL = helpURL

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

        # dict of system name: wdg
        self.nameWdgDict = dict()
        
        self.sopModel = TUI.Models.getModel("sop")
       
        self.sopModel.bypassed.addCallback(self.bypassedCallback)
        self.sopModel.bypassNames.addCallback(self.bypassNamesCallback)

    def bypassedCallback(self, keyVar):
        """bypassed keyvar callback
        """
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
        print "newSystems=%s; oldSystems=%s; deletedSystems=%s; addedSystems=%s" % \
            (newSystems, oldSystems, deletedSystems, addedSystems)
        for delSys in deletedSystems:
            wdg = self.nameWdgDict.pop(delSys)
            wdg.grid_forget()
        for addSys in addedSystems:
            wdg = RO.Wdg.Button(
                master = self.bypassWdgFrame,
                text = addSys,
                callFunc = self.doUnbypass,
                helpText = "Push to stop bypassing %s" % (addSys,),
                helpURL = self.helpURL,
            )
            self.nameWdgDict[addSys] = wdg
        self.gridWdg()
    
    def bypassNamesCallback(self, keyVar):
        """bypassNames keyvar callback
        """
        if None in keyVar:
            return
        self.bypassNames = keyVar[:]

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
        self.doCmd(cmdStr="bypass subSystem=%r" % (systemName,))

    def doUnbypass(self, wdg):
        """Stop bypassing a system
        """
        systemName = wdg["text"]
        self.doCmd("bypass subSystem=%r clear" % (systemName,))

    def doCmd(self, cmdStr, wdg=None, **keyArgs):
        """Run the specified command
        
        Inputs:
        - cmdStr: command string
        - wdg: widget that started the command (to disable it while the command runs)
        **keyArgs: all other keyword arguments are used to construct opscore.actor.keyvar.CmdVar
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "sop",
            cmdStr = cmdStr,
        **keyArgs)
        self.statusBar.doCmd(cmdVar)
    
    def gridWdg(self):
        row = 0
        col = 0
        sysNames = sorted(self.nameWdgDict.keys())
        maxCol = self.MaxSystemsInARow - 1
        for sysName in sysNames:
            wdg = self.nameWdgDict[sysName]
            wdg.grid_forget()
            wdg.grid(row=row, column=col)
            print "row=%s; col=%s" % (row, col)
            if col >= maxCol:
                row += 1
                col = 0
            else:
                col += 1

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
