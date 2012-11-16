#!/usr/bin/env python
"""Status and control for the MCP

History:
2011-09-02 ROwen    Split from MCPWdg and added display of APOGEE and MARVELS gang connectors.
2011-09-02 ROwen    Gang connector status was wrong (off by one).
2012-11-15 ROwen    Removed MARVELS gang connector.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models
import CounterweightWdg
import SlitheadWdg

class StatusWdg (Tkinter.Frame):
    def __init__(self,
        master,
        helpURL = None,
    **kargs):
        """Create a widget to control the MCP
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.mcpModel = TUI.Models.getModel("mcp")
        
        self.gridder = RO.Wdg.Gridder(self, sticky="w")
        
        self.apogeeGangWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "State of APOGEE gang connector",
            helpURL = helpURL,
        )
        self.gridder.gridWdg("APOGEE Gang", self.apogeeGangWdg)

        self.cwWdgList = CounterweightWdg.CounterweightWdgList(self, helpURL=helpURL)
        for i, wdg in enumerate(self.cwWdgList):
            self.gridder.gridWdg("CW %d" % (i+1,), wdg)
        
        self.spSlitWdgList = SlitheadWdg.SlitheadWdgList(self, helpURL=helpURL)
        for i, wdg in enumerate(self.spSlitWdgList):
            self.gridder.gridWdg("SP%d Slit" % (i+1,), wdg)
        
        nextRow = self.gridder.getNextRow()
        for row in range(nextRow):
            self.rowconfigure(row, pad=3)
        
        self.mcpModel.apogeeGang.addCallback(self._apogeeGangCallback)
        
    def _apogeeGangCallback(self, keyVar):
        strVal, severity = {
            "0": ("Disconnected", RO.Constants.sevWarning),
            "1": ("Podium", RO.Constants.sevNormal),
            "2": ("Cart", RO.Constants.sevNormal),
            "3": ("Sparse Cals", RO.Constants.sevNormal),
        }.get(keyVar[0], ("?", RO.Constants.sevWarning))
        self.apogeeGangWdg.set(strVal, isCurrent=keyVar.isCurrent, severity=severity)

    def __str__(self):
        return self.__class__.__name__

        
if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = StatusWdg(root)
    testFrame.pack()

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.start()

    tuiModel.reactor.run()
