#!/usr/bin/env python
"""State of BOSS ICC and configuration controls.

To do:
- Set collimator status summary fields
- Add environment fields
- Add Hartmann screen and collimator controls
- Add exposure controls
"""
import Tkinter
import RO.Wdg
import RO.Constants
import RO.SeqUtil
import TUI.Base.Wdg
import TUI.PlaySound
import TUI.Models.BOSSModel
import ExposureStateWdg

_HelpURL = None

_ShutterStateSevDict = {
    None: ("?",       RO.Constants.sevNormal),
    0:    ("?",       RO.Constants.sevWarning),
    1:    ("Closed",  RO.Constants.sevNormal),
    2:    ("Open",    RO.Constants.sevNormal),
    3:    ("Invalid", RO.Constants.sevError),
}

def _computeHarmannDict():
    retDict = {}
    retDict[None] = (_ShutterStateSevDict[None],)*2 
    basicDict = _ShutterStateSevDict
#    basicDict["Closed"] = ("Closed",  RO.Constants.sevWarning)
    for leftVal, leftNameSev in basicDict.iteritems():
        if leftVal == None:
            continue
        for rightVal, rightNameSev in basicDict.iteritems():
            if rightVal == None:
                continue
            retDict[leftVal + (rightVal << 2)] = (leftNameSev, rightNameSev)
    return retDict

_computeHarmannDict()

_HarmannStateDict = _computeHarmannDict()

# a list of (motor status bit, description, severity) in order from most serious to least
_MotorStatusBits = (
    (1, "Limit Switch", RO.Constants.sevError),
    (6, "Find Edge",    RO.Constants.sevWarning),
    (3, "Moving",       RO.Constants.sevWarning),
    (7, "Stopped",      RO.Constants.sevNormal),
    (2, "Motor Off",    RO.Constants.sevNormal),
)

class BOSSStatusConfigWdg(Tkinter.Frame):
    """Status and configuration of BOSS
    """
    CollCat = "coll"

    def __init__(self, master, helpURL=None):
        Tkinter.Frame.__init__(self, master)
        self.bossModel = TUI.Models.BOSSModel.Model()

        
        gr = RO.Wdg.Gridder(self, sticky="")

        self.exposureStateWdg = ExposureStateWdg.ExposureStateWdg(
            master = self,
            helpURL = _HelpURL,
        )
        gr.gridWdg("Exp Status", self.exposureStateWdg, colSpan=5, sticky="ew")
        
        spLabelWdgSet = [
            RO.Wdg.StrLabel(
                master = self,
                text = "Spectro %s" % spNum,
                anchor = "c",
            ) for spNum in (1, 2)]
        gr.gridWdg(None, spLabelWdgSet, sticky="")
        
        maxShutterStateLen = max(len(val[0]) for val in _ShutterStateSevDict.itervalues())
        self.shutterWdgSet = self._makeWdgPair(
            wdgClass = RO.Wdg.StrLabel,
            width = maxShutterStateLen,
            anchor = "c",
            helpText = "Status of shutter",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Shutter", self.shutterWdgSet),
        
        # hartmannWdgSet[spectrograph] = [left wdg, right wdg]
        self.hartmannWdgSet = []
        for side in ("left", "right"):
            wdgSet = (self._makeWdgPair(
                wdgClass = RO.Wdg.StrLabel,
                width = maxShutterStateLen,
                anchor = "c",
                helpText = "Status of %s Hartmann screen" % (side,),
                helpURL = _HelpURL,
            ))
            gr.gridWdg("%s Hartmann" % (side[0].upper(),), wdgSet)
            self.hartmannWdgSet.append(wdgSet)
        self.hartmannWdgSet = zip(*self.hartmannWdgSet)

        # or if you want all Hartmann on one line...
#         self.hartmannWdgSet = []
#         frameSet = []
#         for spNum in (1, 2):
#             wdgSet = []
#             frame = Tkinter.Frame(self)
#             for side in ("left", "right"):
#                 wdg = RO.Wdg.StrLabel(
#                     master = frame,
#                     width = maxShutterStateLen,
#                     anchor = "w",
#                     helpText = "Status of %s Hartmann screen for spectrograph %s" % (side, spNum),
#                     helpURL = _HelpURL,
#                 )
#                 wdg.pack(side="left")
#                 wdgSet.append(wdg)
#             self.hartmannWdgSet.append(wdgSet)
#             frameSet.append(frame)
#         gr.gridWdg("Hartmann", frameSet)

        self.collSummaryWdgSet = self._makeWdgPair(
            RO.Wdg.StrLabel,
            anchor = "c",
            helpText = "collimator status summary",
        )
        self.showCollWdg = RO.Wdg.Checkbutton(
            master = self,
            onvalue = "Hide Collimator",
            offvalue = "Show Collimator",
            defValue = True,
            showValue = True,
            helpText = "show/hide collimator actuators",
            helpURL = _HelpURL,
        )
        gr.addShowHideControl(self.CollCat, self.showCollWdg)
        gr.gridWdg (self.showCollWdg, self.collSummaryWdgSet)
        
        # self.collPosWdgSet = [A1, B1, C1, A2, B2, C2]
        self.collPosWdgSet = []
        for actName in ("A", "B", "C"):
            wdgSet = self._makeWdgPair(
                RO.Wdg.IntLabel,
                helpText = "collimator actuator %s position" % (actName,),
                helpURL = _HelpURL,
            )
            gr.gridWdg("Actuator %s" % (actName,), wdgSet, units="steps", cat=self.CollCat)
            self.collPosWdgSet.append(wdgSet)
        self.collPosWdgSet = RO.SeqUtil.flatten(zip(*self.collPosWdgSet))

        # self.collStatusWdgSet = [A1, B1, C1, A2, B2, C2]
        maxCollStatusLen = max(len(st[1]) for st in _MotorStatusBits)
        self.collStatusWdgSet = []
        for actName in ("A", "B", "C"):
            wdgSet = self._makeWdgPair(
                RO.Wdg.StrLabel,
                width = maxCollStatusLen,
                anchor = "c",
                helpText = "collimator actuator %s status" % (actName,),
                helpURL = _HelpURL,
            )
            gr.gridWdg("Actuator %s" % (actName,), wdgSet, cat=self.CollCat, sticky="e")
            self.collStatusWdgSet.append(wdgSet)
        self.collStatusWdgSet = RO.SeqUtil.flatten(zip(*self.collStatusWdgSet))

        self.bossModel.shutterStatus.addCallback(self._shutterStatusCallback)
        self.bossModel.screenStatus.addCallback(self._screenStatusCallback)
        self.bossModel.motorPosition.addCallback(self._motorPositionCallback)
        self.bossModel.motorStatus.addCallback(self._motorStatusCallback)
        
        self.statusBar = TUI.Base.Wdg.StatusBar(self)
        gr.gridWdg(False, self.statusBar, colSpan=5, sticky="ew")

        # At this point the widgets are all set up;
        # set the flag (so showHideWdg works)
        gr.allGridded()       
     
    def _makeWdgPair(self, wdgClass, **kargs):
        kargs.setdefault("master", self)
        bareHelpText = kargs.get("helpText")
        retWdg = []
        for camNum in (1, 2):
            if bareHelpText:
                kargs["helpText"] = "%s; camera %d" % (bareHelpText, camNum)
            retWdg.append(wdgClass(**kargs))
        return retWdg

    def _shutterStatusCallback(self, keyVar):
        """shutterStatus keyword callback
        """
        for ind, wdg in enumerate(self.shutterWdgSet):
            state, severity = _ShutterStateSevDict[keyVar[ind]]
            wdg.set(state, keyVar.isCurrent, severity = severity)
        
    def _screenStatusCallback(self, keyVar):
        """Hartmann screenStatus keyword callback
        """
        for spectInd, wdgSet in enumerate(self.hartmannWdgSet):
            leftRightNameSev = _HarmannStateDict[keyVar[spectInd]]
            for sideInd in range(2):
                state, severity = leftRightNameSev[sideInd]
                wdgSet[sideInd].set(state, keyVar.isCurrent, severity = severity)

    def _motorPositionCallback(self, keyVar):
        """Collimator motorPositon callback
        """
        isCurrent = keyVar.isCurrent
        for ind, pos in enumerate(keyVar):
            wdg = self.collPosWdgSet[ind]
            wdg.set(pos, isCurrent=keyVar.isCurrent)
        
    def _motorStatusCallback(self, keyVar):
        """Collimator motorStatus callback
        """
        isCurrent = keyVar.isCurrent
        for ind, val in enumerate(keyVar):
            if val == None:
                continue
            wdg = self.collStatusWdgSet[ind]
            for bitNum, descr, severity in _MotorStatusBits:
                if (1 << bitNum) & val != 0:
                    wdg.set(descr, severity=severity, isCurrent=keyVar.isCurrent)
                break
            wdg.set("OK", severity=RO.Constants.sevNormal, isCurrent=keyVar.isCurrent)


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = BOSSStatusConfigWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.exposeAnimate).pack(side="top")

    TestData.exposeStart()

    tuiModel.reactor.run()
