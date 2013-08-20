'''cartchange.py   - it takes two darks for apogee

stui  wrap for cartchange.inp script (11Oct01)
use while the cartridge is being changed'''

# History: 
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
        self.redWarn=RO.Constants.sevError
        self.name="apogee: cartchange"
        self.ver="11Oct01"
        self.logWdg.text.tag_config("a", foreground="magenta")        
        self.logWdg.addMsg('%s, v-%s ' % (self.name,self.ver))
        self.logWdg.addMsg("   %s " % ("  2 10-reads darks"))
        self.logWdg.addMsg("-"*20)
        
    # v1    
    def checkGangPodium(self, sr):   
        self.mcpModel = TUI.Models.getModel("mcp")
        ngang=sr.getKeyVar(self.mcpModel.apogeeGang, ind=0, defVal=None)
      #  ngang="0"    # for debugging
        if ngang==None: 
            self.logWdg.addMsg(" Erros:  gang position is not availble",
                  severity=self.redWarn)
            subprocess.Popen(['say',"gang problem"])
            box.showwarning("gang problem", "gang is not availble")
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
           self.logWdg.addMsg(ss1+" - ok")
           return True

    def getTAITimeStr(self,):
      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
      currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
      self.taiTimeStr = time.strftime("%H:%M:%S", currTAITuple) 
      return self.taiTimeStr
    
    def run(self, sr):       
      tm = self.getTAITimeStr()  
      self.logWdg.addMsg("-- %s -- %s " % (tm,self.name), tags=["a"])
      
      if not self.checkGangPodium(sr):
           raise sr.ScriptError("") 

     # return # for debugging

      subprocess.Popen(['say',"ok, started"]) 
      for actorCmd in [
        #   "tcc show time"
            "apogeecal allOff",
            "apogee shutter close",
            "apogeecal shutterOpen",
            "apogee expose nreads=10 ; object=Dark",
            "apogee expose nreads=10 ; object=Dark",
            "apogeecal shutterClose",
            "apogeecal allOff",          
      ]:
         actor, cmd = actorCmd.split(None, 1)
         self.logWdg.addMsg("%s .... " % (actorCmd,))
         yield sr.waitCmd(actor=actor, cmdStr=cmd, checkFail = False,)
         cmdVar = sr.value
         if cmdVar.didFail:
             self.logWdg.addMsg("   ** FAILED **" % (actorCmd),severity=RO.Constants.sevError)

      self.logWdg.addMsg("-- done --",tags=["a"])  
      self.logWdg.addMsg("")

#apogeecal allOff
#apogee shutter close
#apogeecal shutterOpen
#apogee expose nreads=10 ; object=Dark
#apogee expose nreads=10 ; object=Dark
#apogeecal shutterClose
#apogeecal allOff
