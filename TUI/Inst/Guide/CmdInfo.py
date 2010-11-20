"""
History:
2010-11-19 ROwen    Extracted from GuideWdg.
"""
import opscore.actor

class CmdInfo(object):
    """Information about a pending command
    """
    def __init__(self,
        cmdVar,
        isGuideOn = False,
        wdg = None,
        doneFunc = None,
        failFunc = None,
    ):
        """Create a new CmdInfo object
        
        Inputs:
        - cmdVar    command variable
        - isGuideOn True if this command turns guiding on; this helps re-enable the guide buttons
                    before the command terminates
        - wdg       widget to disable now and enable when command finishes (succeeds or fails)
        - doneFunc  function to call when command finishes (succeeds or fails)
        - failFunc  function to call if command fails
        """
        self.cmdVar = cmdVar
        self.isGuideOn = bool(isGuideOn)
        self.wdg = wdg
        self.doneFunc = doneFunc
        self.failFunc = failFunc
        if not self.cmdVar.isDone:
            self.wdg.setEnable(False)
            if self.wdg or self.failFunc:
                self.cmdVar.addCallback(self._callFunc, callCodes=opscore.actor.DoneCodes)
   
    def removeCallbacks(self, enableWdg=True):
        """Use for guide on commands when guiding has started.
        
        Inputs:
        - enableWdg: enable wdg (if present)
        """
        self.cmdVar.removeCallback(self._callFunc, doRaise=False)
        if enableWdg and self.wdg:
            self.wdg.setEnable(True)
        
    def _callFunc(self, cmdVar):
        if self.wdg:
            self.wdg.setEnable(True)
        if self.doneFunc:
            self.doneFunc()
        if cmdVar.didFail and self.failFunc:
            self.failFunc()

    def __str__(self):
        return "CmdInfo(cmdVar=%s)" % (self.cmdVar,)

    def __repr__(self):
        return "CmdInfo(cmdVar=%s, isGuideOn=%s, wdg=%s, doneFunc=%s, failFunc=%s)" % \
            (self.cmdVar, self.isGuideOn, self.wdg, self.doneFunc, self.failFunc)
