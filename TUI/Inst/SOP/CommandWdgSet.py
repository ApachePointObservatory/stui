"""
TO DO: 
- Indent stage status and controls a bit from commands
"""
import itertools
import re
import time
import Tkinter
import opscore.actor
import RO.Alg
import RO.Astro.Tm
import RO.PhysConst
import RO.AddCallback
import TUI.Models

DefStateWidth = 10
CommandNameWidth = 12
StageNameWidth = 10

class TimerWdg(Tkinter.Frame):
    """A thin wrapper around RO.Wdg.TimeBar that hides itself when necessary
    
    This is not needed for commands or stages. It *may* be wanted for parameters
    and is likely to be wanted for tasks (which will be handled in a different file).
    Meanwhile keep it around...
    """
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)
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


class CmdInfo(object):
    def __init__(self, cmdVar=None, wdg=None):
        self.cmdVar = cmdVar
        self.wdg = wdg
    
    def abort(self):
        if self.cmdVar:
            self.cmdVar.abort()

    @property
    def isDone(self):
        return (not self.cmdVar) or self.cmdVar.isDone

    @property
    def didFail(self):
        return (not self.cmdVar) or self.cmdVar.didFail

    @property
    def isRunning(self):
        return bool(self.cmdVar) and not self.cmdVar.isDone

    def disableIfRunning(self):
        if self.isRunning:
            self.wdg.setEnable(False)


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
        """
#        print "%s._setState(state=%r)" % (self, state)
        self.state = state

        self._doCallbacks()

    def __str__(self):
        return "ItemState(name=%s, state=%s)" % (self.name, self.state)


class ItemWdgSet(ItemState, RO.AddCallback.BaseMixin):
    """Widget showing state of SOP command, stage, or parameter
    
    Subclasses must override:
    enableWdg
    and must grid or pack:
    self.stateWdg
    plus any other widgets it wants
    
    Useful fields:
    - name: name of command, stage or parameter as used in sop commands
    - fullName: full dotted name (command.stage.parameter)
    - dispName: display name
    """
    def __init__(self, name, dispName=None):
        """Construct a partial ItemStateWdg. Call build to finish the job.
        
        Inputs:
        - name: name of command, stage or parameter as used in sop commands
        - dispName: displayed name (text for control widget); if None then use name
            with a space inserted before each run of capital letters (at least approx.)
        """
        ItemState.__init__(self, name=name, callFunc=self.enableWdg)
        RO.AddCallback.BaseMixin.__init__(self)

        self.name = name
        if dispName == None:
            dispName = (" ".join(val for val in re.split("([A-Z]+[a-z]*)", name) if val)).title()
        self.dispName = dispName
        self.stateWdg = None

    def build(self, master, typeName, stateWidth=DefStateWidth, callFunc=None, helpURL=None):
        """Finish building the widget, including constructing wdgSet.
        
        Warning: must call before using the object!
        
        Inputs:
        - master: master widget for stateWdg
        - typeName: one of "command", "stage" or "parameter"; used for stateWdg's help string
        - stateWidth: width of state widget
        - callFunc: callback function for state changes
        - helpURL: URL of help file
        """
        if self.stateWdg:
            raise RuntimeError("%r.build called after built" % (self,))

        self.stateWdg = RO.Wdg.StrLabel(
            master = master,
            width = stateWidth,
            anchor = "w",
            helpText = "State of %s %s" % (self.dispName, typeName,),
            helpURL = helpURL,
        )

        if callFunc:
            self.addCallback(callFunc, callNow=False)

    def enableWdg(self, dumWdg=None):
        """Enable widget based on current state
        
        If only CommandWdgSet wants this, then probably better to make it
        a callback function that Command explicitly issues.
        """
        pass

    @property
    def isCurrent(self):
        """Does the state of the control widget match the state of the sop command?
        """
        raise RuntimeError("Must subclass")
        return self.controlWdg.getIsCurrent()

    @property
    def isDefault(self):
        """Is the control widget set to its default state?
        """
        raise RuntimeError("Must subclass")

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
        return "%s(%r)" % (type(self).__name__, self.dispName,)


class CommandWdgSet(ItemWdgSet):
    """SOP command widget
    
    Useful fields (in addition to those listed for ItemWdgSet):
    - self.wdg: the command widget, including all sub-widgets
    """
    def __init__(self, name, dispName=None, stageList=(), actor="sop", canAbort=True, abortCmdStr=None):
        """Construct a partial CommandWdgSet. Call build to finish the job.
        
        Inputs:
        - name: name of command, stage or parameter as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - stageList: a list of zero or more stage objects
        - actor: name of actor to which to send commands
        - canAbort: if True then command can be aborted
        - abortCmdStr: command string to abort command; if None then the default "name abort" is used
        """
        ItemWdgSet.__init__(self,
            name = name,
            dispName = dispName,
        )
        self.actor = actor
        self.canAbort = bool(canAbort)
        if self.canAbort and abortCmdStr == None:
            abortCmdStr = "%s abort" % (self.name,)
        self.abortCmdStr = abortCmdStr

        # set stageDict = dictionary of known stages: stage base name: stage
        # and set fullName and actor parameter of all stages and parameters
        self.stageDict = dict()
        for stage in stageList:
            self.stageDict[stage.name] = stage
            stage.fullName = "%s.%s" % (self.name, stage.name)
            stage.actor = self.actor
            for parameter in stage.parameterList:
                parameter.fullName = "%s.%s" % (self.name, parameter.name)
                parameter.actor = self.actor

        # ordered dictionary of visible stages: stage base name: stage
        self.visibleStageODict = RO.Alg.OrderedDict()
        self.currCmdInfo = CmdInfo()
        
    def build(self, master, statusBar, callFunc=None, helpURL=None):
        """Finish building the widget, including stage and parameter widgets.
        
        Warning: must call before using the object!
        
        Inputs:
        - master: master widget for stateWdg
        - statusBar: status bar widget
        - callFunc: callback function for state changes
        - helpURL: URL of help file
        """
        self.wdg = Tkinter.Frame(master, borderwidth=1, relief="ridge")
        
        ItemWdgSet.build(self, master=self.wdg, typeName="command", callFunc=callFunc)

        self.statusBar = statusBar
        
        self.stateWdg.grid(row=0, column=0, sticky="w")
        self.commandFrame = Tkinter.Frame(self.wdg)
        self.commandFrame.grid(row=0, column=1, columnspan=3, sticky="w")
        self._makeCmdWdg(helpURL)
        
        self.stageFrame = Tkinter.Frame(self.wdg)
        self.stageFrame.grid(row=1, column=0, columnspan=2, sticky="w")
        self.paramFrame = Tkinter.Frame(self.wdg)
        self.paramFrame.grid(row=1, column=2, columnspan=2, sticky="w")
        self.wdg.grid_columnconfigure(3, weight=1)

        for stage in self.stageDict.itervalues():
            stage.build(
                master = self.stageFrame,
                paramMaster = self.paramFrame,
                callFunc = self.enableWdg,
            )

        # If there is only one stage (or no stages) then grid it now.
        # Otherwise wait until we see the <name>Stages keyword and grid the specified stages
        # (which may not be all of them) in the specified order.
        if len(self.stageDict) < 2:
            # there is only one stage; display it and ignore the <name>Stages keyword
            self._gridStages(self.stageDict.keys(), isFirst=True)

        if self.actor == "sop":
            sopModel = TUI.Models.getModel("sop")
            commandStateKeyVar = getattr(sopModel, "%sState" % (self.name,))
            commandStateKeyVar.addCallback(self._commandStateCallback)
            if len(self.stageDict) > 1:
                # multiple stages; pay attention to which ones sop says to use
                commandStagesKeyVar = getattr(sopModel, "%sStages" % (self.name,))
                commandStagesKeyVar.addCallback(self._commandStagesCallback)

    def doAbort(self, wdg=None):
        """Abort the command
        """
        if not self.currCmdInfo.isDone:
            self.currCmdInfo.abort()
        elif self.isRunning and self.canAbort:
            self.doCmd(cmdStr=self.abortCmdStr, wdg=wdg)

    def doStart(self, wdg=None):
        """Start or modify the command
        """
        self.doCmd(cmdStr=self.getCmdStr(), wdg=wdg)

    def doCmd(self, cmdStr, wdg=None, **keyArgs):
        """Run the specified command
        
        Inputs:
        - cmdStr: command string
        - wdg: widget that started the command (to disable it while the command runs)
        **keyArgs: all other keyword arguments are used to construct opscore.actor.keyvar.CmdVar
        """
        if self.canAbort and cmdStr != self.abortCmdStr:
            keyArgs.setdefault("abortCmdStr", self.abortCmdStr)
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = self.actor,
            cmdStr = cmdStr,
            callFunc = self.enableWdg,
        **keyArgs)
        self.statusBar.doCmd(cmdVar)
        self.currCmdInfo = CmdInfo(cmdVar, wdg)
        self.enableWdg()

    def enableWdg(self, dumWdg=None):
        """Enable widgets according to current state
        """
        self.startBtn.setEnable(self.isDone or self.state == None)
        
        # can modify if not current and sop is running this command
        canModify = not self.isCurrent and self.isRunning
        self.modifyBtn.setEnable(canModify)

        # can abort this sop is running this command or if I have a running cmdVar for sop
        canAbort = self.isRunning or (not self.currCmdInfo.isDone)
        self.abortBtn.setEnable(canAbort)

        self.defaultBtn.setEnable(not self.isDefault)
        self.currentBtn.setEnable(not self.isCurrent)
        self.currCmdInfo.disableIfRunning()

    def getCmdStr(self):
        """Return the command string for the current settings
        """
        cmdStrList = [self.name]
        for stage in self.visibleStageODict.itervalues():
            cmdStrList.append(stage.getCmdStr())
        return " ".join(cmdStrList)        

    @property
    def isCurrent(self):
        """Does the state of the control widgets match the state of the sop command?
        """
        for stage in self.visibleStageODict.itervalues():
            if not stage.isCurrent:
#                print "%s.isCurrent False because %s.isCurrent False" % (self, stage)
                return False
#        print "%s.isCurrent True" % (self,)
        return True

    @property
    def isDefault(self):
        """Is the control widget set to its default state?
        """
        for stage in self.visibleStageODict.itervalues():
            if not stage.isDefault:
#                print "%s.isDefault False because %s.isDefault False" % (self, stage)
                return False
#        print "%s.isDefault True" % (self,)
        return True

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
        """Callback for <command>Stages keyword
        
        If the list of visible stages changes then regrid all stages and parameters,
        reset all stages and their parameters to default values
        """
#         print "_commandStagesCallback(keyVar=%s)" % (keyVar,)
        visibleStageNameList = keyVar[:]
        if not visibleStageNameList or None in visibleStageNameList:
            return
        
        self._gridStages(visibleStageNameList)

    def _commandStateCallback(self, keyVar):
        """Callback for <command>State keyword

        as of 2010-05-18:
        Key("<command>State",
           Enum('idle',                'running','done','failed','aborted',
                help="state of the entire command"),
           String(help="possibly useful text"),
           Enum('idle','off','pending','running','done','failed','aborted'
                help="state of all the individual stages of this command...")*(1,6)),
        """
#         print "_commandStateCallback(keyVar=%s)" % (keyVar,)
        
        # set state of the command
        self.setState(
            state=keyVar[0],
            isCurrent = keyVar.isCurrent,
        )
        
        # set state of the command's stages
        stageStateList = keyVar[2:]
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
                raise RuntimeError("Wrong number of stage states for %s; expected %d; got %d" % 
                    (keyVar.name, len(self.visibleStageODict), len(stageStateList)))

        for stage, stageState in itertools.izip(self.visibleStageODict.itervalues(), stageStateList):
            stage.setState(
                state = stageState,
                isCurrent = keyVar.isCurrent,
            )

    def _gridStages(self, visibleStageNameList, isFirst=False):
        """Grid the specified stages in the specified order
        """
#        print "%s._gridStages(%s)" % (self, visibleStageNameList)
        if (list(self.visibleStageODict.keys()) == visibleStageNameList) and not isFirst:
            return

        newVisibleStageNameSet = set(visibleStageNameList)
        unknownNameSet = newVisibleStageNameSet - set(self.stageDict.keys())
        if unknownNameSet:
            unknownNameList = [str(unk) for unk in unknownNameSet]
            raise RuntimeError("%s contains unknown stages %s" % (keyVar, unknownNameList))

        # withdraw all stages and their parameters
        for stage in self.stageDict.itervalues():
            stage.stateWdg.grid_forget()
            stage.controlWdg.grid_forget()
            for param in stage.parameterList:
                param.gridForgetWdg()
            stage.removeCallback(self.enableWdg, doRaise=False)
        
        # grid visible stages (unless there is 0 or 1) and update visibleStageODict
        hasParameters = False
        self.visibleStageODict.clear()
        stageRow = 0
        paramRow = 0
        for stageName in visibleStageNameList:
            stage = self.stageDict[stageName]
            if len(visibleStageNameList) > 1:
                stage.stateWdg.grid(row=stageRow, column=0, sticky="w")
                stage.controlWdg.grid(row=stageRow, column=1, sticky="w")
            stageRow += 1
            
            if stage.parameterList:
                hasParameters = True
            
            paramCol = 0
            for param in stage.parameterList:
                paramRow, paramCol = param.gridWdg(paramRow, paramCol)
            self.visibleStageODict[stageName] = stage
            stage.addCallback(self.enableWdg)
        
        hasAdjustments = hasParameters or len(self.visibleStageODict) > 1
        if hasAdjustments:
            self.currentBtn.grid()
            self.defaultBtn.grid()
        else:
            self.currentBtn.grid_remove()
            self.defaultBtn.grid_remove()
        if hasAdjustments and self.actor == "sop":
            self.modifyBtn.grid()
        else:            
            self.modifyBtn.grid_remove()

    def _makeCmdWdg(self, helpURL):
        col = 0

        self.startBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = self.dispName,
            callFunc = self.doStart,
            helpText = "Start %s command" % (self.name,),
            helpURL = helpURL,
        )
        self.startBtn.grid(row = 0, column = col)
        col += 1

        self.modifyBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Modify",
            callFunc = self.doStart,
            helpText = "Modify %s command" % (self.name,),
            helpURL = helpURL,
        )
        self.modifyBtn.grid(row = 0, column = col)
        col += 1

        self.abortBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "X",
            callFunc = self.doAbort,
            helpText = "Abort %s command" % (self.name,),
            helpURL = helpURL,
        )
        self.abortBtn.grid(row = 0, column = col)
        col += 1
        
        self.currentBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Current",
            callFunc = self.restoreCurrent,
            helpText = "Restore current stages and parameters",
            helpURL = helpURL,
        )
        self.currentBtn.grid(row = 0, column = col)
        col += 1
        
        self.defaultBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Default",
            callFunc = self.restoreDefault,
            helpText = "Restore default stages and parameters",
            helpURL = helpURL,
        )
        self.defaultBtn.grid(row = 0, column = col)
        col += 1


class StageWdgSet(ItemWdgSet):
    """An object representing a SOP command stage
    """
    def __init__(self, name, dispName=None, parameterList=(), defEnabled=True):
        """Construct a partial StageWdgSet. Call build to finish the job.
        
        Inputs:
        - name: name of stage, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - parameterList: a list of zero or more parameter objects
        - defEnabled: is stage enabled by default?
        """
        ItemWdgSet.__init__(self,
            name = name,
            dispName = dispName,
        )
        self.defEnabled = bool(defEnabled)

        self.parameterList = parameterList[:]

    def build(self, master, paramMaster, callFunc=None, helpURL=None):
        """Finish building the widget, including parameter widgets.
        
        Warning: must call before using the object!
        
        Inputs:
        - master: master widget for stateWdg
        - paramMaster: master widget for parameters
        - callFunc: callback function for state changes
        - helpURL: URL of help file
        
        self.stateWdg and self.controlWdg are the stage widgets
        self.parameterList contains a list of parameters (including parameter widgets).
        """
        ItemWdgSet.build(self, master=master, typeName="stage", callFunc=callFunc)

        self.controlWdg = RO.Wdg.Checkbutton(
            master = master,
            callFunc = self.enableWdg,
            text = self.dispName,
            autoIsCurrent = True,
            defValue = self.defEnabled,
            helpText = "Enable/disable %s stage" % (self.name,),
            helpURL = helpURL,
        )
        
        for param in self.parameterList:
            param.build(master=paramMaster, callFunc = self._parameterCallback, helpURL=helpURL)

    def getCmdStr(self):
        """Return the command string for the current settings
        """
        if not self.controlWdg.getBool():
            return "no" + self.name

        cmdStrList = []
        for param in self.parameterList:
            cmdStrList.append(param.getCmdStr())
        return " ".join(cmdStrList)

    @property
    def isCurrent(self):
        """Are the stage enabled checkbox and parameters the same as the current or most recent sop command?
        """
        if not self.controlWdg.getIsCurrent():
#             print "%s.isCurrent False because controlWdg.getIsCurrent False" % (self,)
            return False
        for param in self.parameterList:
#             print "Test %s.isCurrent" % (param,)
            if not param.isCurrent:
#                 print "%s.isCurrent False because %s.isCurrent False" % (self, param)
                return False
#         print "%s.isCurrent True" % (self,)
        return True

    @property
    def isDefault(self):
        """Are the stage enabled checkbox and parameters set to their default state?
        """
        if self.controlWdg.getBool() != self.defEnabled:
#             print "%s.isDefault False because controlWdg.getBool() != self.defEnabled" % (self,)
            return False
        for param in self.parameterList:
            if not param.isDefault:
#                 print "%s.isDefault False because %s.isDefault False" % (self, param)
                return False
#         print "%s.isDefault True" % (self,)
        return True

    def _parameterCallback(self, dumParameter=None):
        """Call when a parameter changes state.
        """
        self._doCallbacks()

    def restoreCurrent(self, dumWdg=None):        
        """Restore control widget and parameters to match the running or most recently run command
        """
        # the mechanism for tracking the current value uses the widget's default
        self.controlWdg.restoreDefault()
        for param in self.parameterList:
            param.restoreCurrent()

    def restoreDefault(self, dumWdg=None):
        """Restore control widget and parameters to their default state.
        """
        self.controlWdg.set(self.defEnabled)
        for param in self.parameterList:
            param.restoreDefault()

    def setState(self, state, isCurrent=True):
        ItemWdgSet.setState(self, state, isCurrent=isCurrent)
        
        if state != None:
            isEnabledInSOP = self.state not in self.DisabledStates
            self.controlWdg.setDefault(isEnabledInSOP)
#            print "%s setState set controlWdg default=%r" % (self, self.controlWdg.getDefBool())

    def enableWdg(self, controlWdg=None):
        """Enable widgets
        """
        doEnable = self.controlWdg.getBool()
        for param in self.parameterList:
            param.controlWdg.setEnable(doEnable)
        self._doCallbacks()


class BaseParameterWdgSet(ItemWdgSet):
    """An object representing a basic parameter for a SOP command stage
    
    Subclasses must override buildControlWdg and may want to override isDefault
    """
    def __init__(self, name, dispName=None, defValue=None, units=None, skipRows=0, startNewColumn=False):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - defValue: default value for parameter
        - units: units of parameter (a string); if provided then self.unitsWdg is set to
            an RO.Wdg.StrLabel containing the string; otherwise it is set to None
        - skipRows: number of rows to skip before displaying
        - startNewColumn: if True then display parameter in a new column (then skip skipRows before gridding)
        """
        ItemWdgSet.__init__(self,
            name = name,
            dispName = dispName,
        )
        self.defValue = defValue
        self.units = units
        self.skipRows = skipRows
        self.startNewColumn = startNewColumn
        self.stateWidth = DefStateWidth # subclasses can override in __init__(...) for use in build(...)
        # list of (widget, sticky, columnspan)
        self.wdgInfoList = []

    def build(self, master, callFunc=None, helpURL=None):
        """Finish building the widget, including constructing wdgSet.
        
        Warning: must call before using the object!
        
        Inputs:
        - master: master widget for stateWdg
        - callFunc: callback function for state changes
        - helpURL: URL of help file
        
        self.stateWdg and self.controlWdg are the stage widgets
        self.parameterList contains a list of parameters (including parameter widgets).
        """
        ItemWdgSet.build(self, master=master, typeName="parameter", stateWidth=self.stateWidth, callFunc=callFunc)

        if self.actor == "sop":
            sopModel = TUI.Models.getModel("sop")
            keyVarName = self.fullName.replace(".", "_")
            keyVar = getattr(sopModel, keyVarName).addCallback(self._keyVarCallback)

        self.stateWdg["anchor"] = "e"

        self.nameWdg = RO.Wdg.StrLabel(
            master = master,
            text = self.dispName,
            helpURL = helpURL,
        )
        
        if self.units:
            self.unitsWdg = RO.Wdg.StrLabel(
                master = master,
                text = self.units,
                helpURL = helpURL,
            )
        else:
            self.unitsWdg = None

        self._buildWdg(master=master, helpURL=helpURL)
        self._buildWdgInfoList()

    def enableWdg(self, dumWdg=None):
#         print "%s.enableWdg(dumWdg=%r)" % (self, dumWdg)
        self._doCallbacks()

    def getCmdStr(self):
        """Return a portion of a command string for this parameter
        """
        strVal = self.controlWdg.getString()
        if not strVal:
            return ""
        return "%s=%s" % (self.name, strVal)

    def _buildWdg(self, master, helpURL=None):
        """Build self.controlWdg and perhaps other widgets. Subclasses must override!
        
        A default self.nameWdg, self.statusWdg and self.unitsWdg are already created;
        you may use them, ignore them or replace them as desired.
        self.unitsWdg will be None if units=None.
        """
        raise RuntimeError("%s._buildWg: need an implementation!" % (type(self).__name__,))

    def _buildWdgInfoList(self):
        """Build self.wdgInfoList. Subclasses may override, but the default will handle most cases.
        """
        controlWdgSpan = 1
        if not self.nameWdg:
            controlWdgSpan += 1
        if not self.unitsWdg:
            controlWdgSpan += 1
            
        self.wdgInfoList = [
            (self.stateWdg, "w", 1),
        ]
        if self.nameWdg:
            self.wdgInfoList.append((self.nameWdg, "e", 1))
        self.wdgInfoList.append((self.controlWdg, "w", controlWdgSpan))
        if self.unitsWdg:
            self.wdgInfoList.append((self.unitsWdg, "w", 1))

    def _keyVarCallback(self, keyVar):
        """Parameter keyword variable callback
        """
        if not keyVar.isCurrent:
            return
        self.defValue = keyVar[1]
        self.controlWdg.setDefault(keyVar[0])

    def gridWdg(self, startingRow, startingCol):
        """Grid the widgets starting at the specified startingRow and startingCol
        
        Return the next starting startingRow and startingCol
        """
        if self.startNewColumn:
            startingCol += 5
            startingRow = 0
        if self.skipRows:
            startingRow += self.skipRows
        
        row = startingRow
        col = startingCol
        
        for wdg, sticky, columnSpan in self.wdgInfoList:
            wdg.grid(row=row, column=col, sticky=sticky, columnspan=columnSpan)
            col += 1

        return (startingRow + 1, startingCol)
    
    def gridForgetWdg(self):
        """grid_forget all widgets.
        """
        for wdg, sticky, columnSpan in self.wdgInfoList:
            wdg.grid_forget()

    @property
    def isCurrent(self):
        """Does value of parameter match most current command?
        """
#        print "%s.isCurrent = %r" % (self, self.controlWdg.isDefault())
        return self.controlWdg.isDefault()

    @property
    def isDefault(self):
        """Does value of parameter match most current command?
        """
        if self.defValue == None:
            return not self.controlWdg.defValueStr
        return self.controlWdg.getString() == self.defValue

    def restoreCurrent(self, dumWdg=None):
        """Restore parameter to current state.
        """
        # the mechanism for tracking the current value uses the widget's default
        self.controlWdg.restoreDefault()

    def restoreDefault(self, dumWdg=None):
        """Restore paraemter to default state.
        """
        self.controlWdg.set(self.defValue)


class FloatParameterWdgSet(BaseParameterWdgSet):
    """An object representing an floating point parameter for a SOP command stage
    """
    def __init__(self, name, dispName=None, defValue=None, skipRows=0, startNewColumn=False,
        defFormat="%0.1f", units=None, epsilon=1.0e-5):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - parameterList: a list of zero or more parameter objects
        - defEnabled: is stage enabled by default?
        - defFormat default format used when converting numbers to strings
        - units: units string
        - epsison: values that match to within epsilon are considered identical
            for purposes of detecting isDefault
        """
        if defValue != None:
            defValue = float(defValue)

        BaseParameterWdgSet.__init__(self,
            name = name,
            dispName = dispName,
            defValue = defValue,
            units = units,
            skipRows = skipRows,
            startNewColumn = startNewColumn,
        )
        self.stateWidth = 0
        self.defFormat = str(defFormat)
        self.epsilon = float(epsilon)

    def _buildWdg(self, master, helpURL=None):
        """Build widgets and set self.wdgInfoList
        """
        self.controlWdg = RO.Wdg.FloatEntry(
            master = master,
            callFunc = self.enableWdg,
            autoIsCurrent = True,
            defValue = self.defValue,
            defFormat = self.defFormat,
            helpText = "Desired value for %s" % (self.dispName,),
            helpURL = helpURL,
        )

    @property
    def isDefault(self):
        """Does value of parameter match most current command?
        """
        if self.defValue == None:
            return not self.controlWdg.defValueStr
        return abs(self.controlWdg.getNum() - self.defValue) < self.epsilon


class CountParameterWdgSet(BaseParameterWdgSet):
    """An object representing a count; the state shows N of M
    """
    def __init__(self, name, dispName=None, defValue=None, skipRows=0, startNewColumn=False):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - parameterList: a list of zero or more parameter objects
        - defEnabled: is stage enabled by default?
        """
        if defValue != None: defValue = int(defValue)
        
        BaseParameterWdgSet.__init__(self,
            name = name,
            dispName = dispName,
            defValue = defValue,
            skipRows = skipRows,
            startNewColumn = startNewColumn,
        )

    def _buildWdg(self, master, helpURL=None):
        """Build widgets and set self.wdgInfoList
        """
        self.controlWdg = RO.Wdg.IntEntry(
            master = master,
            callFunc = self.enableWdg,
            autoIsCurrent = True,
            defValue = self.defValue,
            helpText = "Desired value for %s" % (self.dispName,),
            helpURL = helpURL,
        )

    def _keyVarCallback(self, keyVar):
        """Parameter keyword variable callback
        """
        if not keyVar.isCurrent:
            self.stateWdg.setIsCurrent(False)
            return
        numDone, currValue = keyVar[0:2]
        self.stateWdg.set("%s of %s" % (numDone, currValue))
        self.controlWdg.setDefault(currValue)

    @property
    def isDefault(self):
        """Does value of parameter match most current command?
        """
        if self.defValue == None:
            return not self.controlWdg.defValueStr
        return self.controlWdg.getNum() == self.defValue


class OptionParameterWdgSet(BaseParameterWdgSet):
    """An object representing a set of options
    """
    def __init__(self, name, dispName=None, items=None, defValue=None, skipRows=0, startNewColumn=False):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - parameterList: a list of zero or more parameter objects
        - defEnabled: is stage enabled by default?
        """
        self.items = items
        BaseParameterWdgSet.__init__(self,
            name = name,
            dispName = dispName,
            defValue = defValue,
            skipRows = skipRows,
            startNewColumn = startNewColumn,
        )

    def _buildWdg(self, master, helpURL=None):
        """Build widgets and set self.wdgInfoList
        """
        self.controlWdg = RO.Wdg.OptionMenu(
            master = master,
            items = self.items,
            callFunc = self.enableWdg,
            autoIsCurrent = True,
            defValue = self.defValue,
            helpText = "Desired value for %s" % (self.dispName,),
            helpURL = helpURL,
        )

    def _keyVarCallback(self, keyVar):
        """Parameter keyword variable callback
        """
        if not keyVar.isCurrent:
            self.stateWdg.setIsCurrent(False)
            return
        numDone, currValue = keyVar[0:2]
        self.stateWdg.set("%s of %s" % (numDone, currValue))
        self.controlWdg.setDefault(currValue)


class PointingParameterWdgSet(OptionParameterWdgSet):
    def __init__(self):
        OptionParameterWdgSet.__init__(self,
            name = "pointing",
            items = ("A", "B"),
            defValue = "A",
        )
    
    def build(self, *args, **kargs):
        OptionParameterWdgSet.build(self, *args, **kargs)
        self.nameWdg.configure(text = "")
        self.controlWdg.helpText = "Desired pointing"
        self.stateWdg.configure(width = 27, anchor = "w")
        self.stateWdg.grid_forget()
        self.stateWdg.grid(row=0, column=0, columnspan=2)
        guiderModel = TUI.Models.getModel("guider")
        guiderModel.cartridgeLoaded.addCallback(self._keyVarCallback)

    def _keyVarCallback(self, keyVar):
        """Keyword variable callback
        Key("cartridgeLoaded",
        Int(name="cartridgeID", invalid=-1, help="Cartridge number"),
        Int(name="plateID", invalid=-1, help="Plate number"),
        String(name="pointing", invalid="?", help="The pointing being observed"),
        Int(name="fscanMJD", invalid=-1, help="MJD when the plate was mapped"),
        Int(name="fscanID", invalid=-1, help="Which of the mappings on fscanMJD we are using"),
        """
        print "%s._keyVarCallback(keyVar=%s)" % (self, keyVar)
        if None in keyVar:
            self.stateWdg.set("Cartridge ?  Plate ?  Pointing ?", keyVar.isCurrent)
            return
        cartridgeID, plateID, pointing = keyVar[0:3]
        self.controlWdg.setDefault(pointing, isCurrent = keyVar.isCurrent)
        stateStr = "Cartridge %s  Plate %s  Pointing %s" % (cartridgeID, plateID, pointing)
        self.stateWdg.set(stateStr, isCurrent = keyVar.isCurrent)
        




class LoadCartridgeCommandWdgSetSet(CommandWdgSet):
    """Guider load cartridge command widget set
    """
    def __init__(self, stageList=()):
        """Create a LoadCartridgeCommandWdgSet
        
        Inputs: same as ItemWdgSet plus:
        - statusBar: status bar widget
        """
        CommandWdgSet.__init__(self,
            name = "loadCartridge",
            actor = "guider",
            canAbort = False,
            stageList = (
                StageWdgSet(
                    name = "loadCartridge",
                    parameterList = (
                        PointingParameterWdgSet(),
                    )
                ),
            )
        )
