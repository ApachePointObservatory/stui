#!/usr/bin/env python
"""Menu bar and menus for the TUI application.

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
2009-03-31 ROwen    Updated for tuiModel.root -> tuiModel.tkRoot.
2009-07-23 ROwen    Modified for dispatcher change to refreshAllVar.
2009-09-14 ROwen    Removed Guide menu; guider is under Inst because there is only one guider.
2009-11-05 ROwen    Fixed to use TUI.TCC.StatusWindow instead of incorrect "None.Status".
2010-03-12 ROwen    Changed to use Models.getModel.
2010-06-25 ROwen    List log windows in a sub menu.
2010-06-29 ROwen    Bug fix: would fail on unix as it tried to get the name of the TCC status window.
                    Replaced all instances of the string STUI with TUI.Version.ApplicationName
2012-06-11 ROwen    To avoid duplicate application menus on Mac OS X, Tcl/Tk 8.5 requires that the
                    application menu have all entries added before setting the menu property of the toplevel.
2012-08-10 ROwen    Updated for RO.Comm 3.0.
2014-10-28 ROwen    Bug fix on MacOS X: a duplicate Preferences menu was shown. Now supports cmd-comma.
                    Bug fix: an error if no parentTL found was mis-generated.
                    Bug fix: TUI Help was shown twice and the first entry didn't work.
                    Switched from RO.Alg.GenericCallback to functools.partial.
                    Added attribute appname.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""

import functools
import subprocess
import Tkinter
import warnings

import RO.Comm.BrowseURL
import RO.Constants
import RO.OS
import RO.TkUtil
import TUI.Models.TUIModel
import TUI.ScriptMenu
import TUI.TCC.StatusWdg.StatusWindow
import TUI.Version


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

        self.tuiModel = TUI.Models.getModel("tui")
        self.tlSet = self.tuiModel.tlSet
        self.connection = self.tuiModel.dispatcher.connection
        self.appName = TUI.Version.ApplicationName

        self.wsys = RO.TkUtil.getWindowingSystem()

        self.menu_color = self._get_menu_color()

        # determine parent toplevel and create menu for it
        if self.wsys == RO.TkUtil.WSysAqua:
            parentTL = self.tuiModel.tkRoot
        else:
            parentTL = self.tlSet.getToplevel(TUI.TCC.StatusWdg.StatusWindow.WindowName)
            if not parentTL:
                raise RuntimeError("Could not find window %s" % (TUI.TCC.StatusWdg.StatusWindow.WindowName,))
        self.parentMenu = Tkinter.Menu(parentTL)

        self.tuiMenu = None
        self.connectMenuIndex = None

        # add the TUI menu
        self.addTUIMenu()

        self.connection.addStateCallback(self._connStateFunc, callNow = True)

        # if Mac Aqua, add an edit menu
        if self.wsys == RO.TkUtil.WSysAqua:
            self.addMacEditMenu()

        # add the automatic menus
        for menuTitle in ("TCC", "Inst", "Misc"):
            self.addAutoMenu(menuTitle)

        # add the script menu
        self.addScriptMenu()

        # add the help menu
        self.addHelpMenu()

        # this must come after addTUIMenu, else two application menus show up in Mac OS X
        parentTL["menu"] = self.parentMenu

    def addAutoMenu(self, name):
        """Add automatically built menu
        """
        mnu = Tkinter.Menu(self.parentMenu, tearoff=False, fg=self.menu_color)
        tlNames = self.tlSet.getNames(name + ".")
        for tlName in tlNames:
            self._addWindow(tlName, mnu)
        self.parentMenu.add_cascade(label=name, menu=mnu)

    def addHelpMenu(self):
        mnu = Tkinter.Menu(self.parentMenu, name="help", tearoff=False, fg=self.menu_color)

        begInd = 0
        if self.wsys == RO.TkUtil.WSysAqua:
            # MacOS adds the first help item
            def doMacHelp(*args):
                print "doMacHelp(%s)" % (args,)
                self.doHelp("index.html")
            self.tuiModel.tkRoot.createcommand("::tk::mac::ShowHelp", doMacHelp)
            begInd = 1

        for itemName, url in ((self.appName + " Help", "index.html"),
                              ("Introduction", "Introduction.html"),
                              ("Version History", "VersionHistory.html"))[begInd:]:
            mnu.add_command(
                label=itemName,
                command=functools.partial(self.doHelp, url))
        self.parentMenu.add_cascade(label="Help", menu=mnu)

    def addMacEditMenu(self):
        mnu = Tkinter.Menu(self.parentMenu, fg=self.menu_color)
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
                    command = functools.partial(self.doEditItem, label)
                )
            else:
                mnu.add_separator()
        self.parentMenu.add_cascade(label="Edit", menu=mnu)

    def addScriptMenu(self):
        mnu = TUI.ScriptMenu.getScriptMenu(self.parentMenu, fg=self.menu_color)
        self.parentMenu.add_cascade(label="Scripts", menu=mnu)

    def addTUIMenu(self):
        if self.wsys == RO.TkUtil.WSysAqua:
            name = "apple"
        else:
            name = None
        mnu = Tkinter.Menu(self.parentMenu, name=name, tearoff=0, fg=self.menu_color)

        # predefined windows: titles of windows
        # whose positions in the TUI menu are predefined
        predef = ["About %s" % (self.appName,), "Connect", "Preferences", "Downloads"]
        predef = ["%s.%s" % (self.appName, wtitle) for wtitle in predef]

        # add first batch of predefined entries
        self._addWindow("%s.About %s" % (self.appName, self.appName), mnu)
        mnu.add_separator()
        self._addWindow("%s.Connect" % (self.appName,), mnu)
        self.connectMenuIndex = mnu.index("end")
        mnu.add_command(label="Disconnect", command=self.doDisconnect)
        mnu.add_command(label="Refresh Display", command=self.doRefresh)
        mnu.add_separator()

        self._addWindow("%s.Downloads" % (self.appName,), mnu)

        self.logMenu = Tkinter.Menu(mnu, tearoff=False,
                                    postcommand=self._populateLogMenu, fg=self.menu_color)
        mnu.add_cascade(label="Logs", menu=self.logMenu)

        # add non-predefined windows here
        tlNames = self.tlSet.getNames("%s." % (self.appName,))
        for tlName in tlNames:
            if tlName in predef:
                continue
            if tlName.startswith("%s.Log" % (self.appName,)):
                continue
            self._addWindow(tlName, mnu)

        # add the remaining predefined entries
        mnu.add_separator()
        if self.wsys == RO.TkUtil.WSysAqua:
            self.tuiModel.tkRoot.createcommand("::tk::mac::ShowPreferences",
                functools.partial(self.showToplevel, "%s.Preferences" % (self.appName,)))
        else:
            self._addWindow("%s.Preferences" % (self.appName,), mnu)

        mnu.add_command(label="Save Window Positions", command=self.doSaveWindowPos)
        if self.wsys == RO.TkUtil.WSysX11:
            mnu.add_separator()
            mnu.add_command(label="Quit", command=self.doQuit)
        elif self.wsys == RO.TkUtil.WSysWin:
            mnu.add_separator()
            mnu.add_command(label="Exit", command=self.doQuit)
        else:
            # Mac already has a Quit item. Unfortunately, when using Twisted it has no effect and it cannot be
            # programmed in the usual tcl/tk way. However, it can be caught as follows, with thanks to
            # Daniel Steffen for the information:
            self.tuiModel.tkRoot.createcommand("::tk::mac::Quit", self.doQuit)

        self.tuiMenu = mnu
        self.parentMenu.add_cascade(label = self.appName, menu = mnu)

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
        self.tuiModel.dispatcher.refreshAllVar(resetAll=True)

    def doSaveWindowPos(self):
        self.tlSet.writeGeomVisFile()

    def showToplevel(self, tlName):
        self.tlSet.makeVisible(tlName)

    def _addWindow(self, tlName, mnu, label=None):
        """Add a toplevel named tlName to the specified menu.
        tlName must be of the form menu.title
        """
        if label is None:
            label = tlName.split(".")[-1]
        mnu.add_command(label=label, command=functools.partial(self.showToplevel, tlName))

    def _connStateFunc(self, conn):
        """Called whenever the connection changes state"""
        if conn.isConnected:
            self.tuiMenu.entryconfigure(self.connectMenuIndex, state="disabled")
            self.tuiMenu.entryconfigure(self.connectMenuIndex+1, state="normal")
            self.tuiMenu.entryconfigure(self.connectMenuIndex+2, state="normal")
        else:
            self.tuiMenu.entryconfigure(self.connectMenuIndex, state="normal")
            self.tuiMenu.entryconfigure(self.connectMenuIndex+1, state="disabled")
            self.tuiMenu.entryconfigure(self.connectMenuIndex+2, state="disabled")

    def _get_menu_color(self):
        """Returns the color to use for the menu foreground.

        Checks whether we are running on a Mac and if the dark mode is enabled.

        """

        if self.wsys != RO.TkUtil.WSysAqua:
            return None

        # try:
        #     process = subprocess.Popen('defaults read -g AppleInterfaceStyle',
        #                                shell=True, stdout=subprocess.PIPE)
        #     out, __ = process.communicate()

        #     if out is not None and 'Dark' in out:
        #         return 'white'
        #     else:
        #         return None
        # except subprocess.CalledProcessError:
        #     warnings.warn('cannot determine whether the dark mode is enabled.')
        #     return None

    def _populateLogMenu(self):
        """Populate the log menu.
        """
        self.logMenu.delete(0, "end")
        for num in range(TUI.Models.TUIModel.MaxLogWindows):
            name = "%s.Log %d" % (self.appName, num + 1,)
            isActive = self.tlSet.getToplevel(name).wm_state() != "withdrawn"
            if isActive:
                label = "* Log %d" % (num + 1,)
            else:
                label = "  Log %d" % (num + 1,)
            self._addWindow(name, self.logMenu, label=label)


if __name__ == "__main__":
    import TUI.Base.TestDispatcher

    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
    tuiModel = testDispatcher.tuiModel

    menuBar = MenuBar()

    tuiModel.reactor.run()
