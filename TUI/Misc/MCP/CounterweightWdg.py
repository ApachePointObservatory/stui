#!/usr/bin/env python
"""Counterweight widgets

History:
2010-10-29 ROwen
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Base.Wdg
import TUI.Models

class CounterweightWdgList(object):
    _StatusDict = {
        "..": ("OK", RO.Constants.sevNormal),
        "L.": ("L Lim", RO.Constants.sevError),
        ".U": ("U Lim", RO.Constants.sevError),
        "LU": ("Bad", RO.Constants.sevError),
        None: ("", RO.Constants.sevNormal),
    }
    def __init__(self, master, posWidth=6, statusWidth=5, helpURL=None):
        posWidth = int(posWidth)
        statusWidth = int(statusWidth)
        mcpModel = TUI.Models.getModel("mcp")
        
        self.wdgList = []
        self.posWdgList = []
        self.statusWdgList = []

        for i in range(4):
            frame = Tkinter.Frame(master)
            cwNum = i + 1
            posWdg = RO.Wdg.IntLabel(
                master = frame,
                width = posWidth,
                helpText = "position of counterweight %s" % (cwNum,),
                helpURL = helpURL,
            )
            self.posWdgList.append(posWdg)
            posWdg.pack(side="left")
            
            statusWdg = RO.Wdg.StrLabel(
                master = frame,
                width = statusWidth,
                anchor = "w",
                helpText = "status of counterweight %s" % (cwNum,),
                helpURL = helpURL,
            )
            self.statusWdgList.append(statusWdg)
            statusWdg.pack(side="left")
            
            self.wdgList.append(frame)

        mcpModel.cwPositions.addCallback(self.cwPositionsCallback)
        mcpModel.cwStatus.addCallback(self.cwStatusCallback)

    def __getitem__(self, ind):
        return self.wdgList[ind]

    def __len__(self):
        return len(self.wdgList)

    def __iter__(self):
        return iter(self.wdgList)
        
    def cwPositionsCallback(self, cwPositions):
        isCurrent = cwPositions.isCurrent
        for i, wdg in enumerate(self.posWdgList):
            wdg.set(cwPositions[i], isCurrent=isCurrent)
        
    def cwStatusCallback(self, cwStatus):
        isCurrent = cwStatus.isCurrent
        for i, wdg in enumerate(self.statusWdgList):
            statusStr, severity = self._StatusDict.get(cwStatus[i], ("???", RO.Constants.sevError))
            wdg.set(statusStr, isCurrent=isCurrent, severity=severity)
            
        
if __name__ == '__main__':
    from . import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    row = 0
    cwWdgList = CounterweightWdgList(root)
    for i, wdg in enumerate(cwWdgList):
        cwNum = i + 1
        RO.Wdg.StrLabel(root, text="CW %d" % (cwNum,)).grid(row=row, column=0)
        wdg.grid(row=row, column=1)
        row += 1

    statusBar = TUI.Base.Wdg.StatusBar(
        master = root,
    )
    statusBar.grid(row=row, column=0, columnspan=5, sticky="ew")
    row += 1
    
    Tkinter.Button(root, text="Demo", command=TestData.animate).grid(row=row, column=0)
    row += 1
    
    TestData.start()

    tuiModel.reactor.run()
