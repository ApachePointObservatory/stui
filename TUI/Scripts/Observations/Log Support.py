''' Elena Malanushenko  01/30/2011
script to gather information for night log

History: 
05/16/2011  removed scale from 1st block 
.. 
09/09/2013 EM: changed format of calibOffset to 4 digits to fit 80 chars line size. 
some day in the past:  added 4th window for hartmann output.
03/25/2015 EM:  formated hartmann output to fit 80 chars width in night log;
               removed all print to stui error log
03/30/2015 EM: format hartmann block;  fixed  bug with cart number
2015-11-05 ROwen    Stop using dangerous bare "except:"
2016-02-03 EM  Added  callback functions for hartmann values;  print values 
    only specific for the last hartmann;  if failed, no old values output in the table but '?'.  
'''

import RO.Wdg
import TUI.Models
import time

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

        # log4  -- hartmann
        self.logWdg4 = RO.Wdg.LogWdg(master = sr.master, width = width, height = height,
            helpText = "Hartman", relief = "sunken", bd = 2)
        self.logWdg4.grid(row=3, column=0, sticky="nsew")


        #resizeable window-2
        sr.master.rowconfigure(0, weight=1)
        sr.master.rowconfigure(1, weight=1)
        sr.master.rowconfigure(2, weight=1)
        sr.master.rowconfigure(3, weight=1)
        sr.master.columnconfigure(0, weight=1)

        # stui models
        self.tccModel = TUI.Models.getModel("tcc")
        self.guiderModel = TUI.Models.getModel("guider")
        self.apoModel = TUI.Models.getModel("apo")
        self.apogeeModel = TUI.Models.getModel("apogee")
        self.cmdsModel = TUI.Models.getModel("cmds")
        self.hartmannModel = TUI.Models.getModel("hartmann")
        self.sopModel = TUI.Models.getModel("sop")

        fs="12"   # font size
        ft="Monaco" # "Courier"  #"Menlo"  # font type
        self.logWdg1.text.tag_config("cur", font=(ft,fs))        
        self.logWdg2.text.tag_config("cur", font=(ft,fs))       
        self.logWdg3.text.tag_config("cur", font=(ft,fs))
        self.logWdg4.text.tag_config("cur", font=(ft,fs))
        
        self.logWdg1.text.tag_config("b", foreground="darkblue")
        self.logWdg2.text.tag_config("g", foreground="darkgreen")
        self.logWdg4.text.tag_config("c", foreground="Brown")
        self.logWdg4.text.tag_config("r", foreground="Red")


        # title lines
        s=" "; sw="%s" % (width*"-")

        self.logWdg1.addMsg("--- Offsets --- (arcsec) ", tags=["b","cur"])
        ssoff="    objArcOff   guideRot     calibOff  "
        ss = "Time %s Inst %s Az    Alt   Rot %s" % (2*s,3*s,ssoff)        
        self.logWdg1.addMsg("%s" % (ss), tags=["b","cur"])
        self.logWdg1.addMsg("%s" % (sw),tags=["b","cur"])

        self.logWdg2.addMsg("--- Focus ---", tags=["g","cur"])
        ss="Time    Inst     Scale    M1    M2  Focus   Az   Alt    Temp Wind Dir <fwhm>"
        self.logWdg2.addMsg("%s" % (ss,), tags=["g","cur"])
        self.logWdg2.addMsg("%s" % (sw),tags=["g","cur"])
                                
        self.logWdg3.addMsg("--- Weather ---", tags=["cur"])
        ss="Time %s Inst    Temp   DP   Dif  Humid Wind Dir Dust,1um IRSC  IRSCm <fwhm>" % (2*s,)
        self.logWdg3.addMsg("%s" % (ss,), tags=["cur"])
        self.logWdg3.addMsg("%s" % (sw),tags=["cur"])

        self.logWdg4.addMsg("--- Hartmann ---", tags=["cur","c"])
        ss="Time    Inst         r1   b1  move1 b1pred Tsp1      r2   b2  move2 b2pred Tsp2"
        self.logWdg4.addMsg("%s" % (ss), tags=["cur","c"])
        sline="%s     %s    %s" % (14*'-', 28*"-", 28*"-")
        self.logWdg4.addMsg("%s" % (sline), tags=["cur","c"])

        self.bossModel = TUI.Models.getModel("boss")
        self.expState=self.bossModel.exposureState[0]
        self.bossModel.exposureState.addCallback(self.updateBossState,callNow=True)
        self.apogeeState=self.apogeeModel.exposureWroteSummary[0]
        self.apogeeModel.exposureWroteSummary.addCallback(self.updateApogeeExpos, callNow=True)
    
        self.startHartmannCollimate=None
        self.cmdsModel.CmdQueued.addCallback(self.hartStart,callNow=False)
        self.cmdsModel.CmdDone.addCallback(self.hartEnd,callNow=False)
        self.cartHart=" x-xxxxA"
        
        self.hartInfo=["?"]*8
        self.hartmannModel.r1PistonMove.addCallback(self.r1PistonMoveFun,callNow=False)
        self.hartmannModel.r2PistonMove.addCallback(self.r2PistonMoveFun,callNow=False)
        
        self.hartmannModel.b1RingMove.addCallback(self.b1RingMoveFun,callNow=False)
        self.hartmannModel.b2RingMove.addCallback(self.b2RingMoveFun,callNow=False)
        self.hartmannModel.sp1AverageMove.addCallback(self.sp1AverageMoveFun,callNow=False)
        self.hartmannModel.sp2AverageMove.addCallback(self.sp2AverageMoveFun,callNow=False)
        self.hartmannModel.sp1Residuals.addCallback(self.sp1ResidualsFun,callNow=False)
        self.hartmannModel.sp2Residuals.addCallback(self.sp2ResidualsFun,callNow=False)

        
    def r1PistonMoveFun(self, keyVar):
        if not keyVar.isGenuine: return
        self.hartInfo[0]=keyVar[0]        
    def r2PistonMoveFun(self, keyVar):
        if not keyVar.isGenuine: return
        self.hartInfo[1]=keyVar[0]
        
    def b1RingMoveFun(self,keyVar):
        if not keyVar.isGenuine: return
        self.hartInfo[2]=keyVar[0]
    def b2RingMoveFun(self,keyVar):
        if not keyVar.isGenuine: return
        self.hartInfo[3]=keyVar[0]

    def sp1AverageMoveFun(self,keyVar):
        if not keyVar.isGenuine: return
        self.hartInfo[4]=keyVar[0]
    def sp2AverageMoveFun(self,keyVar):
        if not keyVar.isGenuine: return
        self.hartInfo[5]=keyVar[0]
            
    def sp1ResidualsFun(self,keyVar):
        if not keyVar.isGenuine: return
        self.hartInfo[6]=keyVar[1]
    def sp2ResidualsFun(self,keyVar):
        if not keyVar.isGenuine: return
        self.hartInfo[7]=keyVar[1]
                               
    def hartStart(self, keyVar):
        if not keyVar.isGenuine: 
            return
        q1=(keyVar[4]=="hartmann")  and (keyVar[6]=="collimate")
        q2=(keyVar[4]=="sop") and  (keyVar[6]=="collimateBoss")
        if q1 or q2:
            self.startHartmannCollimate=keyVar[0]     # setup flag   
            self.hartInfo=["?"]*8

    def hartEnd(self, keyVar):
        if not keyVar.isGenuine: 
            return
        if keyVar[0]==self.startHartmannCollimate:
            self.startHartmannCollimate=None 
            self.print_hartmann_to_log()

    def print_hartmann_to_log(self):
        tm=self.getTAITimeStr()
        ss1="%s %s   "% (tm,self.getCart(self.sr)) 
        
        rPiston=self.hartInfo[0]
        bRing=self.hartInfo[2]
        spAvMove=self.hartInfo[4]
        spRes=self.hartInfo[6]
        spTemp=self.bossModel.sp1Temp[0]
        try:
            ss2="%5i %5.1f %5i %5.1f %4.1f" % (rPiston, bRing, spAvMove, spRes, spTemp)
        except Exception: 
            ss2="%5s %5s %5s %5s %4s" % (rPiston, bRing, spAvMove, spRes, spTemp)        

        rPiston=self.hartInfo[1]
        bRing=self.hartInfo[3]
        spAvMove=self.hartInfo[5]
        spRes=self.hartInfo[7]
        spTemp=self.bossModel.sp2Temp[0]
        try:
            ss3="%5i %5.1f %5i %5.1f %4.1f" % (rPiston, bRing, spAvMove, spRes, spTemp)
        except Exception: 
            ss3="%5s %5s %5s %5s %4s" % (rPiston, bRing, spAvMove, spRes, spTemp)        

        self.logWdg4.addMsg("%s  %s    %s" % (ss1,ss2,ss3), tags=["c","cur"])


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
                  
      ss0="(%s,%s)" % (objOff0, objOff1)
      ss1="(%s)" % (guideOff2)
      ss2="(%s,%s,%s)" % (calibOff0, calibOff1, calibOff2)
      ss="%s %s %6.1f %4.1f %6.1f  %s %s %s %s " % (tm,cart, az, alt, rot, ss0, ss1, ss2, atm)  
      self.logWdg1.addMsg("%s" % (ss), tags=["b","cur"])
      
      # focus
      ss1="%s %s %8.6f %s %s %s" % (tm,cart,scale,primOr,secOr,secFoc)
      ss2=" %6.1f  %4.1f  %5.1f  %s  %s  %3.1f %s"  %  (az,alt, airT, wind, dir,fwhm,atm)
      ss=ss1+ss2
      self.logWdg2.addMsg("%s" % (ss), tags=["g","cur"])
      
      # weather
      ss1="%s %s %5.1f %5.1f %5.1f  %s"  % (tm, cart, airT, dp, diff, humid,)
      ss2="   %s  %s  %s  %5.1f  %4i  %3.1f %s" % (wind,dir, dustb, irsc, irscmean,fwhm,atm)
      ss=ss1+ss2      
      self.logWdg3.addMsg("%s " % (ss), tags=["cur"] )

    def run(self,sr):
       self.record(sr,"")
       self.print_hartmann_to_log()
