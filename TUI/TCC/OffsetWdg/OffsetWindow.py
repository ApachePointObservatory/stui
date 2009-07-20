#!/usr/bin/env python
"""Offset control.

History:
2003-04-04 ROwen
2003-04-15 ROwen    Bug fix: window could be resized.
2003-04-21 ROwen    Renamed StatusWdg to StatusBar to avoid conflicts.
2003-04-22 ROwen    Renamed from SimpleOffsetWdg to OffsetWdg
2003-06-09 ROwen    Removed most args from addWindow
                    and dispatcher and prefs args from OffsetWdg.
2003-06-12 ROwen    Added helpText entries.
2003-06-25 ROwen    Modified test case to handle message data as a dict
2003-11-06 ROwen    Changed Offset.html to OffsetWin.html
2003-11-19 ROwen    PR 8 fix: I changed slews to computed (in InputWdg)
                    but did not add timeLimKeyword="SlewDuration" to the KeyCommand,
                    so commands could time out.
2003-12-05 ROwen    Disable the Offset button during the offset.    
2004-02-23 ROwen    Modified to play cmdDone/cmdFailed for commands.
2004-05-18 ROwen    Eliminated redundant import in test code.
2004-06-22 ROwen    Modified for RO.Keyvariable.KeyCommand->CmdVar
2005-01-05 ROwen    Changed level to severity for RO.Wdg.StatusBar.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2009-04-01 ROwen    Modified for tuisdss.
2009-07-19 ROwen    Changed cmdVar.timeLimKeyword to timeLimKeyVar.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import opscore.actor.keyvar
import InputWdg
import TUI.Base.Wdg
import TUI.TCC.TCCModel
import TUI.PlaySound

_HelpPrefix = "Telescope/OffsetWin.html#"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = "TCC.Offset",
        defGeom = "+0+507",
        resizable = False,
        wdgFunc = OffsetWdg,
    )

class OffsetWdg(Tkinter.Frame):
    def __init__ (self,
        master = None,
     **kargs):
        """creates a new widget for specifying simple offsets

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master, **kargs)

        self.inputWdg = InputWdg.InputWdg(self)
        self.inputWdg.pack(side="top", anchor="nw")
        self.inputWdg.addCallback(self._offsetEnable)
        
        self.tccModel = TUI.TCC.TCCModel.Model()

        # set up the command monitor
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
            helpURL = _HelpPrefix + "StatusBar",
        )
        self.statusBar.pack(side="top", anchor="nw", expand="yes", fill="x")
        
        # command buttons
        self.buttonFrame = Tkinter.Frame(self)
        self.offsetButton = RO.Wdg.Button(
            master=self.buttonFrame,
            text="Offset",
            command=self.doOffset,
            helpText = "Offset the telescope",
            helpURL=_HelpPrefix + "OffsetButton",
        )
        self.offsetButton.pack(side="left")

        self.clearButton = RO.Wdg.Button(
            master=self.buttonFrame,
            text="Clear",
            command=self.inputWdg.clear,
            helpText = "Clear the displayed values",
            helpURL=_HelpPrefix + "ClearButton",
        )
        self.clearButton.pack(side="left")

        def restoreOffset(name, valueDict):
            """Restore an offset from the history menu"""
            self.inputWdg.setValueDict(valueDict)

        self.historyMenu = RO.Wdg.HistoryMenu(
            master = self.buttonFrame,
            callFunc = restoreOffset,
            removeAllDup = True,
            helpText = "A list of past offsets",
            helpURL = _HelpPrefix + "HistoryWdg",
        )
        self.historyMenu.pack(side="left")

        self.buttonFrame.pack(side="top", anchor="nw")
    
    def cmdSummary(self, valueDict):
        """Returns a short string describing a dictionary of settings.
        """
        typeStr = valueDict["type"].replace(" ", "_")
        amt =  valueDict["amount"]
        amt = [val or "0" for val in amt]
        amtStr = ', '.join(amt)
        return "%s %s %s" % (typeStr, amtStr, valueDict["absOrRel"])

    def addCmdToHistory(self):
        """Add the current settings to the history menu.
        """
        valueDict = self.inputWdg.getValueDict()
        self.historyMenu.addItem(self.cmdSummary(valueDict), valueDict)
        
    def doOffset(self):
        """Perform the offset.
        """
        self.inputWdg.neatenDisplay()
        self._offsetEnable(False)
        try:
            cmdStr = self.inputWdg.getCommand()
        except ValueError, e:
            self.statusBar.setMsg(
                "Rejected: %s" % e,
                severity = RO.Constants.sevError,
                isTemp = True,
            )
            TUI.PlaySound.cmdFailed()
            return

        def offsetEnableShim(*args, **kargs):
            self._offsetEnable(True)
            
        cmdVar = opscore.actor.keyvar.CmdVar (
            actor = "tcc",
            cmdStr = cmdStr,
            timeLim = 10,
            timeLimKeyVar = self.tccModel.slewDuration,
            isRefresh = False,
            callFunc = offsetEnableShim,
        )
        self.statusBar.doCmd(cmdVar)
        self.addCmdToHistory()
    
    def _offsetEnable(self, doEnable=True):
        """Enables or disables the Apply button
        """
        if doEnable:
            self.offsetButton["state"] = "normal"
        else:
            self.offsetButton["state"] = "disabled"

if __name__ == "__main__":
    import TUI.Base.TestDispatcher

    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher(actor="tcc")
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot

    testFrame = OffsetWdg(root)
    testFrame.pack(anchor="nw")
    tuiModel.tkRoot.resizable(width=0, height=0)

    dataList = (
        "ObjInstAng=30.0, 0.0, 1.0",
    )

    testDispatcher.dispatch(dataList)

    tuiModel.reactor.run()
