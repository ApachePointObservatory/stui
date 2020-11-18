#!/usr/bin/env python
"""Interlocks widget.

Questions:
- Should the timestamp be updated by:
  - ab_statusCallback
  - instrumentNumCallback
  - instrumentNumConsistentCallback

- Why is set mcpDataNames(name) set for bits and ctime
  but not for aliveAt, pclVersion, instrumentNum, etc.?
  
- Why can aliveAt, plcVersion and the many bits be set by calling set_name
  but instrumentNum and instrumentNumConsisten cannot?
  
History:
2009-09-18 ROwen    Added callbacks for instrumentNum and instrumentNumConsistent.
"""
import os
import time
import Tkinter
import opscore.protocols
import plc

__all__ = ["InterlocksWdg"]

class InterlocksWdg(Tkinter.Frame):
    def __init__(self, master, mcpModel):
        """A wrapper around the tcl/tk code.
        
        Inputs:
        - master: master widget
        - mcpModel: the MCP model
        """
        Tkinter.Frame.__init__(self, master)
        
        # the following are required to find the plc and interlocks tcl code in a bundled application
        # they will have no effect when running from source since the resulting environment variables
        # will match the ones that already exist
        plcRootDir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(plc.__file__))))
        os.environ["PLC_DIR"] = plcRootDir
        plcTclDir = os.path.abspath(os.path.join(plcRootDir, "etc"))

        interlocksRootDir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
        os.environ["PLC_DIR"] = interlocksRootDir
        interlocksTclDir = os.path.abspath(os.path.join(interlocksRootDir, "etc"))
        
        self.tk.call("source", os.path.join(plcTclDir, "dervish.tcl"))
   
        # Define callbacks for all KeyVar's beginning "ab_"
        for keyVar in mcpModel.keyVarDict.values():
            if keyVar.name.startswith("ab_") and keyVar.name != "ab_status":
                self.addTclCallback(keyVar)

                # Tell the displays that this bit will (eventually) appear
                t = keyVar.key.typedValues.vtypes[0]
                if isinstance(t, opscore.protocols.types.Bits):
                    for k in t.bitFields.keys():
                        self.addDataName(k)

        mcpModel.ab_status.addCallback(self.ab_statusCallback, callNow=False)
        self.addTclCallback(mcpModel.aliveAt)
        self.addTclCallback(mcpModel.plcVersion)
        
        mcpModel.instrumentNum.addCallback(self.instrumentNumCallback, callNow=False)
        mcpModel.instrumentNumConsistent.addCallback(self.instrumentNumConsistentCallback, callNow=False)
    
        self.addDataName("ctime")
    
        try:
            self.tk.call("source", os.path.join(interlocksTclDir, "interlockStartup.tcl"))
            self.tk.call("startInterlocks", self, 1)
        except:
            self.tk.call("tb")                 # traceback; print tcl's $errorinfo

    def addDataName(self, name):
        """Tell the displays that this named data will eventually appear
        """
        self.tk.call("set", "mcpDataNames(%s)" % (name,), "1")

    def addTclCallback(self, keyVar):
        """Add a callback for Allen-Bradley field (e.g. ab_I1_L13)
        
        Also sets other variables that can be set using the tcl command set_<name>.
        """
        if keyVar.name.startswith("ab_"):
            tclSetName = "set_" + keyVar.name[3:]
        else:
            tclSetName = "set_" + keyVar.name

        def callFunc(keyVar, tclSetName=tclSetName):
            #print "%s", keyVar
            if keyVar[0] is not None:
                self.tk.call(tclSetName, int(keyVar[0]))
                self.setTimestamp()

        keyVar.addCallback(callFunc, callNow=False)    

    def ab_statusCallback(self, keyVar):
        """Status is 4 ints, so handle specially.
        """
        if keyVar[0] is not None:
            self.tk.call("set_status", keyVar[0], keyVar[1], keyVar[2], keyVar[3])
#            self.setTimestamp() # is this wanted? RHL's code didn't set it

    def instrumentNumCallback(self, keyVar):
        if not keyVar.isCurrent:
            return
        value = keyVar[0]
        if value == None:
            value = -1
        self.setMcpData(keyVar.name, value)
#       self.setTimestamp() # is this wanted?

        
    def instrumentNumConsistentCallback(self, keyVar):
        if not keyVar.isCurrent:
            return
        self.setMcpData(keyVar.name, keyVar[0])
#        self.setTimestamp() # is this wanted?

    def setMcpData(self, name, value):
        """Set specified entry of the tcl associative array mcpData.
        
        Some known entries:
        - ctime (an integer version of unix time)
        - instrumentNum (an integer)
        - instrumentNumConsistent (a boolean)
        """
        self.tk.call("set", "mcpData(%s)" % (name,), value)

    def setTimestamp(self):
        """Set mcp timestamp
        """
        self.tk.call("set", "mcpData(ctime)", int(time.time()))
        

if __name__ == "__main__":
    import getpass
    import twisted.internet.tksupport
    import opscore.actor
    import RO.Comm

    root = Tkinter.Tk()
    root.resizable(False, False)
    twisted.internet.tksupport.install(root)

    def connectCallback(connection):
        print connection.getFullState()[1]

    connection = RO.Comm.HubConnection.HubConnection("hub25m", 9877)
    connection.addStateCallback(connectCallback)
    progID = raw_input("Program ID? ")
    progID = progID.upper()
    pwd = getpass.getpass("Password for program %s? " % progID)
    connection.connect(username="interlocksDisplay", progID=progID, password=pwd)

    dispatcher = opscore.actor.CmdKeyVarDispatcher(connection=connection)
    opscore.actor.Model.setDispatcher(dispatcher)
    mcpModel = opscore.actor.Model("mcp")
    
    testFrame = InterlocksWdg(root, mcpModel)
    testFrame.pack(fill="both", expand=True)

    dispatcher.reactor.run()
