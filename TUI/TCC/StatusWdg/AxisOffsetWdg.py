#!/usr/bin/env python
"""Displays calibration and guide offsets

History:
2011-02-16 ROwen
"""
import Tkinter
import RO.CnvUtil
import RO.CoordSys
import RO.StringUtil
import RO.Wdg
import TUI.Models

_HelpURL = "Telescope/StatusWin.html#Offsets"
_DataWidth = 10

class AxisOffsetWdg (Tkinter.Frame):
    def __init__ (self, master=None, **kargs):
        """creates a new offset display frame

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.tccModel = TUI.Models.getModel("tcc")
        gr = RO.Wdg.Gridder(self, sticky="w")
        
        MountLabels = ("Az", "Alt", "Rot")

        # calib offset
        gr.gridWdg("Calib Off")
        gr.startNewCol()
        self.calibOffWdgSet = [
            RO.Wdg.DMSLabel(
                master = self,
                precision = 1,
                width = _DataWidth,
                helpText = "Calibration offset",
                helpURL = _HelpURL,
            )
            for ii in range(3)
        ]
        for ii, label in enumerate(MountLabels):
            wdgSet = gr.gridWdg (
                label = label,
                dataWdg = self.calibOffWdgSet[ii],
                units = RO.StringUtil.DMSStr,
            )
            wdgSet.labelWdg.configure(width=4, anchor="e")
        
        bottomRow = gr.getNextRow()

        # guide offset
        gr.startNewCol()
        gr.gridWdg("Guide Off")
        gr.startNewCol()
        self.guideOffWdgSet = [
            RO.Wdg.DMSLabel(
                master = self,
                precision = 1,
                width = _DataWidth,
                helpText = "Guide offset",
                helpURL = _HelpURL,
            )
            for ii in range(3)
        ]
        for ii, label in enumerate(MountLabels):
            wdgSet = gr.gridWdg (
                label = label,
                dataWdg = self.guideOffWdgSet[ii],
                units = RO.StringUtil.DMSStr,
            )
            wdgSet.labelWdg.configure(width=4, anchor="e")

        # allow the last+1 column to grow to fill the available space
        self.columnconfigure(gr.getMaxNextCol(), weight=1)

        self.tccModel.calibOff.addValueListCallback([wdg.set for wdg in self.calibOffWdgSet], cnvFunc=RO.CnvUtil.posFromPVT)
        self.tccModel.guideOff.addValueListCallback([wdg.set for wdg in self.guideOffWdgSet], cnvFunc=RO.CnvUtil.posFromPVT)

        
if __name__ == "__main__":
    import TestData

    tuiModel = TestData.tuiModel

    testFrame = OffsetWdg(tuiModel.tkRoot)
    testFrame.pack()

    TestData.init()

    tuiModel.reactor.run()
