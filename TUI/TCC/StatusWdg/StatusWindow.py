#!/usr/bin/env python
"""Create the main TCC status window
(which is also the main TUI window, since it has the menus)

History:
2003-06-09 ROwen    added addWindow and renamed from StatusWdg to StatusWindow.
2003-06-25 ROwen    Modified test case to handle message data as a dict
2003-12-17 ROwen    Modified to use renamed TUI.MainMenu.
2004-02-04 ROwen    Modified _HelpURL to match minor help reorg.
2004-02-17 ROwen    Changed buildAutoMenus to buildMenus.
2004-05-18 ROwen    Removed unused local variable in addWindow.
2004-08-11 ROwen    Modified for updated RO.Wdg.Toplevel.
2006-03-16 ROwen    Modified to use TestData module for testing.
"""
import Tkinter
import AxisStatus
import NetPosWdg
import OffsetWdg
import MiscWdg
import RO.Wdg
import TUI.Base.Wdg
import SlewStatus

def addWindow(tlSet):
    """Set up the main status window
    Use name "None.Status" so it doesn't show up in any menu.
    This is because the menus are in this very window --
    so if you can select the menu, this window is already
    the current window.
    """
    tlSet.createToplevel(
        name = "None.Status",
        defGeom = "+0+22",
        resizable = False,
        closeMode = RO.Wdg.tl_CloseDisabled,
        wdgFunc = StatusWdg,
    )

_HelpPrefix = "Telescope/StatusWin.html#"

class StatusWdg (Tkinter.Frame):
    def __init__ (self,
        master = None,
    **kargs):
        """creates a new telescope status frame

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master=master, **kargs)

        self.netPosWdg = NetPosWdg.NetPosWdg(
            master=self,
            borderwidth=1,
        )
        self.netPosWdg.grid(row=1, column=0, sticky="w")
        
        self.slewStatusWdg = SlewStatus.SlewStatusWdg(
            master = self,
        )
        self.slewStatusWdg.grid(row=1, column=1, sticky="ns")

        self.offsetWdg = OffsetWdg.OffsetWdg(
            master=self,
            borderwidth=1,
            relief="ridge",
        )
        self.offsetWdg.grid(row=2, column=0, columnspan=2, sticky="nwse")
        
        self.miscWdg = MiscWdg.MiscWdg(
            master=self,
            borderwidth=1,
            relief="ridge",
        )
        self.miscWdg.grid(row=3, column=0, columnspan=2, sticky="nwse")
        
        self.axisStatusWdg = AxisStatus.AxisStatusWdg(
            master=self,
            borderwidth=1,
            relief="ridge",
        )
        self.axisStatusWdg.grid(row=4, column=0, columnspan=2, sticky="nwse")

        # set up status bar; this is only for showing help,
        # not command status, so we can omit dispatcher and prefs
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            helpURL = _HelpPrefix + "StatusBar",
        )
        self.statusBar.grid(row=5, column=0, columnspan=2, sticky="ew")
    

if __name__ == "__main__":
    import TestData
    
    tuiModel = TestData.testDispatcher.tuiModel

    testFrame = StatusWdg(tuiModel.tkRoot)
    testFrame.pack()

    TestData.runTest()

    tuiModel.reactor.run()
