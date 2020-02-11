'''
STUI wrap for APOGEE dither_clearing_script.txt

John Wilson requested to run 'dither clearing script' for
the apogee dither mechanism once per month by the observers
during dark time.  We think this clearing helps to distribute solid
lubricant more uniformly along the mechanism's fine pitched lead screw.
..
The script, 'dither_clearing_script.txt', can be found in the
attachments at the bottom of
https://trac.sdss3.org/wiki/APOGEE/Observing   It moves the mechanism
back and forth by up to +/- 4 pixels of its nominal position.  It leaves
the mechanism in the 'A' position when complete.
..
https://trac.sdss3.org/wiki/APOGEE/Observing/dither_clearing_script.txt 

03/04/2014 by EM, initial wrap of that script to STUI 

'''

import RO.Wdg
import TUI.Models
from datetime import datetime
import time
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
        self.name="dither_clearing_script"        
        self.logWdg.text.tag_config("a", foreground="magenta")
        self.logWdg.text.tag_config("g", foreground="grey")
        self.cmdListTest=[
            "apogeecal allOff",
            "apogee shutter close",
            "apogeecal shutterOpen",
            "apogee expose nreads=3 ; object=Dark",
            "apogeecal shutterClose",
            "apogeecal allOff", ]        
        self.cmdList=[
            "apogeecal allOff",                                   
            "apogee shutter open",
            "apogeecal shutterOpen",
            "apogeecal SourceOn source=ThAr",
            "apogee dither namedpos=A",
            "apogee expose nreads=10; object=ArcLamp",
            "apogee dither pixelpos=11.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=13.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=15.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=13.0",
            "apogee expose nreads=10; object=ArcLamp",
            "apogee dither pixelpos=9.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=13.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=17.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=13.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=10.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=13.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=15.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=13.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=12.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither pixelpos=13.0",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither init",
            "apogee dither namedpos=B",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogee dither namedpos=A",
            "apogee expose nreads=10;  object=ArcLamp",
            "apogeecal SourceOff source=ThAr",
            "apogeecal shutterClose",
            "apogeecal allOff",
            "apogee shutter close",]
        
        self.cmdListWork=self.cmdList
        
        self.logWdg.addMsg("-- %s -" % (self.name),  tags=["a"] )
        for ll in self.cmdListWork: 
            self.logWdg.addMsg("%s" % ll,tags=["g"] )
     
    def getTAITimeStr(self,):
      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
      currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
      self.taiTimeStr = time.strftime("%H:%M:%S", currTAITuple) 
      return self.taiTimeStr
            
    def run(self, sr):       
      self.logWdg.clearOutput() 
      tm = self.getTAITimeStr()[0]      
      self.logWdg.addMsg("-- %s -- %s " % (self.name, tm),tags=["a"])  
               
      for actorCmd in self.cmdListWork:
         actor, cmd = actorCmd.split(None, 1)
         self.logWdg.addMsg("%s" % (actorCmd)) 
         yield sr.waitCmd(actor=actor, cmdStr=cmd, checkFail = True,)
         cmdVar = sr.value
         if cmdVar.didFail:
             ss1=" %s   ** FAILED **" % (actorCmd)
             self.logWdg.addMsg("      %s" % (ss1),severity=RO.Constants.sevError)
             break

      self.logWdg.addMsg("-- done --",tags=["a"])  
      self.logWdg.addMsg("")
        