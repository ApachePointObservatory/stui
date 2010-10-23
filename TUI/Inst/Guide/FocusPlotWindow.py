#!/usr/bin/env python
"""Alerts window.

History:
2009-09-14 ROwen
"""
import FocusPlotWdg

WindowName = "Inst.Focus Plot"

def addWindow(tlSet):
    # about window
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "400x400+400+400",
        resizable = True,
        visible = True,
        wdgFunc = FocusPlotWdg.FocusPlotWdg,
    )


if __name__ == "__main__":
    import Tkinter
    import GuideTest

    tlSet = GuideTest.tuiModel.tlSet
    
    addWindow(tlSet)
    tlSet.makeVisible(WindowName)
#     Tkinter.Button(GuideTest.tuiModel.tkRoot, text="Demo", command=GuideTest.animate).pack()
#     GuideTest.start()
    GuideTest.tuiModel.reactor.run()
