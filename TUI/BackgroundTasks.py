#!/usr/bin/env python
"""
Handle background (invisible) tasks for the telescope UI

To do: put up a log window so the intentional error in the test case can be seen

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
"""
import sys
import RO.CnvUtil
import RO.Constants
import RO.PhysConst
import RO.Astro.Tm
import TUI.Models

class BackgroundKwds(object):
    """Processes various keywords that are handled in the background"""
    def __init__(self,
        maxTimeErr = 10.0,  # max clock error (sec) before a warning is printed
    ):
        self.tuiModel = TUI.Models.getModel("tui")
        self.tccModel = TUI.Models.getModel("tcc")
        self.didSetUTCMinusTAI = False

        self.maxTimeErr = maxTimeErr

        self.tccModel.utc_TAI.addCallback(self._utcMinusTAICallback, callNow=False)
        
        self.tccModel.tai.addCallback(self._taiCallback, callNow=False)
        
    def _utcMinusTAICallback(self, keyVar):
        """Updates UTC-TAI
        """
        if not keyVar.isCurrent:
            return
        utcMinusTAI = keyVar[0]
        if utcMinusTAI != None:
            RO.Astro.Tm.setUTCMinusTAI(utcMinusTAI)
            self.didSetUTCMinusTAI = True

    def _taiCallback(self, keyVar):
        """Check accuracy of computer clock.
        """
        if not keyVar.isCurrent or not self.didSetUTCMinusTAI:
            return

        currTAI = keyVar[0]
        try:
            if currTAI != None:
                timeErr = (RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay) - currTAI
                
                if abs(timeErr) > self.maxTimeErr:
                    self.tuiModel.logMsg(
                        "Your clock appears to be off; time error = %.1f" % (timeErr,),
                        severity = RO.Constants.sevError,
                    )
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            self.tuiModel.logMsg(
                "TAI time keyword seen but clock check failed; error=%s" % (e,),
                severity = RO.Constants.sevError,
            )
                

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
