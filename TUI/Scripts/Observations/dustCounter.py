import RO.Wdg
import TUI.Models
#import Tkinter
import time

class ScriptClass(object):
    def __init__(self, sr, ):
        self.name="dustCounter  "
       # print self.name, "-- init --"
        self.dustIntegr=0.0
        
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.logWdg = RO.Wdg.LogWdg(master=sr.master,width=40,height =10,)
        self.logWdg.grid(row=0, column=0, sticky="nsew")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.apoModel = TUI.Models.getModel("apo")

    def getTAITimeStr(self,):
        return time.strftime("%H:%M:%S",
              time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))

    def run(self, sr):
        print self.name
        self.logWdg.addMsg("%s" % (self.name))
        startTime=time.time()
        dust=sr.getKeyVar(self.apoModel.dustb, ind=0,  defVal=Exception)
        ss="xx:xx:xx  dTime=0 sec,  Dust,1um = %i,   Sum = 0" % (dust,)
        self.logWdg.addMsg(ss)
        print self.name, ss             

        while True:
           yield sr.waitKeyVar(self.apoModel.dustb, ind=0,  defVal=Exception, waitNext=True)
           dust=sr.value   # dust in unit/hour counts
           endTime=time.time()
           tm=self.getTAITimeStr()
           dTime=endTime-startTime   # time between reading in sec
         #  dTime=5*60  # 5 min --  in sec            
           self.dustIntegr= self.dustIntegr+dust*dTime/3600.00
           ss="%s:  dTime=%3.0f sec,  Dust,1um = %i,  Sum = %i" % (tm, dTime, dust, self.dustIntegr,)
           self.logWdg.addMsg(ss)
           print self.name, ss             
           startTime=endTime
           
    def end(self, sr): 
         pass
         