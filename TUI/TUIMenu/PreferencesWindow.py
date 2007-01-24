#!/usr/bin/env python
"""Preferences window

2003-12-17 ROwen
"""
import RO.Alg
import RO.Prefs.PrefWdg
import TUI.TUIModel

def addWindow(tlSet):
    tuiModel = TUI.TUIModel.getModel()

    # preferences window
    tlSet.createToplevel (
        name = "TUI.Preferences",
        defGeom = "+62+116",
        resizable = False,
        visible = False,
        wdgFunc = RO.Alg.GenericCallback(
            RO.Prefs.PrefWdg.PrefWdg,
            prefSet=tuiModel.prefs,
        ),
    )
