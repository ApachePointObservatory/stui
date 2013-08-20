#   APOGEE STUI Script  to wrap for  JH  morningcals ver. from tar file 11Oct01
#       by EM, 10/22/2011 copied on landru, minidru, and telescope laptop
#   takes morning calibration sequence: 
#   3 long darks 
#   3 QTH
#   ThAr and UNe at both dither A and dither B
#   internal flat field


# History
# 02-21-2013 EM: proceed if gang connector is in podium;  
# 02-21-2013 EM: UT time changed to TAI
# 02-21-2013 EM: check time when to run 22-24 h, if other time - ask conformation
# 03-06-2013 EM: fixed bug (sr not found)

import RO.Wdg
import TUI.Models
import time, datetime
import RO.Astro.Tm
import subprocess
import tkMessageBox as box

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
        self.name="apogee: morningcals "
        self.ver="11Oct01"
        self.logWdg.text.tag_config("a", foreground="magenta")
        
        self.logWdg.addMsg('%s, v-%s ' % (self.name,self.ver))
        self.logWdg.addMsg("   %s " % ("  3 60-reads darks"))
        self.logWdg.addMsg("   %s " % ("  3 QuartzFlats"))
        self.logWdg.addMsg("   %s " % ("  ThAr and UNe at both dither A and dither B"))
        self.logWdg.addMsg("   %s " % ("  1 30-reads darks"))       
        self.logWdg.addMsg("   %s " % ("  3 Internal flats"))
        self.logWdg.addMsg("   %s " % ("  1 30-reads darks"))
        self.logWdg.addMsg("-"*20)

    def getTAITimeStr(self,):
        currPythonSeconds = RO.Astro.Tm.getCurrPySec()
        self.currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
        self.taiTimeStr = time.strftime("%H:%M:%S", self.currTAITuple) 
        self.taiDateStr = time.strftime("%Y-%m-%d", self.currTAITuple) 
        return self.taiTimeStr,  self.taiDateStr,self.currTAITuple
    
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

    #v1           
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
      tm=self.getTAITimeStr()[0]
      self.logWdg.addMsg('--%s  %s' % (tm,self.name), tags=["a"])                                  
                     
      if not self.checkGangPodium(sr):
           raise sr.ScriptError("")        
                   
      h1= 8; h2=12; mes1="MORNING cals"
      if not self.checkTime(h1,h2,mes1):
          return 
                                            
      for actorCmd in [
        # "tcc show time"
          "apogeecal allOff",
          "apogee shutter close",
          "apogee expose nreads=60 ; object=Dark",
          "apogee expose nreads=60 ; object=Dark",
          "apogee expose nreads=60 ; object=Dark",
          "apogee shutter open",
          "apogeecal shutterOpen",
          "apogeecal SourceOn source=Quartz",
          "apogee expose nreads=10 ; object=QuartzFlat",
          "apogee expose nreads=10 ; object=QuartzFlat",
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
          "apogee expose nreads=30 ; object=Dark",
          "apogee shutter ledControl=15",
          "apogee expose nreads=30 ; object=InternalFlat",
          "apogee expose nreads=30 ; object=InternalFlat",
          "apogee expose nreads=30 ; object=InternalFlat",
          "apogee shutter ledControl=0",
          "apogee expose nreads=30 ; object=Dark",
          "apogee shutter close"
      ]:
         actor, cmd = actorCmd.split(None, 1)
         self.logWdg.addMsg("%s .... " % (actorCmd,))
         yield sr.waitCmd(actor=actor, cmdStr=cmd, checkFail = False,)
         cmdVar = sr.value
         if cmdVar.didFail:
             self.logWdg.addMsg("   ** FAILED **" % (actorCmd),severity=RO.Constants.sevError)

      self.logWdg.addMsg("-- done --")
      self.logWdg.addMsg("")
