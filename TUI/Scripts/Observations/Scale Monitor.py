import RO.Wdg
import TUI.Models
#from datetime import datetime
import TUI.PlaySound
import Tkinter
import time

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False
        sr.master.winfo_toplevel().wm_resizable(True, True)

        self.labWdg = RO.Wdg.Label(master=sr.master, text = "Delta Scale Correction", )
        self.labWdg.grid(row=0, column=0, sticky="w")

        F1 = Tkinter.Frame(sr.master)
        gr = RO.Wdg.Gridder(F1)
        F1.grid(row=1, column=0, sticky="w")

        warn=True
        self.checkWdg = RO.Wdg.Checkbutton(master=F1, 
            text = "sound;            ", defValue=warn, helpText ="Play sound",)
        self.checkWdg.grid(row=0, column=0, sticky="news")

        scaleLev=0.0025
        self.scaleRange = RO.Wdg.FloatEntry(master =F1,
             defValue =scaleLev, defFormat="%.4f",
             minValue =0.0, maxValue = 0.1,
             helpText ="Level to consider out of spec")
        gr.gridWdg("level=", self.scaleRange)
        self.scaleRange.grid(row=0, column=1, sticky="news")       
       
        self.logWdg = RO.Wdg.LogWdg(master=sr.master,  width=25, height =13,)
        self.logWdg.grid(row=2, column=0, sticky="news")
        sr.master.rowconfigure(2, weight=1)
        sr.master.columnconfigure(0, weight=1)

        self.guiderModel = TUI.Models.getModel("guider")

    def getTAITimeStr(self,):
        return time.strftime("%H:%M:%S",
              time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))
    
    def run(self, sr):
        playS=self.checkWdg.getBool()
        scaleLev=self.scaleRange.getNum()
        self.logWdg.addMsg("---------- ")
        while True:
	  yield sr.waitKeyVar(self.guiderModel.scaleError, ind=0,    
                 defVal=Exception, waitNext=True)
          scaleError = -sr.value*100
          timeStr = self.getTAITimeStr()
          self.logWdg.addMsg(" %s   %7.4f " % (timeStr, scaleError))
          if abs(scaleError) > scaleLev and playS: TUI.PlaySound.noGuideStar()
 

  #      keysModel = TUI.Models.getModel("keys")
  #      yield sr.waitCmd(actor="keys", cmdStr="getFor=guider seeing",
  #          keyVars=[keysModel.text])
   #     seeing=sr.getKeyVar(keysModel.text, ind=0)
   #     seeing= sr.value.getLastKeyVarData(keysModel.text)[0]
