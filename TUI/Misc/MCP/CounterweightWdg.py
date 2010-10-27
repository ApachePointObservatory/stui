#!/usr/bin/env python
"""Counterweight widgets

History:
2010-10-27
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Base.Wdg
import TUI.Models

_HelpURL = "Misc/MCPWin.html"
Width = 6

class CounterweightPosWdg(Tkinter.Frame):
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)
        self.wdgSet = CounterweightPosWdgSet(master = self, width = Width, helpURL = _HelpURL)
        for wdg in self.wdgSet.wdgList:
            wdg.pack(side="left")

class CounterweightStatusWdg(Tkinter.Frame):
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)
        self.wdgSet = CounterweightStatusWdgSet(master = self, width = Width, helpURL = _HelpURL)
        for wdg in self.wdgSet.wdgList:
            wdg.pack(side="left")

class CounterweightPosWdgSet(object):
    """Contains a set of widgets that display counterweight position
    
    The widgets are NOT gridded or packed into their master.
    
    The widgets are in self.wdgList
    """
    def __init__(self,
        master,
        width,
        helpURL = None,
    ):
        """Create a CounterweightWdgSet
        
        Inputs:
        - master: parent widget
        """
        width = int(width)
        mcpModel = TUI.Models.getModel("mcp")
        self.wdgList = []
        for i in range(4):
            cwNum = i + 1
            wdg = RO.Wdg.IntLabel(
                master = master,
                width = width,
                helpText = "position of counterweight %s" % (cwNum,),
                helpURL = helpURL,
            )
            self.wdgList.append(wdg)
        mcpModel.cwPositions.addCallback(self.cwPositionsCallback)
        
    def cwPositionsCallback(self, cwPositions):
        isCurrent = cwPositions.isCurrent
        for i, wdg in enumerate(self.wdgList):
            wdg.set(cwPositions[i], isCurrent=isCurrent)

class CounterweightStatusWdgSet(object):
    """Contains a set of widgets that display counterweight status
    
    The widgets are NOT gridded or packed into their master.
    
    The widgets are in self.wdgList
    """
    _StatusDict = {
        "..": ("OK", RO.Constants.sevNormal),
        "L.": ("L Lim", RO.Constants.sevError),
        ".U": ("U Lim", RO.Constants.sevError),
        "LU": ("Bad", RO.Constants.sevError),
        None: ("", RO.Constants.sevNormal),
    }
    def __init__(self,
        master,
        width,
        helpURL = None,
    ):
        """Create a CounterweightWdgSet
        
        Inputs:
        - master: parent widget
        """
        width = int(width)
        mcpModel = TUI.Models.getModel("mcp")
        self.wdgList = []
        for i in range(4):
            cwNum = i + 1
            wdg = RO.Wdg.StrLabel(
                master = master,
                width = width,
                helpText = "status of counterweight %s" % (cwNum,),
                helpURL = helpURL,
            )
            self.wdgList.append(wdg)
        mcpModel.cwStatus.addCallback(self.cwStatusCallback)
        
    def cwStatusCallback(self, cwStatus):
        isCurrent = cwStatus.isCurrent
        for i, wdg in enumerate(self.wdgList):
            statusStr, severity = self._StatusDict.get(cwStatus[i], ("???", RO.Constants.sevError))
            wdg.set(statusStr, isCurrent=isCurrent, severity=severity)
            
        
if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    row = 0
    RO.Wdg.StrLabel(root, text="CW Pos").grid(row=row, column=0)
    posFrame = CounterweightPosWdg(root)
    posFrame.grid(row=row, column=1)
    row += 1
    
    RO.Wdg.StrLabel(root, text="CW Status").grid(row=row, column=0)
    statusFrame = CounterweightStatusWdg(root)
    statusFrame.grid(row=row, column=1)
    row += 1

    statusBar = TUI.Base.Wdg.StatusBar(
        master = root,
        helpURL = _HelpURL,
    )
    statusBar.grid(row=row, column=0, columnspan=5, sticky="ew")
    row += 1
    
    Tkinter.Button(root, text="Demo", command=TestData.animate).grid(row=row, column=0)
    row += 1
    
    TestData.start()

    tuiModel.reactor.run()
