#!/usr/bin/env python
"""
To do:
- Add a log area to show substage (multicommands) state

History:
2010-06-28 ROwen    Removed many unused imports (thanks to pychecker).
2011-07-05 ROwen    Added support for new sop keyword "surveyCommands"
2014-08-29          Enhanced output of guider keyword "survey" to show the second field.
                    Added output of new sop keyword "survey"; only shown if different than guider.survey.
"""
import tkinter
if __name__ == "__main__":
    import RO.Comm.Generic
    RO.Comm.Generic.setFramework("tk")
import TUI.Base.Wdg
import TUI.Models
from . import BypassWdg
from . import ScriptWdg
from . import Descr

_HelpURL = "Instruments/SOPWindow.html"


class SOPWdg(tkinter.Frame):
    """Main sop widget
    """
    def __init__(self, master):
        """Construct the main sop widget

        Inputs:
        - master: master widget
        - helpURL: URL of help file
        """
        tkinter.Frame.__init__(self, master)

        self.sopModel = TUI.Models.getModel("sop")

        self.msgBar = TUI.Base.Wdg.StatusBar(
            master=self,
            helpURL=_HelpURL,
            helpText="sop status",
        )
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master=self,
            playCmdSounds=True,
            helpURL=_HelpURL,
        )

        row = 0

        self.alwaysShowCommands = set(["loadcartridge"])

        self.commandList = Descr.getCommandList()

        for command in self.commandList:
            command.build(
                master=self,
                msgBar=self.msgBar,
                statusBar=self.statusBar,
                helpURL=_HelpURL,
            )
            command.wdg.grid(row=row, column=0, sticky="ew")
            row += 1

        script_wdg = ScriptWdg.ScriptWdg(
            master=self,
            msgBar=self.msgBar,
            statusBar=self.statusBar,
            helpURL=_HelpURL)
        script_wdg.wdg.grid(row=row, column=0, sticky="ew")
        row += 1

        BypassWdg.BypassWdg(
            master=self,
            statusBar=self.statusBar,
            helpURL=_HelpURL,
        ).grid(row=row, column=0, sticky="ew")
        row += 1

        self.msgBar.grid(row=row, column=0, columnspan=10, sticky="ew")
        row += 1
        self.statusBar.grid(row=row, column=0, columnspan=10, sticky="ew")
        row += 1

        self.sopModel.surveyCommands.addCallback(self._surveyCommandsCallback)

    def _surveyCommandsCallback(self, keyVar):
        """Callback function for the surveyCommands keyword
        """
        if None in keyVar:
            return
        commandsToShow = set(name.lower() for name in keyVar) | self.alwaysShowCommands
        for command in self.commandList:
            if command.name.lower() in commandsToShow:
                command.wdg.grid()
            else:
                command.wdg.grid_remove()


if __name__ == "__main__":
    from . import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = SOPWdg(root)
    testFrame.pack()

    tkinter.Button(root, text="Demo", command=TestData.animate).pack()

    TestData.start()

    tuiModel.reactor.run()
