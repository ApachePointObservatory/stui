#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-04-04 ROwen    Prerelease test code
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models
import EnvironmentWdgSet

_EnvWidth = 6 # width of environment value columns

class ExposureStateWdgSet(object):
    EnvironCat = "environ"
    def __init__(self, gridder, helpURL=None):
        """Create a status widget
        """
        master = gridder._master
        
        self.model = TUI.Models.getModel("apogee")

        self.expStateWdg = RO.Wdg.StrLabel(
            master = master,
            helpText = "Status of current exposure",
            helpURL = helpURL,
            anchor="w",
            width = 11
        )
        gridder.gridWdg("Exp Status", self.expStateWdg)
        
        stateFrame = Tkinter.Frame(master)
        self.utrStateWdg = RO.Wdg.StrLabel(
            master = stateFrame,
            helpText = "Status of current up-the-ramp read",
            helpURL = helpURL,
            anchor="w",
            width = 11
        )
        self.utrStateWdg.pack(side="left")
        self.utrTimer = RO.Wdg.TimeBar(
            master = stateFrame,
            valueFormat = "%3.1f sec",
            isHorizontal = True,
            autoStop = True,
            helpText = "Status of current exposure",
            helpURL = helpURL,
        )
        gridder.gridWdg("UTR Read", stateFrame, sticky="ew")
        
        self.readNameWdg = RO.Wdg.StrLabel(
            master = master,
            helpText = "Name of current UTR read",
            helpURL = helpURL,
            anchor="w",
            width = 11
        )
        gridder.gridWdg("Read Name", self.readNameWdg)

        self.model.exposureState.addCallback(self._exposureStateCallback)
        self.utrStateWdg.set("?")
        self.readNameWdg.set("?")
    
    def _exposureStateCallback(self, keyVar):
        """exposureState keyVar callback
        """
        if keyVar[0] == None:
            stateStr = "?"
        else:
            stateStr = " ".join(str(val) for val in keyVar)
        self.expStateWdg.set(stateStr, isCurrent=keyVar.isCurrent)
    
    def _updUTRReadState(self, utrState):
        """UTR read state has been updated
        """
        raise NotImplementedError("No such keyVar yet")


if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = Tkinter.Frame(root)
    gridder = RO.Wdg.Gridder(testFrame)
    expStateWdg = ExposureStateWdgSet(gridder)
    testFrame.pack(side="top", expand=True)
    
    statusBar = TUI.Base.Wdg.StatusBar(root)
    statusBar.pack(side="top", expand=True, fill="x")

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
