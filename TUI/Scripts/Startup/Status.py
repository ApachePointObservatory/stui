import RO.Wdg
import TUI.Models
import string
from datetime import datetime

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode 
        # if False, real time run
        sr.debug = False
        self.logWdg = RO.Wdg.LogWdg(
            master=sr.master,
            width=40, 
            height =35,
        )
        self.logWdg.grid(row=0, column=0, sticky="news")
        self.blueWarn=RO.Constants.sevWarning
        self.redWarn=RO.Constants.sevError
        
    def run(self,sr):
      print "-----status---"  
      mcpModel = TUI.Models.getModel("mcp")
      guiderModel = TUI.Models.getModel("guider")
      bossModel = TUI.Models.getModel("boss")
      tccModel = TUI.Models.getModel("tcc")
      gcameraModel = TUI.Models.getModel("gcamera")
      apoModel = TUI.Models.getModel("apo")

     # self.logWdg.addMsg("-----Status --------- ")
      self.logWdg.addMsg("-- Status --  %s  " % (str(datetime.utcnow())))
      self.logWdg.addMsg(" ")

      yield sr.waitCmd(actor="apo", cmdStr="status",
                 keyVars=[apoModel.encl25m], checkFail=False)
      if sr.value.didFail: encl=-1
      else: encl=sr.value.getLastKeyVarData(apoModel.encl25m)[0]          
      if encl > 0: enclM="open"
      elif encl == 0: enclM="closed"
      else : enclM="unknown"
      self.logWdg.addMsg("Enclosure is %s; " % (enclM))

  #    self.logWdg.addMsg(" ") 
      mcpW=[0,0,0,0]
      for i in range(0,4):
           mcpW[i]=sr.getKeyVar(mcpModel.cwPositions, ind=i)          
      mcpWs=str(mcpW[0])+","+str(mcpW[1])+","+str(mcpW[2])+","+str(mcpW[3])
      self.logWdg.addMsg("cwPositions =  %s  %s  %s  %s;  " %
          (str(mcpW[0]),str(mcpW[1]),str(mcpW[2]),str(mcpW[3])))

      mcpInst = sr.getKeyVar(mcpModel.instrumentNum, ind=0)
      self.logWdg.addMsg("MCP instr %s  (mounted);  "  % (str(mcpInst)))

      ctLoad=guiderModel.cartridgeLoaded
      gc = sr.getKeyVar(ctLoad, ind=0)
      gp = sr.getKeyVar(ctLoad, ind=1)
      gs = sr.getKeyVar(ctLoad, ind=2)
      ss="Guider cart= %s,   pl= %s,  side= %s (loaded)"  % (str(gc),str(gp),str(gs))
      if mcpInst != gc:  self.logWdg.addMsg("%s;  " % (ss), severity=self.redWarn)
      else: self.logWdg.addMsg("%s;  " % (ss), severity=0 )

      self.logWdg.addMsg(" ") 
      motPos=[0,0,0,0,0,0]
      for i in range(0,6):
         motPos[i]=sr.getKeyVar(bossModel.motorPosition, ind=i)          
      self.logWdg.addMsg("motorPosition") 
      self.logWdg.addMsg("   sp1:  %6i,  %6i,  %6i;  " % (motPos[0],motPos[1],motPos[2]))
      self.logWdg.addMsg("   sp2:  %6i,  %6i,  %6i;  " % (motPos[3],motPos[4],motPos[5]))

      self.logWdg.addMsg(" ") 
      yield sr.waitCmd(actor="boss", cmdStr="status",
                 keyVars=[bossModel.sp1Temp,bossModel.sp2Temp], checkFail=False)
      if sr.value.didFail:
          sp1T="failed"; sp2T="failed"
      else:    
         sp1T=sr.value.getLastKeyVarData(bossModel.sp1Temp)[0]
         sp2T=sr.value.getLastKeyVarData(bossModel.sp2Temp)[0]
      self.logWdg.addMsg("Median spectrographs temperatures:")
      self.logWdg.addMsg("   Tsp1= %s,  Tsp2= %s;  " % (str(sp1T),str(sp2T)))
      airT=sr.getKeyVar(tccModel.airTemp, ind=0)     
      self.logWdg.addMsg("Outside air temperature= %s;  " % (str(airT)))
      
    #  primT=sr.getKeyVar(tccModel.primF_BFTemp, ind=0)
    #  secT=sr.getKeyVar(tccModel.secF_BFTemp, ind=0)     
    #  self.logWdg.addMsg("Temp prim="+str(primT)+"C   sec="+str(secT)+"C")
    
      self.logWdg.addMsg(" ")
      bossModel = TUI.Models.getModel("boss")
      sp1r0N=sr.getKeyVar(bossModel.SP1R0CCDTempNom, ind=0, defVal=0)
      sp1b2N=sr.getKeyVar(bossModel.SP1B2CCDTempNom, ind=0)
      sp2r0N=sr.getKeyVar(bossModel.SP2R0CCDTempNom, ind=0)
      sp2b2N=sr.getKeyVar(bossModel.SP2B2CCDTempNom, ind=0)
      sp1r0=sr.getKeyVar(bossModel.SP1R0CCDTempRead, ind=0, defVal=0)
         
      sp1b2=sr.getKeyVar(bossModel.SP1B2CCDTempRead, ind=0)
      sp2r0=sr.getKeyVar(bossModel.SP2R0CCDTempRead, ind=0)
      sp2b2=sr.getKeyVar(bossModel.SP2B2CCDTempRead, ind=0)
      def sevf(rr,nom,vv):
          if abs(rr-nom)>vv: sev=self.redWarn
          else: sev=0
          return sev      
      self.logWdg.addMsg("Boss CCD Temp :")
      self.logWdg.addMsg("    sp1r0= %6.1f (%6.1f);  " % (sp1r0, sp1r0N), severity=sevf(sp1r0, sp1r0N,5))
      self.logWdg.addMsg("    sp1b2= %6.1f (%6.1f);  " % (sp1b2, sp1b2N), severity=sevf(sp1b2, sp1b2N,5))
      self.logWdg.addMsg("    sp2r0= %6.1f (%6.1f);  " % (sp2r0, sp2r0N), severity=sevf(sp2r0, sp2r0N,5))
      self.logWdg.addMsg("    sp2b2= %6.1f (%6.1f);  " % (sp2b2, sp2b2N), severity=sevf(sp2b2, sp2b2N,5))

      self.logWdg.addMsg(" ")
      SP1SecDewPress=sr.getKeyVar(bossModel.SP1SecondaryDewarPress, ind=0)
      SP2SecDewPress=sr.getKeyVar(bossModel.SP2SecondaryDewarPress, ind=0)
      self.logWdg.addMsg("sp1LN2: %4.1f;  " % (SP1SecDewPress),severity=sevf(SP1SecDewPress,10,5))
      self.logWdg.addMsg("sp2LN2: %4.1f;  " % (SP2SecDewPress), severity=sevf(SP1SecDewPress,10,5))
   
      self.logWdg.addMsg(" ")
   #   gcamTempN=sr.getKeyVar(gcameraModel.cooler, ind=0)
      gcamTempN=-40.0 
      gcamTemp=sr.getKeyVar(gcameraModel.cooler, ind=1)
      self.logWdg.addMsg("gcameraTemp= %5.1f (%5.1f);  " % (gcamTemp, gcamTempN),
                severity=sevf(gcamTemp,gcamTempN,3))
      
#      self.logWdg.addMsg(" ") 
      secFoc=sr.getKeyVar(tccModel.secFocus, ind=0)
      self.logWdg.addMsg("Rel. Focus =  %s;  " % (str(secFoc)))

#      self.logWdg.addMsg(" ") 
      ra=sr.getKeyVar(tccModel.objArcOff, ind=0)
      dec=sr.getKeyVar(tccModel.objArcOff, ind=1)
      def offStr (off):
          off1=str(off)   
          off1=string.replace(off1,"PVT","")
          off1=string.replace(off1,"(","")
          off1=string.replace(off1,")","")
          off2,off3=off1.split(None,1)
          off2=string.replace(off2,",","")
          return off2
      self.logWdg.addMsg("objArcOff = %s,  %s;  " % (offStr(ra),offStr(dec)))

      def sevLevL(rr,lev1,lev2):
          if rr < lev2: sev=self.redWarn
          elif lev2 < rr <lev1: sev=self.blueWarn
          elif rr>lev1: sev=0
          else: pass
          return sev

      def sevLevU(rr,lev1,lev2):
          if rr > lev2: sev=self.redWarn
          elif lev1 < rr <lev2: sev=self.blueWarn
          elif rr<lev1: sev=0
          else: pass
          return sev
          
      self.logWdg.addMsg(" ") 
      humidPT=sr.getKeyVar(apoModel.humidPT, ind=0)
      self.logWdg.addMsg("humid25m =  %s;  " % (str(humidPT)), severity=sevLevU(humidPT,75,85))
      airTempPT=sr.getKeyVar(apoModel.airTempPT, ind=0)
      dpTempPT=sr.getKeyVar(apoModel.dpTempPT, ind=0)
      diff=airTempPT-dpTempPT 
      self.logWdg.addMsg("airTemp25m =  %sC,  dpTemp25m =  %sC;  " % (str(airTempPT), str(dpTempPT)))
      self.logWdg.addMsg("      diff= %sC;  " % (str(diff)),severity=sevLevL(diff,5.0,2.5))

      if encl > 0:
          dir25m=sr.getKeyVar(apoModel.windd25m, ind=0, defVal="fail")
          wind25m=sr.getKeyVar(apoModel.winds25m, ind=0, defVal="fail")         
          ww=str(wind25m); dd=str(dir25m)
          self.logWdg.addMsg("wind25m = %s mph,  direction = %s;  " %  (str(wind25m),str(dir25m)),
                           severity=sevLevU(wind25m,30,35))
      else:
          self.logWdg.addMsg("wind25m = n/a,  direction = n/a;  " )
          
      self.logWdg.addMsg("---------------------------") 


#      yield sr.waitCmd(actor="boss", cmdStr="status",
#                 keyVars=[bossModel.sp1Temp,bossModel.sp2Temp], checkFail=False)
#      if sr.value.didFail:
#          sp1T="failed"; sp2T="failed"
#      else:    
#         sp1T=sr.value.getLastKeyVarData(bossModel.sp1Temp)[0]
#         sp2T=sr.value.getLastKeyVarData(bossModel.sp2Temp)[0]
