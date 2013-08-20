# threeReadsDark.py
## takes short dark to check apogee binding 
# 02-21-2013 EM: proceed if gang connector is in podium;  UT time changed to TAI

import RO.Wdg
import TUI.Models
from datetime import datetime
import time
#import RO.Astro.Tm
import subprocess
import tkMessageBox as box

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False
        
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.logWdg = RO.Wdg.LogWdg(master=sr.master, width=35, height =20,)
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
  #      self.redWarn=RO.Constants.sevError
        self.name="apogee: threeReadsDark "        
        self.logWdg.text.tag_config("a", foreground="magenta")
    
    def getTAITimeStr(self,):
      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
      currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
      self.taiTimeStr = time.strftime("%H:%M:%S", currTAITuple) 
      return self.taiTimeStr
      
    def checkGangPodium(self, sr): 
        self.mcpModel = TUI.Models.getModel("mcp")
        ngang=sr.getKeyVar(self.mcpModel.apogeeGang, ind=0, defVal=None)
     #   ngang="1"  
        if ngang==None: 
            raise sr.ScriptError("gang position is not availble")   
        ngang=int(ngang)
        labelHelp=["Disconnected", "Podium", "Cart", "Sparse cals"]
        sgang=labelHelp[ngang]
        ss1="GANG: %s" % sgang
        if ngang != 1:
           ss2="\n   gang must be in Podium,\n      cannot start calibration"
           self.logWdg.addMsg(ss1+ss2, severity=RO.Constants.sevError)
           subprocess.Popen(['say',"gang problem"])
           box.showwarning(self.name, ss1+ss2)
           raise sr.ScriptError("")   
           return False   
        else:
           self.logWdg.addMsg(ss1+" - ok, started")
           return True  
      
    def run(self, sr):       
      tm = self.getTAITimeStr()      
      self.logWdg.addMsg("-- %s -- %s " % (tm,self.name),tags=["a"])  

      if not self.checkGangPodium(sr):
           raise sr.ScriptError("") 
 
      for actorCmd in [
            "apogeecal allOff",
            "apogee shutter close",
            "apogeecal shutterOpen",
            "apogee expose nreads=3 ; object=Dark",
         #   "apogee expose nreads=10 ; object=Dark",
            "apogeecal shutterClose",
            "apogeecal allOff",          
      ]:
         actor, cmd = actorCmd.split(None, 1)
         self.logWdg.addMsg("%s" % (actorCmd)) 
         yield sr.waitCmd(actor=actor, cmdStr=cmd, checkFail = False,)
         cmdVar = sr.value
         if cmdVar.didFail:
             ss1=" %s   ** FAILED **" % (actorCmd)
             self.logWdg.addMsg("      %s" % (ss1),severity=RO.Constants.sevError)
             print self.name, ss1
             break

      self.logWdg.addMsg("-- done --",tags=["a"])  
      self.logWdg.addMsg("")

#mcp.py
#Key("apogeeGang",
#Enum("0", "1", "2", "3", labelHelp=("Disconnected", "Podium", "Cart", "Sparse cals"))),

#apogeecal allOff
#apogee shutter close
#apogeecal shutterOpen
#apogee expose nreads=3 ; object=Dark
#apogeecal shutterClose
#apogeecal allOff
