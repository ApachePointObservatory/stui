#!/usr/bin/env python
"""Alerts window.

History:
2009-09-14 ROwen
"""
import GuideWdg

_WindowTitle = "Inst.Guide"

def addWindow(tlSet):
    # about window
    tlSet.createToplevel(
        name = _WindowTitle,
        defGeom = "609x642+1234+422",
        resizable = True,
        visible = True,
        wdgFunc = GuideWdg.GuideWdg,
    )


if __name__ == "__main__":
    import Tkinter
    import GuideTest

    tlSet = GuideTest.tuiModel.tlSet
    
    addWindow(tlSet)
    tlSet.makeVisible(_WindowTitle)
#     Tkinter.Button(GuideTest.tuiModel.tkRoot, text="Demo", command=GuideTest.animate).pack()
#     GuideTest.start()
    GuideTest.tuiModel.reactor.run()
