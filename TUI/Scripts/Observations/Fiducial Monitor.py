# fiducialMon.py

import RO.Wdg
import Tkinter
import TUI.Models
from datetime import datetime
import sys,os
import time

#print "---fiducialMon----"

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False

        self.name="fiducialMon"
        print self.name, "--init--"
       # sPath=os.getcwd()
        sPath="/Library/Application Support/STUIAdditions"
        ffid=sPath+"/Scripts/fiducialsCL.wav"
        self.soundFid = RO.Wdg.SoundPlayer(ffid)
      #  self.warning()
        
        sr.master.winfo_toplevel().wm_resizable(True, True)

        height=4;  width=40
    #log1
        self.logWdg1 = RO.Wdg.LogWdg(master=sr.master, width=width, height =height,  
              helpText = "AZ fiducial window",)
        self.logWdg1.grid(row=0, column=0, sticky="news") 
    # log2
        self.logWdg2 = RO.Wdg.LogWdg(master = sr.master, width = width, height = height,
              helpText = "Alt fiducial window",  relief = "sunken", bd = 2,)
        self.logWdg2.grid(row=1, column=0, sticky="news")
    # log3
        self.logWdg3 = RO.Wdg.LogWdg(master = sr.master, width = width, height = height,
            helpText = "Rot fiducial window", relief = "sunken", bd = 2)
        self.logWdg3.grid(row=2, column=0, sticky="news")

        sr.master.rowconfigure(0, weight=1)
        sr.master.rowconfigure(1, weight=1)
        sr.master.rowconfigure(2, weight=1)
        sr.master.columnconfigure(0, weight=1)

        self.mcpModel = TUI.Models.getModel("mcp")
        azFid0=self.crossFidFun(sr,self.mcpModel.azFiducialCrossing)
        altFid0=self.crossFidFun(sr,self.mcpModel.altFiducialCrossing)
        rotFid0=self.crossFidFun(sr,self.mcpModel.rotFiducialCrossing)
        
        self.azMax=sr.getKeyVar(self.mcpModel.msOnMaxCorrection, ind=0, defVal=600)
        self.altMax=sr.getKeyVar(self.mcpModel.msOnMaxCorrection, ind=1, defVal=600)
        self.rotMax=sr.getKeyVar(self.mcpModel.msOnMaxCorrection, ind=2, defVal=600)

    #    self.azMax=2;  self.altMax=2;  self.rotMax=20
        
        self.largeMes=" "*20+"error is too large to be corrected"
        self.blueWarn=RO.Constants.sevWarning
        
        self.logWdg1.addMsg("xx:xx:xx  Az:  %s " % (self.fidSS(azFid0)))
        if abs(azFid0[3])>self.azMax : 
            self.logWdg1.addMsg("%s ( > %s)" % (self.largeMes,str(self.azMax)),severity=self.blueWarn)
            self.warning()
                  
        self.logWdg2.addMsg("xx:xx:xx  Alt:   %s " % (self.fidSS(altFid0)))
        if abs(altFid0[3])>self.altMax : 
           self.logWdg2.addMsg("%s ( > %s)" % (self.largeMes,str(self.altMax)),severity=self.blueWarn)
           self.warning()
                  
        self.logWdg3.addMsg("xx:xx:xx  Rot:  %s " % (self.fidSS(rotFid0)))
        if abs(rotFid0[3])>self.rotMax : 
           self.logWdg3.addMsg("%s ( > %s)" % (self.largeMes,str(self.rotMax)),severity=self.blueWarn)
           self.warning()
                 
        self.mcpModel.azFiducialCrossing.addCallback(self.updateAz, callNow=False)
        self.mcpModel.altFiducialCrossing.addCallback(self.updateAlt, callNow=False)
        self.mcpModel.rotFiducialCrossing.addCallback(self.updateRot, callNow=False)
        
    def getTAITimeStr(self,):
        return time.strftime("%H:%M:%S",
               time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))
    
    def fidSS(self,fid):
        return "ind=%i,  deg=%5.1f,   err= %i" % (fid[0],fid[1],fid[3])

    def crossFidFun(self,sr,keyVar):
        crossFid=[0,0.0,0,0]
        for i in range(0,4):
            crossFid[i]=sr.getKeyVar(keyVar, ind=i, defVal=0)
        return crossFid
  
    def updateAz(self,keyVar):
        if not keyVar.isGenuine: return
        timeStr = self.getTAITimeStr()
        self.logWdg1.addMsg("%s   Az:  %s " % (timeStr, self.fidSS(keyVar)))
        ss="%s   AZ:  %s " % (timeStr, self.fidSS(keyVar))
        print "fiducialMon: ", ss  
        if abs(keyVar[3])>self.azMax :
           self.logWdg1.addMsg("%s ( > %s)" % (self.largeMes,str(self.azMax)),severity=self.blueWarn)
           self.warning()
           ss="Az: %s ( > %s)" % (self.largeMes,str(self.azMax))
           print "fiducialMon: ", ss

    def updateAlt(self,keyVar):
        if not keyVar.isGenuine: return
        timeStr = self.getTAITimeStr()
        self.logWdg2.addMsg("%s   Alt:  %s " % (timeStr, self.fidSS(keyVar)))
        ss="%s   Alt:  %s " % (timeStr, self.fidSS(keyVar))
        print "fiducialMon: ", ss        
        if abs(keyVar[3])>self.altMax :
           self.logWdg2.addMsg("%s ( > %s)" % (self.largeMes,str(self.altMax)),severity=self.blueWarn)
           self.warning()
           ss="Alt: %s ( > %s)" % (self.largeMes,str(self.altMax))
           print "fiducialMon: ", ss

    def updateRot(self,keyVar):
        if not keyVar.isGenuine:  return
        timeStr = self.getTAITimeStr()
        self.logWdg3.addMsg("%s   Rot:  %s " % (timeStr, self.fidSS(keyVar)))
        ss="%s   Rot:  %s " % (timeStr, self.fidSS(keyVar))
        print "fiducialMon: ", ss
        if abs(keyVar[3])>self.rotMax :
           self.logWdg3.addMsg("%s ( > %s)" % (self.largeMes,str(self.rotMax)),severity=self.blueWarn)
           self.warning()
           ss="Rot: %s ( > %s)" % (self.largeMes,str(self.rotMax))
           print "fiducialMon: ", ss
           

    def warning(self,):
       self.soundFid.play()
       pass

    def run(self, sr):
       pass
    
    def end(self, sr):
       pass 
   #    self.mcpModel.azFiducialCrossing.removeCallback(self.updateAz)
   #    self.mcpModel.altFiducialCrossing.removeCallback(self.updateAlt)
   #    self.mcpModel.rotFiducialCrossing.removeCallback(self.updateRot)    
   #     self.logWdg1.addMsg("  stopped")
   #     self.logWdg2.addMsg("  stopped")
   #     self.logWdg3.addMsg("  stopped")
 
