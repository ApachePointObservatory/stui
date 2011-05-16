#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-04-04 ROwen    Prerelease test code
2011-04-28 ROwen    Modified for new keyword dictionary.
2011-05-02 ROwen    Display dither state if bad: indexer off or limit switches fired.
2011-05-16 ROwen    Fix bug in handling unknown dither pixel position.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models
import LimitParser
import TelemetryWdgSet
import ExposureStateWdgSet

_EnvWidth = 6 # width of environment value columns

class StatusWdg(Tkinter.Frame):
    EnvironCat = "environ"
    def __init__(self, master, helpURL=None):
        """Create a status widget
        """
        Tkinter.Frame.__init__(self, master)
        
        gridder = RO.Wdg.Gridder(master=self, sticky="w")
        self.gridder = gridder
        
        self.model = TUI.Models.getModel("apogee")

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

        ditherFrame = Tkinter.Frame(self)
        self.ditherPositionWdg = RO.Wdg.StrLabel(
            master = ditherFrame,
            helpText = "Dither position",
            helpURL = helpURL,
            anchor="w",
        )
        self.ditherPositionWdg.pack(side="left")
        self.ditherStateWdg = RO.Wdg.StrLabel(
            master = ditherFrame,
            helpText = "Dither actuator state",
            helpURL = helpURL,
            anchor="w",
        )
        self.ditherStateWdg.pack(side="left")
        gridder.gridWdg("Dither", ditherFrame)
        
        self.model.ditherPosition.addCallback(self._ditherPositionCallback)
        self.model.ditherIndexer.addCallback(self._ditherStateCallback)
        self.model.ditherLimitSwitch.addCallback(self._ditherStateCallback)
        self.shutterStateWdg.set("?")
        self.ledStateWdg.set("?")

        self.environWdgSet = TelemetryWdgSet.TelemetryWdgSet(
            gridder = gridder,
            colSpan = 4,
            helpURL = helpURL,
        )

        self.columnconfigure(3, weight=1)

        gridder.allGridded()
    
    def _ditherStateCallback(self, *dum):
        """ditherIndexer and ditherLimitSwitch callback
        """
        strVal = ""
        severity = RO.Constants.sevNormal
        isCurrent = self.model.ditherIndexer.isCurrent and self.model.ditherLimitSwitch.isCurrent
        
        if self.model.ditherIndexer[0] == False:
            strVal = "Off"
            severity = RO.Constants.sevError
            self.ditherPositionWdg.set("")
        else:
            limStrList, severity = LimitParser.limitParser(self.model.ditherLimitSwitch)
            if severity != RO.Constants.sevNormal:
                strVal = "Limits %s" % (" ".join(limStrList),)

# nicer output but less direct                    
#             strVal, severity = {
#                 (False, False): ("", RO.Constants.sevNormal),
#                 (None,  True):  ("Fwd limit", RO.Constants.sevWarning),
#                 (False, True):  ("Fwd limit", RO.Constants.sevWarning),
#                 (True,  False): ("Rev limit", RO.Constants.sevWarning),
#                 (True,  None):  ("Rev limit", RO.Constants.sevWarning),
#                 (True,  True):  ("Both limits", RO.Constants.sevError),
#             }.get(tuple(self.model.ditherLimitSwitch[0:2]), ("Unknown limits", RO.Constants.sevWarning))
        self.ditherStateWdg.set(strVal, isCurrent=isCurrent, severity=severity)
       
    def _ditherPositionCallback(self, keyVar):
        """ditherPosition keyVar callback
        """
        severity = RO.Constants.sevNormal
        if self.model.ditherIndexer[0] == False:
            strVal = ""
        elif keyVar[0] == None:
            strVal = "?"
            severity = RO.Constants.sevWarning
        elif keyVar[1] == "?":
            strVal = "%0.2f pixels" % (keyVar[0],)
        else:
            strVal = "%s = %0.2f pixels" % (keyVar[1], keyVar[0])
        self.ditherPositionWdg.set(strVal, isCurrent=keyVar.isCurrent, severity=severity)
    
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
