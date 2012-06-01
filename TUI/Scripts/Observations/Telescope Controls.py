# camCommands - wrap and buttons for camera commands
# and for telescope moves
# 09/09/2011  by EM

import RO.Wdg
import TUI.Models
import Tkinter
import time

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.sr = sr
        self.bossModel = TUI.Models.getModel("boss")
                
        ff=("Times", "17", "bold")
        ff1=("Times", "16", "bold")
        ht=2;  padx=6

        F2 = Tkinter.Frame(master=sr.master, )
        F2.grid(row=0, column=0, )        
        self.butAxisInit=RO.Wdg.Button(master=F2, helpText ="tcc axis init",font=ff,height=ht, padx=padx,
            callFunc =self.axisInit, text="axis init").grid(row = 0,column=0)
        self.butGoto6=RO.Wdg.Button(master=F2, helpText ="tcc track 121,6 mount",
            height=ht, padx=padx, font= ff,
            callFunc =self.goto6, text="goto-6").grid(row = 0,column=1)
        self.butStow=RO.Wdg.Button(master=F2, helpText = "tcc track 121,30 mount /rota=0 /rotty=mount",
            height=ht, padx=padx,font= ff,                 
            callFunc =self.stow, text="stow",).grid(row = 0,column=2)
        self.butInstChange=RO.Wdg.Button(master=F2, helpText ="tcc track 121,90 mount /rota=0 /rotty=mount",
            height=ht,padx=padx,font= ff,  
            callFunc =self.instChange, text="instChange",).grid(row = 0,column=3)
        self.butAxisStop=RO.Wdg.Button(master=F2, helpText ="tcc axis stop",height=ht,padx=padx, font=ff,  
            callFunc =self.axisStop, text="axis stop",).grid(row = 0,column=4)

        F0 = Tkinter.Frame(master=sr.master, )
        F0.grid(row=1, column=0, )        
        self.but121_60_0=RO.Wdg.Button(master=F0,
            helpText ="tcc track 121,60 mount /rota=0 /rotty=mount",
            font=ff1,height=ht, padx=padx,
            callFunc =self.fun121_60_0, text="(121,60,0)").grid(row = 0,column=0)        
        self.but60_60_60=RO.Wdg.Button(master=F0,
            helpText ="tcc track 60,60  mount /rota=60 /rotty=mount",
            height=ht, padx=padx, font= ff1,
            callFunc =self.fun60_60_60, text="(60,60,60)").grid(row = 0,column=1)        
        self.butAz_45_Rot=RO.Wdg.Button(master=F0,
            helpText = "tcc track az,45 mount /rota=rot /rotty=mount",
            height=ht, padx=padx,font= ff1,                 
            callFunc =self.funAz_45_Rot, text="(az,45,rot)",).grid(row = 0,column=2)

        F1 = Tkinter.Frame(master=sr.master)
        F1.grid(row=2, column=0,)
        self.butStartfillseq=RO.Wdg.Button(master=F1, helpText ="boss sp[1,2]cam raw=startfillseq",
            height=ht, padx=4,font= ff,
            callFunc =self.startfillseq, text="startfillseq",).grid(row = 0,column=0 )        
    #    self.butStopfillseq=RO.Wdg.Button(master=F1, helpText ="boss sp[1,2]cam raw=stopfillseq",
    #        height=ht, padx=4,font= ff,
    #        callFunc =self.stopfillseq, text="stopfillseq",).grid(row = 0,column=1 )
        self.butSpecstat=RO.Wdg.Button(master=F1, helpText = "boss sp[1,2]cam raw=specstat",
            height=ht, padx=4,font= ff,
            callFunc =self.specstat, text="specstat",).grid(row = 0, column=2)
        self.butLn2stat=RO.Wdg.Button(master=F1, helpText = "boss sp[1,2]cam raw=ln2stat",
            height=ht, padx=4,font= ff,
            callFunc =self.ln2stat, text="ln2stat",).grid(row = 0, column=3)
        self.butTcheck=RO.Wdg.Button(master=F1, helpText = "boss sp[1,2]cam raw=1 tcheck 2 tcheck",
            height=ht, padx=4,font= ff,
            callFunc =self.tcheck, text="tcheck",).grid(row = 0, column=4)
        
        self.logWdg = RO.Wdg.LogWdg(master=sr.master,  width=50, height =5,)
        self.logWdg.grid(row=3, column=0, sticky="news")        
        sr.master.rowconfigure(3, weight=1)
        sr.master.columnconfigure(0, weight=1)

        self.tccModel = TUI.Models.getModel("tcc")

    def axisInit(self,bt):self.run(self.sr, 1)
    def axisStop(self,bt): self.run(self.sr, 2)
    def goto6(self,bt):  self.run(self.sr, 3)
    def stow(self,bt):  self.run(self.sr, 4)
    def instChange(self,bt): self.run(self.sr, 5)
    def specstat(self,bt): self.run(self.sr, 6)
    def startfillseq(self,bt): self.run(self.sr, 7)
 #   def stopfillseq(self,bt): self.run(self.sr, 8)
    def ln2stat(self,bt): self.run(self.sr, 9)
    def tcheck(self,bt): self.run(self.sr, 10)

    def fun121_60_0(self,bt): self.run(self.sr,11)
    def fun60_60_60(self,bt): self.run(self.sr,12)
    def funAz_45_Rot(self,bt): self.run(self.sr,13)
             
    def trackCmd(self,az,alt,rot):
        return "track %s,%s mount /rota=%s /rotty=mount" % (az,alt,rot)

    def getTAITimeStr(self,):
        return time.strftime("%H:%M:%S",
              time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))

    def run(self, sr, sel=0):
      tm=self.getTAITimeStr()
      
      if sel == 0:  self.logWdg.addMsg("%s -- nothing --" % (tm))
      if sel == 1:  # axis init
          act="tcc";  cmd="axis init"
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
          
      if sel == 2:  # axis stop
          act="tcc";  cmd="axis stop"
          self.logWdg.addMsg("%s    %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
          
      if sel == 3:  # goto6
          act="tcc";  cmd="track 121,6 mount";
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
          
      if sel == 4:  # stow
          act="tcc";  cmd="track 121,30 mount /rota=0 /rotty=mount";
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
          
      if sel == 5:  # instChange
          act="tcc";   cmd="track 121,90 mount /rota=0 /rotty=mount";
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
          
      if sel == 6:  # specstat
          #  00:40:19 APO.Craig: boss sp1cam raw=specstat
          #  00:38:33 APO.Craig: specstat gives ln2 temps, ccd temps, and ion pumps.
          ss="specstat";  act="boss";
          cmd1="sp1cam raw= %s " % (ss)
          cmd2="sp2cam raw= %s " % (ss)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd1))
          sr.startCmd(actor=act, cmdStr=cmd1)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd2))
          sr.startCmd(actor=act, cmdStr=cmd2)          

      if sel == 7:  # startfillseq
          #  00:33:44 APO.Craig: boss sp2cam raw=startfillseq
          ss="startfillseq";    act="boss"
          cmd1="sp1cam raw= %s" % (ss)
          cmd2="sp2cam raw= %s" % (ss)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd1))
          sr.startCmd(actor=act, cmdStr=cmd1)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd2))
          sr.startCmd(actor=act, cmdStr=cmd2)
          
  #    if sel == 8:  # stopfillseq
  #        ss="stopfillseq";   act="boss";
  #        cmd1="sp1cam raw= %s" % (ss)
  #        cmd2="sp2cam raw= %s" % (ss)
  #        self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd1))
  #        sr.startCmd(actor=act, cmdStr=cmd1)
  #        self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd2))
  #        sr.startCmd(actor=act, cmdStr=cmd2)

      if sel == 9:  # ln2stat
          ss="ln2stat";  act="boss";
          cmd1="sp1cam raw=%s" % (ss)
          cmd2="sp2cam raw=%s "% (ss)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd1))
          sr.startCmd(actor=act, cmdStr=cmd1)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd2))
          sr.startCmd(actor=act, cmdStr=cmd2)
          
      if sel == 10:  # tcheck
          ss="tcheck";  act="boss"
          cmd1="sp1cam raw=1 %s 2 %s " % (ss,ss)
          cmd2="sp2cam raw=1 %s 2 %s " % (ss,ss)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd1))
          sr.startCmd(actor=act, cmdStr=cmd1)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd2))
          sr.startCmd(actor=act, cmdStr=cmd2)

      if sel == 11:  #  fun121_60_0
          act="tcc";  cmd=self.trackCmd(121,60,0)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
        
      if sel == 12:  #  fun60_60_60
          act="tcc";  cmd=self.trackCmd(60,60,60)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)

      if sel == 13:  #  funAz_45_Rot
          az=self.tccModel.axePos[0]
          alt=self.tccModel.axePos[1]
          rot=self.tccModel.axePos[2]
          act="tcc";  cmd=self.trackCmd(az,45,rot)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)

    def end(self, sr):
         pass
           
