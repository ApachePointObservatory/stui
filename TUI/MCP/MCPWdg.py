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

class Device(object):
    """Represents a device with a bipolar commanded state and a possibly more complex measured state"""
    def __init__(self,
        master,
        name,
        model,
        doCmdFunc,
        btnStrs,
        cmdStrs,
        cmdKeyVar,
        measKeyVar=None,
        devNames=(),
        stateNameDict = None,
        stateCharDict = None,
        cmdMeasStateDict = None,
        warnStates = (),
        errorStates = (),
    ):
        """Create a Device
        
        Inputs:
        - master: parent widget
        - model: model for this actor
        - doCmdFunc: function that runs a command, taking one cmdVar as argument
        - name: name of device, for help string
        - btnStrs: a pair of strings for the button: in order False/True
        - cmdStrs: a pair of command strings: in order: command button False/True
        - cmdKeyVar: the keyVar for the commanded state
        - measKeyVar: the keyVar for the measured state, if any
        - devNames: name of each device in measKeyVar
        - stateNameDict: dict of meas state: name to report it by
        - stateCharDict: dict of meas report state name: summary char
        - cmdMeasStateDict: dict of cmd state: corresponding meas state
        - warnStates: report state names that produce a warning
        - errorStates: reported state names that indicate an error
        """
        self.master = master
        self.name = name
        self.model = model
        self.doCmdFunc = doCmdFunc
        if len(btnStrs) != 2:
            raise ValueError("btnStrs=%s must have 2 elements" % (btnStrs,))
        if len(cmdStrs) != 2:
            raise ValueError("cmdStrs=%s must have 2 elements" % (cmdStrs,))
        self.btnStrs = btnStrs
        self.cmdStrs = cmdStrs
        self.cmdKeyVar = cmdKeyVar
        self.measKeyVar = measKeyVar
        self.devNames = devNames
        self.stateNameDict = stateNameDict or dict()
        self.stateCharDict = stateCharDict or dict()
        self.cmdMeasStateDict = cmdMeasStateDict or dict()
        self.warnStates = warnStates        
        self.errorStates = errorStates
        self.cmdBtn = RO.Wdg.Checkbutton(
            master = self.master,
            callFunc = self.startCmd,
            indicatoron = False,
            helpText = "Commanded state of %s" % (self.name,),
            helpURL = _HelpURL,
        )
        self.stateNameDict = stateNameDict or dict()
        self.stateCharDict = stateCharDict or dict()
        self.cmdMeasStateDict = cmdMeasStateDict or dict()
        if self.measKeyVar:
            self.stateWdg = RO.Wdg.StrLabel(
                master = self.master,
                anchor = "w",
                helpText = "Measured state of %s" % (self.name,),
                helpURL = _HelpURL,
            )
        else:
            self.stateWdg = None
            
        self.enableCmds = True
        self.pendingCmd = None

        if self.measKeyVar:
            self.measKeyVar.addCallback(self.stateCallback, callNow=False)
        self.cmdKeyVar.addCallback(self.stateCallback, callNow=True)
        self.enableBtn()
    
    def cancelCmd(self, *args):
        if self.hasPendingCmd:
            print "%s cancelling cmd %s" % (self, self.pendingCmd)
            self.pendingCmd.abort()

    def enableBtn(self, *args):
        self.cmdBtn.setEnable(not self.hasPendingCmd)
        if self.hasPendingCmd:
            return
        self.enableCmds = False
        try:
            cmdState = self.cmdKeyVar[0]
            if cmdState == None:
                cmdState = True
            btnStr = self.btnStrs[int(cmdState)]
            self.cmdBtn["text"] = btnStr
            self.cmdBtn.setBool(cmdState)
        finally:
            self.enableCmds = True
        self.updateMeasState()
    
    @property
    def hasPendingCmd(self):
        return bool(self.pendingCmd and not self.pendingCmd.isDone)

    def startCmd(self, wdg=None):
        """Command button callback"""
        if not self.enableCmds:
            return
        cmdState = self.cmdBtn.getBool()
        btnStr = self.btnStrs[int(cmdState)]
        cmdStr = self.cmdStrs[int(cmdState)]
        if cmdStr != None:
            cmdVar = opscore.actor.keyvar.CmdVar(
                actor = self.model.actor,
                cmdStr = cmdStr,
                callFunc = self.enableBtn,
            )
            self.pendingCmd = cmdVar
            self.doCmdFunc(cmdVar)
        self.cmdBtn["text"] = btnStr
        self.enableBtn()
    
    def updateMeasState(self):
        """Update measured state, but do not affect buttons"""
        if not self.measKeyVar:
            return
        isCurrent = self.measKeyVar.isCurrent

        stateStr, severity = self.formatStateStr()
        if not isCurrent:
            severity = RO.Constants.sevNormal
        self.stateWdg.set(stateStr, severity=severity, isCurrent=isCurrent)
    
    def stateCallback(self, *args):
        """Update flat-field leaf status"""
        self.updateMeasState()
        self.enableBtn()

    def formatStateStr(self):
        """Format a state string for a set of devices
        
        Return a formatted string and a severity
        """
        measStates = self.measKeyVar.valueList
        cmdState = self.cmdKeyVar[0]
        print "measStates=%s; cmdState=%s" % (measStates, cmdState)

        if len(self.devNames) != len(measStates):
            raise RuntimeError("devNames=%s, measStates=%s; lengths do not match" % (self.devNames, measStates))
        
        statusByName = [self.stateNameDict.get(str(state), str(state)) for state in measStates]
        print "statusByName=", statusByName
        
        numDevs = len(self.devNames)
        # order the severities so we can keep track of maximum severity encountered
        sevIndexDict = {
            0: RO.Constants.sevNormal,
            1: RO.Constants.sevWarning,
            2: RO.Constants.sevError,
        }
        # a dictionary of non-normal severity states: state: index, but omitting normal
        sevStateIndexDict = dict()
        for state in self.warnStates:
            sevStateIndexDict[state] = 1
        for state in self.errorStates:
            sevStateIndexDict[state] = 2

        # a dictionary of state name: list of indices (as strings) of devices in this list
        stateDict = {}
        for devName, devState in zip(self.devNames, measStates):
            devList = stateDict.setdefault(devState, [])
            devList.append(str(devName)) # use str in case devName is an integer
        stateStrList = []
        sevIndex = 0
        desMeasState = None
        cmdState = self.cmdKeyVar[0]
        if cmdState != None:
            desMeasState = self.cmdMeasStateDict.get(cmdState, None)
        
        for state, devList in stateDict.iteritems():
            if len(devList) == numDevs:
                stateStr = "All " + str(state)
                sevIndex = max(sevIndex, sevStateIndexDict.get(state, 0))
                if desMeasState and state not in (None, desMeasState):
                    sevIndex = max(sevIndex, 1)
                return stateStr, sevIndexDict[sevIndex]
            stateChar = self.stateCharDict.get(state, "?")
            stateStrList.append(stateChar)
        if desMeasState:
            sevIndex = max(sevIndex, 1)
        return "".join(stateStrList), sevIndexDict[sevIndex]
    
        def __str__(self):
            return self.__class__.__name__

class IackDevice(Device):
    def __init__(self, master, model, doCmdFunc):
        Device.__init__(self,
            master = master,
            name = "Iack",
            model = model,
            doCmdFunc = doCmdFunc,
            btnStrs = ("Needed", "Done"),
            cmdStrs = (None, "iack"),
            cmdKeyVar = model.needIack,
            measKeyVar = None,
        )

class FFLeavesDevice(Device):
    def __init__(self, master, model, doCmdFunc):
        stateNameDict = {
            None: "?",
            "00": "?",
            "01": "Closed",
            "10": "Open",
            "11": "Invalid",
        }
        stateCharDict = {
            None: "?",
            "Closed": "-",
            "Open": "|",
            "Invalid": "X",
        }
        cmdMeasStateDict = {
            "Closed": "Closed",
            "Opened": "Open",
        }
        Device.__init__(self,
            master = master,
            name = "FF Leaves",
            model = model,
            doCmdFunc = doCmdFunc,
            btnStrs = ("Closed", "Opened"),
            cmdStrs = ("ffl_close", "ffl_open"),
            cmdKeyVar = model.ffLeafCommandedOn,
            measKeyVar = model.ffLeafStatus,
            devNames = [str(ind+1) for ind in range(8)],
            stateNameDict = stateNameDict,
            stateCharDict = stateCharDict,
            cmdMeasStateDict = cmdMeasStateDict,
        )

class LampDevice(Device):
    def __init__(self, master, name, model, doCmdFunc, cmdKeyVar, measKeyVar=None):
        stateNameDict = {
            None: "?",
            False: "Off",
            True: "On",
        }
        stateCharDict = {
            None: "?",
            "Off": "O",
            "On": "*",
        }
        lowName = name.lower()
        cmdStrs = ["%s_%s" % (name.lower(), cmd) for cmd in ("off", "on")]
        Device.__init__(self,
            master = master,
            name = name,
            model = model,
            doCmdFunc = doCmdFunc,
            btnStrs = ("Off", "On"),
            cmdStrs = cmdStrs,
            cmdKeyVar = cmdKeyVar,
            measKeyVar = measKeyVar,
            devNames = [str(ind+1) for ind in range(4)],
        )


class MCPWdg (Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        """Create a widget to control the MCP
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.mcpModel = MCPModel.Model()
        
        gr = RO.Wdg.Gridder(self, sticky="e")
        self.gridder = gr
        self.devList = []
        
        iackDev = IackDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
        )
        self.addDev(iackDev)
        
        ffLeavesDev = FFLeavesDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
        )
        self.addDev(ffLeavesDev)
        
        ffLampDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "ffl",
            cmdKeyVar = self.mcpModel.ffLampCommandedOn,
            measKeyVar = self.mcpModel.ffLamp,
        )
        self.addDev(ffLampDev)
        
        hgCdDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "hgcd",
            cmdKeyVar = self.mcpModel.hgCdLampCommandedOn,
            measKeyVar = self.mcpModel.hgCdLamp,
        )
        self.addDev(hgCdDev)

        neDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "ne",
            cmdKeyVar = self.mcpModel.neLampCommandedOn,
            measKeyVar = self.mcpModel.neLamp,
        )
        self.addDev(neDev)

        uvDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "uv",
            cmdKeyVar = self.mcpModel.uvLampCommandedOn,
            measKeyVar = None,
        )
        self.addDev(uvDev)

        whtDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "wht",
            cmdKeyVar = self.mcpModel.whtLampCommandedOn,
            measKeyVar = None,
        )
        self.addDev(whtDev)

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
        
        self.enableButtons()
    
    def addDev(self, dev):
        self.devList.append(dev)
        self.gridder.gridWdg(dev.name, dev.cmdBtn, dev.stateWdg, sticky=None)

    def _cancelBtnCallback(self, wdg=None):
        """Cancel all pending commands"""
        for dev in self.devList:
            dev.cancelCmd()
        
    def doCmd(self, cmdVar):
        """Execute a command variable and update cancel button state"""
        cmdVar.addCallback(self.enableCancelBtn)
        self.statusBar.doCmd(cmdVar)
        self.enableCancelBtn()
    
    def enableCancelBtn(self, *args):
        hasPendingCmds = False
        for dev in self.devList:
            hasPendingCmds |= dev.hasPendingCmd
        self.cancelBtn.setEnable(hasPendingCmds)
        
    def enableButtons(self, *args):
        """Enable or disable buttons"""
        self.enableCancelBtn()
        for dev in self.devList:
            dev.enableBtn()

    def __str__(self):
        return self.__class__.__name__

        
if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = MCPWdg(root)
    testFrame.pack()

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.init()

    tuiModel.reactor.run()
