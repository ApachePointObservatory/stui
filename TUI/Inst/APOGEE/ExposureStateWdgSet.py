#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-04-04 ROwen    Prerelease test code
2011-04-28 ROwen    Modified for new keyword dictionary.
2011-05-02 ROwen    Modified to ignore data for older reads. This makes the countdown timer work better.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models

_EnvWidth = 6 # width of environment value columns

class ExposureStateWdgSet(object):
    EnvironCat = "environ"
    def __init__(self, gridder, helpURL=None):
        """Create a status widget
        """
        master = gridder._master
        
        self.model = TUI.Models.getModel("apogee")
        self.currReadNum = -1

        self.expStateWdg = RO.Wdg.StrLabel(
            master = master,
            helpText = "Status of current exposure",
            helpURL = helpURL,
            anchor="w",
            width = 35, # wide enough for a long object type and also reserves space for read timer
        )
        gridder.gridWdg("Exp Status", self.expStateWdg)
        
        stateFrame = Tkinter.Frame(master)
        self.readStateWdg = RO.Wdg.StrLabel(
            master = stateFrame,
            helpText = "Status of current up-the-ramp read",
            helpURL = helpURL,
            anchor="w",
#            width = 23, # room for "Reading 99 of 99: 60 sec"
        )
        self.readStateWdg.grid(row=0, column=0)
        self.readTimer = RO.Wdg.TimeBar(
            master = stateFrame,
            valueFormat = "%3.1f sec",
            isHorizontal = True,
            autoStop = True,
            countUp = True,
            helpText = "Status of current exposure",
            helpURL = helpURL,
        )
        self.readTimer.grid(row=0, column=1, sticky="ew")
        stateFrame.grid_columnconfigure(1, weight=1)
        gridder.gridWdg("UTR Read", stateFrame, sticky="ew")

        self.model.exposureState.addCallback(self._exposureStateCallback)
        self.model.utrReadState.addCallback(self._utrReadStateCallback)
    
    def _exposureStateCallback(self, keyVar):
        """exposureState keyVar callback

        Key("exposureState",
            Enum("Exposing", "Done", "Stopping", "Stopped", "Failed", name="expState", help="state of exposure"),
            String(name="expType", help="type of exposure (object argument)"),
            Int(name="nReads", help="total number of UTR reads requested"),
            String(name="expName", help="name of exposure"),
        ),
        """
        if keyVar[0] == None:
            stateStr = "?"
            self.currReadNum = -1
        else:
            if keyVar[0] != "Stopping":
                self.currReadNum = -1
            stateStr = "%s %s %s" % (keyVar[0], keyVar[1], keyVar[3])
        self.expStateWdg.set(stateStr, isCurrent=keyVar.isCurrent)
    
    def _utrReadStateCallback(self, keyVar):
        """utrReadState keyVar callback

        Key("utrReadState",
            String(name="expName", help="name of exposure"),
            Enum("Reading", "Saving", "Done", "Failed", name="readState", help="state of UTR read"),
            Int(name="readNum", help="number of current UTR read, starting from 1"),
            Int(name="nReads", help="total number of UTR reads requested"),
        ),
        Key("utrReadTime", Float(units="sec"), help="time required for a UTR read"),
        
        Warning: reads are inter-threaded. When read n is done Reading
        read n+1 reports Reading before read n reports Saving and Done or Failed.
        Users mostly care about the current read so once I see data for a new read
        I ignore data for older reads. That way the countdown timer works!
        """
        if None in keyVar[0:3]:
            stateStr = "?"
            isReading = False
        elif keyVar[2] < self.currReadNum:
            # data about an old read; ignore it
            return
        else:
            self.currReadNum = keyVar[2]
            stateStr = "%s %d of %d" % (keyVar[1], keyVar[2], keyVar[3])
            isReading = keyVar[1].lower() == "reading"
        readTime = self.model.utrReadTime[0]
        if isReading and readTime != None:
            stateStr += ": %d sec" % (readTime,)
            self.readTimer.grid()
            self.readTimer.start(newMax=readTime)
        else:
            self.readTimer.grid_remove()
        self.readStateWdg.set(stateStr, isCurrent=keyVar.isCurrent)


if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = Tkinter.Frame(root)
    gridder = RO.Wdg.Gridder(testFrame)
    expStateWdg = ExposureStateWdgSet(gridder)
    testFrame.pack(side="top", expand=True)
    
    statusBar = TUI.Base.Wdg.StatusBar(root)
    statusBar.pack(side="top", expand=True, fill="x")

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
