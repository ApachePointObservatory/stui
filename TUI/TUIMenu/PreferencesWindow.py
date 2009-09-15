#!/usr/bin/env python
"""Preferences window

2003-12-17 ROwen
"""
import RO.Alg
import RO.Prefs.PrefWdg
import TUI.Models.TUIModel

def addWindow(tlSet):
    tuiModel = TUI.Models.TUIModel.Model()

    # preferences window
    tlSet.createToplevel (
        name = "STUI.Preferences",
        defGeom = "+62+116",
        resizable = False,
        visible = False,
        wdgFunc = RO.Alg.GenericCallback(
            RO.Prefs.PrefWdg.PrefWdg,
            prefSet=tuiModel.prefs,
        ),
    )
