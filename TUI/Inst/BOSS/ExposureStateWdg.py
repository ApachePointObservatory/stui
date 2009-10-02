#!/usr/bin/env python
"""Display exposure state and countdown timer
"""
import Tkinter
import RO.Wdg
import TUI.PlaySound
import TUI.Models.BOSSModel

_HelpURL = None

class ExposureStateWdg(Tkinter.Frame):
    """A widget that displays the name of the exposure state and a countdown timer if relevant
    """
    def __init__(self, master, helpURL=None):
        Tkinter.Frame.__init__(self, master)
        bossModel = TUI.Models.BOSSModel.Model()
        self.wasExposing = None # True, False or None if unknown
        
        stateKeys = bossModel.exposureState.key.typedValues.vtypes[0].enumValues.keys()
        maxStateLen = max(len(stateKey) for stateKey in stateKeys)

        self.exposureStateWdg = RO.Wdg.StrLabel(
            master = self,
            width = maxStateLen,
            anchor = "w",
            helpText = "Status of current exposure",
            helpURL = helpURL,
        )
        self.exposureStateWdg.grid(row=0, column=0, sticky="w")

        self.expTimer = RO.Wdg.TimeBar(
            master = self,
            valueFormat = "%3.1f sec",
            isHorizontal = True,
            autoStop = True,
            helpText = "Status of current exposure",
            helpURL = helpURL,
        )
        self.expTimer.grid(row=0, column=1, sticky="ew")
        self.columnconfigure(1, weight=1)

        bossModel.exposureState.addCallback(self._exposureStateCallback)
     
#     def _makeWdgPair(self, wdgClass, **kargs):
#         kargs.setdefault("master", self)
#         bareHelpText = kargs.get("helpText")
#         retWdg = []
#         for camNum in (1, 2):
#             if bareHelpText:
#                 kargs["helpText"] = "%s; camera %d" % (bareHelpText, camNum)
#             retWdg.append(wdgClass(**kargs))
#         return retWdg
    
    def _exposureStateCallback(self, keyVar):
        """Exposure state has changed.
        
        Fields are:
        - exposure state
        - remaining time (sec) ??
        - total time (sec) ??
        """
        print "_exposureStateCallback(%s)" % (keyVar,)
        expState = keyVar[0]
        if expState == None:
            self.wasExposing = None
            self.expTimer.grid_remove()
            self.expTimer.clear()
            return
        remTime = keyVar[1] or 0.0  # change None to 0.0
        netTime = keyVar[2] or 0.0  # change None to 0.0
        
        expStateLow = expState.lower()
        isPaused = (expStateLow == "paused")
        isExposing = expStateLow in ("integrating", "resume")

        # set text state
        if isPaused:
            severity = RO.Constants.sevWarning
        else:
            severity = RO.Constants.sevNormal
        self.exposureStateWdg.set(expState.title(), severity = severity, isCurrent=keyVar.isCurrent)
        
        if not keyVar.isCurrent:
            # cancel countdown timer; don't play sounds
            self.wasExposing = None
            self.expTimer.grid_remove()
            self.expTimer.clear()
            return

        if not keyVar.isGenuine:
            # data is cached; don't mess with the countdown timer or sounds
            self.wasExposing = isExposing
            return
        
        # handle exposure timer
        print "netTime=%r" % (netTime,)
        if netTime > 0:
            print "starting a timer; remTime = %r, netTime = %r" % (remTime, netTime)
            # handle a countdown timer
            # it should be stationary if expStateStr = paused,
            # else it should count down
            if isExposing:
                # count up exposure
                self.expTimer.start(
                    value = netTime - remTime,
                    newMax = netTime,
                    countUp = True,
                )
            elif lowState == "paused":
                # pause an exposure with the specified time remaining
                self.expTimer.pause(
                    value = netTime - remTime,
                )
            else:
                # count down anything else
                self.expTimer.start(
                    value = remTime,
                    newMax = netTime,
                    countUp = False,
                )
            self.expTimer.grid()
        else:
            # hide countdown timer
            print "hide timer"
            self.expTimer.grid_remove()
            self.expTimer.clear()
        
        # play sound, if appropriate
        if self.wasExposing != None \
            and self.wasExposing != isExposing \
            and self.winfo_ismapped():
            # play the appropriate sound
            if isExposing:
                TUI.PlaySound.exposureBegins()
            else:
                TUI.PlaySound.exposureEnds()
        self.wasExposing = isExposing


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = ExposureStateWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.exposeAnimate).pack(side="top")

    TestData.exposeStart()

    tuiModel.reactor.run()
