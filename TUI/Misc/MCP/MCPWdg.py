#!/usr/bin/env python
"""Status and control for the MCP

History:
2009-04-03 ROwen
2009-07-09 ROwen    Modified button enable code.
2009-08-25 ROwen    Modified for change to mcp dictionary: ffsCommandedOn -> ffsCommandedOpen.
2010-03-12 ROwen    Changed to use Models.getModel.
2010-06-28 ROwen    Bug fix: Device.__str__ was not defined due to incorrect indentation (thanks to pychecker).
                    Removed two statements that had no effect (thanks to pychecker).
2010-10-29 ROwen    Added counterweight status and spectrograph slithead status.
                    Moved bipolar device code to a new module BipolarDeviceWdg.
2011-09-02 ROwen    Separated functionality into CmdWdg and StatusWdg.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Base.Wdg
import CmdWdg
import StatusWdg

_HelpURL = "Misc/MCPWin.html"

class MCPWdg (Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        """Create a widget to control the MCP
        """
        Tkinter.Frame.__init__(self, master, **kargs)

        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
            helpURL = _HelpURL,
        )

        self.cmdWdg = CmdWdg.CmdWdg(
            master = self,
            statusBar = self.statusBar,
            helpURL = _HelpURL,
        )
        self.cmdWdg.grid(row=0, column=0, sticky="nw")

        self.statusWdg = StatusWdg.StatusWdg(
            master = self,
            helpURL = _HelpURL,
        )
        self.statusWdg.grid(row=0, column=1, sticky="nw")

        self.statusBar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def __str__(self):
        return self.__class__.__name__


if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = MCPWdg(root)
    testFrame.pack()

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()

    TestData.start()

    tuiModel.reactor.run()
