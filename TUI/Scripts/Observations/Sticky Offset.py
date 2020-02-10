import RO.Wdg
import TUI.Models
import tkinter
import time

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False
        self.name="-stickyOffset-"

# set resizable window
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.sr = sr
        row=0 
        self.labWdg = RO.Wdg.Label(master=sr.master,
            text = "Offsets control panel: ").grid(row=row, column=0, sticky="w")
        row += 1     

#     set frame with buttons
        butList = (" Save_offset ", " Apply_offset "," Clear_offsets ", " gotoFK5->3 ", " gotoFK5->11")
        helpText=("Save current offset", "Apply saved offset","Clear current offset"," GotoFK5-3"," GotoFK5-11")
        F0 = tkinter.Frame(master=sr.master)
        F0.grid(row=row, column=0, sticky="w",)
        self.but0=RO.Wdg.Button(master=F0, helpText = helpText[0],
            callFunc =self.saveOff, text=butList[0],).grid(row = row,column=0)
        self.but1=RO.Wdg.Button(master=F0,helpText =helpText[1],
            callFunc = self.applOff, text=butList[1],).grid(row = row,column=1 )
        self.but2=RO.Wdg.Button(master=F0,helpText = helpText[2],
            callFunc =self.clearOff, text=butList[2],).grid(row = row,column=2 )
        row += 1

        F1 = tkinter.Frame(master=sr.master)
        F1.grid(row=row, column=0, sticky="w",)
        self.but3=RO.Wdg.Button(master=F1, helpText = helpText[3],
            callFunc =self.gotofk5to3, text=butList[3],).grid(row = row,column=0)
        self.but4=RO.Wdg.Button(master=F1, helpText = helpText[4],
            callFunc =self.gotofk5to11, text=butList[4],).grid(row = row,column=1)
        row += 1

# set resizable  log window                
        self.logWdg = RO.Wdg.LogWdg(master=sr.master,  width=60, height =15,)
        self.logWdg.grid(row=row, column=0, sticky="news")
        sr.master.rowconfigure(3, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.logWdg.text.tag_config("b", foreground="darkblue")
        self.logWdg.text.tag_config("r", foreground="darkred")
        self.logWdg.text.tag_config("g", foreground="darkgreen")        
# models        
        self.tccModel = TUI.Models.getModel("tcc")
        self.guiderModel = TUI.Models.getModel("guider")        
        self.objOff0=(0.0,0.0)  # save offsets in degrees

    def gotofk5to3(self,bt):
        sr=self.sr
        tm=self.getTAITimeStr()
        act="guider";  cmd="fk5InFiber probe=3"
        sr.startCmd(actor=act, cmdStr=cmd, checkFail=False)
        self.logWdg.addMsg("%s   %s,   %s  %s " %
                           (tm, self.getCart(sr,), act,cmd))
        
    def gotofk5to11(self,bt):
        sr=self.sr
        tm=self.getTAITimeStr()
        act="guider";  cmd="fk5InFiber probe=11"
        sr.startCmd(actor=act, cmdStr=cmd, checkFail=False)
        self.logWdg.addMsg("%s   %s,   %s  %s " %
                           (tm,self.getCart(sr,), act,cmd))        

# get curremnt offset in degrees
    def getOff(self,):
        sr=self.sr
        a0=self.tccModel.objArcOff[0]
        a1=self.tccModel.objArcOff[1]
   #     a0=sr.getKeyVar(self.tccModel.objArcOff, ind=0, defVal=0)
   #     a1=sr.getKeyVar(self.tccModel.objArcOff, ind=1, defVal=0) 
        objOff0 = RO.CnvUtil.posFromPVT(a0)
        objOff1 = RO.CnvUtil.posFromPVT(a1)
        return (objOff0,objOff1)

# save current offset to variable in degrees, but in arcsec
    def saveOff(self,bt):
        tm=self.getTAITimeStr()
        self.objOff0=self.getOff()
        def ff(ofs): 
           if ofs==None:  return "%s" % "None"
           else:  return '%5.1f"' % (ofs*3600.0)
        ss0='(%5s, %5s)' % (ff(self.objOff0[0]), ff(self.objOff0[1]))
        self.logWdg.addMsg("%s   %s,   objArcOff = %s  (saved)" %
                           (tm, self.getCart(self.sr,), ss0),tags=["b"])

# apply saved offset
# tcc offset arc 0.001,0.001,0.
    def applOff(self,bt):        
        tm=self.getTAITimeStr()
        sr=self.sr
        if (self.objOff0[0]==None) or (self.objOff0[1]==None):
            self.logWdg.addMsg("%s %s,  no offsets " %  (tm, self.getCart(self.sr,)))
        else:             
            act="tcc";  cmd="offset arc %s, %s, 0" %  (self.objOff0[0],self.objOff0[1])         
            sr.startCmd(actor=act, cmdStr=cmd, checkFail=False)
            self.logWdg.addMsg("%s   %s,   %s  %s " %
                (tm, self.getCart(self.sr,), act,cmd),tags=["r"])

    #    ss0='(%5.1f",%5.1f")' % (self.objOff0[0]*3600.0, self.objOff0[1]*3600.0)
    #    self.logWdg.addMsg("%s   Cart = %s,   objArcOff = %s  (applied)" %
    #                       (tm, self.getCart(self.sr,), ss0),tags=["r"])
                      
    def clearOff(self,bt):
        tm=self.getTAITimeStr()
        sr=self.sr
        act="tcc";  cmd="offset arc /pabs"
        sr.startCmd(actor=act, cmdStr=cmd, checkFail=False)
        self.logWdg.addMsg("%s   %s,   %s  %s " %
                           (tm, self.getCart(self.sr,), act,cmd),tags=["g"])

    def getTAITimeStr(self,):
        return time.strftime("%H:%M:%S",
              time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))

    def getCart (self,sr,):
      ct=self.guiderModel.cartridgeLoaded[:]
      if ct[0]==None:
           ss="no cart"
      else:     
           ss="%s - %s%s" % (ct[0],ct[1],ct[2])
      return ss

    def ff(self, ofs): 
        if ofs==None:  return "%s" % "None"
        else:  return '%5.1f"' % (ofs*3600.0)
 
    def run(self, sr):
      tm=self.getTAITimeStr()
      objOff=self.getOff()
 #     ss0='(%5.1f",%5.1f")' % (objOff[0]*3600.0, objOff[1]*3600.0)
      ss0='(%5s,  %5s)' % (self.ff(objOff[0]), self.ff(objOff[1]))
      self.logWdg.addMsg("%s   %s,   objArcOff = %s" % (tm, self.getCart(sr,), ss0))

    def end(self, sr):
       pass
           
