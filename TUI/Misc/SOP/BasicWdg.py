import itertools
import time
import Tkinter
import RO.Alg
import RO.Astro.Tm
import RO.PhysConst
import RO.AddCallback
import TUI.Models
import opscore.actor

StateWidth = 10
CommandNameWidth = 12
StageNameWidth = 10

class TimerWdg(Tkinter.Frame):
    """A thin wrapper around RO.Wdg.TimeBar that hides itself when necessary
    """
    def __init__(self, master):
        Tkinter.Frame.__init__(master)
        self._timerWdg = RO.Wdg.TimeBar(
            master = self,
            countUp = False,
        )
        self._timerWdg.grid(row=0, column=0)
    
    def setTime(self, startTime=0, totDuration=0):
        """Run or hide the countdown timer
        
        Inputs:
        - startTime: predicted start time (TAI, MJD seconds); 0 = now
        - totDuration: total predicted duration of timer (sec); 0 = hide timer
        """
        if totDuration <= 0:
            self._timerWdg.grid_withdraw()
            self._timerWdg.clear()
        else:
            if startTime == 0:
                remTime = totDuration
            else:
                currTime = RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay
                remTime = currTime - startTime
            self._timerWdg.start(
                newMax = totDuration,
                value = remTime,
            )
            self._timerWdg.grid()

    def clear(self):
        """Clear and hide the timer widget
        """
        self.setTime(0, 0)


# class KeywordRouter(object):
#     """Route keywords to the correct object
#     """
#     def __init__(self):
#         self.sopModel = TUI.Models.getModel("sop")
#         self.commandStateDict = RO.Alg.ListDict()
#         self.stageStateDict = RO.Alg.ListDict()
#         self.taskStateDict = RO.Alg.ListDict()
#         self.sopModel.commandState.addCallback(self.commandStateCallback)
#         self.sopModel.stageState.addCallback(self.stageStateCallback)
#         try:
#             self.sopModel.taskState.addCallback(self.taskStateCallback)
#         except:
#             print "Warning: no taskState keyword in sop model yet"
# 
#     def registerCommandWdgSet(self, name, callFunc):
#         """Register a command
#         """
#         self.commandStateDict[name] = callFunc
# 
#     def registerStateWdgSet(self, name, callFunc):
#         self.stageStateDict[name] = callFunc
#         
#     def registerTask(self, name, callFunc):
#         self.taskStateDict[name] = callFunc
#     
#     def commandStateCallback(self, keyVar):
#         callFuncList = self.commandStateDict.get(keyVar[0], ())
#         for callFunc in callFuncList:
#             callFunc(keyVar)
# 
#     def stageStateCallback(self, keyVar):
#         callFuncList = self.stageStateDict.get(keyVar[0], ())
#         for callFunc in callFuncList:
#             callFunc(keyVar)
# 
#     def taskStateCallback(self, keyVar):
#         callFuncList = self.taskStateDict.get(keyVar[0], ())
#         for callFunc in callFuncList:
#             callFunc(keyVar)

class ItemState(RO.AddCallback.BaseMixin):
    """Keep track of the state of an item
    
    Callback functions are called when the state changes.
    """
    DoneStates = set(("aborted", "done", "failed", "idle", "off"))
    FailedStates = set(("aborted", "failed"))
    ErrorStates = FailedStates
    RunningStates = set(("starting", "prepping", "running"))
    DisabledStates = set(("off",))
    ValidStates = set((None,)) | DoneStates | FailedStates | ErrorStates | RunningStates | DisabledStates
    def __init__(self, name="", callFunc=None, callNow=False):
        """Constructor
        """
        self.name = name
        self.state = None
        RO.AddCallback.BaseMixin.__init__(self, callFunc=callFunc, callNow=callNow)

    @property
    def didFail(self):
        """Did this stage of the sop command fail?
        """
        return self.state in self.FailedStates

    @property
    def isDone(self):
        """Is this object finished (whether successfully or not)?
        """
        return self.state in self.DoneStates

    @property
    def isRunning(self):
        """Is this object running normally?
        """
        return self.state in self.RunningStates

    def _setState(self, state):
        """Set the state of this item
        
        Inputs:
        - state: desired state for object
        
        @raise RuntimeError if called after state is done
        """
        print "%s._setState(state=%r)" % (self, state)
        if self.isDone:
            raise RuntimeError("%s already done; cannot set state to %s" % (self, state))
        self.state = state

        self._doCallbacks()

        if self.isDone:
            self._removeAllCallbacks()

    def __str__(self):
        return "State(name=%s, state=%s)" % (self.name, self.state)


class ItemStateWdgSet(ItemState, RO.AddCallback.BaseMixin):
    """Widget showing state of SOP command, stage, or parameter
    
    Subclasses must override:
    enableWdg
    and must grid or pack:
    self.stateWdg
    plus any other widgets it wants
    """
    def __init__(self, master, name, dispName, callFunc=None, helpURL=None):
        """Constructor
        
        Inputs:
        - master: master widget for stateWdg
        - name: name of command, stage or parameter as known by sop (full dotted notation)
        - dispName: displayed name (text for control widget); if None then use last field of name
        - callFunc: callback function for state changes
        - helpURL: URL of help file
        """
        ItemState.__init__(self, name=name)
        RO.AddCallback.BaseMixin.__init__(self)

        self.name = name
        self.dispName = dispName
        self.helpURL = helpURL
        
        self.stateWdg = RO.Wdg.StrLabel(
            master = master,
            width = StateWidth,
            anchor = "w",
            helpText = "State of %s" % (self,),
            helpURL = self.helpURL,
        )

        if callFunc:
            self.addCallback(callFunc, callNow=False)

    def enableWdg(self):
        """Enable widget based on current state
        """
        raise RuntimeError("Must subclass")

    @property
    def isCurrent(self):
        """Does the state of the control widget match the state of the sop command?
        
        The result may not be meaningful if the command is not running.
        """
        isEnabledInSop = self.state not in self.DisabledStates
        return self.controlWdg.getBool() == isEnabledInSop

    @property
    def isDefault(self):
        """Is the control widget set to its default state?
        """
        return self.controlWdg.isDefault()

    def setState(self, state, isCurrent=True):
        """Set the state of this item
        
        Inputs:
        - state: desired state for object
        - text: new text; if None then left unchanged
        
        @raise RuntimeError if called after state is done
        """
        ItemState._setState(self, state)

        if state in self.ErrorStates:
            severity = RO.Constants.sevError
        else:
            severity = RO.Constants.sevNormal

        
        if self.state == None:
            dispState = None
        else:
            dispState = self.state.title()
        self.stateWdg.set(dispState, severity = severity, isCurrent = isCurrent)
        
        self.enableWdg()

    def __str__(self):
        return self.name


class CommandWdg(Tkinter.Frame, ItemStateWdgSet):
    """SOP command widget
    """
    def __init__(self,
        master,
        commandDescr,
        statusBar,
        callFunc = None,
        helpURL = None,
    ):
        """Create a CommandWdg
        
        Inputs: same as ItemStateWdgSet plus:
        - commandDescr: a CommandDescr object describing the command and its stages and parameters
        - statusBar: status bar widget
        """
        Tkinter.Frame.__init__(self, master)
        ItemStateWdgSet.__init__(self,
            master = self,
            name = commandDescr.baseName,
            dispName = commandDescr.dispName,
            callFunc = callFunc,
            helpURL = helpURL,
        )
        self.statusBar = statusBar
        self.actor = commandDescr.actor
        # dictionary of known stages: stage base name: stage
        self.stageDict = dict()
        # ordered dictionary of visible stages: stage base name: stage
        self.visibleStageODict = RO.Alg.OrderedDict()

        self.sopModel = TUI.Models.getModel("sop")
        
        self.stateWdg.grid(row=0, column=0, sticky="w")
        self.commandFrame = Tkinter.Frame(self)
        self.commandFrame.grid(row=0, column=1, columnspan=2, sticky="w")
        self._makeCmdWdg()
        
        self.stageFrame = Tkinter.Frame(self)
        self.stageFrame.grid(row=1, column=0, columnspan=2, sticky="w")
        self.paramFrame = Tkinter.Frame(self)
        self.paramFrame.grid(row=1, column=1, sticky="w")

        for stageDescr in commandDescr.descrList:
            stage = StageWdg(
                master = self.stageFrame,
                paramMaster = self.paramFrame,
                stageDescr = stageDescr,
            )
            self.stageDict[stage.name] = stage

        commandStateKeyVar = getattr(self.sopModel, "%sState" % (self.name,))
        commandStateKeyVar.addCallback(self._commandStateCallback)
        commandStagesKeyVar = getattr(self.sopModel, "%sStages" % (self.name,))
        commandStagesKeyVar.addCallback(self._commandStagesCallback)

    def _makeCmdWdg(self):
        self.nameWdg = RO.Wdg.StrLabel(
            master = self.commandFrame,
            text = self.dispName,
            width = CommandNameWidth,
            anchor = "w",
            helpText = "%s command" % (self.name,),
            helpURL = self.helpURL,
        )
        self.nameWdg.pack(side="left")
        
        self.startBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Start",
            callFunc = self.doStart,
            helpText = "Start %s command" % (self.name,),
            helpURL = self.helpURL,
        )
        self.startBtn.pack(side="left")

        self.modifyBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Modify",
            callFunc = self.doStart,
            helpText = "Modify %s command" % (self.name,),
            helpURL = self.helpURL,
        )
        self.modifyBtn.pack(side="left")

        self.abortBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "X",
            callFunc = self.doAbort,
            helpText = "Abort %s command" % (self.name,),
            helpURL = self.helpURL,
        )
        self.abortBtn.pack(side="left")
        
        self.currentBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Current",
            callFunc = self.restoreCurrent,
            helpText = "Restore current stages and parameters",
            helpURL = self.helpURL,
        )
        self.currentBtn.pack(side="left")
        
        self.defaultBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Default",
            callFunc = self.restoreDefault,
            helpText = "Restore default stages and parameters",
            helpURL = self.helpURL,
        )
        self.defaultBtn.pack(side="left")

    def doAbort(self, wdg=None):
        """Abort the command
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = self.actor,
            cmdStr = "%s abort" % (self.name,),
            callFunc = self.enableWdg,
        )

    def doStart(self, wdg=None):
        """Start or modify the command
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = self.actor,
            cmdStr = self.getCmdStr(),
            callFunc = self.enableWdg,
        )
        wdg.setEnable(False)

    def enableWdg(self, dumSelf=None):
        """Enable widgets according to current state
        """
        isRunning = self.state in ("running",)
        self.abortBtn.setEnable(isRunning)
        self.startBtn.setEnable(self.isDone)
        isCurrent = isRunning # current values = value for current command; meaningless if no curr cmd
        isDefault = True
        for stage in self.stageDict.itervalues():
            if not stage.isCurrent:
                isCurrent = False
            if not stage.isDefault:
                isDefault = False
        self.defaultBtn.setEnable(not isDefault)
        self.currentBtn.setEnable(not isCurrent)

    def getCmdStr(self):
        """Return the command string for the current settings
        """
        cmdStrList = [self.name]
        for stage in self.visibleStageODict.itervalues():
            cmdStrList.append(stage.getCmdStr)
        return " ".join(cmdStrList)        

    def restoreDefault(self, dumWdg=None):
        """Restore default stages and parameters
        """
        for stage in self.stageDict.itervalues():
            stage.restoreDefault()

    def restoreCurrent(self, dumWdg=None):
        """Restore current parameters
        
        WARNING: it may be better to restore defaults for hidden stages,
        or restore defaults for all, then restore current afterwards.
        On the other hand, maybe that's what restoreCurrent should do anyway.
        """
        for stage in self.stageDict.itervalues():
            stage.restoreCurrent()

    def _commandStagesCallback(self, keyVar):
        """<command>Stages keyword callback
        
        If the list of visible stages changes then regrid all stages and parameters,
        reset all stages and their parameters to default values
        """
        print "_commandStagesCallback(keyVar=%s)" % (keyVar,)
        newVisibleStageNameList = keyVar[:]
        if not newVisibleStageNameList or None in newVisibleStageNameList:
            return
        if list(self.visibleStageODict.keys()) == newVisibleStageNameList:
            return

        newVisibleStageNameSet = set(newVisibleStageNameList)
        unknownNameSet = newVisibleStageNameSet - set(self.stageDict.keys())
        if unknownNameSet:
            unknownNameList = [str(unk) for unk in unknownNameSet]
            raise RuntimeError("%s contains unknown stages %s" % (keyVar, unknownNameList))

        # withdraw all stages and their parameters
        # and set all stages and parameters to default values
        for stage in self.stageDict.itervalues():
            stage.grid_forget()
            for param in stage.paramList:
                param.grid_forget()
            stage.removeCallback(self.enableWdg, doRaise=False)
            stage.restoreDefault()
        
        # grid visible stages (unless there is only one) and update visibleStageODict
        self.visibleStageODict.clear()
        stageRow = 0
        paramRow = 0
        for stageName in newVisibleStageNameList:
            stage = self.stageDict[stageName]
            if len(newVisibleStageNameList) != 1:
                stage.grid(row=stageRow, column=0, sticky="w")
            stageRow += 1
            for param in stage.paramList:
                param.grid(row=paramRow, column=0, sticky="w")
                paramRow += 1
            self.visibleStageODict[stageName] = stage
            stage.addCallback(self.enableWdg)

    def _commandStateCallback(self, keyVar):
        """<command>State keyword callback

        as of 2010-05-18:
        Key("<command>State",
           String("commandName", help="the name of the sop command"),
           Enum('idle','running','done','failed',
                help="state of the entire command"),
           Enum('idle','off','pending','running','done','failed', 'aborted'
                help="state of all the individual stages of this command...")*(1,6)),
        """
        print "_commandStateCallback(keyVar=%s)" % (keyVar,)
        self.setState(
            state=keyVar[0],
            isCurrent = keyVar.isCurrent,
        )
        stageStateList = keyVar[1:]
        
        if len(self.visibleStageODict) != len(stageStateList):
            # invalid state data; this can happen for two reasons:
            # - have not yet connected; keyVar values are [None, None]; accept this silently
            # - invalid data; raise an exception
            # in either case null all stage stages since we don't know what they are
            for stage in self.stageDict.itervalues():
                stage.setState(
                    state = None,
                    isCurrent = False,
                )
  
            if None in stageStateList:
                return
            else:
                # log an error message to the status panel? but for now...
                raise RuntimeError("Wrong number of stage states for %s; got %d; expected %d" % 
                    (keyVar.name, len(self.visibleStageODict), len(stageStateList)))

        for stage, stageState in itertools.izip(self.visibleStageODict.itervalues(), stageStateList):
            stage.setState(
                state = stageState,
                isCurrent = keyVar.isCurrent,
            )

    def __str__(self):
        return "%s command" % (self.dispName,)

class StageWdg(Tkinter.Frame, ItemStateWdgSet):
    """An object representing a SOP command stage
    """
    def __init__(self, master, paramMaster, stageDescr, callFunc=None, helpURL=None):
        """Constructor
        
        Inputs: same as ItemStateWdgSet plus:
        - master: master widget for the stage widget
        - paramMaster: master widget for parameter widgets
        - stageDescr: a StageDescr object describing the stage and its parameters
        """
        Tkinter.Frame.__init__(self, master)
        ItemStateWdgSet.__init__(self,
            master = self,
            name = stageDescr.baseName,
            dispName = stageDescr.dispName,
            callFunc = callFunc,
            helpURL = helpURL,
        )
        self.defEnabled = stageDescr.defEnabled

# NEED ParamWdg and code to create them here
        self.paramList = []
        for paramDescr in stageDescr.descrList:
            print "Should add param %s" % (paramDescr.fullName)

        self.controlWdg = RO.Wdg.Checkbutton(
            master = self,
            callFunc = self._controlWdgCallback,
            text = self.dispName,
            defValue = self.defEnabled,
            helpText = "Enable/disable %s stage" % (self.name,),
            helpURL = self.helpURL,
        )

        self.stateWdg.grid(row=0, column=0, sticky="w")
        self.controlWdg.grid(row=0, column=1, sticky="w")

    def _controlWdgCallback(self, controlWdg=None):
        """Control widget callback
        """
        doEnable = self.controlWdg.getBool()
        self.controlWdg.setIsCurrent(self.isCurrent)
        for param in self.paramList:
            param.enableWdg(doEnable)

    def enableWdg(self, dumSelf=None):
        """Enable widgets according to current state
        """
        pass

    def restoreDefault(self, dumWdg=None):
        """Restore control widget and parameters to their default state.
        """
        self.controlWdg.restoreDefault()
        for param in self.paramList:
            param.restoreDefault()

    def restoreCurrent(self, dumWdg=None):        
        """Restore control widget and parameters to match the currently running command.
        
        Meaningless if command is not running.
        """
        print "implement restoreCurrent for stages!"


    def __str__(self):
        return "%s stage" % (self.dispName,)
