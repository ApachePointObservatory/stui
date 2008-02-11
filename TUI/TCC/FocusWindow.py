#!/usr/bin/env python
"""Secondary mirror focus control.

History:
2004-01-09 ROwen    first draft
2004-02-23 ROwen    Modified to play cmdDone/cmdFailed for commands.
2004-03-11 ROwen    Bug fix: assumed the secondary mirror would start moving
                    within 10 seconds (a poor assumption if others are moving
                    the mirror). Fixed by removing the time limit.
2004-05-18 ROwen    Eliminated redundant import in test code.
2004-06-22 ROwen    Modified for RO.Keyvariable.KeyCommand->CmdVar
2005-01-05 ROwen    Overhauled to improve usability.
2005-01-12 ROwen    Rewrote Set dialog to avoid a bug in tkSimpleDialog.
2005-07-07 ROwen    Modified for moved RO.TkUtil.
2005-07-27 ROwen    Bug fix: _HelpURL was mis-set.
                    Added Help ctx menu to the increment menu.
2005-08-03 ROwen    Modified to not put up a timer when cmdTime <= 0.
2005-08-08 ROwen    Bug fix: cmdTime->cmdDtime.
2008-02-04 ROwen    Modified to use new TUI.Base.FocusWdg.
2008-02-11 ROwen    Bug fix: was trying to get the TUIModel in test mode.
"""
import Tkinter
import RO.Wdg
import RO.TkUtil
import RO.StringUtil
import TUI.TUIModel
import TUI.TCC.TCCModel
import TUI.Base.FocusWdg

_HelpURL = "Telescope/SecFocusWin.html"
_MaxFocus = 9999 # microns; this is a bit larger than the current total range of the secondary, hence a bit more than twice what it needs to be

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = "TCC.Secondary Focus",
        defGeom = "+240+507",
        resizable = False,
        visible = True,
        wdgFunc = SecFocusWdg,
    )
    

class SecBasicFocusWdg(TUI.Base.FocusWdg.FocusWdg):
    """Secondary mirror focus widget, main display and controls"""
    def __init__(self, master, statusBar, buttonFrame):
        TUI.Base.FocusWdg.FocusWdg.__init__(self,
            master,
            name = "secondary",
            statusBar = statusBar,
            increments = (25, 50, 100),
            defIncr = 50,
            helpURL = _HelpURL,
            label = "Sec Focus",
            minFocus = 0,
            maxFocus = 20000,
            fmtStr = "%.1f",
            currWidth = 5,
            buttonFrame = buttonFrame,
        )

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = "tcc",
            nval = 1,
            converters = RO.CnvUtil.asFloatOrNone,
            dispatcher = self.tuiModel.dispatcher,
        )

        self.cmdDTimeVar = keyVarFact(
            keyword = "CmdDTime",
        )
        self.cmdDTimeVar.addIndexedCallback(self._doCmdDTime)
    
        self.secActMountVar = keyVarFact(
            keyword = "SecActMount",
            nval = (3, None),
        )
        self.secActMountVar.addCallback(self.endTimer)
        
        tccModel = TUI.TCC.TCCModel.getModel()
        tccModel.secFocus.addIndexedCallback(self.updFocus)
        
    def _doCmdDTime(self, cmdDTime, isCurrent, keyVar):
        """Called when CmdDTime seen, to put up a timer.
        """
        if not isCurrent:
            return
        if cmdDTime <= 0:
            return
        msgDict = keyVar.getMsgDict()
        for key in msgDict["data"].keys():
            if key.lower() == "seccmdmount":
                self.startTimer(predTime = cmdDTime)
    
    def _updSecActMount(self, actMount, isCurrent, keyVar=None):
        self.updFocus(actMount, isCurrent)
        if isCurrent:
            self.endTimer()

    def createFocusCmd(self, newFocus, isIncr=False):
        """Create and return the focus command"""
        if isIncr:
            incrStr = "/incr"
        else:
            incrStr = ""
        cmdStr = "set focus=%s%s" % (newFocus, incrStr)

        return RO.KeyVariable.CmdVar (
            actor = "tcc",
            cmdStr = cmdStr,
#            timeLim = 0,
#            timeLimKeyword="CmdDTime",
        )


class SecFocusWdg(Tkinter.Frame):
    def __init__ (self,
        master = None,
     **kargs):
        """creates a new widget for specifying secondary focus

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master, **kargs)
 
        tuiModel = TUI.TUIModel.getModel()

        # set up the command monitor
        self.statusBar = RO.Wdg.StatusBar(
            master = self,
            dispatcher = tuiModel.dispatcher,
            prefs = tuiModel.prefs,
            playCmdSounds = True,
            helpURL = _HelpURL,
        )
        self.statusBar.grid(row=1, column=0, columnspan=4, sticky="ew")

        # command buttons
        buttonFrame = Tkinter.Frame(self)
        
        self.focusWdg = SecBasicFocusWdg(
            master = self,
            statusBar = self.statusBar,
            buttonFrame = buttonFrame,
        )
        self.focusWdg.grid(row=0, column=0, columnspan=4, sticky="w")
        
        buttonFrame.grid(row=2, column=0, columnspan=4, sticky="ew")
    

if __name__ == "__main__":
    root = RO.Wdg.PythonTk()

    tuiModel = TUI.TUIModel.getModel(True)
    kd = tuiModel.dispatcher
    addWindow(tuiModel.tlSet)

    dataDict = {
        "SecFocus": (325.0,),
    }
    msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
    kd.dispatch(msgDict)

    root.mainloop()
