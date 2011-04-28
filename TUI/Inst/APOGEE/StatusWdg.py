#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-04-04 ROwen    Prerelease test code
2011-04-28 ROwen    Modified for new keyword dictionary.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models
import TelemetryWdgSet
import ExposureStateWdgSet

_EnvWidth = 6 # width of environment value columns

class StatusWdg(Tkinter.Frame):
    EnvironCat = "environ"
    def __init__(self, master, helpURL=None):
        """Create a status widget
        """
        Tkinter.Frame.__init__(self, master)
        
        gridder = RO.Wdg.StatusConfigGridder(master=self, sticky="w")
        
        self.model = TUI.Models.getModel("apogee")
#        self.qlModel = TUI.Models.getModel("apogeeql")
        self.tuiModel = TUI.Models.getModel("tui")

        self.expStateWdgSet = ExposureStateWdgSet.ExposureStateWdgSet(
            gridder = gridder,
            helpURL = helpURL,
        )
        self.shutterStateWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Status of cold shutter",
            helpURL = helpURL,
            anchor="w",
            width = 11
        )
#        gridder.gridWdg("Shutter", self.shutterStateWdg)

        self.ledStateWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Status of LEDs on cold shutter",
            helpURL = helpURL,
            anchor="w",
            width = 11
        )
#        gridder.gridWdg("LEDs", self.ledStateWdg)

        self.ditherStateWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Current dither position",
            helpURL = helpURL,
            anchor="w",
        )
        gridder.gridWdg("Dither", self.ditherStateWdg)
        
        self.model.ditherPosition.addCallback(self._ditherPositionCallback)
        self.shutterStateWdg.set("?")
        self.ledStateWdg.set("?")

        
        self.environWdgSet = TelemetryWdgSet.TelemetryWdgSet(
            gridder = gridder,
            colSpan = 4,
            helpURL = helpURL,
        )

        self.columnconfigure(3, weight=1)

        gridder.allGridded()
        
    def _ditherPositionCallback(self, keyVar):
        """ditherPosition keyVar callback
        """
        if keyVar[0] is None:
            strVal = "?"
        elif keyVar[1] == "?":
            strVal = "%0.2f pixels" % (keyVar[0],)
        else:
            strVal = "%s = %0.2f pixels" % (keyVar[1], keyVar[0])
        self.ditherStateWdg.set(strVal, isCurrent=keyVar.isCurrent)
    
    def _shutterStateCallback(self, shutter):
        """shutter state has been updated
        """
        self.shutterStateWdg.set(shutter[0], isCurrent=keyVar.isCurrent)
        raise NotImplementedError("No such keyVar yet")
    
    def _ledStateCallback(self, led):
        """led state has been updated
        """
        self.ledStateWdg.set(shutter[0], isCurrent=keyVar.isCurrent)
        

if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = StatusWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand=True)
    
    statusBar = TUI.Base.Wdg.StatusBar(root)
    statusBar.pack(side="top", expand=True, fill="x")

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
