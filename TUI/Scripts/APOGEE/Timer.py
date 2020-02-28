"""A timer for APOGEE exposures

History:
2013-08-20: EM: moved to STUI
2013-03-11: EM: changed voice to mac system Glass.wav
2013-04-20: EM: multiple refinement,  added format and colors,
    changed time left for None if no exposures left in sop sequence.
2013-04-22: EM:
    changed colors to self.fgList=["black", "ForestGreen","OrangeRed"]
    changed name from Timer to apogeeTimer
    added check button for sound on / off, default on.
2012-05-17 EM: change label text to just "apogeeTimer"
"""
import os
import Tkinter
import RO.OS
import RO.Wdg
import TUI
import TUI.Models

SoundsDir = RO.OS.getResourceDir(TUI, "Sounds")
SoundFileName = "Glass.wav"

class ScriptClass(object):
    def __init__(self, sr, ):
        self.sr = sr
        self.fgList = ["DarkGrey", "ForestGreen", "Brown"]

        soundFilePath = os.path.join(SoundsDir, SoundFileName)
        self.soundPlayer = RO.Wdg.SoundPlayer(soundFilePath)

        self.sopModel = TUI.Models.getModel("sop")
        self.apogeeModel = TUI.Models.getModel("apogee")

        self.alertTime = 5.0  # min
        self.alert = True
        self.name=" APOGEE Timer: "

        sr.master.winfo_toplevel().wm_resizable(True, True)
        F1 = Tkinter.Frame(sr.master)
        gr = RO.Wdg.Gridder(F1)
        F1.grid(row=0, column=0, sticky="ns")
        self.labWdg = RO.Wdg.Label(master=F1, text =self.name, fg=self.fgList[0])
        self.labWdg.grid(row=0, column=0, sticky="ew")
        self.checkWdg = RO.Wdg.Checkbutton(master=F1, text = "", defValue=True, helpText ="Play sound",)
        self.checkWdg.grid(row=0, column=1, sticky="ew")
        self.expTimer = RO.Wdg.ProgressBar(master = sr.master, valueFormat = "%4.1f", label = None, )
        self.expTimer.grid(row=1, column=0, sticky="ew")
        sr.master.rowconfigure(0, weight=1)
        sr.master.rowconfigure(1, weight=1)
        sr.master.columnconfigure(0, weight=1)

        self.record()
        self.sopModel.doApogeeScience_sequenceState.addCallback(self.seqState,callNow=False)
        self.sopModel.doApogeeScienceState.addCallback(self.sopState,callNow=False)
        self.apogeeModel.utrReadState.addCallback(self.utrState,callNow=False)

    def sopState (self, keyVar):
        if not keyVar.isGenuine: return
        self.record()

    def seqState(self, keyVar):
        if not keyVar.isGenuine: return
        self.record()

    def utrState(self, keyVar):
        if not keyVar.isGenuine: return
        if keyVar[1] == "Done":
            self.record()

    def setNone(self, state):
        self.labWdg.set("%s  %s " % (self.name,state))
        self.expTimer.setValue(newValue=0.0, newMin=0.0, newMax=0.0001)
        self.labWdg.config(fg=self.fgList[0])
        return

    def record(self,):
        self.state=self.sopModel.doApogeeScienceState[0]
        if self.state!='running':
            self.setNone(self.state)
            return

        #sop
        self.sq, self.indState = self.sopModel.doApogeeScience_sequenceState[0:2]
        self.seqCount = self.sopModel.doApogeeScience_seqCount[0]
        self.sopExp = self.sopModel.doApogeeScience_expTime[0] / 60.0
        self.sqTotal = len(self.sq) * self.sopExp
        self.sqOver = (self.indState) * self.sopExp

        #apogee
        self.utr2, self.utr3 =self.apogeeModel.utrReadState[2:4]
        self.utrExp=self.apogeeModel.utrReadTime[0]/60.
        self.utrTotal=self.utr3*self.utrExp
        self.utrOver=self.utr2*self.utrExp

        # total time estimation
        if self.sqTotal > self.sqOver:
            total = self.sqTotal
            self.timeLeft = self.sqTotal - self.sqOver - self.utrOver
        else:
            total = self.utrTotal
            self.timeLeft = self.utrTotal - self.utrOver
        self.labWdg.set("%s %5.1f min " % (self.name,self.timeLeft))
        if self.timeLeft > self.alertTime:
           self.alert = True
           fgInd = 1
        elif 0 < self.timeLeft <= self.alertTime:
            if self.alert and  self.checkWdg.getBool():
                self.soundPlayer.play()
                self.soundPlayer.play();
            self.alert = False
            fgInd = 2;
        else:
            fgInd = 0
        self.labWdg.config(fg=self.fgList[fgInd])
        self.expTimer.setValue(newValue=self.timeLeft, newMin=0, newMax=total)
        return

    def run(self, sr):
        self.record()

    def end(self, sr):
        pass
      #  self.sopModel.doApogeeScience_sequenceState.removeCallback(self.seqState)
      #  self.apogeeModel.utrReadState.removeCallback(self.utrState)

#    Key("doApogeeScience_expTime", Float(help="exposure time", units="sec"), Float(help="default", units="sec")),
#    Key("doApogeeScience_sequenceState", String(help="full exposure sequence. Basically ditherSeq * seqCount"),
#        Int(help="index of running exposure")),

