#!/usr/bin/env python
"""
Display status of BOSS ICC

There are two panels:
- exposure status
- other status
this allows easy display of exposure status in other panels, e.g. SOP and scripts
"""
import Tkinter
import RO.Wdg
import TUI.Models.BOSSModel

_HelpURL = None

class ExposureStatusWdg(Tkinter.Frame):
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)
        self.bossModel = TUI.Models.BOSSModel.Model()
        
        self.expModel = ExposeModel.getModel(instName)
        self.tuiModel = self.expModel.tuiModel
        self.wasExposing = None # True, False or None if unknown
        self.minExposureBeginsSoundTime = 0
        gr = RO.Wdg.Gridder(self, sticky="w")

        self.seqStateWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Status of exposure sequence",
            helpURL = helpURL,
            anchor="w",
            width = _DataWidth,
        )
        gr.gridWdg("Seq Status", self.seqStateWdg, sticky="ew")
        
        stateFrame = Tkinter.Frame(self)
        self.expStateWdg = RO.Wdg.StrLabel(
            master = stateFrame,
            helpText = "Status of current exposure",
            helpURL = helpURL,
            anchor="w",
            width = 11
        )
        self.expStateWdg.pack(side="left")
        self.expTimer = RO.Wdg.TimeBar(
            master = stateFrame,
            valueFormat = "%3.1f sec",
            isHorizontal = True,
            autoStop = True,
            helpText = "Status of current exposure",
            helpURL = helpURL,
        )
        gr.gridWdg("Exp Status", stateFrame, sticky="ew")

        self.userWdg = RO.Wdg.StrLabel(self,
            helpText = "Who is taking this exposure",
            helpURL = helpURL,
            anchor="w",
            width = _DataWidth,
        )
        gr.gridWdg("User", self.userWdg, sticky="ew")

        self.commentWdg = RO.Wdg.StrLabel(self,
            helpText = "User's comment, if any",
            helpURL = helpURL,
            anchor="w",
            width = _DataWidth,
        )
        gr.gridWdg("Comment", self.commentWdg, sticky="ew")
        self.expModel.comment.addROWdg(self.commentWdg)

        self.fileNameWdgs = []
        for camName in self.expModel.instInfo.camNames:
            if camName:
                helpSuffix = " from %s camera" % (camName.lower())
                labelStr = "%s File" % (camName.capitalize())
            else:
                helpSuffix = ""
                labelStr = "File"

            wdg = RO.Wdg.StrLabel(self,
                helpText = "File for current exposure" + helpSuffix,
                helpURL = helpURL,
                anchor = "w",
                width = _DataWidth,
            )
            self.fileNameWdgs.append(wdg)

            gr.gridWdg(labelStr, wdg, sticky="ew")
        
        self.columnconfigure(1, weight=1)

        self.expModel.newFiles.addCallback(self._updFiles)
        self.expModel.expState.addCallback(self._updExpState)
        self.expModel.seqState.addCallback(self._updSeqState)
        
    def _updFiles(self, fileInfo, isCurrent, **kargs):
        """newFiles has changed. newFiles is file(s) that will be saved
        at the end of the current exposure:
        - cmdr (progID.username)
        - host
        - common root directory
        - program subdirectory
        - user subdirectory
        - file name(s)
        """
#       print "ExposeStatusWdg._updFiles(%r, %r)" % (fileInfo, isCurrent)
        if not isCurrent:
            for wdg in self.fileNameWdgs:
                wdg.setNotCurrent()
            return
        
        subdir = "".join(fileInfo[3:5])
        names = fileInfo[5:]
        for ii in range(self.expModel.instInfo.getNumCameras()):
            if names[ii] != "None":
                self.fileNameWdgs[ii].set(subdir + names[ii])
            else:
                self.fileNameWdgs[ii].set("")
    
    def _updExpState(self, expState, isCurrent, keyVar):
        """exposure state has changed. expState is:
        - program ID
        - user name
        - exposure state string (e.g. flushing, reading...)
        - start time (huh?)
        - remaining time for this state (sec; 0 or None if short or unknown)
        - total time for this state (sec; 0 or None if short or unknown)
        """
        if not isCurrent:
            self.expStateWdg.setNotCurrent()
            self.wasExposing = None
            return

        cmdr, expStateStr, startTime, remTime, netTime = expState
        if not expStateStr:
            return
        lowState = expStateStr.lower()
        remTime = remTime or 0.0 # change None to 0.0
        netTime = netTime or 0.0 # change None to 0.0

        if lowState == "paused":
            errState = RO.Constants.sevWarning
        else:
            errState = RO.Constants.sevNormal
        self.expStateWdg.set(expStateStr, severity = errState)

        isExposing = lowState in ("integrating", "resume")
        
        if not keyVar.isGenuine():
            # data is cached; don't mess with the countdown timer or sounds
            self.wasExposing = isExposing
            return
        
        if netTime > 0:
            # print "starting a timer; remTime = %r, netTime = %r" % (remTime, netTime)
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
            self.expTimer.pack(side="left", expand="yes", fill="x")
        else:
            # hide countdown timer
            self.expTimer.pack_forget()
            self.expTimer.clear()
        
        if self.wasExposing != None \
            and self.wasExposing != isExposing \
            and self.winfo_ismapped():
            # play the appropriate sound
            if isExposing:
                currTime = time.time()
                if currTime > self.minExposureBeginsSoundTime:
                    TUI.PlaySound.exposureBegins()
                    self.minExposureBeginsSoundTime = currTime + MinExposureBeginsSoundInterval
            else:
                if self.expModel.instInfo.playExposureEnds:
                    TUI.PlaySound.exposureEnds()
        
        self.wasExposing = isExposing
        
    def _updSeqState(self, seqState, isCurrent, **kargs):
        """sequence state has changed; seqState is:
            - cmdr (progID.username)
            - exposure type
            - exposure duration
            - exposure number
            - number of exposures requested
            - sequence status (a short string)
        """
        if not isCurrent:
            self.seqStateWdg.setNotCurrent()
            self.userWdg.setNotCurrent()
            return
        
        cmdr, expType, expDur, expNum, totExp, status = seqState
        progID, username = cmdr.split('.')
                
        lstatus = status.lower()
        if lstatus == "failed":
            severity = RO.Constants.sevError
        elif lstatus in ("paused", "stopped", "aborted"):
            severity = RO.Constants.sevWarning
        else:
            severity = RO.Constants.sevNormal
        self.seqStateWdg.set(
            "%s, %.1f sec, %d of %d %s" % (expType, expDur, expNum, totExp, status),
            severity = severity,
        )
        if cmdr == self.tuiModel.getCmdr():
            userStr = "Me"
        elif progID == self.tuiModel.getProgID():
            userStr = "%s: collaborator" % (username,)
        else:
            userStr = "%s" % (cmdr,)
        self.userWdg.set(userStr)


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = BOSSExposeStatusWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.exposeAnimate).pack(side="top")

    TestData.exposeStart()

    tuiModel.reactor.run()
