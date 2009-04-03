#!/usr/bin/env python
"""Display a slew countdown timer
(and, eventually, also trigger blink or some other indicator in certain
text fields such as net position).

Relevant keywords are:
SlewDuration: indicates a slew has begun
SlewEnd
SlewSuperseded

Warnings:
- It is possible for slewSuperceded to arrive after slewDuration for the next slew.
On the other hand, it doesn't appear necessary to use that keyword.
- It may also be possible for SlewEnd to appear before SlewBegin,
but I doubt that. If it proves so, check command IDs.
- Status may return TTT shortly after a slew has started. It is good to
look for T (as a safety measure) but be careful to ignore it if too close to slew start.

To do:
- Compute the bar length based on the available space this should be an option
to add to ProgressBar itself -- if length is None then compute it based on
the size of the containing frame).

History:
2002-03-15 R Owen: modified to reuse the existing progress bar.
2002-06-11 R Owen: bug fix: if one slew superseded another, the 2nd progress bar
    halted very early because SlewSuperceded (sic) for the old slew
    comes after SlewDuration for the new slow
2002-11-25 R Owen: changed actor from "TCC" to "tcc".
2003-03-05 ROwen    Modified to use simplified KeyVariables without isValid.
2003-03-26 ROwen    Modified to use the tcc model.
2003-04-28 ROwen    Added sound cue for end of slew.
2003-05-08 ROwen    Modified to use RO.CnvUtil.
2003-05-28 ROwen    Moved slew duration and slew end vars to TCCModel.
2003-06-09 ROwen    Removed dispatcher arg; made countdown more reliable by having
                    a time limit before status=T ends the timer
                    and printing a warning when it does.
2003-06-25 ROwen    Modified test case (rather crudely) to handle message data as a dict
2003-11-17 ROwen    Modified to use TUI.PlaySound.
2004-05-21 ROwen    Bug fix: do not start timer unless slewDuration is current.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2006-02-21 ROwen    Fix PR 358: stop timer when SlewSuperseded seen.
2006-03-06 ROwen    Modified to use tccModel.axisCmdState instead of tccStatus
                    to make sure the timer is halted.
2006-04-27 ROwen    Bug fix: halted countdown timer prematurely for track/stop.
                    Changed a tests from if <x> == True: to if <x>: (thanks pychecker).
2009-03-31 ROwen    Updated for new TCC model.
"""
import sys
import time
import Tkinter
import RO.CnvUtil
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.PlaySound

class SlewStatusWdg(Tkinter.Frame):
    def __init__ (self,
        master = None,
    **kargs):
        """Displays a slew progress bar

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master=master, **kargs)
        self.model = TUI.TCC.TCCModel.Model()
        self.cmdID = None  # command ID of slew being counted down
        self.startTime = None
        
        self.progBar = RO.Wdg.TimeBar(
               master = self,
               valueFormat = ("%3.0f sec", "??? sec"),
               barThick = 10,
               isHorizontal = False,
               label = "Slewing",
               autoStop = True,
               countUp = False,
            )
        self.progBarVisible = False
        
        self.model.slewDuration.addCallback(self._slewDurationCallback)
        self.model.slewEnd.addCallback(self._slewEndCallback)
        self.model.slewSuperseded.addCallback(self._slewEndCallback)
        self.model.axisCmdState.addCallback(self._axisCmdStateCallback)

    def _slewDurationCallback(self, keyVar):
        """Start the slew indicator"""
        # print "%s._slewEndCallback(%s)" % (self.__class__.__name__, keyVar)
        isCurrent = keyVar.isCurrent
        slewDuration = keyVar[0]
        if slewDuration:
            if isCurrent:
                self.startTime = time.time()
                self.progBar.start(newMax = slewDuration)
                self.progBar.pack(expand=True, fill="y")
                self.progBarVisible = True
        else:
            self._slewEndCallback()

    def _slewEndCallback(self, keyVar=None):
        """End the slew indicator"""
        # print "%s._slewEndCallback(%s)" % (self.__class__.__name__, keyVar)
        if self.progBarVisible:
            self.progBarVisible = False
            self.progBar.clear()  # halt time updates
            self.progBar.pack_forget()  # remove from display
            
    def _axisCmdStateCallback(self, keyVar):
        """Handle axis commanded state.
        
        If drifting, start timer in unknown state.
        If tracking, halt timer.
        """
        if not keyVar.isCurrent:
            self._slewEndCallback()
            return

        axisCmdState = keyVar.valueList
        isDrifting = False
        isSlewing = False
        for cmdState in axisCmdState:
            if cmdState == "Drifting":
                isDrifting = True
            elif cmdState in ("Slewing", "Halting"):
                isSlewing = True
            
        if isSlewing:
            return
        elif isDrifting:
            self.progBar.setUnknown()
            self.progBar.pack(expand=True, fill="y")
            self.progBarVisible = True
        elif self.progBarVisible:
            sys.stderr.write("Warning: halting countdown timer due to AxisCmdState\n")
            self._slewEndCallback()


if __name__ == "__main__":
    import TestData

    tuiModel = TestData.testDispatcher.tuiModel
    kd = tuiModel.dispatcher

    testFrame = SlewStatusWdg (tuiModel.tkRoot)
    testFrame.pack()

    dataDictSet = (
        dict(delay=1, dataList=("SlewDuration=10.0",)),
        dict(delay=1, dataList=("TCCStatus=TTT, NNN",)),
        dict(delay=2, dataList=("TCCStatus=SSS, NNN",)),
        dict(delay=2, dataList=("TCCStatus=SSS, NNN",)),
        dict(delay=3, dataList=("SlewDuration=5.0",)),
        dict(delay=2, dataList=("SlewDuration=0.0",)),
        dict(delay=6, dataList=("SlewDuration=4.0",)),
        dict(delay=1, dataList=("TCCStatus=TTT, NNN",)),
        dict(delay=6, dataList=("SlewDuration=4.0",)),
        dict(delay=5, dataList=("SlewEnd",)),
    )

    TestData.testDispatcher.runDataDictSet(dataDictSet)

    tuiModel.reactor.run()
        
