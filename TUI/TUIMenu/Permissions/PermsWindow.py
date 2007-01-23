#!/usr/local/bin/python
"""Specify what users from each program are allowed to do.

2003-12-18 ROwen    Preliminary version; html help is broken.
2003-12-29 ROwen    Implemented html help.
2004-02-17 ROwen    Moved to the TUI menu (now that this is possible!)
                    and changed to visible by default.
2004-07-29 ROwen    Added read-only support.
                    Updated for new RO.KeyVariable
2005-01-05 ROwen    Added Read Only button to test code.
2006-04-10 ROwen    Updated Sort button help text because actors are now sorted.
"""
import Tkinter
import RO.KeyVariable
import RO.Wdg
import PermsModel
import PermsInputWdg

_HelpPrefix = "TUIMenu/PermissionsWin.html#"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = "TUI.Permissions",
        defGeom = "180x237+172+722",
        visible = True,
        resizable = (False, True),
        wdgFunc = PermsWdg,
    )
    Tkinter.Label().update_idletasks()

class PermsWdg(Tkinter.Frame):
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)

        self._titleFrame = Tkinter.Frame(self)
        self._titleFrame.grid(row=0, sticky="w")
        
        self._permsModel = PermsModel.getModel()

        self._statusBar = RO.Wdg.StatusBar(
            master = self,
            dispatcher = self._permsModel.dispatcher,
        )
        
        self._scrollWdg = RO.Wdg.ScrolledWdg(
            master = self,
            hscroll = False,
            vscroll = True,
        )
        
        self.inputWdg = PermsInputWdg.PermsInputWdg(
            master = self._scrollWdg.getWdgParent(),
            statusBar = self._statusBar,
            titleFrame = self._titleFrame,
            readOnlyCallback = self.doReadOnly,
        )
        self._scrollWdg.setWdg(
            wdg = self.inputWdg,
            vincr = self.inputWdg.getVertMeasWdg(),
        )

        self._scrollWdg.grid(row=1, sticky="ns")
        self.grid_rowconfigure(1, weight=1)

        self._statusBar.grid(row=2, sticky="ew")
    
        self.butFrame = Tkinter.Frame(self)
        
        RO.Wdg.StrLabel(self.butFrame, text="Add:").pack(side="left", anchor="e")
        newEntryWdg = RO.Wdg.StrEntry (
            master = self.butFrame,
            partialPattern = r"^[a-zA-Z]{0,2}[0-9]{0,2}$",
            finalPattern = r"^[a-zA-Z][a-zA-Z][0-9][0-9]$",
            width = 4,
            helpText = "type new program name and <return>",
            
        )
        newEntryWdg.bind("<Return>", self.doNew)
        newEntryWdg.pack(side="left", anchor="w")
        
        purgeWdg = RO.Wdg.Button(
            master = self.butFrame,
            text = "Purge",
            command = self.inputWdg.purge,
            helpText = "Purge unregistered programs",
            helpURL = _HelpPrefix + "Purge",
        )
        purgeWdg.pack(side="left")

        sortWdg = RO.Wdg.Button(
            master = self.butFrame,
            text = "Sort",
            command = self.inputWdg.sort,
            helpText = "Sort programs and actors",
            helpURL = _HelpPrefix + "Sort",
        )
        sortWdg.pack(side="left")
        
        self.butFrame.grid(row=3, sticky="w")
        self.butFrame.grid_remove() # start in read-only state
    
    def doReadOnly(self, readOnly):
        """Callback for readOnly state changing.
        """
        if readOnly:
            self.butFrame.grid_remove()
        else:
            self.butFrame.grid()
    
    def doApply(self, wdg=None):
        pass

    def doNew(self, evt):
        """Callback for Add entry widget."""
        wdg = evt.widget
        if not wdg.isOK():
            return

        progName = wdg.getString().upper()

        newCmd = RO.KeyVariable.CmdVar (
            cmdStr = "register " + progName,
            actor="perms",
            timeLim = 5,
            description="create a new program to authorize",
        )
        self._statusBar.doCmd(newCmd)
        wdg.clear()
        wdg.focus_set()


if __name__ == "__main__":
    root = RO.Wdg.PythonTk()
    root.resizable(False, True)

    import TestData
    
    testFrame = PermsWdg(master=root)
    testFrame.pack(side="top", expand=True, fill="both")

    def doReadOnly(but):
        readOnly = but.getBool()
        testFrame.inputWdg._setReadOnly(readOnly)
    
    butFrame = Tkinter.Frame(root)
    
    Tkinter.Button(butFrame, text="Demo", command=TestData.animate).pack(side="left")
    
    RO.Wdg.Checkbutton(butFrame, text="Read Only", callFunc=doReadOnly).pack(side="left")

    butFrame.pack(side="top")
    
    TestData.start()

    root.mainloop()
