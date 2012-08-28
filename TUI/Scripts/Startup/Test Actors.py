"""
History:
2010-06-09 EM added check of fail for guider cartridge
2011-05-16 EM resizable window, added three apogee actors 
2012-06-01 RO use asynchronous calls
2012-08-28 EM design - output actor + cmd 
"""
import RO.Constants
import RO.Wdg
import TUI.Models
from datetime import datetime

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.logWdg = RO.Wdg.LogWdg(master=sr.master, width=25, height=21)
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.redWarn=RO.Constants.sevError
        self.actorCmdVarList = []
        self.startTimeStr = None
    
    def cmdCallback(self, dum=None):
        """Command callback: redisplay all information
        
        Note: redisplaying everything keeps the actors in the desired order.
        """
        self.logWdg.clearOutput()
        self.logWdg.addMsg("Test Actors, %s" % (self.startTimeStr))
        self.logWdg.addMsg("-"*30)        
        for actor, cmd, cmdVar in self.actorCmdVarList:
            if not cmdVar.isDone:
#                self.logWdg.addMsg("%s - ?" % (cmdVar.actor, ), severity=RO.Constants.sevWarning)
                 self.logWdg.addMsg("%s %s - ?" % (actor, cmd,), severity=RO.Constants.sevWarning)
            elif cmdVar.didFail:
#                self.logWdg.addMsg("%s - FAILED" % (cmdVar.actor,), severity=RO.Constants.sevError)
                 self.logWdg.addMsg("%s %s - **FAILED**" % (actor,cmd), severity=RO.Constants.sevError)
            else:
 #               self.logWdg.addMsg("%s  - OK" % (cmdVar.actor))
                 self.logWdg.addMsg("%s  %s  - ok" % (actor, cmd))
 
    
    def run(self, sr):
        utc_datetime = datetime.utcnow()
        self.startTimeStr = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

        self.actorCmdVarList = []
        cmdVarList = []
        for actorCmd in [
            "alerts ping",
            "apo ping",
            "apogee ping",
            "apogeecal ping",
            "apogeeql ping",            
            "boss ping",
            "ecamera ping",
            "gcamera ping",
            "guider ping",
            "hub ping",
            "keys getFor=hub version",
            "mcp ping",
            "msg (testing actors)",
            "perms status",
            "platedb ping",
            "sop ping",
            "sos ping",
            "tcc show time",
            "test to fail",
        ]:
            actor, cmd = actorCmd.split(None, 1)
            cmdVar = sr.startCmd(
                actor = actor,
                cmdStr = cmd,
                callFunc = self.cmdCallback,
                checkFail = False,
            )
            cmdVarList.append(cmdVar)
            self.actorCmdVarList.append((actor,cmd, cmdVar))

        
        self.cmdCallback()

        yield sr.waitCmdVars(cmdVarList, checkFail=False)            
        self.logWdg.addMsg("-- done --")
		
