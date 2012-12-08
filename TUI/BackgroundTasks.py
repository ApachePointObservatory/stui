#!/usr/bin/env python
"""
Handle background (invisible) tasks for the telescope UI

History:
2003-02-27 ROwen    Error messages now go to the log, not stderr.
2003-03-05 ROwen    Modified to use simplified KeyVariables.
2003-05-08 ROwen    Modified to use RO.CnvUtil.
2003-06-18 ROwen    Modified to test for StandardError instead of Exception
2003-06-25 ROwen    Modified to handle message data as a dict
2004-02-05 ROwen    Modified to use improved KeyDispatcher.logMsg.
2005-06-08 ROwen    Changed BackgroundKwds to a new style class.
2005-06-16 ROwen    Modified to use improved KeyDispatcher.logMsg.
2005-09-28 ROwen    Modified _taiCallback to use standard exception handling template.
2006-10-25 ROwen    Modified to use TUIModel and so not need the dispatcher keyword.
                    Modified to log errors using tuiModel.logMsg.
2007-07-25 ROwen    Modified to use time from the TCC model.
                    Modified to not test the clock unless UTCMinusTAI set
                    (but TUI now gets that using getKeys so it normally will
                    see UTCMinusTAI before it sees the current TAI).
2009-04-01 ROwen    Modified to use new keyVar callbacks.
                    Test code updated to use TUI.Base.TestDispatcher.
2010-03-12 ROwen    Changed to use Models.getModel.
2010-07-21 ROwen    Added support for detecting sleep and failed connections.
2010-10-27 ROwen    Fixed "no data seen" message to report correct time interval.
2012-08-10 ROwen    Updated for RO.Comm.TCPConnection 3.0.
2012-12-07 ROwen    Improved time keeping so TUI can show the correct time even if the clock is not keeping perfect UTC.
                    Sets time error using RO.Astro.Tm.setClockError(0) based on TAI reported by the TCC.
                    If the clock appears to be keeping UTC or TAI then the clock is assumed to be keeping that time perfectly.
"""
import sys
import time
import opscore.utility.timer
import opscore.actor.keyvar
import RO.Astro.Tm
import RO.CnvUtil
import RO.Constants
import RO.PhysConst
import TUI.Models
import TUI.PlaySound

class BackgroundKwds(object):
    """Processes various keywords that are handled in the background.
    
    Also verify that we're getting data from the hub (also detects computer sleep)
    and try to refresh variables if there is a problem.
    """
    def __init__(self,
        maxTimeErr = 10.0,
        checkConnInterval = 5.0,
        maxEntryAge = 60.0,
    ):
        """Create BackgroundKwds
        
        Inputs:
        - maxTimeErr: maximum clock error (sec) before a warning is printed
        - checkConnInterval: interval (sec) at which to check connection
        - maxEntryAge: maximum age of log entry (sec)
        """
        self.maxTimeErr = float(maxTimeErr)
        self.checkConnInterval = float(checkConnInterval)
        self.maxEntryAge = float(maxEntryAge)

        self.tuiModel = TUI.Models.getModel("tui")
        self.tccModel = TUI.Models.getModel("tcc")
        self.connection = self.tuiModel.getConnection()
        self.dispatcher = self.tuiModel.dispatcher
        self.didSetUTCMinusTAI = False
        self.checkConnTimer = opscore.utility.timer.Timer()
        self.clockType = None # set to "UTC" or "TAI" if keeping that time system

        self.tccModel.utc_TAI.addCallback(self._utcMinusTAICallback, callNow=False)
    
        self.connection.addStateCallback(self.connCallback, callNow=True)

    def connCallback(self, conn):
        """Called when connection changes state

        When connected check the connection regularly,
        when not, don't
        """
        if conn.isConnected:
            self.checkConnTimer.start(self.checkConnInterval, self.checkConnection)
            self.checkClock()
        else:
            self.checkConnTimer.cancel()
    
    def checkConnection(self):
        """Check for aliveness of connection by looking at the time of the last hub message
        """
        doQueue = True
        try:
            entryAge = time.time() - self.dispatcher.readUnixTime
            if entryAge > self.maxEntryAge:
                self.tuiModel.logMsg(
                    "No data seen in %s seconds; testing the connection" % (self.maxEntryAge,),
                    severity = RO.Constants.sevWarning)
                cmdVar = opscore.actor.keyvar.CmdVar(
                    actor = "hub",
                    cmdStr = "version",
                    timeLim = 5.0,
                    callFunc = self.checkCmdCallback,
                )
                self.dispatcher.executeCmd(cmdVar)
                doQueue = False
        finally:
            if doQueue:
                self.checkConnTimer.start(self.checkConnInterval, self.checkConnection)
    
    def checkClock(self):
        """Check computer clock by asking the TCC for time
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "tcc",
            cmdStr = "show time",
            timeLim = 2.0,
            callFunc = self.checkClockCallback,
            keyVars = (self.tccModel.tai,),
        )
        self.dispatcher.executeCmd(cmdVar)

    def checkCmdCallback(self, cmdVar):
        if not cmdVar.isDone:
            return
        doQueue = True
        try:
            if cmdVar.didFail:
                self.connection.disconnect(isOK = False, reason="Connection is dead")
                doQueue = False
                TUI.PlaySound.cmdFailed()
            else:
                self.dispatcher.refreshAllVar()
        finally:
            if doQueue:
                self.checkConnTimer.start(self.checkConnInterval, self.checkConnection)

    def checkClockCallback(self, cmdVar):
        """Callback from TCC "show time" command
        
        Determine if clock is keeping UTC, TAI or something else, and act accordingly.
        """
        if not cmdVar.isDone:
            return
        if cmdVar.didFail:
            self.tuiModel.logMsg(
                "clock check failed: tcc show time failed; assuming UTC",
                severity = RO.Constants.sevError,
            )
            return
        
        taiValList = cmdVar.getLastKeyVarData(self.tccModel.tai)
        currTAI = taiValList[0] if taiValList else None
        if currTAI is None:
            self.tuiModel.logMsg(
                "clock check failed: current TAI unknown; assuming UTC",
                severity = RO.Constants.sevError,
            )
            return
        if not self.didSetUTCMinusTAI:
            self.tuiModel.logMsg(
                "clock check failed: UTC-TAI unknown; assuming UTC",
                severity = RO.Constants.sevError,
            )
            return
        utcMinusTAI = RO.Astro.Tm.getUTCMinusTAI()
        currUTC = utcMinusTAI + currTAI

        RO.Astro.Tm.setClockError(0)
        clockUTC = RO.Astro.Tm.utcFromPySec() * RO.PhysConst.SecPerDay
        
        if abs(clockUTC - currUTC) < 3.0:
            # clock keeps accurate UTC (as well as we can figure); set time error to 0
            self.clockType = "UTC"
            self.tuiModel.logMsg("Your computer clock is keeping UTC")
        elif abs(clockUTC - currTAI) < 3.0:
            # clock keeps accurate TAI (as well as we can figure); set time error to UTC-TAI
            self.clockType = "TAI"
            RO.Astro.Tm.setClockError(-utcMinusTAI)
            self.tuiModel.logMsg("Your computer clock is keeping TAI")
        else:
            # clock system unknown or not keeping accurate time; adjust based on current UTC
            self.clockType = None
            timeError = clockUTC - currUTC
            RO.Astro.Tm.setClockError(timeError)
            self.tuiModel.logMsg(
                "Your computer clock is off by = %f.1 seconds" % (timeError,),
                severity = RO.Constants.sevWarning,
            )

    def _utcMinusTAICallback(self, keyVar):
        """Updates UTC-TAI in RO.Astro.Tm
        """
        if not keyVar.isCurrent:
            return
        utcMinusTAI = keyVar[0]
        if utcMinusTAI != None:
            RO.Astro.Tm.setUTCMinusTAI(utcMinusTAI)
            self.didSetUTCMinusTAI = True
                

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
    tuiModel = testDispatcher.tuiModel

    bkgnd = BackgroundKwds()

    print "Setting TAI and UTC_TAI correctly; this should work silently."
    dataList = (
        "UTC_TAI=-33", # a reasonable value
        "TAI=%s" % (RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay,),
    )
    testDispatcher.dispatch(dataList)
    
    # now generate an intentional error
    print "Setting TAI incorrectly; this would log an error if we had a log window up:"
    dataList = (
        "TAI=%s" % ((RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay) + 999.0,),
    )

    testDispatcher.dispatch(dataList)

    tuiModel.reactor.run()
