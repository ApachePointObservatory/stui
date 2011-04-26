#!/usr/bin/env python
"""Display status of APOGEE QuickLook Actor
"""
import Tkinter
import RO.Wdg
import APOGEEWdg

_HelpURL = None
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
    )


if __name__ == '__main__':
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot

    addWindow(tuiModel.tlSet, visible=True)

    tuiModel.reactor.run()
