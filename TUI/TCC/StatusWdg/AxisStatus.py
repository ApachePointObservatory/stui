#!/usr/bin/env python
"""Displays the axis position and various status.

To do:
- Offer some simple way of showing all status bits (as words)

History:
2003-03-26 ROwen    Modified to use the tcc model.
2003-03-31 ROwen    Switched from RO.Wdg.LabelledWdg to RO.Wdg.Gridder
2003-06-09 Rowen    Removed dispatcher arg.
2003-06-12 ROwen    Added helpText entries.
2003-06-25 ROwen    Modified test case to handle message data as a dict.
2003-11-24 ROwen    Modified to play sounds when axis state changes.
2004-02-04 ROwen    Modified _HelpURL to match minor help reorg.
2004-08-11 ROwen    Modified for improved TCCModel.
                    If axis controller status is None, displays "Not responding".
                    Use modified RO.Wdg state constants with st_ prefix.
2004-09-03 ROwen    Modified for RO.Wdg.st_... -> RO.Constants.st_...
2005-01-05 ROwen    Modified for RO.Wdg.Label state->severity and RO.Constants.st_... -> sev...
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2005-09-12 ROwen    Put "stop switch" near the end because it really means
                    "axis controller shut itself down for some reason".
                    Bug fix: used TUI.PlaySound without importing it.
2006-03-06 ROwen    Modified to use tccModel.axisCmdState and rotExists instead of tccStatus.
                    Modified to play sounds in a particular order
                    and with some time between them.
                    Modified to hide rotator AxisErrCode when no rotator
                    (and thus shown only one "NotAvailable").
                    Reduced width of commanded state field by one.
2006-03-16 ROwen    Modified to use TestData module for testing.
                    Moved Stop Switch error bit to beginning of ErrorBits
                    to stop display of "overcurrent" when a stop button is in.
2006-03-27 ROwen    Restored Stop Switch error bit's earlier position;
                    the problem is that the stop bit may go on
                    due to overcurrent or other serious problems.
2006-04-27 ROwen    Modified to hide rotator axis position units when no rotator.
                    Removed unused _StateDict (thanks pychecker).
2006-05-09 ROwen    Modified to play "axisHalt" sound when an axis reports an error.
                    Removed old hack that reset controller state to 0,
                    since the TCC reliably reports controller state.
2006-05-18 ROwen    Modified to play axisHalt less often in response to status;
                    now it only plays if the status is newly bad,
                    but not if it changes from one bad state to another.
2008-04-01 ROwen    Updated status bit descriptions for new axis controller.
2009-03-31 ROwen    Updated for new TCC model.
2009-09-11 ROwen    Updated status bits for MCP.
2010-03-12 ROwen    Changed to use Models.getModel.
"""
import time
import Tkinter
import RO.CnvUtil
import RO.Constants
import RO.Alg
import RO.BitDescr
import RO.StringUtil
import RO.Wdg
import TUI.PlaySound
import TUI.Models

_CtrllrWaitSec = 1.0 # time for status of all 3 controllers to come in (sec)
_SoundIntervalMS = 100 # time (ms) between the start of each sound (if more than one)

ErrorBits = (
    ( 6, 'Hit minimum limit switch'),
    ( 7, 'Him maximum limit switch'),
    (10, 'A/D converter problem'),
    (13, 'Stop button'),
    ( 2, 'Hit minimum soft limit'),
    ( 3, 'Hit maximum soft limit'),
    (15, '1 Hz clock signal lost'),
    (11, 'Out of closed loop'),
    (12, 'Amplifier bad'),
)
WarningBits = (
    ( 0, 'Motor control buffer empty'),
    ( 1, 'Position update late'),
    (14, 'Semaphore owned by somebody else'),
    (17, 'Pos error too large to correct'),
    (18, 'Windscreen touch down/cw'),
    (19, 'Windscreen touch up/ccw'),
    ( 4, 'Velocity limited'),
    ( 5, 'Acceleration limited'),
)

def _getSoundData():
    """Return a collection of sound data:
    - a dictionary of axis comanded state: (index, soundFunc)
      where the sounds should be sorted by index before playing
    
    soundFunc is a function: call it to play the sound
    """
    soundData = (
        (TUI.PlaySound.axisHalt, 'halted', 'halting'),
        (TUI.PlaySound.axisSlew, 'drifting', 'slewing'),
        (TUI.PlaySound.axisTrack, 'tracking'),
    )
    stateIndSoundDict = {}
    for ind in range(len(soundData)):
        item = soundData[ind]
        soundFunc = item[0]
        states = item[1:]
        for state in states:
            stateIndSoundDict[state] = (ind, soundFunc)
    return stateIndSoundDict

_StateIndSoundDict = _getSoundData()    

_HelpPrefix = "Telescope/StatusWin.html#"

def _computeBitInfo():
    """Compute bitInfo array for RO.BitDescr module"""
    bitInfo = []
    for (bit, info) in ErrorBits:
        bitInfo.append((bit, (info, RO.Constants.sevError)))
    for (bit, info) in WarningBits:
        bitInfo.append((bit, (info, RO.Constants.sevWarning)))
    return bitInfo
_BitInfo = _computeBitInfo()

class AxisStatusWdg(Tkinter.Frame):
    def __init__ (self, master=None, **kargs):
        """Displays information about the axes

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master=master, **kargs)
        self.tccModel = TUI.Models.getModel("tcc")
        self.prevSounds = [None]*3 # sounds played last time we received AxisCmdState
        self.prevCtrlStatusOK = [None]*3
        self.ctrlBadTime = 0 # time of last "controller bad" sound

        # magic numbers
        PosPrec = 1 # number of digits past decimal point
        PosWidth = 5 + PosPrec  # assumes -999.99... degrees is longest field
        AxisCmdStateWidth = 8
        AxisErrCodeWidth = 13
        CtrlStatusWidth = 25
        
        # commanded state dictionary:
        # - keys are axis commanded state keywords, cast to lowercase
        # - values are the severity
        self._CmdStateDict = {
            "Drifting": RO.Constants.sevWarning,
            "Halted": RO.Constants.sevError,
            "Halting": RO.Constants.sevError,
            "Slewing": RO.Constants.sevWarning,
            "Tracking": RO.Constants.sevNormal,
            "NotAvailable": RO.Constants.sevNormal,
        }

        self.axisInd = range(len(self.tccModel.axisNames))
        
        # actual axis position widget set
        self.axePosWdgSet = [
            RO.Wdg.FloatLabel(self,
                precision = PosPrec,
                width = PosWidth,
                helpText = "Current axis position, as reported by the controller",
                helpURL = _HelpPrefix+"AxisPosition",
            )
            for axis in self.axisInd
        ]
        self.tccModel.axePos.addValueListCallback([wdg.set for wdg in self.axePosWdgSet])
        
        # TCC status widget set (e.g. tracking or halted)
        self.axisCmdStateWdgSet = [
            RO.Wdg.StrLabel(self,
                width=AxisCmdStateWidth,
                helpText = "What the TCC is telling the axis to do",
                helpURL=_HelpPrefix+"AxisTCCStatus",
                anchor = "nw",
            )
            for axis in self.axisInd
        ]
        self.tccModel.axisCmdState.addCallback(self._axisCmdStateCallback)
    
        self.tccModel.rotExists.addCallback(self._rotExistsCallback)
        
        # axis error code widet set (why the TCC is not moving the axis)
        self.axisErrCodeWdgSet = [
            RO.Wdg.StrLabel(self,
                width=AxisErrCodeWidth,
                helpText = "Why the TCC halted the axis",
                helpURL = _HelpPrefix + "AxisTCCErrorCode",
                anchor = "nw",
            )
            for axis in self.axisInd
        ]
        self.tccModel.axisErrCode.addValueListCallback([wdg.set for wdg in self.axisErrCodeWdgSet])
    
        # controller status widget set (the status word)
        self.ctrlStatusWdgSet = [
            RO.Wdg.StrLabel(self,
                width=CtrlStatusWidth,
                helpText = "Status reported by the axis controller",
                helpURL = _HelpPrefix + "AxisCtrlStatus",
                anchor = "nw",
            )
            for axis in self.axisInd
        ]
        
        # handle Az/Alt/RotCtrlStatus
        for axisInd, axisName in enumerate(self.tccModel.axisNames):
            statusVar = getattr(self.tccModel, axisName.lower() + "Stat")
            statusVar.addCallback(RO.Alg.GenericCallback(self._ctrlStatusCallback, axisInd))
                
        # grid the axis widgets
        gr = RO.Wdg.Gridder(self, sticky="w")
        for axis in self.axisInd:
            unitsLabel = Tkinter.Label(self, text=RO.StringUtil.DegStr)
            if axis == 2:
                self.rotUnitsLabel = unitsLabel
            wdgSet = gr.gridWdg (
                label = self.tccModel.axisNames[axis],
                dataWdg = (
                    self.axePosWdgSet[axis],
                    unitsLabel,
                    self.axisCmdStateWdgSet[axis],
                    self.axisErrCodeWdgSet[axis],
                    self.ctrlStatusWdgSet[axis],
                )
            )
            nextCol = wdgSet.nextCol
        
        # widen rotator commanded state widget
        # so there's room to display "NotAvailable"
        # (note that the error code widget will be hidden when this occurs
        # so the text will not overlap anything).
        rotCmdWdg = self.axisCmdStateWdgSet[2]
        rotCmdWdg.grid_configure(columnspan=2)
        rotCmdWdg["width"] = 12

        # allow the last column to grow to fill the available space
        self.columnconfigure(nextCol, weight=1)
    
    def _axisCmdStateCallback(self, keyVar):
        if not keyVar.isCurrent:
            for wdg in self.axisCmdStateWdgSet:
                wdg.setIsCurrent(False)
            return

        axisCmdState = keyVar.valueList

        # set axis commanded state widgets
        for axis in self.axisInd:
            cmdState = axisCmdState[axis]
            severity = self._CmdStateDict.get(cmdState, RO.Constants.sevError)
            self.axisCmdStateWdgSet[axis].set(cmdState, severity=severity)

        # play sounds, if appropriate
        indSoundsToPlay = set() # add new sounds to play to a set to avoid duplicates
        for axis in self.axisInd:
            soundInd, soundFunc = _StateIndSoundDict.get(axisCmdState[axis].lower(), (0, None))
            if soundFunc and (soundFunc != self.prevSounds[axis]) and keyVar.isGenuine:
                indSoundsToPlay.add((soundInd, soundFunc))
            self.prevSounds[axis] = soundFunc
        
        if indSoundsToPlay:
            indSoundsToPlay = list(indSoundsToPlay)
            indSoundsToPlay.sort()
            soundsToPlay = list(zip(*indSoundsToPlay)[1])
            soundsToPlay.reverse() # since played from back to front
            self._playSounds(soundsToPlay)
        
    def _ctrlStatusCallback(self, axisInd, keyVar):
#        print "_ctrlStatusCallback(axisInd=%s, keyVar=%s)" % (axisInd, keyVar)
        if axisInd == 2 and not self.tccModel.rotExists[0]:
            # rotator does not exist; this is handled by _rotExistsCallback
            return
        
        isCurrent = keyVar.isCurrent
        statusWord = keyVar[3]
        statusOK = True

        ctrlStatusWdg = self.ctrlStatusWdgSet[axisInd]

        if statusWord != None:
            infoList = RO.BitDescr.getDescr(_BitInfo, statusWord)
            
            # for now simply show the first status;
            # eventually provide a pop-up list showing all status bits
            if infoList:
                info, severity = infoList[0]
                ctrlStatusWdg.set(info, isCurrent, severity=severity)
                if severity == RO.Constants.sevError:
                    statusOK = False
            else:
                ctrlStatusWdg.set("", isCurrent, severity=RO.Constants.sevNormal)
        elif isCurrent:
            ctrlStatusWdg.set("Not responding", isCurrent=isCurrent, severity=RO.Constants.sevError)
            statusOK = False
        else:
            ctrlStatusWdg.setNotCurrent()
        
        statusNewlyBad = (self.prevCtrlStatusOK[axisInd] and not statusOK)
        self.prevCtrlStatusOK[axisInd] = statusOK
        
        if statusNewlyBad and keyVar and keyVar.isGenuine \
            and (time.time() - self.ctrlBadTime > _CtrllrWaitSec):
            TUI.PlaySound.axisHalt()
            self.ctrlBadTime = time.time()
    
    def _rotExistsCallback(self, keyVar):
        if not keyVar.isCurrent:
            return
        rotExists = keyVar[0]
        if rotExists:
            self.rotUnitsLabel.grid()
            self.axisErrCodeWdgSet[2].grid()
            self.ctrlStatusWdgSet[2].grid()
            self.ctrlStatusWdgSet[2].set("", severity=RO.Constants.sevNormal)
        else:
            self.rotUnitsLabel.grid_remove()
            self.axisErrCodeWdgSet[2].grid_remove()
            self.ctrlStatusWdgSet[2].grid_remove()
    
    def _playSounds(self, sounds):
        """Play one or more of a set of sounds,
        played in order from last to first.
        """
        if not sounds:
            return
        soundFunc = sounds.pop(-1)
        soundFunc()
        if sounds:
            self.after(_SoundIntervalMS, self._playSounds, sounds)

            
if __name__ == "__main__":
    import TestData

    tuiModel = TestData.tuiModel

    testFrame = AxisStatusWdg(tuiModel.tkRoot)
    testFrame.pack()

    TestData.runTest()

    tuiModel.reactor.run()
