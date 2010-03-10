#!/usr/bin/env python
"""Downloads window

2005-07-08 ROwen
2009-09-14 ROwen    Added WindowName variable; tweaked default geometry.
2010-03-10 ROwen    Compute WindowName from TUI.Version.ApplicationName
"""
import RO.Alg
import RO.Wdg.HTTPGetWdg
import TUI.Version

_MaxLines = 100
_MaxTransfers = 5

WindowName = "%s.Downloads" % (TUI.Version.ApplicationName,)

def addWindow(tlSet, visible=False):
    tlSet.createToplevel (
        name = WindowName,
        defGeom = "403x374+1235+23",
        wdgFunc = RO.Alg.GenericCallback(
            RO.Wdg.HTTPGetWdg.HTTPGetWdg,
            maxTransfers = _MaxTransfers,
            maxLines = _MaxLines,
            helpURL = "TUIMenu/DownloadsWin.html",
        ),
        visible = visible,
    )
