import itertools
import time
import Tkinter
import RO.AddCallback
import TUI.Base.Wdg
import TUI.Models
import opscore.actor
import BasicWdg
import Descr

"""
TO DO: handle commands with stages that may be hidden depending on the current instrument.
Do we have to worry about *DIFFERENT* stages depending on the instrument?
If so, that gets much messier.

But even if it's always the same ones, hidden stages must not be allowed to affect the
Current and Default buttons. Thus the command probably should know which stages are hidden
(perhaps by simply calling isHidden; similarly a setHidden method would be handy).
"""
StateWidth = 10

class MainWdg(Tkinter.Frame):
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
        
        for commandDescr in Descr.CommandDescrList:
            command = BasicWdg.CommandWdg(
                master = self,
                commandDescr = commandDescr,
                statusBar = self.statusBar,
                helpURL = helpURL,
            )
            command.grid(row = row, column = 0)
            row += 1
        
        self.statusBar.grid(row = row, column = 0, columnspan=10, sticky="ew")
        row += 1

if __name__ == "__main__":
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = MainWdg(root)
    testFrame.pack()

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.start()

    tuiModel.reactor.run()

