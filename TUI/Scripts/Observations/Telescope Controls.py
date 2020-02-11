''' 
# Created on 09/09/2011  by EM
#     telControls - buttons to call boss camera commands
#     and tcc track commands 
#  History:
# 10/09/2012  by EM
#      commented goto-6;  adjusted button sizes;  
#      adjusted design to new RO rules
#      does not allow to move to (60,60,60) if enclosure closed
# 11/05/2014 by EM,  
#   1) replaced tcc commands with sop commands, ticket 2173
#   2) replaced obsolet goto6 button and command with guider loadCartridge command
03/26/2015  EM: removed all output to stui error log; 
     replace tcc moves with sop moves for sop gotoStow60 and  sop gotoAll60
01/25/2016 GF:  added button to show memory
'''

import RO.Wdg
import TUI.Models
import tkinter
import time, os

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False
        sr.master.winfo_toplevel().wm_resizable(True, True)
        
        self.sr = sr
        self.name="telControls"
        
        self.bossModel = TUI.Models.getModel("boss")
        self.tccModel = TUI.Models.getModel("tcc")
        self.apoModel = TUI.Models.getModel("apo")
        self.mcpModel = TUI.Models.getModel("mcp")
                        
        ff=("Times", "17", "bold")
        ff1=("Times", "16","bold")  
        padx=6  # smaller padx does not work ? 
        pady=7   #6

        F2 = tkinter.Frame(master=sr.master, )
        F2.grid(row=0, column=0, )        
        self.butAxisInit=RO.Wdg.Button(master=F2, helpText ="tcc axis init",
            font=ff,  pady=pady, padx=padx, 
            callFunc =self.axisInit, text="axis init").grid(row = 0,column=0)                        
        self.butLoadCart=RO.Wdg.Button(master=F2, helpText ="guider loadCartridge",
            font=ff,  pady=pady, padx=padx, 
            # state="disabled",
            callFunc =self.loadCart, text="load_cart").grid(row = 0,column=1)
        self.butStow=RO.Wdg.Button(master=F2, helpText = "sop gotoStow",
            font=ff,  pady=pady, padx=padx, 
            callFunc =self.stow, text="stow",).grid(row = 0,column=2)
        self.butInstChange=RO.Wdg.Button(master=F2, helpText ="sop gotoInstrumentChange", 
            font=ff,  pady=pady,  padx=padx, 
            callFunc =self.instChange, text="instChange",).grid(row = 0,column=3)
        self.butAxisStop=RO.Wdg.Button(master=F2, helpText ="tcc axis stop",
            font=ff,  pady=pady,   padx=padx, 
            callFunc =self.axisStop, text="axis stop",).grid(row = 0,column=4)

        F0 = tkinter.Frame(master=sr.master, )
        F0.grid(row=1, column=0, )        
        self.but121_60_0=RO.Wdg.Button(master=F0,
            helpText ="sop gotoStow60",
            font=ff1,  pady=pady,   padx=padx, 
            callFunc =self.fun121_60_0, text="(121,60,0)").grid(row = 0,column=0)        
        self.but60_60_60=RO.Wdg.Button(master=F0,
            helpText =" sop gotoAll60",
            font=ff1,  pady=pady,  padx=padx, 
            callFunc =self.fun60_60_60, text="(60,60,60)").grid(row = 0,column=1)        
        self.butAz_45_Rot=RO.Wdg.Button(master=F0,
            helpText = "tcc track az,45 mount /rota=rot /rotty=mount",
            font=ff1,  pady=pady,  padx=padx, 
            callFunc =self.funAz_45_Rot, text="(az,45,rot)",).grid(row = 0,column=2)
        self.butSTUIMemCheck=RO.Wdg.Button(master=F0,
    		helpText ="STUI Memory comsumption check",
    		font=ff1,  pady=pady,   padx=padx, 
    		callFunc =self.STUIMemCheck, 
    		text="STUI Memory").grid(row = 0,column=3,sticky="e")

        F1 = tkinter.Frame(master=sr.master)
        F1.grid(row=2, column=0,)
        self.butStartfillseq=RO.Wdg.Button(master=F1, 
            helpText ="boss sp[1,2]cam raw=startfillseq",
            font=ff,  pady=pady,   padx=padx,
            callFunc =self.startfillseq, text="startfillseq",).grid(row = 0,column=0 )        
        self.butSpecstat=RO.Wdg.Button(master=F1, 
            helpText = "boss sp[1,2]cam raw=specstat",
            font=ff,  pady=pady,  padx=padx,
            callFunc =self.specstat, text="specstat",).grid(row = 0, column=2)
        self.butLn2stat=RO.Wdg.Button(master=F1, 
            helpText = "boss sp[1,2]cam raw=ln2stat",
            font=ff,  pady=pady,  padx=padx,
            callFunc =self.ln2stat, text="ln2stat",).grid(row = 0, column=3)
        self.butTcheck=RO.Wdg.Button(master=F1, 
            helpText = "boss sp[1,2]cam raw=1 tcheck 2 tcheck",
            font=ff,  pady=pady,   padx=padx,
            callFunc =self.tcheck, text="tcheck",).grid(row = 0, column=4)
        
        self.logWdg = RO.Wdg.LogWdg(master=sr.master,  width=40, height =5,)
        self.logWdg.grid(row=3, column=0, sticky="news")        
        sr.master.rowconfigure(3, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.logWdg.text.tag_config("v", foreground="darkviolet")
        
        self.semOwn="n/a"
        self.mcpModel.semaphoreOwner.addCallback(self.updateSemOwn1,callNow=False)

    def updateSemOwn1(self, keyVar): 
        if not keyVar.isGenuine: return
        if keyVar[0] != self.semOwn:
            self.semOwn=keyVar[0]            
            ss="%s  mcp.semOwner = %s" % (self.getTAITimeStr(), self.semOwn)
            self.logWdg.addMsg("%s" % (ss),tags="v")
            
    def axisInit(self,bt):self.run(self.sr, 1)
    def axisStop(self,bt): self.run(self.sr, 2)
    def loadCart(self,bt):  self.run(self.sr, 3)
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
    def STUIMemCheck(self,bt): self.run(self.sr,14)
                 
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
          
      if sel == 3:  # loadCart
          act="guider";  cmd="loadCartridge";
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
          
      if sel == 4:  # stow
          #see ticket 2173
          act="sop";  cmd="gotoStow"
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
          
      if sel == 5:  # instChange
          #see ticket 2173
          act="sop";   cmd="gotoInstrumentChange";   
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
          #see ticket 2173
          act="sop";  cmd="gotoStow60"
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
        
      if sel == 12:  #  fun60_60_60
          # encl=sr.getKeyVar(self.apoModel.encl25m, ind=0, defVal=Exception)
          encl=sr.getKeyVar(self.apoModel.encl25m, ind=0, defVal=None)
          if encl > 0 :
             act="sop";  cmd="gotoAll60"             
             self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
             sr.startCmd(actor=act, cmdStr=cmd)
          else:
             self.logWdg.addMsg("%s cannot move to (60,60,60) inside enclosure" % (tm))  

      if sel == 13:  #  funAz_45_Rot
          az=self.tccModel.axePos[0]
          alt=self.tccModel.axePos[1]
          rot=self.tccModel.axePos[2]
          act="tcc";  cmd=self.trackCmd(az,45,rot)
          self.logWdg.addMsg("%s   %s %s" % (tm, act, cmd))
          sr.startCmd(actor=act, cmdStr=cmd)
          
      if sel == 14: # STUI Memory Check
      	  pid=os.getpid()           
          sz="rss"
          mem=int(os.popen('ps -p %d -o %s | tail -1' % (pid, sz)).read())
          ss2="memory = %s MB" %  (mem/1000)
          self.logWdg.addMsg("%s %s" % (tm,ss2))      

    def end(self, sr):
         pass