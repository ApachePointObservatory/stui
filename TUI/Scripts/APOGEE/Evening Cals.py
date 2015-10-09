'''
eveningcals: takes evening calibration sequence: 
#   1 long darks 
#   1 QTH
#   ThAr and UNe at both dither A and dither B
#   1 long darks 
#  10/1/2011

History
02-21-2013 EM: proceed if gang connector is in podium;  
02-21-2013 EM: UT time changed to TAI
02-21-2013 EM: check time when to run 22-24 h, if other time - ask conformation
08/29/2013 EM: changed mcp.gang descriptions for updated keyword 

02-17-2014 EM: fixed bug: checkFail was False, and I change to True, to halt script 
                is command fault
10-02-2015  Changed enum value for gang position (podium 12)  from int to string, 
               based on recent opscore changes
               
'''



import RO.Wdg
import TUI.Models
import time, datetime
import RO.Astro.Tm
import subprocess
import tkMessageBox as box
import subprocess

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False
        self.sr=sr
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.logWdg = RO.Wdg.LogWdg(master=sr.master, width=35, height =20,)
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.redWarn=RO.Constants.sevError
        self.name="APOGEE: Evening Cals"
        self.ver="11Oct01"
        self.logWdg.text.tag_config("a", foreground="magenta")
    
        self.logWdg.addMsg('%s, v-%s ' % (self.name,self.ver))
        self.logWdg.addMsg("   %s " % ("  60-reads dark"))
        self.logWdg.addMsg("   %s " % ("  QuartzFlat"))
        self.logWdg.addMsg("   %s " % ("  ThAr and UNe at both dither A and dither B"))
        self.logWdg.addMsg("   %s " % ("  60-reads dark"))
        self.logWdg.addMsg("-"*20)
                                         
    def getTAITimeStr(self,):
      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
      self.currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
      self.taiTimeStr = time.strftime("%H:%M:%S", self.currTAITuple) 
      self.taiDateStr = time.strftime("%Y-%m-%d", self.currTAITuple) 
      return self.taiTimeStr,  self.taiDateStr,self.currTAITuple

    # 08/29    
    def checkGangPodium(self, sr):   
        self.mcpModel = TUI.Models.getModel("mcp")
        ngang=sr.getKeyVar(self.mcpModel.apogeeGang, ind=0, defVal=0)
        hlp=self.mcpModel.apogeeGangLabelDict.get(ngang, "?")
        self.logWdg.addMsg("mcp.gang=%s  (%s)" % (ngang, hlp))
        if ngang != '12':         
          self.logWdg.addMsg(" Error: mcp.gang must be = 12 (podium dense)",    
                  severity=RO.Constants.sevError)
          subprocess.Popen(['say','gang error'])       
          return False 
        else:
          return True
 
    def checkTime(self,h1,h2, mes1):
        sr=self.sr
        tai, date, currTAITuple= self.getTAITimeStr()
        mes2="TAI = %s (expect %2i:00-%2i:00)" % (tai,h1,h2)
        timeNow = datetime.datetime.utcnow() 
        def todayAt (timeNow, hr, min=0, sec=0, micros=0):
           if hr == 24:  hr=23; min=59; sec=59;     
           return timeNow.replace(hour=hr, minute=min, second=sec, microsecond=micros)              
        q1 = todayAt(timeNow,h1) <=timeNow <= todayAt(timeNow,h2)
        if  q1: 
            self.logWdg.addMsg("%s - ok " % (mes2))   
            ask=True   
        else:  
            self.logWdg.addMsg("%s" % (mes2))       
            mes4="  Time WARNING:  start anyway?  "
            self.logWdg.addMsg("%s" % (mes4), severity=self.redWarn)   
            subprocess.Popen(['say'," time warning"])
            df='no'; ss="%s\n\n %s\n\n %s" % (mes1,mes2,mes4)
            ask=box.askyesno(mes1, ss, default=df,icon="warning")
            if ask==False: 
                self.logWdg.addMsg(" -- canceled")
                subprocess.Popen(['say',"canceled"]) 
                self.logWdg.addMsg("  ") 
                raise sr.ScriptError("canceled") 
            else: 
                self.logWdg.addMsg(" -- started")
                subprocess.Popen(['say',"started"])     
        return ask 
        
    def run(self, sr):       
      tm = self.getTAITimeStr()[0]      
      self.logWdg.addMsg("-- %s -- %s " % (tm,self.name),tags=["a"])  
 
      if not self.checkGangPodium(sr):
           raise sr.ScriptError("") 
    
      h1=22; h2=24; mes1="EVENING cals"    
      if not self.checkTime(h1,h2,mes1):
          return 
      subprocess.Popen(['say',"apogee Cals started"])
          
      for actorCmd in [
          "apogeecal allOff",
          "apogee shutter close",
          "apogee expose nreads=60 ; object=Dark",
          "apogee shutter open",
          "apogeecal shutterOpen",
          "apogeecal SourceOn source=Quartz",
          "apogee expose nreads=10 ; object=QuartzFlat",
          "apogeecal SourceOff source=Quartz",
          "apogee dither namedpos=A",
          "apogeecal SourceOn source=ThAr",
          "apogee expose nreads=12 ; object=ArcLamp",
          "apogeecal SourceOff source=ThAr",
          "apogeecal SourceOn source=UNe",
          "apogee expose nreads=40 ; object=ArcLamp",
          "apogeecal SourceOff source=UNe",
          "apogee dither namedpos=B",
          "apogeecal SourceOn source=ThAr",
          "apogee expose nreads=12 ; object=ArcLamp",
          "apogeecal SourceOff source=ThAr",
          "apogeecal SourceOn source=UNe",
          "apogee expose nreads=40 ; object=ArcLamp",
          "apogeecal SourceOff source=UNe",
          "apogee dither namedpos=A",
          "apogeecal shutterClose",
          "apogeecal allOff",
          "apogee shutter close",
          "apogee expose nreads=60 ; object=Dark",
      ]:
         actor, cmd = actorCmd.split(None, 1)
         self.logWdg.addMsg("%s .... " % (actorCmd,))
         yield sr.waitCmd(actor=actor, cmdStr=cmd, checkFail = True,)
         cmdVar = sr.value
         if cmdVar.didFail:
             self.logWdg.addMsg("   ** FAILED **" % (actorCmd),severity=RO.Constants.sevError)
             raise sr.ScriptError("")

      tm = self.getTAITimeStr()[0]  
      self.logWdg.addMsg("-- %s-- done --" % (tm) ,tags=["a"])  
      subprocess.Popen(['say',"apogee Cals finished"])

      self.logWdg.addMsg("")


#    def getTAITimeStr(self,):
#      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
#      self.currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
#      self.taiTimeStr = time.strftime("%H:%M:%S", self.currTAITuple) 
#      self.taiDateStr = time.strftime("%Y-%m-%d", self.currTAITuple) 
#      return self.taiTimeStr,  self.taiDateStr,self.currTAITuple

#  call:  tai, date, currTAITuple= self.getTAITimeStr()
