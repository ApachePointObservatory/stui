#  sop-apogee timer
#  history
#  added say alert 
# 03/11/2013:  EM: changed voice to mac system Glass.wav
# 04/20/2013:  EM: multiple refinement,  added format and colors,  
#  changed time left for None if no exposures left in sop sequence. 

import RO.Wdg
import TUI.Models

class ScriptClass(object):
    def __init__(self, sr, ):

       sr.master.winfo_toplevel().wm_resizable(True, True)
       self.ft=("Times", "16", "bold") 
       self.labWdg = RO.Wdg.Label(master=sr.master, text ="           ", font=self.ft, fg="black")
       self.labWdg.grid(row=0, column=0, sticky="nsw")                           
       sr.master.rowconfigure(0, weight=1)
       sr.master.columnconfigure(0, weight=1)

       sPath="/Library/Application Support/STUIAdditions"
       ffid=sPath+"/Scripts/Glass.wav"
       self.soundFid = RO.Wdg.SoundPlayer(ffid)

       self.sr=sr 
       self.alertTime=5.0
       self.alert=True
       self.sopModel = TUI.Models.getModel("sop")
       self.apogeeModel = TUI.Models.getModel("apogee")
       self.utr2=self.apogeeModel.utrReadState[2]
       self.utrTimeOver=self.utr2*self.apogeeModel.utrReadTime[0]  
       self.sopModel.doApogeeScience_sequenceState.addCallback(self.seqState,callNow=True)
       self.apogeeModel.utrReadState.addCallback(self.utrState,callNow=True)
       self.record()
                
    def seqState(self, keyVar): 
        if not keyVar.isGenuine: return
        self.record()

    def utrState(self, keyVar):
         if not keyVar.isGenuine: return
         if keyVar[1] == "Done" and keyVar[2] != self.utr2: 
             self.utr2=keyVar[2]
             expTime=self.apogeeModel.utrReadTime[0]
             self.utrTimeOver=self.utr2*expTime
             self.record()

    def record(self,):
         sr=self.sr
         sq, indState =self.sopModel.doApogeeScience_sequenceState[0:2]   
              #  sq -  sequence ABBAABBA, indState - number of A/B completed  
         if len(sq)==indState: 
             self.labWdg.set("  SOP/Apogee time left  = None")
             return 

         expTime=self.sopModel.doApogeeScience_expTime[0]   # time for one A or B  
         sqTime=len(sq)*expTime  # full time requested, len(ABBAABBA)* expTime                    
         sqTimeOver=indState*expTime  #  time over for completed some of ABBAABBA
           
         timeLeft=(sqTime - sqTimeOver - self.utrTimeOver)/60.0
         self.labWdg.set("  SOP/Apogee time left  =  %5.1f min" % (timeLeft))         
         if (timeLeft > self.alertTime):
              self.alert=True;  fg="darkgreen"
         elif (0 < timeLeft <= self.alertTime):
              fg="red" 
              if  self.alert: 
                    self.alert = False;  
                    self.soundFid.play() 
         else:  fg="black" 
         self.labWdg.config(fg=fg)
         return
                          
    def run(self, sr):
        self.record()
                
    def end(self, sr): 
        pass        
      #  self.sopModel.doApogeeScience_sequenceState.removeCallback(self.seqState)
      #  self.apogeeModel.utrReadState.removeCallback(self.utrState)
      #  print "-- call removed,  done --"
         
