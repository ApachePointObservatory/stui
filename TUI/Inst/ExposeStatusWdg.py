#!/usr/local/bin/python
"""Exposure status widget

History:
2003-07-25 ROwen
2003-07-30 ROwen    Modified to be generic for all instruments and to use Inst.ExposeModel
2003-08-01 ROwen    Added comment field even though the hub does not yet send me the necessary info.
2003-09-30 ROwen    Updated the help prefix.
2003-10-01 ROwen    Modified to use new versions of seqState and expState (for new hub).
2003-10-06 ROwen    Modified to use unified progID, etc. naming convention.
2003-10-16 ROwen    Bug fix: was not ignoring files named None.
2003-12-04 ROwen    Added sound cues for exposure begins and ends.
2004-01-29 ROwen    Bug fix: exposure countdown timer restarted on refresh;
                    fixed by not messing with timer for data from the cache.
2004-05-18 ROwen    In _updExpState local variable expState (string repr. of state)
                    masked argument expState (a tuple of state info).
2004-08-11 ROwen    Use modified RO.Wdg state constants with st_ prefix.
2004-09-10 ROwen    Modified for RO.Wdg.st_... -> RO.Constants.st_...
                    Increased field width and use a constant for it.
                    Added __all__.
                    Removed some unused import statements.
2004-09-23 ROwen    Moved prefs display here from ExposeInputWdg.
2004-09-28 ROwen    Finally added callback for comment field.
2005-01-05 ROwen    Modified for RO.Wdg.Label state->severity and RO.Constants.st_... -> sev...
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2005-09-15 ROwen    Moved prefs back to ExposeInputWdg, since users can set them again.
"""
__all__ = ["ExposeStatusWdg"]

import Tkinter
import RO.Constants
import RO.Wdg
import TUI.PlaySound
import ExposeModel

_HelpPrefix = "Instruments/ExposeWin.html#"
_DataWidth = 40

class ExposeStatusWdg (Tkinter.Frame):
    def __init__(self,
        master,
        instName,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)


        self.expModel = ExposeModel.getModel(instName)
        self.tuiModel = self.expModel.tuiModel
        self.exposing = None # True, False or None if unknown
        gr = RO.Wdg.Gridder(self, sticky="w")

        self.seqStateWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Status of exposure sequence",
            helpURL = _HelpPrefix + "SeqStatus",
            anchor="w",
            width = _DataWidth,
        )
        gr.gridWdg("Seq Status", self.seqStateWdg, sticky="ew")
        
        stateFrame = Tkinter.Frame(self)
        self.expStateWdg = RO.Wdg.StrLabel(
            master = stateFrame,
            helpText = "Status of current exposure",
            helpURL = _HelpPrefix + "ExpStatus",
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
            helpURL = _HelpPrefix + "ExpStatus",
        )
        gr.gridWdg("Exp Status", stateFrame, sticky="ew")

        self.userWdg = RO.Wdg.StrLabel(self,
            helpText = "Who is taking this exposure",
            helpURL = _HelpPrefix + "UserStatus",
            anchor="w",
            width = _DataWidth,
        )
        gr.gridWdg("User", self.userWdg, sticky="ew")

        self.commentWdg = RO.Wdg.StrLabel(self,
            helpText = "User's comment, if any",
            helpURL = _HelpPrefix + "CommentStatus",
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
                helpURL = _HelpPrefix + "FileNameStatus",
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
        - remaining time for this state (sec; 0 if short or unknown)
        - total time for this state (sec; 0 if short or unknown)
        """
        if not isCurrent:
            self.expStateWdg.setNotCurrent()
            return

        cmdr, expStateStr, startTime, remTime, netTime = expState
        lowState = expStateStr.lower()

        if lowState == "paused":
            errState = RO.Constants.sevWarning
        else:
            errState = RO.Constants.sevNormal
        self.expStateWdg.set(expStateStr, severity = errState)
        
        if not keyVar.isGenuine():
            # data is cached; don't mess with the countdown timer
            return
        
        exposing = lowState in ("integrating", "resume")
        
        if netTime > 0:
            # print "starting a timer; remTime = %r, netTime = %r" % (remTime, netTime)
            # handle a countdown timer
            # it should be stationary if expStateStr = paused,
            # else it should count down
            if lowState in ("integrating", "resume"):
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
        
        if self.exposing in (True, False) \
            and self.exposing != exposing \
            and self.winfo_ismapped():
            if exposing:
                TUI.PlaySound.exposureBegins()
            else:
                TUI.PlaySound.exposureEnds()
        
        self.exposing = exposing
        
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

    import ExposeTestData

    testFrame = ExposeStatusWdg(root, "DIS")
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=ExposeTestData.animate).pack(side="top")

    ExposeTestData.dispatch()

    root.mainloop()
