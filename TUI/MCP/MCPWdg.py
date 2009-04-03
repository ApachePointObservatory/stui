#!/usr/bin/env python
"""Status and control for the MCP

History:
2009-04-02 ROwen
"""
import numpy
import Tkinter
import RO.Alg
import RO.Constants
import RO.Wdg
import opscore.actor.keyvar
import TUI.Base.Wdg
import MCPModel

_HelpURL = "Misc/MCPWin.html"

_ColsPerDev = 3 # number of columns for each device widget

def formatStateStr(devInfo, warnStates=(), errorStates=()):
    """Format a state string for a set of devices
    
    Inputs:
    - devInfo: a collectionn of (device name/index, device state)
    - warnStates: states which should generate a warning
    - errorStates: states which should generate an error
    
    Return a formatted string and a severity
    """
    numDevs = len(devInfo)
    # order the severities so we can keep track of maximum severity encountered
    sevIndexDict = {
        0: RO.Constants.sevNormal,
        1: RO.Constants.sevWarning,
        2: RO.Constants.sevError,
    }
    # a dictionary of non-normal severity states: sate: index, but omitting normal
    sevStateIndexDict = dict()
    for state in warnStates:
        sevStateIndexDict[state] = 1
    for state in errorStates:
        sevStateIndexDict[state] = 2

    # a dictionary of state name: list of indices (as strings) of devices in this list
    stateDict = {}
    for devName, devState in devInfo:
        if devState == None:
            continue
        devList = stateDict.setdefault(devState, [])
        devList.append(str(devName)) # use str in case devName is an integer
    stateStrList = []
    sevIndex = 0
    for state, devList in stateDict.iteritems():
        if len(devList) == numDevs:
            stateStr = "All " + str(state)
            sevIndex = max(sevIndex, sevStateIndexDict.get(state, 0))
            return stateStr, sevIndexDict[sevIndex]
        stateStrList.append("%s %s" % (",".join(devList)), str(state))
    return " ".join(stateStrList), sevIndexDict[sevIndex]

class LampSet(object):
    def __init__(self, name, mcpWdg):
        self.name = name
        self.mcpWdg = mcpWdg
        

class MCPWdg (Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        """Create a widget to control the MCP
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.actor = "mcp"
        self.mcpModel = MCPModel.Model()
        
        self._enableCmds = True
        
        self.pendingCmdVarSet = set()
        self.pendingCmdWdgSet = set()
        
        gr = RO.Wdg.Gridder(self, sticky="e")

        self.iackBtn = RO.Wdg.Button(
            master = self,
            text = "Iack",
            callFunc = self._iackBtnCallback,
            helpText = "Send Iack to acknowledge reboot",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Iack", self.iackBtn)
        
        self.ffLeafBtn = RO.Wdg.Checkbutton(
            master = self,
            text = "Open",
            callFunc = self._ffLeafBtnCallback,
            indicatoron = False,
            autoIsCurrent = True,
            helpText = "Commanded state of flat field leaves",
            helpURL = _HelpURL,
        )
       
        self.ffLeafStateWdg = RO.Wdg.StrLabel(
            master = self,
            width = 10,
            helpText = "True state of flat field leaves",
            helpURL = _HelpURL,
        )
        gr.gridWdg("FF Leaves", self.ffLeafBtn, self.ffLeafStateWdg)
        
        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "Cancel",
            callFunc = self._cancelBtnCallback,
            helpText = "Cancel all pending commands",
            helpURL = _HelpURL,
        )
        gr.gridWdg(self.cancelBtn)
        
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
            helpURL = _HelpURL,
        )
        
        gr.gridWdg(False, self.statusBar, colSpan=10, sticky="ew")
        
#        self.mcpModel.needIack.addROWdg(self.iackBtn, setDefault=True)
#        self.mcpModel.needIack.addCallback(self.enableButtons)
        self.mcpModel.ffLeafStatus.addCallback(self._ffLeafCallback)
#        self.mcpModel.ffLeafCommandedOn.addCallback(self._ffLeafCallback)
        self.enableButtons()

    def _cancelBtnCallback(self, wdg=None):
        """Cancel all pending commands"""
        cmdsToCancel = self.pendingCmdVarSet.copy() 
        for cmdVar in cmdsToCancel:
            print "Cancelling command", cmdVar
            cmdVar.abort()
        print "There are now %s pending commands" % (len(self.pendingCmdVarSet),)
        
            
    def doCmd(self, cmdStr, wdg):
        """Execute a command; disabling the widget while the command runs"""
        if not self._enableCmds:
            return
            
        def cmdDone(cmdVar, self=self, wdg=wdg):
            try:
                self.pendingCmdVarSet.remove(cmdVar)
            except Exception:
                sys.stderr.write("%s error: could not find %s in pendingCmdVarSet" % (self, cmdVar))
            try:
                self.pendingCmdWdgSet.remove(wdg)
            except Exception:
                sys.stderr.write("%s error: could not find %s in pendingCmdWdgSet" % (self, wdg))
            self.enableButtons()
            
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = self.actor,
            cmdStr = cmdStr,
            callFunc = cmdDone,
            callCodes = opscore.actor.keyvar.DoneCodes,
        )
        wdg.setEnable(False)
        self.statusBar.doCmd(cmdVar)
        self.pendingCmdVarSet.add(cmdVar)
        self.pendingCmdWdgSet.add(wdg)
        self.enableCancelBtn()

    def _iackBtnCallback(self, wdg):
        """Send iack command"""
        self.doCmd("iack", wdg)
    
    def _ffLeafBtnCallback(self, wdg=None):
        """Callback for ffLeafBtn"""
        doOpen = self.ffLeafBtn.getBool()
        verb = "Open" if doOpen else "Close"
        cmdStr = "ffs_" + verb.lower()
        self.ffLeafBtn["text"] = verb
        self.doCmd(cmdStr, self.ffLeafBtn)

    def enableCancelBtn(self, *args):
        self.cancelBtn.setEnable(len(self.pendingCmdVarSet) != 0)
        
    def enableFFLeafBtn(self, *args):
        self._enableCmds = False
        try:
            if self.ffLeafBtn not in self.pendingCmdWdgSet:
                commandedToOpen = self.mcpModel.ffLeafCommandedOn[0]
                if commandedToOpen:
                    self.ffLeafBtn.setBool(True),
                    self.ffLeafBtn.text = "Open"
                else:
                    self.ffLeafBtn.setBool(False)
                    self.ffLeafBtn.text = "Close"
                self.ffLeafBtn.setEnable(True)
        finally:
            self._enableCmds = True
    
    def enableIackBtn(self, *args):
        print "needIack=%s; isCurrent=%s" % (self.mcpModel.needIack, self.mcpModel.needIack.isCurrent)
        if self.iackBtn not in self.pendingCmdWdgSet:
            needIack = self.mcpModel.needIack[0] in (None, True)
            self.iackBtn.setEnable(needIack)

    def enableButtons(self, *args):
        """Enable or disable buttons"""
        self.enableCancelBtn()
        self.enableIackBtn()
        self.enableFFLeafBtn()
    
    def _ffLeafCallback(self, keyVar):
        """Handle the main flat field leaf keyVars"""
        print "%s._ffLeafCallback(%s)" % (self, keyVar)
        ffStates = self.mcpModel.ffLeafStatus.valueList
        ffStatesIsCurr = self.mcpModel.ffLeafStatus.isCurrent
        print "_ffLeafCallback ffStates=%s, isCurrent=%s" % (ffStates, ffStatesIsCurr)
        commandedOn = self.mcpModel.ffLeafCommandedOn.valueList
        commandedOnIsCurrent = self.mcpModel.ffLeafCommandedOn.isCurrent
        isCurrent = ffStatesIsCurr and commandedOnIsCurrent
        
        stateNameDict = {
            None: "?",
            "00": "?",
            "01": "Closed",
            "10": "Open",
            "11": "Invalid",
        }
        statusByName = [stateNameDict.get(state, state) for state in ffStates]

        devInfo = [(ind+1, name) for (ind, name) in enumerate(statusByName)]
        warnStates=["?"]
        if commandedOn != None:
            if commandedOn:
                warnStates.append("Closed")
            else:
                warnStates.append("Open")
        stateStr, severity = formatStateStr(devInfo, warnStates=warnStates, errorStates=["Invalid"])
        self.ffLeafStateWdg.set(stateStr, severity=severity, isCurrent=isCurrent)
        self.enableFFLeafBtn()

    def __str__(self):
        return self.__class__.__name__

        
if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = MCPWdg(root)
    testFrame.pack()

#    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.runTest()

    tuiModel.reactor.run()
