#!/usr/bin/env python
"""Python window

2003-12-17 ROwen
2004-05-18 ROwen    Stopped obtaining TUI model in addWindow; it was ignored.
                    Added test code.
2004-06-22 ROwen    Modified to use ScriptWdg->PythonWdg.
2009-11-05 ROwen    Added WindowName.
2010-02-18 ROwen    Fixed the test code.
"""
import RO.Wdg

WindowName = "STUI.Python"

def addWindow(tlSet):
    tlSet.createToplevel (
        name = WindowName,
        defGeom = "+0+507",
        wdgFunc = RO.Wdg.PythonWdg,
        visible = False,
    )

if __name__ == "__main__":
    import TUI.Models.TUIModel

    tuiModel = TUI.Models.TUIModel.Model(True)
    root = tuiModel.tkRoot

    tm = TUI.Models.TUIModel.Model(True)
    addWindow(tm.tlSet)
    tm.tlSet.makeVisible('STUI.Python')

    root.lower()

    tuiModel.reactor.run()
