#04/24/2012;  EM:  added apogee vacuum, and ln2level; 
# change font for title;   
# added stui memory use, and mcp.semOwner  10/25/2012 

import RO.Wdg
import TUI.Models
import string, os, time
#from datetime import datetime

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode 
        # if False, real time run
        sr.debug = False
        self.name="Status"
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.logWdg = RO.Wdg.LogWdg(
            master=sr.master,
            width=40, 
            height =35,
        )
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
        
        self.blueWarn=RO.Constants.sevWarning
        self.redWarn=RO.Constants.sevError
        self.apogeeModel = TUI.Models.getModel("apogee")
        
    def getTAITimeStr(self,):
        return time.strftime("%H:%M:%S",
           time.gmtime(time.time() - RO.Astro.Tm.getUTCMinusTAI()))
        
    def run(self,sr):
      defstr='n/a'; defval=0

      ff=("Times", "17", "bold italic")
      fs="12"   # font size
      ft="Monaco" # "Courier"  #"Menlo"  # font type
      self.logWdg.text.tag_config("cur", font=(ft,fs,"bold"))
      
      mcpModel = TUI.Models.getModel("mcp")
      guiderModel = TUI.Models.getModel("guider")
      bossModel = TUI.Models.getModel("boss")
      tccModel = TUI.Models.getModel("tcc")
      gcameraModel = TUI.Models.getModel("gcamera")
      apoModel = TUI.Models.getModel("apo")

      tm = self.getTAITimeStr()
      self.logWdg.addMsg("-- Status  --  %s ---- " % (tm,), tags=["cur"])

      yield sr.waitCmd(actor="apo", cmdStr="status",
                 keyVars=[apoModel.encl25m], checkFail=False)
      if sr.value.didFail: encl=-1
      else: encl=sr.value.getLastKeyVarData(apoModel.encl25m)[0]          
      if encl > 0: enclM="open"
      elif encl == 0: enclM="closed"
      else : enclM="n/a"
      self.logWdg.addMsg("Enclosure = %s; " % (enclM))

 
      mcpW=[0,0,0,0]
      for i in range(0,4):
           mcpW[i]=sr.getKeyVar(mcpModel.cwPositions, ind=i, defVal='n/a')          
      mcpWs=str(mcpW[0])+","+str(mcpW[1])+","+str(mcpW[2])+","+str(mcpW[3])
      self.logWdg.addMsg("cwPositions =  %s  %s  %s  %s;  " %
          (str(mcpW[0]),str(mcpW[1]),str(mcpW[2]),str(mcpW[3])))

      mcpInst = sr.getKeyVar(mcpModel.instrumentNum, ind=0, defVal='n/a')
      self.logWdg.addMsg("MCP instr =  %s  (mounted);  "  % (str(mcpInst)))

      ctLoad=guiderModel.cartridgeLoaded
      gc = sr.getKeyVar(ctLoad, ind=0, defVal='n/a')
      gp = sr.getKeyVar(ctLoad, ind=1, defVal='n/a')
      gs = sr.getKeyVar(ctLoad, ind=2, defVal='n/a')
      ss="Guider cart= %s,  plate= %s,  side= %s (loaded)"  % (str(gc),str(gp),str(gs))
      if mcpInst != gc:  self.logWdg.addMsg("%s;  " % (ss), severity=self.redWarn)
      else: self.logWdg.addMsg("%s;  " % (ss), severity=0 )
      self.logWdg.addMsg("%s" % ('-'*30))

      motPos=[0,0,0,0,0,0]
      for i in range(0,6):
         motPos[i]=sr.getKeyVar(bossModel.motorPosition, ind=i, defVal=0)          
      self.logWdg.addMsg("motorPosition") 
      self.logWdg.addMsg("%s sp1:  %6i,  %6i,  %6i;  " % (" "*4, motPos[0],motPos[1],motPos[2]))
      self.logWdg.addMsg("%s sp2:  %6i,  %6i,  %6i;  " % (" "*4,motPos[3],motPos[4],motPos[5]))
      self.logWdg.addMsg("%s" % ('-'*30))

      yield sr.waitCmd(actor="boss", cmdStr="status",
                 keyVars=[bossModel.sp1Temp,bossModel.sp2Temp], checkFail=False)
      if sr.value.didFail:
          sp1T="n/a"; sp2T="n/a"
      else:    
         sp1T=sr.value.getLastKeyVarData(bossModel.sp1Temp)[0]
         sp2T=sr.value.getLastKeyVarData(bossModel.sp2Temp)[0]
      self.logWdg.addMsg("Median spectrographs temperatures:")
      self.logWdg.addMsg("%s Tsp1= %s,  Tsp2= %s;  " % (" "*4,str(sp1T),str(sp2T)))
      airT=sr.getKeyVar(tccModel.airTemp, ind=0, defVal='n/a')     
      self.logWdg.addMsg("%s Outside air temperature= %s;  " % (" "*4,str(airT)))
      
    #  primT=sr.getKeyVar(tccModel.primF_BFTemp, ind=0)
    #  secT=sr.getKeyVar(tccModel.secF_BFTemp, ind=0)     
    #  self.logWdg.addMsg("Temp prim="+str(primT)+"C   sec="+str(secT)+"C")
    
      self.logWdg.addMsg("%s" % ('-'*30))
      bossModel = TUI.Models.getModel("boss")
      sp1r0N=sr.getKeyVar(bossModel.SP1R0CCDTempNom, ind=0, defVal=0)
      sp1b2N=sr.getKeyVar(bossModel.SP1B2CCDTempNom, ind=0, defVal=0)
      sp2r0N=sr.getKeyVar(bossModel.SP2R0CCDTempNom, ind=0, defVal=0)
      sp2b2N=sr.getKeyVar(bossModel.SP2B2CCDTempNom, ind=0, defVal=0)
      sp1r0=sr.getKeyVar(bossModel.SP1R0CCDTempRead, ind=0, defVal=0)
         
      sp1b2=sr.getKeyVar(bossModel.SP1B2CCDTempRead, ind=0, defVal=0)
      sp2r0=sr.getKeyVar(bossModel.SP2R0CCDTempRead, ind=0, defVal=0)
      sp2b2=sr.getKeyVar(bossModel.SP2B2CCDTempRead, ind=0, defVal=0)
      def sevf(rr,nom,vv):
          if abs(rr-nom)>vv: sev=self.redWarn
          else: sev=0
          return sev      
      self.logWdg.addMsg("Boss CCD Temp :")
      self.logWdg.addMsg("    sp1r0= %6.1f (%6.1f);  " % (sp1r0, sp1r0N), severity=sevf(sp1r0, sp1r0N,5))
      self.logWdg.addMsg("    sp1b2= %6.1f (%6.1f);  " % (sp1b2, sp1b2N), severity=sevf(sp1b2, sp1b2N,5))
      self.logWdg.addMsg("    sp2r0= %6.1f (%6.1f);  " % (sp2r0, sp2r0N), severity=sevf(sp2r0, sp2r0N,5))
      self.logWdg.addMsg("    sp2b2= %6.1f (%6.1f);  " % (sp2b2, sp2b2N), severity=sevf(sp2b2, sp2b2N,5))

#      self.logWdg.addMsg(" ")
      SP1SecDewPress=sr.getKeyVar(bossModel.SP1SecondaryDewarPress, ind=0, defVal=defval)
      SP2SecDewPress=sr.getKeyVar(bossModel.SP2SecondaryDewarPress, ind=0, defVal=defval)
      self.logWdg.addMsg("%s sp1LN2: %4.1f;  " % (" "*8, SP1SecDewPress),severity=sevf(SP1SecDewPress,10,5))
      self.logWdg.addMsg("%s sp2LN2: %4.1f;  " % (" "*8, SP2SecDewPress), severity=sevf(SP1SecDewPress,10,5))
      self.logWdg.addMsg("%s" % ('-'*30))

   #   self.logWdg.addMsg(" ")
   #   gcamTempN=sr.getKeyVar(gcameraModel.cooler, ind=0)
      gcamTempN=-40.0 
      gcamTemp=sr.getKeyVar(gcameraModel.cooler, ind=1, defVal=defval)
  #    self.logWdg.addMsg("gcameraTemp= %5.1f (%5.1f);  " % (gcamTemp, gcamTempN),
      self.logWdg.addMsg("gcameraTemp= %s (%s);  " % (gcamTemp, gcamTempN),
                severity=sevf(gcamTemp,gcamTempN,3))
      
      secFoc=sr.getKeyVar(tccModel.secFocus, ind=0, defVal=defstr)
      self.logWdg.addMsg("Rel. Focus =  %s;  " % (str(secFoc)))

      ra=sr.getKeyVar(tccModel.objArcOff, ind=0, defVal=[defstr,defstr,defstr,])
      dec=sr.getKeyVar(tccModel.objArcOff, ind=1, defVal=[defstr, defstr])
      def offStr (off):
          off1=str(off)   
          off1=string.replace(off1,"PVT","")
          off1=string.replace(off1,"(","")
          off1=string.replace(off1,")","")
          off1=string.replace(off1,"[","")
          off1=string.replace(off1,"]","")
          off1=string.replace(off1,"'","")
          off2,off3=off1.split(None,1)
          off2=string.replace(off2,",","")
          return off2
      self.logWdg.addMsg("objArcOff = %s,  %s;  " % (offStr(ra),offStr(dec)))
      self.logWdg.addMsg("%s" % ('-'*30))
      def sevLevL(rr,lev1,lev2):
          if rr <= lev2: sev=self.redWarn
          elif lev2 < rr <lev1: sev=self.blueWarn
          elif rr >= lev1: sev=0
          else: pass
          return sev

      def sevLevU(rr,lev1,lev2):
          if rr > lev2: sev=self.redWarn
          elif lev1 < rr <lev2: sev=self.blueWarn
          elif rr<lev1: sev=0
          else: pass
          return sev

      vac = sr.getKeyVar(self.apogeeModel.vacuum, ind=0, defVal=defstr)
      ln2Lev =  sr.getKeyVar(self.apogeeModel.ln2Level, ind=0, defVal=defstr)
      if vac > 1.0e-6:  sev=self.redWarn
      else: sev=0
      self.logWdg.addMsg("Apogee: vacuum = %s (<1.0e-6 )" % (vac), severity=sev)
      self.logWdg.addMsg("Apogee: ln2Level = %s (<85 warn, <75 alert)" %(ln2Lev),severity=sevLevL(ln2Lev,85,70))
      self.logWdg.addMsg("%s" % ('-'*30))
      
      humidPT=sr.getKeyVar(apoModel.humidPT, ind=0, defVal=defstr)
      self.logWdg.addMsg("humid25m =  %s;  " % (str(humidPT)), severity=sevLevU(humidPT,75,85))
      airTempPT=sr.getKeyVar(apoModel.airTempPT, ind=0, defVal=defstr)
      dpTempPT=sr.getKeyVar(apoModel.dpTempPT, ind=0, defVal=defstr)
      self.logWdg.addMsg("airTemp25m =  %sC,  dpTemp25m =  %sC;  " % (str(airTempPT), str(dpTempPT)))
      try:      
          diff=airTempPT-dpTempPT 
      except:
          diff=defstr
    #  self.logWdg.addMsg("airTemp25m =  %sC,  dpTemp25m =  %sC;  " % (str(airTempPT), str(dpTempPT)))
      self.logWdg.addMsg("      diff= %sC;  " % (str(diff)),severity=sevLevL(diff,5.0,2.5))

      if encl > 0:
          dir25m=sr.getKeyVar(apoModel.windd25m, ind=0, defVal=defstr)
          wind25m=sr.getKeyVar(apoModel.winds25m, ind=0, defVal=defstr)         
          ww=str(wind25m); dd=str(dir25m)
          self.logWdg.addMsg("wind25m = %s mph,  direction = %s;  " %  (str(wind25m),str(dir25m)),
                           severity=sevLevU(wind25m,30,35))
      else:
          self.logWdg.addMsg("wind25m = %s,  direction = %s  "% (defstr, defstr) )
          
      self.logWdg.addMsg("%s" % ('-'*30))
      
      self.semOwn = sr.getKeyVar(mcpModel.semaphoreOwner, ind=0, defVal=None) 
      self.logWdg.addMsg("semOwner = %s"% (self.semOwn))
      
      tuiver=TUI.Version.VersionStr
      pid=os.getpid()
      sz="rss"
      mem=int(os.popen('ps -p %d -o %s | tail -1' % (pid, sz)).read())
      ss="%s, stuiVer=(%s),  pid = %s,  mem = %s MB" % (tm, tuiver, pid,  mem/1000)
      self.logWdg.addMsg("%s" % (ss)) 
      print self.name, ss
                 
      self.logWdg.addMsg(" ") 
      self.logWdg.addMsg(" ") 

#      yield sr.waitCmd(actor="boss", cmdStr="status",
#                 keyVars=[bossModel.sp1Temp,bossModel.sp2Temp], checkFail=False)
#      if sr.value.didFail:
#          sp1T="failed"; sp2T="failed"
#      else:    
#         sp1T=sr.value.getLastKeyVarData(bossModel.sp1Temp)[0]
#         sp2T=sr.value.getLastKeyVarData(bossModel.sp2Temp)[0]
