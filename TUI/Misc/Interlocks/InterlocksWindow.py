#!/usr/bin/env python
"""Instant messaging widget.

History:
2009-07-19 ROwen
"""
import os
import time
import Tkinter
import opscore.protocols
import RO.Wdg
import TUI.TUIModel
import TUI.Misc.MCP.MCPModel

def addWindow(tlSet):
    # about window
    tlSet.createToplevel(
        name = "Misc.Interlocks",
        defGeom = "+350+350",
        resizable = False,
        visible = True,
        wdgFunc = InterlockWdg,
    )

_HelpPage = "Misc/InterlocksWin.html"

class InterlockWdg(Tkinter.Frame):
    def __init__(self, master):
        """A wrapper around RHL's Interlocks tcl/tk display.
        
        Inputs:
        - master: master widget
        """
        Tkinter.Frame.__init__(self, master)
        tuiModel = TUI.TUIModel.Model()
        self.tkRoot = tuiModel.tkRoot
        self.mcpModel = TUI.Misc.MCP.MCPModel.Model()

        tclDir = os.path.abspath(os.path.join(os.path.dirname(__file__), "tcl"))

        self.tkRoot.call("source", os.path.join(tclDir, "dervish.tcl"))
   
        # Define callbacks for all KeyVar's beginning "ab_"
        for keyVar in self.mcpModel.keyVarDict.values():
            if keyVar.name.startswith("ab_") and keyVar.name != "ab_status":
                self.addTclCallback(keyVar)

                # Tell the displays that this bit will (eventually) appear
                t = keyVar.key.typedValues.vtypes[0]
                if isinstance(t, opscore.protocols.types.Bits):
                    for k in t.bitFields.keys():
                        self.tkRoot.call("set", "mcpDataNames(%s)" % k, "1")

        self.mcpModel.ab_status.addCallback(self.ab_statusCallback, callNow=False)
        self.addTclCallback(self.mcpModel.aliveAt)
        self.addTclCallback(self.mcpModel.plcVersion)
        self.addTclCallback(self.mcpModel.lavaLamp)
    
        self.tkRoot.call("set", "mcpDataNames(ctime)", "1") # mcpData(ctime) is used too
    
        try:
            self.tkRoot.call("source", os.path.join(tclDir, "interlockStartup.tcl"))
            self.tkRoot.call("startInterlocks", self, 1)
        except:
            self.tkRoot.call("tb")                 # traceback; print tcl's $errorinfo

    def addTclCallback(self, keyVar):
        """Add a callback for Allen-Bradley field (e.g. I1_L13) and other things"""
        if keyVar.name.startswith("ab_"):
            tclSetName = "set_" + keyVar.name[3:]
        else:
            tclSetName = "set_" + keyVar.name

        def callFunc(keyVar, tclSetName=tclSetName, tkRoot=self.tkRoot):
            #print "%s", keyVar
            if keyVar[0] is not None:
                tkRoot.call(tclSetName, int(keyVar[0]))
                tkRoot.call("set", "mcpData(ctime)", int(time.time()))

        keyVar.addCallback(callFunc, callNow=False)    

#         exec """def %s(keyVar):
#     #print "%s", keyVar
#     if keyVar[0] is not None:
#         root.call("%s", int(keyVar[0]))
#         root.call("set", "mcpData(ctime)", int(time.time()))
# 
# mcpModel.%s.addCallback(%s, callNow=False)
# 
# """ % (field, field, tclSetName, field, field)

    def ab_statusCallback(self, keyVar):
        """status is 4 ints, so handle specially"""
        if keyVar[0] is not None:
            self.tkRoot.call("set_status", keyVar[0], keyVar[1], keyVar[2], keyVar[3])
        

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp")
    tuiModel = testDispatcher.tuiModel

    testFrame = InterlockWdg(tuiModel.tkRoot)
    testFrame.pack(fill="both", expand=True)
    
    tuiModel.reactor.run()
