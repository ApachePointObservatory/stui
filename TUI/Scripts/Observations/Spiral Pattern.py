# EM
# spiral pattern script
# 01/10/2011 added:  second spiral, debug check button,
#    tkinter canvas widget test (need more work to clear memory before to use)
#    changes type of for-in cycle to use two variables together
# 01/17/2011 - changed to arcsec units to be consistent with  new guider gui units  
# 09/04/2013 EM:  check commands if some of them failed and rise an exception if so

import RO.Wdg
import Tkinter
import TUI.Models
import time

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode 
        # if False, real time run
        sr.debug = False
        
   #     print "--- spiralPattern1----"
   #     F1 = Tkinter.Toplevel()
   #     self.canvas = Tkinter.Canvas(F1, width=200, height=200)
   #     self.canvas.grid(row=0, column=0, sticky="news")

        sr.master.winfo_toplevel().wm_resizable(True, True)

        row=0
        F0 = Tkinter.Frame(master=sr.master)
        F0.grid(row=row, column=0, sticky="w")
        
        self.debugCheckWdg=RO.Wdg.Checkbutton(master=F0,
            text ="debug", defValue =sr.debug, helpText ="help check 0",)
        self.debugCheckWdg.grid(row = row,column=0, sticky="w")

        wdgR1b = Tkinter.Frame(F0)
        gr1b = RO.Wdg.Gridder(wdgR1b)           
        gexp=5.0 # default ecam integration time
        self.gexpWdg = RO.Wdg.IntEntry(master=wdgR1b,
             text="gcamera integration (1-20)=",
             defValue = gexp,
             minValue =1, maxValue =20, helpText = "Gcam integration time",
             )
        gr1b.gridWdg("        Gcam integration (1-20) =", self.gexpWdg,)
        wdgR1b.grid(row=0, column=1, sticky="e")
        row += 1
        
        self.logWdg = RO.Wdg.LogWdg(master=sr.master,width=40,height =15,)
        self.logWdg.grid(row=row, column=0, sticky="news")

        sr.master.rowconfigure(1, weight=1)
        sr.master.columnconfigure(0, weight=1)
    
    def getTAITimeStr(self,):
        return time.strftime("%H:%M:%S",
              time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))

    def run(self, sr):
        self.logWdg.addMsg("    ")
        print "--- spiralPattern ---"
        self.logWdg.addMsg("--- spiralPattern ---%s" % (self.getTAITimeStr()))
     #   intTime=5.0  # guider integration times
        intTime=self.gexpWdg.getNum()
        cmdG="on oneExposure  time="+str(intTime) # guider command 
        step=10  # arcsec step for offset
        sr.debug=self.debugCheckWdg.getBool()
        self.logWdg.addMsg("Guider integration time = %s" % (str(intTime)))  
        self.logWdg.addMsg("Steps in arcsec =  %s" % (str(step)))

        raOffs=(0,-1,-1,-1,0,1,1,1,       # 1st spiral
                   0,-1,-2,-2,-2,-2,-2,-1,0,1,2,2,2,2,2,1,0)   # 2nd spiral        
        decOffs=(1,1,0,-1,-1,-1,0,1,
                   2,2,2,1,0,-1,-2,-2,-2,-2,-2,-1,0,1,2,2,0)

        rr0=0.0;  dd0=0.0;  # central position 
        kk=0  # iteration number
        for (i,j) in zip(raOffs,decOffs):
           rr=i*step; dd=j*step   #  new offset in arcsec
           self.logWdg.addMsg(" i = %2i,   ra = %4.0f,  dec = %4.0f " % (kk,rr,dd))
           
           rrM=(rr-rr0)/3600.0; ddM=(dd-dd0)/3600.0  #  move to new position in degrees           
           cmdTcc="offset arc %6.4f, %6.4f" % (rrM,ddM)   # tcc  command to move to the next position
         #  self.logWdg.addMsg("   tcc %s" % (cmdTcc))           
           if sr.debug == True:   # if False, real time run
              pass
           else: 
              yield sr.waitCmd(actor="tcc", cmdStr=cmdTcc, abortCmdStr="abort", checkFail=True)
              if sr.value.didFail: 
                    self.logWdg.addMsg(" probably, no connection")
                    raise sr.ScriptError("") 
              yield sr.waitCmd(actor="guider",cmdStr=cmdG,abortCmdStr="abort", checkFail=True)
              if sr.value.didFail: 
                    self.logWdg.addMsg(" probably, no connection")
                    raise sr.ScriptError("") 
           yield sr.waitMS(2000)  # wait for human response
           rr0=rr;  dd0=dd;
           kk=kk+1
           
       #    ic=i*40+100; jc=100-j*40; ds=15
       #    square = self.canvas.create_rectangle(ic-ds,jc-ds,ic+ds,jc+ds, fill="darkgreen")            
        #   self.canvas.delete(square)
        
        self.logWdg.addMsg("%s done " % (5*"-"))   
        self.logWdg.addMsg("%s  " % (5*" "))   

    def end(self, sr): 
        print "run end for spiral pattern1"
         
    def _end(self, sr):
        print "run _end for spiral pattern1"
