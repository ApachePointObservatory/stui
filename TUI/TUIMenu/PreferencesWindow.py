#!/usr/bin/env python
"""Preferences window

2003-12-17 ROwen
2009-11-05 ROwen    Added WindowName.
"""
import RO.Alg
import RO.Prefs.PrefWdg
import TUI.Models.TUIModel

WindowName = "STUI.Preferences"

def addWindow(tlSet):
    tuiModel = TUI.Models.TUIModel.Model()

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
