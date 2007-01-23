#!/usr/local/bin/python
"""Downloads window

2005-07-08 ROwen
"""
import RO.Alg
import RO.Wdg.HTTPGetWdg

_MaxLines = 100
_MaxTransfers = 5

def addWindow(tlSet, visible=False):
    tlSet.createToplevel (
        name = "TUI.Downloads",
        defGeom = "+835+290",
        wdgFunc = RO.Alg.GenericCallback(
            RO.Wdg.HTTPGetWdg.HTTPGetWdg,
            maxTransfers = _MaxTransfers,
            maxLines = _MaxLines,
            helpURL = "TUIMenu/DownloadsWin.html",
        ),
        visible = visible,
    )
