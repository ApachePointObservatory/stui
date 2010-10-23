#!/usr/bin/env python
"""
To do:
- Support showing special engineering bypass (no command or keywords for this yet --
  it's hacked into the bypass command, but that will change and it may not
  show up in the current bypassed keyword
- Support test/science (no command or keywords for this yet)
- Add a log area to show substage (multicommands) state

History:
2010-06-28 ROwen    Removed many unused imports (thanks to pychecker).
"""
import Tkinter
import TUI.Base.Wdg
import TUI.Models
import BypassWdg
import CommandWdgSet
import Descr

_HelpURL = "Instruments/SOPWindow.html"

class SOPWdg(Tkinter.Frame):
    """Main sop widget
    """
    def __init__(self, master):
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
            helpURL = _HelpURL,
        )
        
        row = 0
        
        for command in Descr.getCommandList():
            command.build(
                master = self,
                statusBar = self.statusBar,
                helpURL = _HelpURL,
            )
            command.wdg.grid(row = row, column = 0, sticky="ew")
            row += 1
        
        BypassWdg.BypassWdg(
            master = self,
            statusBar = self.statusBar,
            helpURL = _HelpURL,
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

