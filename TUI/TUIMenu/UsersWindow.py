#!/usr/bin/env python
"""Users window (display a list of users).

2003-12-06 ROwen
2003-12-17 ROwen    Added addWindow and renamed to UsersWindow.py.
2004-05-18 ROwen    Stopped obtaining TUI model in addWindow; it was ignored.
2004-07-22 ROwen    Modified to use TUI.HubModel.
2004-08-11 ROwen    Modified for updated RO.Wdg.CtxMenu.
2004-08-25 ROwen    Modified to use new hubModel.users keyvar.
2004-09-14 ROwen    Stopped importing TUI.TUIModel since it wasn't being used.
2004-11-18 ROwen    Added code to silently handle usernames with no ".".
2005-01-06 ROwen    Modified to indicate the current user with an underline.
2009-04-01 ROwen    Test code updated to use TUI.Base.TestDispatcher.
"""
import time
import Tkinter
import RO.StringUtil
import RO.Wdg
import TUI.HubModel
import TUI.TUIModel

_HelpPage = "TUIMenu/UsersWin.html"

def addWindow(tlSet):
    tlSet.createToplevel(
        name = "TUI.Users",
        defGeom = "170x170+0+722",
        visible = False,
        resizable = True,
        wdgFunc = UsersWdg,
    )

class UsersWdg (Tkinter.Frame):
    """Display the current users and those recently logged out.
    
    Inputs:
    - master    parent widget
    - retainSec time to retain information about logged out users (sec)
    - height    default height of text widget
    - width default width of text widget
    - other keyword arguments are used for the frame
    """
    def __init__ (self,
        master=None,
        retainSec=300,
        height = 10,
        width = 20,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)
        
        hubModel = TUI.HubModel.Model()
        self.tuiModel = TUI.TUIModel.Model()
        
        # entries are commanders (prog.user)
        self._cmdrList = []
        # entries are (cmdr, time deleted); time is from time.time()
        self._delCmdrTimeList = []
        # time to show deleted users
        self._retainSec = retainSec
        
        self.afterID = None
        
                
        self.yscroll = Tkinter.Scrollbar (
            master = self,
            orient = "vertical",
        )
        self.text = Tkinter.Text (
            master = self,
            yscrollcommand = self.yscroll.set,
            wrap = "word",
            height = height,
            width = width,
        )
        self.yscroll.configure(command=self.text.yview)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.yscroll.grid(row=0, column=1, sticky="ns")
        RO.Wdg.Bindings.makeReadOnly(self.text)
        RO.Wdg.addCtxMenu(
            wdg = self.text,
            helpURL = _HelpPage,
        )

        
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        self.text.tag_configure("del", overstrike=True)
        self.text.tag_configure("me", underline=True)

        hubModel.users.addCallback(self._usersCallback)

    def _usersCallback(self, keyVar):
        """Current commander list updated.
        """
        if not keyVar.isCurrent:
            # set background to notCurrent?
            return

        cmdrList = keyVar.valueList
        
        # remove users from deleted list if they appear in the new list
        self._delCmdrTimeList = [cmdrTime for cmdrTime in self._delCmdrTimeList
            if cmdrTime[0] in self._cmdrList]

        # add newly deleted users to deleted list
        for cmdr in self._cmdrList:
            if cmdr not in cmdrList:
                self._delCmdrTimeList.append((cmdr, time.time()))
        
        # save commander list
        self._cmdrList = cmdrList

        self.updDisplay()
    
    def updDisplay(self):
        """Display current data.
        """
        if self.afterID:
            self.afterID = self.after_cancel(self.afterID)

        # remove users from deleted list if they've been around for too long
        maxDelTime = time.time() - self._retainSec
        self._delCmdrTimeList = [cmdrTime for cmdrTime in self._delCmdrTimeList
            if cmdrTime[1] > maxDelTime]
        
        myProgCmdr = self.tuiModel.getCmdr()

        userTagList = [(cmdr, "curr") for cmdr in self._cmdrList]
        if self._delCmdrTimeList:
            userTagList += [(cmdrTime[0], "del") for cmdrTime in self._delCmdrTimeList]
        userTagList.sort()
        self.text.delete("1.0", "end")
        for cmdr, tag in userTagList:
            try:
                prog, user = cmdr.split(".", 1)
                if cmdr == myProgCmdr:
                    tag = "me"
            except StandardError:
                prog = cmdr
                user = "???"
            userStr = "%s\t%s\n" % (prog, user)
            self.text.insert("end", userStr, tag)
        
        if self._delCmdrTimeList:
            self.afterID = self.after(1000, self.updDisplay)

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("hub", delay=2)
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot

    testFrame = UsersWdg (root, retainSec = 5)
    testFrame.pack(expand=True, fill="both")
    
    dataList = (
        "Users=CL01.CPL, TU01.me, TU01.ROwen",
        "Users=CL01.CPL, TU01.me",
        "Users=CL01.CPL, TU01.me, TU01.ROwen",
        "Users=CL01.CPL, TU01.me",
    )
    dataSet = [[elt] for elt in dataList]

    testDispatcher.runDataSet(dataSet)

    tuiModel.reactor.run()
