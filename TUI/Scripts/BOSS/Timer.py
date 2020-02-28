"""A timer for BOSS exposures

History:
2013-04-20 EM: bossTimer.py
2013-04-20 EM: added color and sound
2013-04-22 EM: added check button on/off sound, default on.
2012-04-24 EM: added ProgressBar
2012-05-17 EM: cut label text to just "bossTimer"
2013-08-20 EM: moved to STUI
2014-03-05  changed keyword name sopModel.doScience to sopModel.doBossScience  for new sop
2014-11-05 EM fixed bug with initial keyword value before connection.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
2015-11-05 ROwen    Stop using dangerous bare "except:"
"""
import os.path
import time
import Tkinter
import RO.Astro.Tm
import RO.Comm
import RO.OS
import RO.Wdg
import TUI.Models
import TUI.PlaySound

SoundsDir = RO.OS.getResourceDir(TUI, "Sounds")
SoundFileName = "Glass.wav"

class ScriptClass(object):
    def __init__(self, sr, ):
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.fgList=["DarkGrey", "ForestGreen", "Brown"]

        soundFilePath = os.path.join(SoundsDir, SoundFileName)
        self.soundPlayer = RO.Wdg.SoundPlayer(soundFilePath)

        self.sr=sr

        F1 = Tkinter.Frame(sr.master)
        F1.grid(row=0, column=0, sticky="sn")

        self.labWdg = RO.Wdg.Label(master=F1, text ="      ", fg=self.fgList[0])
        self.labWdg.grid(row=0, column=0, sticky="ns")
        self.checkWdg = RO.Wdg.Checkbutton(master=F1, text ="", defValue=True, helpText="Play sound",)
        self.checkWdg.grid(row=0, column=1, sticky="we")

        self.expTimer = RO.Wdg.ProgressBar(master=sr.master, valueFormat="%5.2f",  label=None)
        self.expTimer.grid(row=1, column=0, sticky="ew")

        sr.master.rowconfigure(0, weight=1)
        sr.master.rowconfigure(1, weight=1)
        sr.master.columnconfigure(0, weight=1)

        self.minAlert = 300.0/60.0
        self.secEnd=None
        self.alert = True
        self.fooTimer = RO.Comm.Generic.Timer()
        self.wait=1
#         self.fooTimer.start(self.wait, foo) # schedule self again
        self.foo()

        self.sopModel = TUI.Models.getModel("sop")
        self.nExp0, self.nExp1 = self.sopModel.doBossScience_nExp[0:2]

        self.expTotal= sr.getKeyVar(self.sopModel.doBossScience_expTime, ind=0, defVal=900)
        # I evaluated the time of reading out as 80 sec
        self.expTotal=self.expTotal+80        
        self.sopModel.doBossScience_nExp.addCallback(self.doScience_nExp, callNow=True)
        
    def getTAITimeStr(self,):
        '''' get timestamp'''
        self.currPythonSeconds = RO.Astro.Tm.getCurrPySec()
        self.currTAITuple = time.gmtime(self.currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
        self.taiTimeStr = time.strftime("%H:%M:%S", self.currTAITuple)
        return self.taiTimeStr,self.currPythonSeconds

    def doScience_nExp(self, keyVar):
        '''callback function if the number of sop done or scheduler exposures changed'''  
        sr=self.sr
        self.expTotal= sr.getKeyVar(self.sopModel.doBossScience_expTime, ind=0, defVal=900)
        self.expTotal=self.expTotal+80

        self.nExp0, self.nExp1 = keyVar[0:2]
        if keyVar[0] == keyVar[1]:   # end seq
            self.secEnd = None
        elif keyVar[0] !=self.nExp0 :   # begin seq, or next exposure
            tai, sec = self.getTAITimeStr()
            self.secEnd = sec + (self.nExp1 - self.nExp0) * self.expTotal
        elif keyVar[1] != self.nExp1:  # modification in progress
            self.secEnd = self.secEnd + (keyVar[1] - self.nExp1) * self.expTotal
        else:
            tai, sec = self.getTAITimeStr()
            self.secEnd = sec + (self.nExp1 - self.nExp0) * self.expTotal

        try:
            newValue = (self.nExp1 - self.nExp0) * self.expTotal / 60.
            newMax = self.nExp1 * self.expTotal / 60.
        except Exception:
            newValue=0
            newMax=900
        else:
            self.expTimer.setValue(newValue=newValue, newMin=0, newMax=newMax)
            self.foo()

    def foo(self):
        ''' Russel's timer'''
        self.fooTimer.cancel()
        lab=" BOSS Timer: "
        if self.secEnd is None:
            self.labWdg.set("%s None   " % (lab))
            self.labWdg.config(fg=self.fgList[0])
        else:
            tai, sec = self.getTAITimeStr()
            self.minLeft = (self.secEnd - sec) / 60.0
            self.labWdg.set("%s %6.2f min   " % (lab,self.minLeft))
            if self.minLeft > self.minAlert:
                fgInd = 1
                self.alert = True
            elif 0 < self.minLeft <= self.minAlert:
                fgInd = 2
                if self.alert:
                    self.alert = False
                    if self.checkWdg.getBool():
                        self.soundPlayer.play()
                        self.soundPlayer.play()
            else:
                fgInd = 0
            self.labWdg.config(fg=self.fgList[fgInd])
            self.expTimer.setValue(newValue=self.minLeft)
            self.fooTimer.start(self.wait, self.foo) # schedule self again

    def run(self, sr):
        pass

    def end(self, sr):
        self.fooTimer.cancel()
