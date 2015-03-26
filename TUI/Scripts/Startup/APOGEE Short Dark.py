
"""
takes short dark to check apogee binding 

History
02-21-2013 EM: proceed if gang connector is in podium;  UT time changed to TAI
08/23/2013 EM: moved to STUI  and changed name to  APOGEE Short Dark.py 
08/29/2013 EM: changed mcp.gang descriptions for updated keyword 
09/05/2013 EM: refinement
09/25/2013  EM:  check gang position, but run at any position. 
01/24/2014  fixed bug,  "apogeecal shutterOpen" changed to  "apogeecal shutterClose",
                    do not know why it was so. 
02-17-2014 EM: fixed bug: set checkFail= True to halt script is command fail
02-21-2014  reverted changes from  01/24/2014 - did not find if it was right or not
03-05-2014  design refinement  
"""

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
        self.name="APOGEE Short Dark"        
        self.logWdg.text.tag_config("a", foreground="DarkOrange")
        self.logWdg.text.tag_config("g", foreground="grey")
        self.logWdg.text.tag_config("n", )
        self.logWdg.text.tag_config("nov", background="lightgreen")

        self.cmdListDark=[
            "apogeecal allOff",
            "apogee shutter close",
            "apogeecal shutterOpen",
            "apogee expose nreads=3 ; object=Dark",
         #   "apogee expose nreads=10 ; object=Dark",
            "apogeecal shutterClose",
            "apogeecal allOff", 
            ]            
        self.cmdListTest=[
            "tcc show time",
            "tcc show time",
            "tcc show time",
            "tcc show time",            
            ]                 

        self.cmdList=self.cmdListDark                        
        self.tagsList=["g"]*len(self.cmdList)
        self.tm=self.getTAITimeStr() 
        self.updateLog()
        
    def updateLog(self, time=False):
        self.logWdg.clearOutput() 
        if time:
            self.tm = self.getTAITimeStr() 
        self.logWdg.addMsg("-- %s - %s" % (self.name, self.tm),  tags=["a"] )
        for ll,tt in zip(self.cmdList,self.tagsList) : 
            self.logWdg.addMsg("%s" % ll,tags=tt)
        
    def getTAITimeStr(self,):
      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
      currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
      self.taiTimeStr = time.strftime("%H:%M:%S", currTAITuple) 
      return self.taiTimeStr

    def run(self, sr):       

      i=0 
      self.tagsList=["g"]*len(self.cmdList)
      self.updateLog(time=True)
      for actorCmd in self.cmdList:
         self.tagsList[i]=["nov"] 
         self.updateLog()
         actor, cmd = actorCmd.split(None, 1)
         yield sr.waitCmd(actor=actor, cmdStr=cmd, checkFail = True,)
         cmdVar = sr.value
         if cmdVar.didFail:
             ss1=" %s   ** FAILED **" % (actorCmd)
             self.logWdg.addMsg("      %s" % (ss1),severity=RO.Constants.sevError)
             break
   #          raise sr.ScriptError("")
         yield sr.waitMS(2*1000) 
         self.tagsList[i]=["n"] 
         self.updateLog()       
         i=i+1 

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
