#!/usr/bin/env python
"""Instant messaging widget.

History:
2009-07-19 ROwen
2010-03-12 ROwen    Changed to use Models.getModel.
2012-09-28 ROwen    Updated to use new plc package (which subsumes interlocks).
"""
import os
import time
import Tkinter
import opscore.protocols
import plc
import RO.Wdg
import TUI.Models

def addWindow(tlSet):
    # about window
    mcpModel = TUI.Models.getModel("mcp")
    tlSet.createToplevel(
        name = "Misc.Interlocks",
        defGeom = "+350+350",
        resizable = False,
        visible = False,
        wdgFunc = RO.Alg.GenericCallback(plc.InterlocksWdg, mcpModel=mcpModel),
    )

_HelpPage = "Misc/InterlocksWin.html"

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp")
    tuiModel = testDispatcher.tuiModel

    testFrame = plc.InterlocksWdg(tuiModel.tkRoot)
    testFrame.pack(fill="both", expand=True)
    
    tuiModel.reactor.run()
