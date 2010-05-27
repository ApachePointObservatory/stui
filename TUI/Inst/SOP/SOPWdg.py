#!/usr/bin/env python
"""
To do:
- Support the bypass command
- Support showing special engineering bypass (no command or keywords for this yet --
  it's hacked into the bypass command, but that will change and it may not
  show up in the current bypassed keyword
- Support test/science (no command or keywords for this yet)
- Add a log area to show substage (multicommands) state
- Add the window to STUI (trivial)
"""
import itertools
import time
import Tkinter
import RO.AddCallback
import TUI.Base.Wdg
import TUI.Models
import opscore.actor
import BypassWdg
import CommandWdgSet
import Descr
import pdb

StateWidth = 10

class SOPWdg(Tkinter.Frame):
    """Main sop widget
    """
    def __init__(self, master, helpURL=None):
        """Construct the main sop widget
        
        Inputs:
        - master: master widget
        - helpURL: URL of help file
        """
        Tkinter.Frame.__init__(self, master)

        self.sopModel = TUI.Models.getModel("sop")

        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
            helpURL = helpURL,
        )
        
        row = 0
        
        for command in Descr.getCommandList():
            command.build(
                master = self,
                statusBar = self.statusBar,
                helpURL = helpURL,
            )
            command.wdg.grid(row = row, column = 0, sticky="ew")
            row += 1
        
        BypassWdg.BypassWdg(
            master = self,
            statusBar = self.statusBar,
            helpURL = helpURL,
        ).grid(row=row, column=0, sticky="ew")
        row += 1
        
        self.statusBar.grid(row = row, column = 0, columnspan=10, sticky="ew")
        row += 1


if __name__ == "__main__":
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = SOPWdg(root)
    testFrame.pack()

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.start()

    tuiModel.reactor.run()

