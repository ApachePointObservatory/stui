''' Elena Malanushenko  01/30/2011
script to gather information for night log

History: 
05/16/2011  removed scale from 1st block 
.. 
09/09/2013 EM: changed format of calibOffset to 4 digits to fit 80 chars line size. 
in ver > 1.3
'''

import RO.Wdg
import TUI.Models
import string
import time
import Tkinter

class ScriptClass(object,):
    def __init__(self, sr, ):
        # if True, run in debug-only mode 
        # if False, real time run
        sr.debug = False
        self.sr = sr
        self.name="-logSupport-"
        width=80 ; height=5

        #resizeable window-1
        sr.master.winfo_toplevel().wm_resizable(True, True)
        
        #log1  - offset
        self.logWdg1 = RO.Wdg.LogWdg(master=sr.master, width=width, height =height,  
              helpText = "Offset",)
        self.logWdg1.grid(row=0, column=0, sticky="news")
        
        # log2  - focus
        self.logWdg2 = RO.Wdg.LogWdg(master = sr.master, width = width, height = height,
              helpText = "Focus",  relief = "sunken", bd = 2,)
        self.logWdg2.grid(row=1, column=0, sticky="nsew")
        
        # log3  -- weather
        self.logWdg3 = RO.Wdg.LogWdg(master = sr.master, width = width, height = height,
            helpText = "Weather", relief = "sunken", bd = 2)
        self.logWdg3.grid(row=2, column=0, sticky="nsew")

        #resizeable window-2
        sr.master.rowconfigure(0, weight=1)
        sr.master.rowconfigure(1, weight=1)
        sr.master.rowconfigure(2, weight=1)
        sr.master.columnconfigure(0, weight=1)

        # stui models
        self.tccModel = TUI.Models.getModel("tcc")
        self.guiderModel = TUI.Models.getModel("guider")
        self.apoModel = TUI.Models.getModel("apo")
        self.apogeeModel = TUI.Models.getModel("apogee")

        fs="12"   # font size
        ft="Monaco" # "Courier"  #"Menlo"  # font type
        self.logWdg1.text.tag_config("cur", font=(ft,fs))        
        self.logWdg2.text.tag_config("cur", font=(ft,fs))       
        self.logWdg3.text.tag_config("cur", font=(ft,fs))
        
        self.logWdg1.text.tag_config("b", foreground="darkblue")
        self.logWdg2.text.tag_config("g", foreground="darkgreen")

        # title lines
        s=" "; sw="%s" % (width*"-")

        self.logWdg1.addMsg("--- Offsets --- (arcsec) ", tags=["b","cur"])
#       ssoff="   objArcOff  guideRot    calibOff    scale"
        ssoff="    objArcOff   guideRot     calibOff  "
        ss = "Time %s Inst %s Az    Alt   Rot %s" % (2*s,3*s,ssoff)        
        self.logWdg1.addMsg("%s" % (ss), tags=["b","cur"])
        print self.name, "Off:",ss        
        self.logWdg1.addMsg("%s" % (sw),tags=["b","cur"])
        print self.name,"Off:", sw        

        self.logWdg2.addMsg("--- Focus ---", tags=["g","cur"])
        ss="Time    Inst     Scale    M1    M2  Focus   Az   Alt    Temp Wind Dir <fwhm>"
        self.logWdg2.addMsg("%s" % (ss,), tags=["g","cur"])
        print self.name,"Foc:", ss
        self.logWdg2.addMsg("%s" % (sw),tags=["g","cur"])
        print self.name,"Foc:",sw
                                
        self.logWdg3.addMsg("--- Weather ---", tags=["cur"])
        ss="Time %s Inst    Temp   DP   Dif  Humid Wind Dir Dust,1um IRSC  IRSCm <fwhm>" % (2*s,)
        self.logWdg3.addMsg("%s" % (ss,), tags=["cur"])
        print self.name,"Weth:", ss                
        self.logWdg3.addMsg("%s" % (sw),tags=["cur"])
        print self.name, "Weth:",sw

        self.bossModel = TUI.Models.getModel("boss")
        self.expState=self.bossModel.exposureState[0]
        self.bossModel.exposureState.addCallback(self.updateBossState,callNow=True)
        self.apogeeState=self.apogeeModel.exposureWroteSummary[0]
        self.apogeeModel.exposureWroteSummary.addCallback(self.updateApogeeExpos, callNow=True)

    def updateApogeeExpos(self, keyVar): 
        if not keyVar.isGenuine: return
        if keyVar[0] != self.apogeeState:
            sr=self.sr
            dd3=self.apogeeModel.utrReadState[3]
            if dd3 == 47:
                self.record(sr,"apog")
                self.apogeeState=keyVar[0]
        
    def updateBossState(self,keyVar):
        if not keyVar.isGenuine: return
        if keyVar[0] != self.expState:
             if  keyVar[0] == "INTEGRATING" and keyVar[1] == 900.00:
                  sr=self.sr
                  self.record(sr,"boss")
             self.expState=keyVar[0]
                
    def getTAITimeStr(self,):
#        return time.strftime("%H:%M:%S",
#              time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))
        return time.strftime("%H:%M",
              time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))

    def getCart (self,sr,):
      ctLoad=self.guiderModel.cartridgeLoaded
      gc = sr.getKeyVar(ctLoad, ind=0,defVal=99)
      gp = sr.getKeyVar(ctLoad, ind=1, defVal=9999)
      gs = sr.getKeyVar(ctLoad, ind=2, defVal="Z")
      ss="%2i-%s%s" % (gc,str(gp),str(gs))
      return ss
  
    def fInt(self,val,num):
      return str(int(val)).rjust(num," ")
  
    def record(self,sr,atm):
     # print self.name
      tm=self.getTAITimeStr()
      scale=sr.getKeyVar(self.tccModel.scaleFac, ind=0, defVal=1.0)
      
      az=sr.getKeyVar(self.tccModel.axePos, ind=0, defVal=999)
      alt=sr.getKeyVar(self.tccModel.axePos, ind=1,defVal=99)
      rot=sr.getKeyVar(self.tccModel.axePos, ind=2,defVal=999)
      cart=self.getCart(sr,)

      primOr=self.fInt(sr.getKeyVar(self.tccModel.primOrient, ind=0, defVal=9999),5)
      secOr=self.fInt(sr.getKeyVar(self.tccModel.secOrient, ind=0, defVal=9999),5)
      secFoc=self.fInt(sr.getKeyVar(self.tccModel.secFocus, ind=0, defVal=9999),4)
      
      def ffsec (n): 
         if n==None: return "%5s"  % "n/a" #  999.9"
         else: return "%5.1f" % (n*3600)
      def ffsecS (n): 
         if n==None: return "%4s"  % "n/a" 
         else: return "%4.1f" % (n*3600)
                           
      objOff0 = ffsec(RO.CnvUtil.posFromPVT(self.tccModel.objArcOff[0]))  # *3600.0
      objOff1 = ffsec( RO.CnvUtil.posFromPVT(self.tccModel.objArcOff[1])) # *3600.0
      
      guideOff0=ffsec(RO.CnvUtil.posFromPVT(self.tccModel.guideOff[0])) # *3600.0
      guideOff1=ffsec(RO.CnvUtil.posFromPVT(self.tccModel.guideOff[1])) # *3600.0
      guideOff2=ffsec(RO.CnvUtil.posFromPVT(self.tccModel.guideOff[2])) # *3600.0
      
      calibOff0=ffsec(RO.CnvUtil.posFromPVT(self.tccModel.calibOff[0])) # *3600.0
      calibOff1=ffsec(RO.CnvUtil.posFromPVT(self.tccModel.calibOff[1])) # *3600.0
      calibOff2=ffsecS(RO.CnvUtil.posFromPVT(self.tccModel.calibOff[2])) # *3600.0

     # rotOff = RO.CnvUtil.posFromPVT(self.tccModel.guideOff[2])

      fwhm=sr.getKeyVar(self.guiderModel.fwhm, ind=4,defVal=99.9 )
           
      airT=sr.getKeyVar(self.apoModel.airTempPT, ind=0, defVal=-99)
      dir=self.fInt(sr.getKeyVar(self.apoModel.windd, ind=0, defVal=-99),3)
      wind=self.fInt(sr.getKeyVar(self.apoModel.winds, ind=0, defVal=99),2)
      dp=sr.getKeyVar(self.apoModel.dpTempPT, ind=0, defVal=-99)
      humid=self.fInt(sr.getKeyVar(self.apoModel.humidPT, ind=0, defVal=999),3)  
      dustb=self.fInt(sr.getKeyVar(self.apoModel.dustb, ind=0, defVal=9999),5)
   #   dustb="%5s" % (sr.getKeyVar(self.apoModel.dustb, ind=0, defVal="n/a"))

      irsc=sr.getKeyVar(self.apoModel.irscsd, ind=0, defVal=999)
      irscmean=sr.getKeyVar(self.apoModel.irscmean, ind=0, defVal=999)

      at=sr.getKeyVar(self.apoModel.airTempPT, ind=0, defVal=999)
      val=sr.getKeyVar(self.apoModel.dpTempPT, ind=0, defVal=999)
      diff=at-val
                  
#      atm="apog"            
      # offsets
#      ss0="(%5.1f,%5.1f)" % (objOff0, objOff1)
      ss0="(%s,%s)" % (objOff0, objOff1)

#      ss1="(%6.1f)" % (guideOff2)
      ss1="(%s)" % (guideOff2)

#      ss2="(%5.1f,%5.1f,%5.1f)" % (calibOff0, calibOff1, calibOff2)
      ss2="(%s,%s,%s)" % (calibOff0, calibOff1, calibOff2)
#     ss2="(%s,%s)" % (calibOff0, calibOff1)
      
  #    ss="%s %s %5.1f %4.1f %5.1f  %s %s %s %s %s" % (tm,cart, az, alt, rot, ss0,ss1, ss2, scale,atm)
      ss="%s %s %6.1f %4.1f %6.1f  %s %s %s %s " % (tm,cart, az, alt, rot, ss0, ss1, ss2, atm)  
      self.logWdg1.addMsg("%s" % (ss), tags=["b","cur"])
      print self.name,"Off:", ss
      
      # focus
      ss1="%s %s %8.6f %s %s %s" % (tm,cart,scale,primOr,secOr,secFoc)
      ss2=" %6.1f  %4.1f  %5.1f  %s  %s  %3.1f %s"  %  (az,alt, airT, wind, dir,fwhm,atm)
      ss=ss1+ss2
      self.logWdg2.addMsg("%s" % (ss), tags=["g","cur"])
      print self.name,"Foc:",ss
      
      # weather
      ss1="%s %s %5.1f %5.1f %5.1f  %s"  % (tm, cart, airT, dp, diff, humid,)
      ss2="   %s  %s  %s  %5.1f  %4i  %3.1f %s" % (wind,dir, dustb, irsc, irscmean,fwhm,atm)
      ss=ss1+ss2      
      self.logWdg3.addMsg("%s " % (ss), tags=["cur"] )
      print self.name, "Weth:",ss 


    def run(self,sr):
       self.record(sr,"")
