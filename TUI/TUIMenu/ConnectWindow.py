#!/usr/bin/env python
"""Connection Dialog Box

2003-02-27 ROwen    First release.
2003-03-05 ROwen    Added validity pattern to username.
2003-03-07 ROwen    Changed RO.Wdg.StringEntry to RO.Wdg.StrEntry.
2003-04-21 ROwen    Renamed StatusWdg to StatusBar to avoid conflicts.
2003-05-09 ROwen    Modified to use TUIModel.
2003-10-06 ROwen    The hub now returns cmdr instead of username; changed to match.
2003-10-14 ROwen    Changed behavior of Cancel button; added hot help;
                    mod. to use RO.Wdg.StatusBar and RO.Wdg.Gridder.
                    Modified to update username if blank and pref changed;
2003-11-17 ROwen    Modified to use modified RO.Wdg.StrEntry
                    (partialPattern instead of validPattern).
2003-12-05 ROwen    Modified for RO.Wdg.Entry changes.
2003-12-17 ROwen    Added addWindow and renamed to ConnectWindow.py.
2004-02-05 ROwen    Modified to use improved KeyDispatcher.logMsg.
2004-05-18 ROwen    Stopped importing sys since it wasn't used.
                    Stopped obtaining TUI model in addWindow; it was ignored.
                    Eliminated unneeded imports in test code.
2005-06-16 ROwen    Modified to use improved KeyDispatcher.logMsg.
2006-10-25 ROwen    Modified to use tuiModel.logMsg
                    and to log messages in keyword=value format.
2007-11-16 ROwen    Modified to allow a port as part of Host address.
2008-02-13 ROwen    Modified to enable/disable the command buttons appropriately.
"""
import Tkinter
import RO.Comm
import RO.Constants
import RO.Wdg
import TUI.Base.Wdg
import TUI.Models.TUIModel

_HelpURL = "TUIMenu/ConnectWin.html"

DefHubPort = 9877

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "STUI.Connect",
        defGeom = "+30+30",
        resizable = False,
        visible = False,
        wdgFunc = ConnectWdg,
    )

class ConnectWdg(Tkinter.Frame):
    """Dialog box for connecting to the remote host
    """
    def __init__(self,
        master,
        **kargs
    ):
        """Inputs:
        - master: master widget
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        
        self.tuiModel = TUI.Models.TUIModel.Model()
        
        gr = RO.Wdg.Gridder(master=self, sticky="ew")

        self.usernameEntry = RO.Wdg.StrEntry(
            master = self,
            width = 20,
            helpText = "Desired username (any word)",
            helpURL = _HelpURL,
            partialPattern = r"^([a-zA-Z_][-_.a-zA-Z0-9]*)?$",
            defMenu = "Default",
        )
        gr.gridWdg("User Name", self.usernameEntry)
        
        self.progIDEntry = RO.Wdg.StrEntry(
            master = self,
            width = 20,
            helpText = "ID of your observing program",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Program ID", self.progIDEntry)
        self.progIDEntry.focus_set()

        self.pwdEntry = RO.Wdg.StrEntry(
            master = self,
            width = 20,
            helpText = "Password for your program ID",
            helpURL = _HelpURL,
            show="*",
        )
        gr.gridWdg("Password", self.pwdEntry)

        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            helpURL = _HelpURL,
            dispatcher = self.tuiModel.dispatcher,
            prefs = self.tuiModel.prefs,
            summaryLen = 10,
        )
        gr.gridWdg(False, self.statusBar, colSpan=3)

        self.progIDEntry.bind("<Return>", self.handleReturn)
        self.pwdEntry.bind("<Return>", self.handleReturn)
        usernamePref = self.tuiModel.prefs.getPrefVar("User Name")
        if usernamePref != None:
            usernamePref.addCallback(self.updateUsernamePref, callNow=True)
        
        buttonFrame = Tkinter.Frame(self)
        
        self.connectButton = RO.Wdg.Button(buttonFrame,
            text="Connect",
            command=self.doConnect,
            default="active",
            helpText = "Start connecting",
            helpURL = _HelpURL,
        )
        self.connectButton.pack(side="left")

        self.cancelButton = RO.Wdg.Button(buttonFrame,
            text="Cancel",
            command=self.doCancel,
            helpText = "Cancel connection and disconnect",
            helpURL = _HelpURL,
        )
        self.cancelButton.setEnable(False)
        self.cancelButton.pack(side="left")
    
        gr.gridWdg(False, buttonFrame, colSpan=3, sticky="")
        
        self.bind("<Unmap>", self.closeEvent)
        
        self.tuiModel.dispatcher.connection.addStateCallback(self.updateStatus)
    
    def doConnect(self):
        """Connect"""
        hostPortStr = self.tuiModel.prefs.getPrefVar("Host").getValue()
        hostPortList = hostPortStr.split()
        host = hostPortList[0]
        if len(hostPortList) > 1:
            port = int(hostPortList[1])
        else:
            port = DefHubPort
        username = self.usernameEntry.get()
        progID = self.progIDEntry.get()
        password = self.pwdEntry.get()
        self.tuiModel.dispatcher.connection.connect(
            username = username,
            port = port,
            progID = progID,
            password = password,
            host = host,
        )

    def doCancel(self):
        """Cancels the dialog box
        """
        self.tuiModel.dispatcher.connection.disconnect()
    
    def updateStatus(self, conn):
        """Update the status display
        and kill dialog once connection is made.
        """
        mayConnect = conn.mayConnect()
        self.connectButton.setEnable(mayConnect)
        self.cancelButton.setEnable(not mayConnect)

        state, stateStr, msg = conn.getFullState()
        if msg:
            text = "%s; Text=%r" % (stateStr, msg)
        else:
            text = stateStr
        if state > 0:
            severity = RO.Constants.sevNormal
        elif state == 0:
            severity = RO.Constants.sevWarning
        else:
            severity = RO.Constants.sevError
        self.tuiModel.logMsg(text, severity = severity, keyword=None)
        self.statusBar.setMsg(text)

        if self.tuiModel.dispatcher.connection.isConnected():
            self.winfo_toplevel().wm_withdraw()
    
    def updateUsernamePref(self, newValue, usernamePref):
        """Called when the username preference has been updated.
        """
        self.usernameEntry.setDefault(newValue)
    
    def handleReturn(self, *args):
        """Handles the user typing <return>
        by connecting if that's reasonable, else doing nothing.
        """
        if not self.tuiModel.dispatcher.connection.isConnected() \
            and self.progIDEntry.get() \
            and self.pwdEntry.get():
            self.doConnect()
    
    def closeEvent(self, *args):
        """Handles the window being closed.
        """
        self.pwdEntry.set("")

if __name__ == "__main__":
    root = RO.Wdg.PythonTk()

    testFrame = ConnectWdg(master=root)
    testFrame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
    
    root.mainloop()
