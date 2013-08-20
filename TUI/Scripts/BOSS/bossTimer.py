# 2013-04-20  EM:  bossTimer.py
# 2013-04-20  EM:  added color and sound 
# 2013-04-22 EM:   added check button on/off sound, default on. 
# 2012-04-24 EM:   added ProgressBar 
# 2012-05-17 EM: cut label text to just "bossTimer"

import RO.Wdg
import TUI.Models
import time
import RO.Astro.Tm
import Tkinter
import TUI.PlaySound

class ScriptClass(object):
    def __init__(self, sr, ):

       sr.master.winfo_toplevel().wm_resizable(True, True)
       self.ft=("Times", "16", "bold") 
  #     self.fg=["black", "ForestGreen","OrangeRed"]
       self.fg=["DarkGrey", "ForestGreen","Brown"]

       
       F1 = Tkinter.Frame(sr.master)
       gr = RO.Wdg.Gridder(F1)
       F1.grid(row=0, column=0, sticky="sn")
       
       self.labWdg = RO.Wdg.Label(master=F1, text ="      ", 
            font=self.ft, fg=self.fg[0])
       self.labWdg.grid(row=0, column=0, sticky="ns")
       self.checkWdg = RO.Wdg.Checkbutton(master=F1, 
            text ="", defValue=True, helpText ="Play sound",)
       self.checkWdg.grid(row=0, column=1, sticky="we")

       self.expTimer = RO.Wdg.ProgressBar(master = sr.master,
          valueFormat = "%5.2f",  label = None,)
       self.expTimer.grid(row=1, column=0, sticky="ew")

       sr.master.rowconfigure(0, weight=1)
       sr.master.rowconfigure(1, weight=1)
       sr.master.columnconfigure(0, weight=1)

       sPath="/Library/Application Support/STUIAdditions"
       ffid=sPath+"/Scripts/Glass.wav"
       self.soundFid = RO.Wdg.SoundPlayer(ffid)

    #   self.expTotal = 80   # 980
    #   self.minAlert = 60./60. # 300./60.

       self.expTotal = 980
       self.minAlert = 300./60.

       self.secEnd=None;  
       self.alert=True
       self.fooTimer = RO.Comm.Generic.Timer()
       self.wait=1
  #     self.fooTimer.start(self.wait, foo) # schedule self again
       self.foo() 

       self.sopModel = TUI.Models.getModel("sop")
       self.nExp0, self.nExp1 =self.sopModel.doScience_nExp[0:2]
       self.sopModel.doScience_nExp.addCallback(self.doScience_nExp,callNow=True)

#----
    def getTAITimeStr(self,):
       self.currPythonSeconds = RO.Astro.Tm.getCurrPySec()
       self.currTAITuple= time.gmtime(self.currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
       self.taiTimeStr = time.strftime("%H:%M:%S", self.currTAITuple) 
       return self.taiTimeStr,self.currPythonSeconds 
#---       
    def doScience_nExp(self, keyVar):
        if keyVar[0] == keyVar[1]:   # end seq
          self.nExp0,self.nExp1 =keyVar[0:2]
          self.secEnd=None
        elif keyVar[0] !=self.nExp0 :   # begin seq, or next exposure
          tai, sec = self.getTAITimeStr()   
          self.nExp0,self.nExp1 =keyVar[0:2]
          self.secEnd=sec+(self.nExp1-self.nExp0)*self.expTotal 
          minleft=(self.nExp1-self.nExp0)*self.expTotal /60.0
        elif  keyVar[1] !=self.nExp1:  # modification in progress
          self.secEnd=self.secEnd+(keyVar[1]-self.nExp1)*self.expTotal  
          self.nExp0,self.nExp1 =keyVar[0:2]
        else: 
          tai, sec = self.getTAITimeStr()   
          self.nExp0,self.nExp1 =keyVar[0:2]
          self.secEnd=sec+(self.nExp1-self.nExp0)*self.expTotal
        newValue=(self.nExp1-self.nExp0)*self.expTotal/60. 
        newMax=self.nExp1*self.expTotal/60.
        self.expTimer.setValue(newValue=newValue, newMin=0, newMax=newMax)  
        self.foo()              
#---            
    def foo(self):
       self.fooTimer.cancel()
       lab=" bossTimer: "
       if self.secEnd == None:  
          self.labWdg.set("%s None   " % (lab))
          self.labWdg.config(fg=self.fg[0])
       else: 
          tai, sec = self.getTAITimeStr()  
          self.minLeft=(self.secEnd-sec)/60.0
          self.labWdg.set("%s %6.2f min   " % (lab,self.minLeft)) 
          if self.minLeft > self.minAlert: 
             fgi=1;  self.alert=True
          elif  0< self.minLeft <= self.minAlert:     
             fgi=2
             if self.alert: 
                self.alert=False
                if self.checkWdg.getBool():  
                    self.soundFid.play(); self.soundFid.play();
          else:  fgi=0
          self.labWdg.config(fg=self.fg[fgi])                   
          self.expTimer.setValue(newValue=self.minLeft)
       self.fooTimer.start(self.wait, self.foo) # schedule self again    
    
    def run(self, sr):
        pass
                
    def end(self, sr): 
       self.fooTimer.cancel()
