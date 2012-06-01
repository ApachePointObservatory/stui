import RO.Wdg
import TUI.Models
#import Tkinter
import time
seqState=0
utrState=1

class ScriptClass(object):
    def __init__(self, sr, ):

       sr.master.winfo_toplevel().wm_resizable(True, True)
       self.labWdg = RO.Wdg.Label(master=sr.master, text ="           ")
       self.labWdg.grid(row=0, column=0, sticky="nsw")
              
 #      self.logWdg = RO.Wdg.LogWdg(master=sr.master,width=50,height =3,)
 #      self.logWdg.grid(row=0, column=0, sticky="nsew")
       sr.master.rowconfigure(0, weight=1)
       sr.master.columnconfigure(0, weight=1)

       print "---start --" 
       self.sr=sr 
       self.sopModel = TUI.Models.getModel("sop")
       self.sopModel.doApogeeScience_sequenceState.addCallback(self.seqState,callNow=True)

       self.apogeeModel = TUI.Models.getModel("apogee")
       self.apogeeModel.utrReadState.addCallback(self.utrState,callNow=True)

     #  self.record()
         
    def seqState(self, keyVar): 
        if not keyVar.isGenuine: return
     #   global seqState
     #   seqState=1
    #   sr=self.sr
        self.record()

    def utrState(self, keyVar):
         if not keyVar.isGenuine: return
       #  global utrState
       #  utrState=1
       #  sr=self.sr
         self.record()

    def record(self,):
         sr=self.sr
       #  sq=sr.getKeyVar(self.sopModel.doApogeeScience_sequenceState,ind=0, defVal="DDDD")
         sq=self.sopModel.doApogeeScience_sequenceState[0]
       #  expTime=sr.getKeyVar(self.sopModel.doApogeeScience_expTime, ind=0, defVal=500)
         expTime=self.sopModel.doApogeeScience_expTime[0]
         indState=self.sopModel.doApogeeScience_sequenceState[1]
         t1=len(sq)*expTime  # total exposure time
         t2=indState*expTime  #  full number of exposures completed 
         utr2=self.apogeeModel.utrReadState[2]
         tm=self.apogeeModel.utrReadTime[0]
         tover=t2+utr2*tm
         self.labWdg.set("Apogee exposure time left  = %5.1f min" % ((t1-tover)/60))
         
       #  return "Record"

    def getTAITimeStr(self,):
        return time.strftime("%H:%M",
              time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))
            
    def run(self, sr):
        self.record()
        pass
                
    def end(self, sr): 
        print "--end--"
         
