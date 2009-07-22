#!/usr/bin/env python
"""Instant messaging widget.

History:
2009-07-19 ROwen
"""
import os
import time
import Tkinter
import opscore.protocols
import interlocks
import RO.Wdg
import TUI.Models.MCP

def addWindow(tlSet):
    # about window
    mcpModel = TUI.Models.MCP.Model()
    tlSet.createToplevel(
        name = "Misc.Interlocks",
        defGeom = "+350+350",
        resizable = False,
        visible = True,
        wdgFunc = RO.Alg.GenericCallback(interlocks.InterlocksWdg, mcpModel=mcpModel),
    )

_HelpPage = "Misc/InterlocksWin.html"

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp")
    tuiModel = testDispatcher.tuiModel

    testFrame = interlocks.InterlocksWdg(tuiModel.tkRoot)
    testFrame.pack(fill="both", expand=True)
    
    tuiModel.reactor.run()
