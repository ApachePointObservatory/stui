'''cartchange.py   - it takes two darks for apogee

stui  wrap for cartchange.inp script (11Oct01)
use while the cartridge is being changed'''

'''
History: 
02-21-2013 EM: proceed if gang connector is in podium;  UT time changed to TAI
08-29-2013 EM:  changed mcp.gang descriptions for updated keyword 
02-17-2014 EM: fixed bug: set checkFail= True to halt script is command fail
10-02-2015  Changed enum value for gang position (podium 12)  from int to string, 
                based on recent opscore changes

'''
import RO.Wdg
import TUI.Models
from datetime import datetime
import time
#import RO.Astro.Tm
import subprocess
import tkinter.messagebox as box

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
        self.name="APOGEE Cart Change"    #   self.ver="11Oct01"
        self.logWdg.text.tag_config("a", foreground="magenta")        
        self.logWdg.addMsg('%s \n Two 10-reads darks \n %s' % (self.name,"-"*20))
        
    # 08/29    
    def checkGangPodium(self, sr):   
        self.mcpModel = TUI.Models.getModel("mcp")
        ngang=sr.getKeyVar(self.mcpModel.apogeeGang, ind=0, defVal=0)
        hlp=self.mcpModel.apogeeGangLabelDict.get(ngang, "?")
        self.logWdg.addMsg("mcp.gang=%s  (%s)" % (ngang, hlp))
        if ngang != '12':         
            self.logWdg.addMsg(" Error: mcp.gang must be = 12 (podium dense) \n",    
                  severity=RO.Constants.sevError)
            subprocess.Popen(['say','error']) 
            return False 
        else:
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
#      return  # for debugging

      for actorCmd in [
            "apogeecal allOff",
            "apogee shutter close",
            "apogeecal shutterOpen",
            "apogee expose nreads=10; object=Dark",
            "apogee expose nreads=10; object=Dark",
            "apogeecal shutterClose",
            "apogeecal allOff",          
      ]:
         actor, cmd = actorCmd.split(None, 1)
         self.logWdg.addMsg("%s .... " % (actorCmd,))
         yield sr.waitCmd(actor=actor, cmdStr=cmd, checkFail=True)
         cmdVar = sr.value
         if cmdVar.didFail:      
             self.logWdg.addMsg("   ** FAILED **" % (actorCmd),severity=RO.Constants.sevError)
             raise sr.ScriptError("") 
      self.logWdg.addMsg("-- done --",tags=["a"])  
      self.logWdg.addMsg("")

#apogeecal allOff
#apogee shutter close
#apogeecal shutterOpen
#apogee expose nreads=10 ; object=Dark
#apogee expose nreads=10 ; object=Dark
#apogeecal shutterClose
#apogeecal allOff
