#!/usr/bin/env python
"""Preferences window

2003-12-17 ROwen
2009-11-05 ROwen    Added WindowName.
2010-03-12 ROwen    Changed to use Models.getModel.
"""
import RO.Alg
import RO.Prefs.PrefWdg
import TUI.Version

WindowName = "%s.Preferences" % (TUI.Version.ApplicationName,)

def addWindow(tlSet):
    tuiModel = TUI.Models.getModel("tui")

    # preferences window
    tlSet.createToplevel (
        name = WindowName,
        defGeom = "+62+116",
        resizable = False,
        visible = False,
        wdgFunc = RO.Alg.GenericCallback(
            RO.Prefs.PrefWdg.PrefWdg,
            prefSet=tuiModel.prefs,
        ),
    )
