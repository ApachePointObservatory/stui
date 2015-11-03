#!/usr/bin/env python
"""Manga Dither widget

History:
2014-10-23 ROwen
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import Tkinter

import RO.Constants
import RO.DS9
import RO.MathUtil
import RO.PhysConst
import RO.OS
import RO.Prefs
import RO.StringUtil
import RO.Wdg
import TUI.Models

class MangaDitherWdg(Tkinter.Frame):
    def __init__(self, master, helpURL=None):
        """Construct a MangaDitherWdg
        
        Inputs:
        - master: master widget
        - helpURL: the help URL for widgets
        """
        Tkinter.Frame.__init__(self, master)
        
        self.guiderModel = TUI.Models.getModel("guider")

        RO.Wdg.StrLabel(
            master = self,
            text = "Manga Dither",
            helpText = "state of MaNGA dither (aka decenter)",
            helpURL = helpURL,
        ).grid(row=0, column=0)

        self.enabledWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "is MaNGA dither (aka decenter) enabled?",
            helpURL = helpURL,
        )
        self.enabledWdg.grid(row=0, column=1)

        self.ditherWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "commanded MaNGA dither (aka decenter) position",
            helpURL = helpURL,
        )
        self.ditherWdg.grid(row=0, column=2)

        self.guiderModel.decenter.addCallback(self.decenterCallback)
        self.guiderModel.mangaDither.addCallback(self.mangaDitherCallback)

    def decenterCallback(self, keyVar):
        """Callback for guider.decenter

        Key("decenter",
            Int(name="expID", help="gcamera exposure number"),
            Bool("disabled", "enabled", help="is decentered guiding mode enabled (was it applied)?"),
            Float(name="RA", help="User specified telescope guiding offset in RA from guider position", units="arcsec"),
            Float(name="DEC", help="User specified telescope offset in Dec from guider position", units="arcsec"),
            Float(name="Rot", help="User specified telescope offset in Rot from guider position", units="arcsec"),
            Float(name="Focus", help="User specified focus offset from guider focus ", units="um"),
            Float(name="Scale", help="User specified scale offset from guider scale ", units="um"),
            doCache = False,
            help="user specified offsets",
        """
        isEnabled = keyVar[1]
        if isEnabled is None:
            enabledStr = "?"
        else:
            enabledStr = "Enabled" if isEnabled else "Disabled"
        self.enabledWdg.set(enabledStr, isCurrent=keyVar.isCurrent)

    def mangaDitherCallback(self, keyVar):
        ditherChar = keyVar[0]
        if ditherChar is None:
            ditherChar = "?"
        self.ditherWdg.set(keyVar[0], isCurrent=keyVar.isCurrent)

if __name__ == "__main__":
    import GuideTest

    root = GuideTest.tuiModel.tkRoot

    testFrame = MangaDitherWdg(root)
    testFrame.pack(expand="yes", fill="both")

    GuideTest.start()
    
    GuideTest.tuiModel.reactor.run()
