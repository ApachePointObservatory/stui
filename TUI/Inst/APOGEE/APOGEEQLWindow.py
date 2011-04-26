#!/usr/bin/env python
"""Display status of APOGEE QuickLook Actor
"""
import Tkinter
import RO.Wdg
import APOGEEQLWdg

_HelpURL = None
WindowName = "Inst.APOGEE QL"

def addWindow(tlSet, visible=False):
    """Create the window.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+434+22",
        visible = visible,
        resizable = False,
        wdgFunc = APOGEEQLWdg.APOGEEQLWdg,
    )


if __name__ == '__main__':
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot

    addWindow(tuiModel.tlSet, visible=True)

    tuiModel.reactor.run()
