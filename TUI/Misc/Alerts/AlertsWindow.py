#!/usr/bin/env python
"""Alerts window.

History:
2009-07-22 ROwen
2009-08-25 ROwen    Improved default window size.
"""
import AlertsWdg


_WindowTitle = "Misc.Alerts"

def addWindow(tlSet):
    # about window
    tlSet.createToplevel(
        name = _WindowTitle,
        defGeom = "494x216+372+305",
        resizable = True,
        visible = True,
        wdgFunc = AlertsWdg.AlertsWdg,
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
