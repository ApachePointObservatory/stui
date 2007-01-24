#!/usr/bin/env python
from __future__ import generators
"""Status/config and exposure windows for the Echelle.

History:
2003-12-08 ROwen
2005-06-10 ROwen    Added test code.
2005-06-14 ROwen    Corrected a comment that said GRIM.
"""
import RO.Alg
import TUI.Inst.ExposeWdg
import StatusConfigWdg

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "None.Echelle Expose",
        defGeom = "+452+280",
        resizable = False,
        wdgFunc = RO.Alg.GenericCallback (
            TUI.Inst.ExposeWdg.ExposeWdg,
            instName = "Echelle",
        ),
        visible=False,
    )
    
    tlSet.createToplevel (
        name = "Inst.Echelle",
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
    expTl = TestData.tuiModel.tlSet.getToplevel("None.Echelle Expose")
    expFrame = expTl.getWdg()
    mainTl = TestData.tuiModel.tlSet.getToplevel("Inst.Echelle")
    mainTl.makeVisible()
    mainFrame = mainTl.getWdg()

    TestData.dispatch()
    
    root.mainloop()
