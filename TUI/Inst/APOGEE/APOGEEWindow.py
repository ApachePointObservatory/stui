#!/usr/bin/env python
"""Display status of APOGEE QuickLook Actor

History:
2011-08-16 ROwen    Save window state.
"""
import tkinter
import RO.Wdg
from . import APOGEEWdg

WindowName = "Inst.APOGEE"

def addWindow(tlSet, visible=False):
    """Create the window.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+346+398",
        visible = visible,
        resizable = False,
        wdgFunc = APOGEEWdg.APOGEEWdg,
        doSaveState = True,
    )


if __name__ == '__main__':
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot

    addWindow(tuiModel.tlSet, visible=True)

    tuiModel.reactor.run()
