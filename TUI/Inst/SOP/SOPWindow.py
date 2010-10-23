#!/usr/bin/env python
"""SOP window.

History:
2010-05-26 ROwen
"""
import SOPWdg

_WindowTitle = "Inst.SOP"

def addWindow(tlSet):
    # about window
    tlSet.createToplevel(
        name = _WindowTitle,
        defGeom = "+300+300",
        resizable = False,
        visible = True,
        wdgFunc = SOPWdg.SOPWdg,
    )


if __name__ == "__main__":
    import Tkinter
    import TestData
    
    tlSet = TestData.tuiModel.tlSet
    addWindow(tlSet)
    tlSet.makeVisible(_WindowTitle)
    Tkinter.Button(TestData.tuiModel.tkRoot, text="Demo", command=TestData.animate).pack()
    TestData.start()
    TestData.tuiModel.reactor.run()
