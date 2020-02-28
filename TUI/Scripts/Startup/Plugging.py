"""
History:  created by EM to list plugged plates and to check if plates duplicated
02-06-2013 EM adjusted window size; added version date, moved to STUI scripts. 
02/19/2014 EM cart 18 is modified to cart 2. Updated the list of available cartridges.
in ver > 1.3.1b3
"""

import RO.Wdg
import Tkinter
import TUI.Models
import  numpy
import sys,os,string
import time

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode 
        # if False, real time run
        sr.name="-- plugging"
        sr.debug = False
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.logWdg = RO.Wdg.LogWdg(master=sr.master, width=30,  height =23,)
        self.logWdg.grid(row=1, column=0, sticky="nsew")
        sr.master.rowconfigure(1, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.logWdg.text.tag_config("a", foreground="magenta") 
        self.logWdg.text.tag_config("g", foreground="darkblue") 

        self.ct=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
        n=len(self.ct)
        self.pl=["...."]*n        

        self.platedbModel = TUI.Models.getModel("platedb")

        fs="12"   # font size
        ft="Monaco" # "Courier"  #"Menlo"  # font type
        self.logWdg.text.tag_config("cur", font=(ft,fs))        
        
    def updatePlugging(self, keyVar): 
        if not keyVar.isGenuine: return
        mm=keyVar[:]
        iii=self.ct.index(mm[0])
        self.pl[iii]=str(mm[1])

    def getTAITimeStr(self,):
        return time.strftime("%H:%M:%S",
           time.gmtime(time.time() - RO.Astro.Tm.getUTCMinusTAI()))
        
    def run(self, sr):
        timeStr = self.getTAITimeStr()
        self.logWdg.addMsg("platedb showActive, %s" % (timeStr), tags=["a"])
        
        self.platedbModel.activePlugging.addCallback(self.updatePlugging,callNow=True)
        yield sr.waitCmd(actor="platedb", cmdStr="showActive", abortCmdStr="abort", checkFail=True)
        self.platedbModel.activePlugging.removeCallback(self.updatePlugging)
        
        n=len(self.ct)
        for i in range(0,n):
           self.logWdg.addMsg("  ct=%2i  pl=%s  --> pl=" % (self.ct[i], self.pl[i]), tags=["cur"] )
        self.logWdg.addMsg("--------------"  )

        err=0
    # test code
    #    self.pl[15]=4013;  self.pl[16]=4013
        for i in range(0,n):
            pl=self.pl[i];  ct=self.ct[i]
            for j in range(i+1,n):
                pl1=self.pl[j];   ct1=self.ct[j]
                if (pl != "....") and (pl1 != "...."): 
                    if int(pl)==int(pl1) :
                        err=1
                        self.logWdg.addMsg("(%s/%s) == (%s/%s)" % \
                                   (ct, pl,ct1, pl1),severity=RO.Constants.sevError, tags=["cur"])
        if err == 0:
            self.logWdg.addMsg("No duplicated plates - ok!")
        else:
            self.logWdg.addMsg("Error:  same plates on different carts ",
                               severity=RO.Constants.sevError, tags=["cur"])
        self.logWdg.addMsg("-- done --", tags=["a"])


    def end(self, sr):
        pass

