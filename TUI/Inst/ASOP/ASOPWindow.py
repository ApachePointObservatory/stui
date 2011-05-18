#!/usr/bin/env python
"""ASOP window.

History:
2011-05-15 SBelend
"""
import ASOPWdg

_WindowTitle = "Inst.ASOP"

def addWindow(tlSet):
    # about window
    tlSet.createToplevel(
        name = _WindowTitle,
        defGeom = "+300+300",
        resizable = False,
        visible = True,
        wdgFunc = ASOPWdg.ASOPWdg,
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
