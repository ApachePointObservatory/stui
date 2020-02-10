#!/usr/bin/env python
"""Slithead widgets

History:
2010-10-29 ROwen
"""
import tkinter
import RO.Constants
import RO.Wdg
import TUI.Base.Wdg
import TUI.Models

class SlitheadWdgList(object):
    _StatusDict = {
        (False, False): ("Out", RO.Constants.sevNormal),
        (True, True): ("In", RO.Constants.sevNormal),
        (False, True): ("Unlatched", RO.Constants.sevWarning),
        (True, False): ("Bad", RO.Constants.sevError),
        
    }
    def __init__(self, master, width=9, helpURL=None):
        width = int(width)
        mcpModel = TUI.Models.getModel("mcp")
        
        self.wdgList = []

        for i in range(2):
            spNum = i + 1
            wdg = RO.Wdg.StrLabel(
                master = master,
                width = width,
                anchor = "w",
                helpText = "Status of spectrograph %d slithead" % (spNum,),
                helpURL = helpURL,
            )
            self.wdgList.append(wdg)

        for i in range(2):
            spNum = i + 1
            def callFunc(keyVar, ind=i):
                self.spSlitheadCallFunc(keyVar, ind)
            keyVar = getattr(mcpModel, "sp%dSlithead" % (spNum,))
            keyVar.addCallback(callFunc)

    def __getitem__(self, ind):
        return self.wdgList[ind]

    def __len__(self):
        return len(self.wdgList)

    def __iter__(self):
        return iter(self.wdgList)
        
    def spSlitheadCallFunc(self, keyVar, ind):
        """
        Key("sp1Slithead", 
            Enum("00", "01", "10", "11", descr=("?", "Open", "Closed", "Invalid")),
            Bool("0", "1", help="Latch extended"),
            Bool("0", "1", help="Slithead in place")),
    
        However, the first field is always 10 so I am ignoring it for now.
        Also "Latch extended" appears to mean "latched".
        """
        wdg = self.wdgList[ind]
        isExtended = keyVar[1]
        isIn = keyVar[2]
        statusStr, severity = self._StatusDict.get((isExtended, isIn), ("???", RO.Constants.sevWarning))
        wdg.set(statusStr, isCurrent=keyVar.isCurrent, severity=severity)

        
if __name__ == '__main__':
    from . import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    row = 0
    cwWdgList = SlitheadWdgList(root)
    for i, wdg in enumerate(cwWdgList):
        spNum = i + 1
        RO.Wdg.StrLabel(root, text="CW %d" % (spNum,)).grid(row=row, column=0)
        wdg.grid(row=row, column=1)
        row += 1

    statusBar = TUI.Base.Wdg.StatusBar(
        master = root,
    )
    statusBar.grid(row=row, column=0, columnspan=5, sticky="ew")
    row += 1
    
    tkinter.Button(root, text="Demo", command=TestData.animate).grid(row=row, column=0)
    row += 1
    
    TestData.start()

    tuiModel.reactor.run()
