#!/usr/bin/env python
"""Menu bar and menus for the TUI application.

To Do:
- See about Windows conventions, for example should we be using
  the system menu for the TUI menu? Is the quit command Exit
  and do we need to specifically specify it, or is it automatic
  the way Quit is on MacOS X.

History:
2002-12-05 ROwen    Added the Help menu.
2002-12-23 ROwen    Removed unneded local variable; thanks to pychecker.
2003-02-27 ROwen    Changed connect to use the new connection dialog
                    (which is supplied as a normal window) and to disable
                    Disconnect when the connection is already closed.
2003-03-20 ROwen    Added Inst menu.
2003-03-21 ROwen    Modified help to use urlparse.urljoin.
2003-03-25 ROwen    Added the ability to rebuild the automatic menus
2003-06-09 ROwen    Removed most arguments.
2003-10-10 ROwen    Modified to use RO.Comm.HubConnection.
2003-10-14 ROwen    Modified help menu to reflect Overview->Introduction.
2003-12-04 ROwen    Changed doCall to callNow in call to addStateCallback.
2003-12-17 ROwen    Renamed to MainMenu.
2004-02-04 ROwen    Modified _HelpURL to match minor help reorg.
2004-02-17 ROwen    Changed addTUIMenu to support extra windows (a few have
                    predefined positions; the rest are listed alphabetically).
                    Changed buildAutoMenus to buildMenus and made it
                    also build the TUI menu.
2004-07-19 ROwen    Added Scripts menu. Made sure Quit always quits.
2004-08-11 ROwen    .
2004-08-11 ROwen    Modified for updated RO.Wdg.CtxMenu and new RO.Wdg.Constants
2004-08-25 ROwen    Bug fix: help was broken due to misuse of new RO.Wdg.Constants.
2004-09-03 ROwen    Modified for RO.Wdg._joinHelpURL -> RO.Constants._joinHelpURL.
2004-10-06 ROwen    Modified to not tie up the event loop while opening html help.
                    Renamed from MainMenu and totally overhauled. In progress!
2005-03-30 ROwen    Added Guide menu.
2005-06-08 ROwen    Changed MenuBar to a new-style class.
2005-07-07 ROwen    Modified for moved RO.TkUtil.
2006-03-09 ROwen    Modified to avoid "improper exit" complaints
                    on Windows by explicitly destroying root on quit.
2009-03-31 ROwen    Modified for tuiModel.root -> tuiModel.tkRoot.
"""
import Tkinter
import RO.Alg
import RO.Comm.BrowseURL
import RO.Constants
import RO.OS
import RO.TkUtil
import RO.Wdg
import TUI.ScriptMenu

class MenuBar(object):
    """Create TUI's application menu bar.

    Call only after all windows have been created
    (else the auto menus Inst, etc. will be missing entries).
    
    Note: if MacOS X Aqua, then the root["menu"] is set
    so that the menu bar applies to all windows.
    Otherwise the menu bar appears in the Status window
    and thus has no Edit menu (since it would only apply to widgets
    in the Status window).
    """
    def __init__(self):
        self.tuiModel = TUI.TUIModel.Model()
        self.tlSet = self.tuiModel.tlSet
        self.connection = self.tuiModel.dispatcher.connection
        
        self.wsys = RO.TkUtil.getWindowingSystem()

        # determine parent toplevel and create menu for it
        if self.wsys == RO.TkUtil.WSysAqua:
            parentTL = self.tuiModel.tkRoot
        else:
            parentTL = self.tlSet.getToplevel("None.Status")
        self.parentMenu = Tkinter.Menu(parentTL)
        parentTL["menu"] = self.parentMenu
        
        self.tuiMenu = None
        self.connectMenuIndex = None

        # add the TUI menu
        self.addTUIMenu()
        
        self.connection.addStateCallback(self._connStateFunc, callNow = True)
        
        # if Mac Aqua, add an edit menu
        if self.wsys == RO.TkUtil.WSysAqua:
            self.addMacEditMenu()
        
        # add the automatic menus
        for menuTitle in ("TCC", "Inst", "Guide", "Misc"):
            self.addAutoMenu(menuTitle)
    
        # add the script menu
        self.addScriptMenu()

        # add the help menu
        self.addHelpMenu()
    
    def addAutoMenu(self, name):
        """Add automatically built menu
        """
        mnu = Tkinter.Menu(self.parentMenu, tearoff=False)
        tlNames = self.tlSet.getNames(name + ".")
        for tlName in tlNames:
            self._addWindow(tlName, mnu)
        self.parentMenu.add_cascade(label=name, menu=mnu)

    def addHelpMenu(self):
        mnu = Tkinter.Menu(self.parentMenu, name = "help", tearoff=False)
        for itemName, url in (
            ("TUI Help", "index.html"),
            ("Introduction", "Introduction.html"),
            ("Version History", "VersionHistory.html"),
        ):
            mnu.add_command (
                label=itemName,
                command=RO.Alg.GenericCallback(self.doHelp, url),
            )
        self.parentMenu.add_cascade(label="Help", menu=mnu)
    
    def addMacEditMenu(self):
        mnu = Tkinter.Menu(self.parentMenu)
        for label, accelLet in (
            ("Cut", "X"),
            ("Copy", "C"),
            ("Paste", "V"),
            ("Clear", None),
            ("Select All", "A"),
        ):
            if accelLet:
                accel = "Command-%s" % accelLet
            else:
                accel = None
            if label:
                mnu.add_command(
                    label = label,
                    accelerator = accel,
                    command = RO.Alg.GenericCallback(self.doEditItem, label)
                )
            else:
                mnu.add_separator()
        self.parentMenu.add_cascade(label="Edit", menu=mnu)
    
    def addScriptMenu(self):
        mnu = TUI.ScriptMenu.getScriptMenu(self.parentMenu)
        self.parentMenu.add_cascade(label="Scripts", menu=mnu)
    
    def addTUIMenu(self):
        if self.wsys == RO.TkUtil.WSysAqua:
            name = "apple"
        else:
            name = None
        mnu = Tkinter.Menu(self.parentMenu, name=name, tearoff=0)
        
        # predefined windows: titles of windows
        # whose positions in the TUI menu are predefined
        predef = ["About TUI", "Connect", "Preferences"]
        predef = ["TUI." + name for name in predef]

        # add first batch of predefined entries
        self._addWindow("TUI.About TUI", mnu)
        mnu.add_separator()
        self._addWindow("TUI.Connect", mnu)
        self.connectMenuIndex = mnu.index("end")
        mnu.add_command(label="Disconnect", command=self.doDisconnect)
        mnu.add_command(label="Refresh Display", command=self.doRefresh)
        mnu.add_separator()
        
        # add non-predefined windows here
        tlNames = self.tlSet.getNames("TUI.")
        for tlName in tlNames:
            if tlName in predef:
                continue
            self._addWindow(tlName, mnu)
        
        # add the remaining predefined entries
        mnu.add_separator()
        self._addWindow("TUI.Preferences", mnu)
        mnu.add_command(label="Save Window Positions", command=self.doSaveWindowPos)
        if self.wsys == RO.TkUtil.WSysX11:
            mnu.add_separator()
            mnu.add_command(label="Quit", command=self.doQuit)
        elif self.wsys == RO.TkUtil.WSysWin:
            mnu.add_separator()
            mnu.add_command(label="Exit", command=self.doQuit)
        # else Mac Aqua, which already has a Quit item

        self.tuiMenu = mnu
        self.parentMenu.add_cascade(label = "TUI", menu = mnu)

    def doDisconnect(self, *args):
        self.connection.disconnect()
        self.tuiMenu.entryconfigure(self.connectMenuIndex, state="normal")

    def doEditItem(self, name):
        wdg = self.tuiModel.tkRoot.focus_get()
        if not wdg:
            return
        evtStr = "<<%s>>" % (name,)
#       print "do Edit item %s by sending %s to %s" % (name, evtStr, wdg)
        wdg.event_generate(evtStr)
    
    def doHelp(self, urlSuffix):
        helpURL = RO.Constants._joinHelpURL(urlSuffix)

        RO.Comm.BrowseURL.browseURL(helpURL)

    def doQuit(self):
        try:
            self.doDisconnect()
        finally:
            self.tuiModel.reactor.stop()
            if RO.OS.PlatformName == "win":
                # avoid "improper exit" complaints
                self.tuiModel.tkRoot.destroy()
    
    def doRefresh(self):
        """Refresh all automatic variables.
        """
        self.tuiModel.dispatcher.refreshAllVar(startOver=True)

    def doSaveWindowPos(self):
        self.tlSet.writeGeomVisFile()
    
    def showToplevel(self, tlName):
        self.tlSet.makeVisible(tlName)
        
    def _addWindow(self, tlName, mnu):
        """Add a toplevel named tlName to the specified menu.
        tlName must be of the form menu.title
        """
        title = tlName.split(".")[-1]
        mnu.add_command(label=title, command=RO.Alg.GenericCallback(self.showToplevel, tlName))

    def _connStateFunc(self, conn):
        """Called whenever the connection changes state"""
        if conn.isConnected():
            self.tuiMenu.entryconfigure(self.connectMenuIndex, state="disabled")
            self.tuiMenu.entryconfigure(self.connectMenuIndex+1, state="normal")
            self.tuiMenu.entryconfigure(self.connectMenuIndex+2, state="normal")
        else:
            self.tuiMenu.entryconfigure(self.connectMenuIndex, state="normal")
            self.tuiMenu.entryconfigure(self.connectMenuIndex+1, state="disabled")
            self.tuiMenu.entryconfigure(self.connectMenuIndex+2, state="disabled")
