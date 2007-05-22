#!/usr/bin/env python
from __future__ import generators
"""Status and configuration for SPIcam.

History:
2007-05-22 ROwen
"""
import RO.Alg
import TUI.Inst.ExposeWdg
import StatusConfigWdg

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "None.SPIcam Expose",
        defGeom = "+452+280",
        resizable = False,
        wdgFunc = RO.Alg.GenericCallback (
            TUI.Inst.ExposeWdg.ExposeWdg,
            instName = "SPIcam",
        ),
        visible = False,
    )
    
    tlSet.createToplevel (
        name = "Inst.SPIcam",
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = StatusConfigWdg.StatusConfigWdg,
        visible = False,
    )


if __name__ == "__main__":
    import RO.Wdg

    root = RO.Wdg.PythonTk()
    
    import TestData

    addWindow(TestData.tuiModel.tlSet)
    expTl = TestData.tuiModel.tlSet.getToplevel("None.SPIcam Expose")
    expFrame = expTl.getWdg()
    mainTl = TestData.tuiModel.tlSet.getToplevel("Inst.SPIcam")
    mainTl.makeVisible()
    mainFrame = mainTl.getWdg()

    TestData.dispatch()
    
    root.mainloop()
