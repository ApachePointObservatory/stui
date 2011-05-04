#!/usr/bin/env python
"""APOGEE Collimator control and status

History:
2011-05-03 ROwen
"""
import Tkinter
import RO.Wdg
import RO.TkUtil
import RO.StringUtil
import TUI.Models
import opscore.actor.keyvar
import TUI.Base.Wdg

class CollWdg(Tkinter.Frame):
    def __init__ (self,
        master,
        statusBar,
        helpURL = None,
        **kargs):
        """creates a new widget for specifying collimator focus, pitch and yaw

        Inputs:
        - master        master Tk widget
        - statusBar     status bar widget
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        
        row = 0

        self.pistonWdg = CollItemWdg(
            master = self,
            name = "Piston",
            statusBar = statusBar,
            helpURL = helpURL,
        )
        self.pistonWdg.grid(row=row, column=0, columnspan=4, sticky="w")
        row += 1

        self.pitchWdg = CollItemWdg(
            master = self,
            name = "Pitch",
            statusBar = statusBar,
            helpURL = helpURL,
        )
        self.pitchWdg.grid(row=row, column=0, columnspan=4, sticky="w")
        row += 1

        self.yawWdg = CollItemWdg(
            master = self,
            name = "Yaw",
            statusBar = statusBar,
            helpURL = helpURL,
        )
        self.yawWdg.grid(row=row, column=0, columnspan=4, sticky="w")
        
        self.model = TUI.Models.getModel("apogee")
        self.model.collOrient.addCallback(self._collOrientCallback)
    
    def _collOrientCallback(self, keyVar):
        """collOrient keyword callback
        """
        self.pistonWdg.currFocusWdg.set(keyVar[0], isCurrent=keyVar.isCurrent)
        self.pitchWdg.currFocusWdg.set(keyVar[1], isCurrent=keyVar.isCurrent)
        self.yawWdg.currFocusWdg.set(keyVar[2], isCurrent=keyVar.isCurrent)


class CollItemWdg(TUI.Base.Wdg.FocusWdg):
    """Control piston, pitch or yaw
    """
    def __init__(self, master, name, statusBar, helpURL=None):
        self.actor = "apogee"
        self.cmdVerb = name.lower()
        if self.cmdVerb == "piston":
            increments = (10, 25, 50, 100)
            defIncr = increments[1]
            units = RO.StringUtil.MuStr + "m"
            formatStr = "%0.0f"
        else:
            increments = "0.25 0.50 0.75 1.0 2.0 3.0 4.0 5.0".split()
            defIncr = increments[3]
            units = "pix"
            formatStr = "%0.2f"

        TUI.Base.Wdg.FocusWdg.__init__(self,
            master,
            label = name,
            statusBar = statusBar,
            increments = increments,
            defIncr = defIncr,
            helpURL = helpURL,
            formatStr = formatStr,
            labelWidth = 5,
            focusWidth = 8,
            units = units,
            buttonFrame = None,
        )
        self.setButton.grid_remove()
    
    def createFocusCmd(self, newFocus, isIncr=False):
        """Create and return the focus command"""
        if not isIncr:
            raise RuntimeError("Absolute moves are not supported")
        cmdStr = "%s=%s" % (self.cmdVerb, newFocus)

        return opscore.actor.keyvar.CmdVar (
            actor = self.actor,
            cmdStr = cmdStr,
        )


if __name__ == "__main__":
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    statusBar = TUI.Base.Wdg.StatusBar(tuiModel.tkRoot)
    testFrame = CollWdg(tuiModel.tkRoot, statusBar=statusBar)
    testFrame.pack(side="top", expand=True)
    statusBar.pack(side="top", fill="x", expand=True)
    
    TestData.start()

    tuiModel.reactor.run()
