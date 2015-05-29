"""SOP command widgets

These objects are used to describe one or more sop commands.

History:
2010-06-23 ROwen    Commented out a diagnostic print statement
2010-06-28 ROwen    Bug fix: an exception was broken (thanks to pychecker)
2010-11-18 ROwen    Added a Stop button for commands that can be aborted.
2011-05-18 SBeland and ROwen    Added StringParameterWdgSet.
2011-07-02 ROwen    Bug fix: The command widgets would not shrink when stages were removed.
2011-07-07 ROwen    Improved computation of displayName from name such that names like
                    doAPOGEEScience are handled correctly.
                    Help strings now show name instead of displayName to simplify the mapping
                    between the SOP window and sop commands.
2011-07-11 ROwen    Enhance parameter widget set classes:
                    - Add arguments trackCurr, ctrlColSpan, ctrlSticky.
                    - Update documentation (it had fallen behind for most subclasses).
2012-11-01 ROwen    Address ticket #1688:
                    - Modified so that X never sends an abort command to SOP. To enforce this,
                      doCmd no longer accepts additional keyword arguments, to avoid abortCmdStr.
                    - Modified to confirm Stop.
2013-03-21 ROwen    Move Stop button after Modify, as per ticket #1735.
2014-06-17 ROwen    Cosmetic fix: BaseParameterWdgSet.build constructed a variable keyVar that wasn't a KeyVar;
                    fortunately it was never used.
2014-06-20 ROwen    Added support for fake stages.
2014-06-23 ROwen    Added support for parameters associated with more than one stage;
                    CommandWdgSet takes stageStr and parameterList instead of stageList;
                    StageWdgSet no longer knows anything about parameters.
2014-07-02 ROwen    Added survey mode display (actually plate type).
2014-07-03 ROwen    Enhanced the survey mode display to show isCurrent and ? if unknown;
                    fixed a bug that caused a traceback if survey[0] == None.
2014-08-29 ROwen    Added paramWidth argument and changed default parameter width from 10 to 6.
                    Tweaked the way stateWidth is handled to simplify overrides.
2015-05-28 ROwen    Fix ticket 2375: the last two fields of cartridgeLoaded are None for engcam.
"""
import contextlib
import collections
import itertools
import re
import Tkinter
import tkMessageBox
import opscore.actor
import RO.AddCallback
import RO.Astro.Tm
import RO.PhysConst
import RO.StringUtil
import TUI.Models

DefParamWidth = 6
DefCountWidth = 3
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
    ErrorStates = set(("failed",))
    WarningStates = set(("aborted",))
    RunningStates = set(("starting", "prepping", "running"))
    DisabledStates = set(("off",))
    ValidStates = set((None,)) | DoneStates | ErrorStates | RunningStates | DisabledStates
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
        return self.state in self.ErrorStates

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
    - dispName: display name
    - fullName: full dotted name (command.stage.parameter); computed later
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
            dispName = (" ".join(val for val in re.split(r"([A-Z][a-z]+)", name) if val)).title()
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
            helpText = "State of %s %s" % (self.name, typeName,),
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
        elif state in self.WarningStates:
            severity = RO.Constants.sevWarning
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
    def __init__(self, name, dispName=None, parameterList=(), realStageStr="", fakeStageStr="", actor="sop", canAbort=True, abortCmdStr=None):
        """Construct a partial CommandWdgSet. Call build to finish the job.
        
        Inputs:
        - name: name of command, stage or parameter as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - parameterList: a list of Parameters for this command
        - realStageStr: a string containing space-separated names of real stages
        - fakeStageStr: a string containing space-separated names of fake stages, e.g. "bias dark cleanup";
            fake stages are stages that cannot be disabled, and which STUI should not show a state field for,
            but for which sop still wants to output state in the <command>State keyword)
        - actor: name of actor to which to send commands
        - canAbort: if True then command can be aborted
        - abortCmdStr: command string to abort command; if None then the default "name abort" is used

        If realStateStr and fakeStageStr are both empty then one fake stage is constructed: fakeStageStr=name
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
        # list of all parameters
        self.parameterList = parameterList[:]
        # list of parameters that are associated with one or more particular stages
        self.stageParameterList = [param for param in parameterList if param.stageNameSet]
        self._hasNonstageParameters = len(self.parameterList) > len(self.stageParameterList)
        self._settingWdgets = False

        if not (realStageStr or fakeStageStr):
            fakeStageStr = name

        # set stageDict = dictionary of known stages: stage base name: stage
        # and set fullName and actor parameter of all stages and parameters
        self.stageDict = dict()
        for stageName in realStageStr.split():
            stage = StageWdgSet(
                name = stageName,
            )
            self.stageDict[stage.name] = stage
            stage.fullName = "%s.%s" % (self.name, stage.name)
            stage.actor = self.actor
        for fakeStageName in fakeStageStr.split():
            self.stageDict[fakeStageName] = FakeStageWdgSet(fakeStageName)

        for parameter in parameterList:
            parameter.fullName = "%s.%s" % (self.name, parameter.name)
            parameter.actor = self.actor

        # ordered dictionary of stages for which state is expected: stage base name: stage (or None for a fake stage)
        self.currStageDict = collections.OrderedDict()
        self.currCmdInfoList = []
        
    def build(self, master, msgBar, statusBar, callFunc=None, helpURL=None):
        """Finish building the widget, including stage and parameter widgets.
        
        Warning: must call before using the object!
        
        Inputs:
        - master: master widget for stateWdg
        - msgBar: message bar widget, for displaying state strings
        - statusBar: status bar widget, for executing commands
        - callFunc: callback function for state changes
        - helpURL: URL of help file
        """
        self.wdg = Tkinter.Frame(master, borderwidth=1, relief="ridge")
        self.msgBar = msgBar
        self.statusBar = statusBar
        
        ItemWdgSet.build(self, master=self.wdg, typeName="command", callFunc=callFunc)

        self.stateWdg.grid(row=0, column=0, sticky="w")
        self.commandFrame = Tkinter.Frame(self.wdg)
        self.commandFrame.grid(row=0, column=1, columnspan=3, sticky="w")
        self._makeCmdWdg(helpURL)
        
        self.stageFrame = Tkinter.Frame(self.wdg)
        self.stageFrame.grid(row=1, column=0, columnspan=2, sticky="w")
        self.paramFrame = Tkinter.Frame(self.wdg)
        self.paramFrame.grid(row=1, column=2, columnspan=2, sticky="w")
        self.wdg.grid_columnconfigure(3, weight=1)

        # pack invisible frames into stageFrame and paramFrame so they shrink to nothing
        # when stages and parameters are removed
        self._stageShrinkFrame = Tkinter.Frame(self.stageFrame)
        self._stageShrinkFrame.grid(row=0, column=0)
        self._paramShrinkFrame = Tkinter.Frame(self.paramFrame)
        self._paramShrinkFrame.grid(row=0, column=0)

        for stage in self.stageDict.itervalues():
            stage.build(
                master = self.stageFrame,
                callFunc = self.enableWdg,
            )

        # If there is only one stage (or no stages) then grid it now.
        # Otherwise wait until we see the <name>Stages keyword and grid the specified stages
        # (which may not be all of them) in the specified order.
        if len(self.stageDict) < 2:
            # there is only one stage; display it and ignore the <name>Stages keyword
            self._gridStages(self.stageDict.keys(), isFirst=True)

        startingRow = 0
        startingCol = 0
        for parameter in self.parameterList:
            parameter.build(
                master = self.paramFrame,
                callFunc = self.enableWdg,
                helpURL = helpURL,
            )
            # grid all parameter widgets, then remove the ones associated with particular stage(s)
            # (those are regridded by a callback)
            startingRow, startingCol = parameter.gridWdg(startingRow=startingRow, startingCol=startingCol)
            if parameter.stageNameSet:
                parameter.ungridWdg()

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
        for cmdInfo in self.currCmdInfoList:
            if not cmdInfo.isDone:
                cmdInfo.abort()

    def doStart(self, wdg=None):
        """Start or modify the command
        """
        self.doCmd(cmdStr=self.getCmdStr(), wdg=wdg)

    def doStop(self, wdg=None):
        """Stop the command
        """
        if tkMessageBox.askquestion("Confirm Stop", "Really stop the current SOP command?", icon="warning") != "yes":
            return
        self.doCmd(cmdStr=self.abortCmdStr, wdg=wdg)

    def doCmd(self, cmdStr, wdg=None):
        """Run the specified command
        
        Inputs:
        - cmdStr: command string
        - wdg: widget that started the command (to disable it while the command runs); None if no widget
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = self.actor,
            cmdStr = cmdStr,
            callFunc = self.enableWdg,
        )
        self.statusBar.doCmd(cmdVar)
        self.currCmdInfoList.append(CmdInfo(cmdVar, wdg))
        self.enableWdg()

    def enableWdg(self, dumWdg=None):
        """Enable widgets according to current state
        """
        if self._settingWdgets:
            return

        with self.setWdgContext(enableWdg=False):
            # purge cmdInfoList
            self.currCmdInfoList = [cmdInfo for cmdInfo in self.currCmdInfoList if not cmdInfo.isDone]

            self.startBtn.setEnable(self.isDone or self.state == None)
            
            # can modify if not current and sop is running this command
            canModify = not self.isCurrent and self.isRunning
            self.modifyBtn.setEnable(canModify)
            
            # can stop if this stage is running
            self.stopBtn.setEnable(self.isRunning)

            # can abort if I have any running commands
            self.abortBtn.setEnable(len(self.currCmdInfoList) > 0)

            self.defaultBtn.setEnable(not self.isDefault)
            self.currentBtn.setEnable(not self.isCurrent)
            for cmdInfo in self.currCmdInfoList:
                cmdInfo.disableIfRunning()

            # disable or enable stage-associated params, depending on which stages are enabled
            enabledStageNameSet = frozenset(stage.name for stage in self.currStageDict.itervalues() \
                if stage.isReal and stage.controlWdg.getBool())
            for param in self.stageParameterList:
                param.setEnable(bool(enabledStageNameSet & param.stageNameSet))

    def getCmdStr(self):
        """Return the command string for the current settings
        """
        cmdStrList = [self.name]
        for stage in self.currStageDict.itervalues():
            cmdStrList.append(stage.getCmdStr())
        for param in self.parameterList:
            cmdStrList.append(param.getCmdStr())
        return " ".join(cmdStrList)        

    @property
    def isCurrent(self):
        """Does the state of the control widgets match the state of the sop command?
        """
        for stage in self.currStageDict.itervalues():
            if not stage.isCurrent:
#                print "%s.isCurrent False because stage %s.isCurrent False" % (self, stage)
                return False

        for param in self.parameterList:
#             print "Test %s.isCurrent" % (param,)
            if not param.isCurrent:
#                 print "%s.isCurrent False because param %s.isCurrent False" % (self, param)
                return False

#        print "%s.isCurrent True" % (self,)
        return True

    @property
    def isDefault(self):
        """Is the control widget set to its default state?
        """
        for stage in self.currStageDict.itervalues():
            if not stage.isDefault:
#                print "%s.isDefault False because stage %s.isDefault False" % (self, stage)
                return False
        for param in self.parameterList:
            if not param.isDefault:
#                 print "%s.isDefault False because param %s.isDefault False" % (self, param)
                return False
#        print "%s.isDefault True" % (self,)
        return True

    def restoreDefault(self, dumWdg=None):
        """Restore default stages and parameters
        """
        with self.setWdgContext():
            for stage in self.stageDict.itervalues():
                stage.restoreDefault()
            for param in self.parameterList:
                param.restoreDefault()

    def restoreCurrent(self, dumWdg=None):
        """Restore current parameters
        
        WARNING: it may be better to restore defaults for hidden stages,
        or restore defaults for all, then restore current afterwards.
        On the other hand, maybe that's what restoreCurrent should do anyway.
        """
        with self.setWdgContext():
            for stage in self.stageDict.itervalues():
                stage.restoreCurrent()
            for param in self.parameterList:
                param.restoreCurrent()

    @contextlib.contextmanager
    def setWdgContext(self, enableWdg=True):
        try:
            self._settingWdgets = True
            yield
        finally:
            self._settingWdgets = False
        if enableWdg:
            self.enableWdg()

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
        # print "_commandStateCallback(keyVar=%s)" % (keyVar,)
        
        # set state of the command
        cmdState = keyVar[0]
        self.setState(
            state = cmdState,
            isCurrent = keyVar.isCurrent,
        )

        textState = keyVar[1]
        if cmdState or textState:
            msgStr = "%s %s: %s" % (self.name, cmdState, textState)
            severity = dict(
                failed = RO.Constants.sevError,
                aborted = RO.Constants.sevWarning,
            ).get(keyVar[0], RO.Constants.sevNormal)
            self.msgBar.setMsg(msgStr, severity = severity)
        else:
            self.msgBar.setMsg("", severity=RO.Constants.sevNormal)
        
        # set state of the command's stages
        stageStateList = keyVar[2:]
        if len(self.currStageDict) != len(stageStateList):
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
                raise RuntimeError("Wrong number of stage states for %s; got %s for stages %s" % 
                    (keyVar.name, stageStateList, self.currStageDict.keys()))

        for stage, stageState in itertools.izip(self.currStageDict.itervalues(), stageStateList):
            stage.setState(
                state = stageState,
                isCurrent = keyVar.isCurrent,
            )

    def _gridStages(self, visibleStageNameList, isFirst=False):
        """Grid the specified stages in the specified order
        """
#        print "%s._gridStages(%s)" % (self, visibleStageNameList)
        if (list(self.currStageDict.keys()) == visibleStageNameList) and not isFirst:
            return

        newVisibleStageNameSet = set(visibleStageNameList)
        unknownNameSet = newVisibleStageNameSet - set(self.stageDict.keys())
        if unknownNameSet:
            unknownNameList = [str(unk) for unk in unknownNameSet]
            raise RuntimeError("%s contains unknown stages %s" % (visibleStageNameList, unknownNameList))

        # withdraw all stages and their parameters
        for stage in self.stageDict.itervalues():
            if stage.isReal:
                stage.stateWdg.grid_forget()
                stage.controlWdg.grid_forget()
                stage.removeCallback(self.enableWdg, doRaise=False)

        # update currStageDict and grid visible real stages
        self.currStageDict.clear()
        hasParameters = self._hasNonstageParameters
        stageRow = 0
        for stageName in visibleStageNameList:
            stage = self.stageDict[stageName]
            self.currStageDict[stageName] = stage
            if stage.isReal:
                stage.stateWdg.grid(row=stageRow, column=0, sticky="w")
                stage.controlWdg.grid(row=stageRow, column=1, sticky="w")
                stageRow += 1
                stage.addCallback(self.enableWdg)

        visibleStageNameSet = frozenset(visibleStageNameList)
        for param in self.stageParameterList:
            if param.stageNameSet & visibleStageNameSet:
                hasParameters = True
                param.regridWdg()
            else:
                param.ungridWdg()
        
        hasAdjustments = hasParameters or len(self.currStageDict) > 1
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
        """Make command widgets. Return next column (the column after the last widget)
        """
        col = 0

        self.startBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = self.dispName,
            callFunc = self.doStart,
            helpText = "Start %s" % (self.name,),
            helpURL = helpURL,
        )
        self.startBtn.grid(row = 0, column = col)
        col += 1

        self.modifyBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Modify",
            callFunc = self.doStart,
            helpText = "Modify %s" % (self.name,),
            helpURL = helpURL,
        )
        self.modifyBtn.grid(row = 0, column = col)
        col += 1
        
        self.stopBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "Stop",
            callFunc = self.doStop,
            helpText = "Stop %s" % (self.name,),
            helpURL = helpURL,
        )
        if self.canAbort:
            self.stopBtn.grid(row = 0, column = col)
            col += 1

        self.abortBtn = RO.Wdg.Button(
            master = self.commandFrame,
            text = "X",
            callFunc = self.doAbort,
            helpText = "Abort my command(s)",
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
        return col


class FakeStageWdgSet(object):
    """An object representing a fake SOP command stage
    """
    def __init__(self, name):
        self.isReal = False
        self.name = name
        self.parameterList = ()

    def build(self, *args, **kwargs):
        pass

    def getCmdStr(self):
        return ""

    def isCurrent(self):
        return True
        
    def isDefault(self):
        return True

    def restoreCurrent(self, dumWdg=None):
        pass

    def restoreDefault(self, dumWdg=None):
        pass

    def setState(self, state, isCurrent=True):
        pass

    def enableWdg(self, controlWdg=None):
        pass
        

class StageWdgSet(ItemWdgSet):
    """An object representing a SOP command stage
    """
    def __init__(self, name, dispName=None, defEnabled=True):
        """Construct a partial StageWdgSet. Call build to finish the job.
        
        Inputs:
        - name: name of stage, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - defEnabled: is stage enabled by default?
        """
        self.isReal = True
        ItemWdgSet.__init__(self,
            name = name,
            dispName = dispName,
        )
        self.defEnabled = bool(defEnabled)

    def build(self, master, callFunc=None, helpURL=None):
        """Finish building the widgets, but do not grid them
        
        Warning: must call before using the object!
        
        Inputs:
        - master: master widget for stateWdg
        - callFunc: callback function for state changes
        - helpURL: URL of help file
        
        self.stateWdg and self.controlWdg are the stage widgets
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

    def getCmdStr(self):
        """Return the command string for the current settings
        """
        if not self.controlWdg.getBool():
            return "no" + self.name
        return ""

    @property
    def isCurrent(self):
        """Is the stage enabled checkbox the same as the current or most recent sop command?
        """
        if not self.controlWdg.getIsCurrent():
#             print "%s.isCurrent False because controlWdg.getIsCurrent False" % (self,)
            return False
#         print "%s.isCurrent True" % (self,)
        return True

    @property
    def isDefault(self):
        """Is the stage enabled checkbox set to its default state?
        """
        if self.controlWdg.getBool() != self.defEnabled:
#             print "%s.isDefault False because controlWdg.getBool() != self.defEnabled" % (self,)
            return False
#         print "%s.isDefault True" % (self,)
        return True

    def restoreCurrent(self, dumWdg=None):        
        """Restore control widget and parameters to match the running or most recently run command
        """
        # the mechanism for tracking the current value uses the widget's default
        self.controlWdg.restoreDefault()

    def restoreDefault(self, dumWdg=None):
        """Restore control widget and parameters to their default state.
        """
        self.controlWdg.set(self.defEnabled)

    def setState(self, state, isCurrent=True):
        ItemWdgSet.setState(self, state, isCurrent=isCurrent)
        
        if state != None:
            isEnabledInSOP = self.state not in self.DisabledStates
            self.controlWdg.setDefault(isEnabledInSOP)
#            print "%s setState set controlWdg default=%r" % (self, self.controlWdg.getDefBool())

    def enableWdg(self, controlWdg=None):
        """Enable widgets
        """
        # doEnable = self.controlWdg.getBool()
        # for param in self.parameterList:
        #     param.controlWdg.setEnable(doEnable)
        self._doCallbacks()


class BaseParameterWdgSet(ItemWdgSet):
    """An object representing a basic parameter for a SOP command stage
    
    Subclasses must override buildControlWdg and may want to override isDefault
    """
    def __init__(self, name, dispName=None, defValue=None, units=None, paramWidth=DefParamWidth, stateWidth=DefStateWidth,
        trackCurr=True, stageStr="", skipRows=0, startNewColumn=False, ctrlColSpan=None, ctrlSticky="w", helpText=None):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - defValue: default value for parameter
        - units: units of parameter (a string); if provided then self.unitsWdg is set to
            an RO.Wdg.StrLabel containing the string; otherwise None
        - paramWidth: width of parameter widget
        - stateWidth: width of state widget
        - trackCurrent: if True then display current value
        - stageStr: a string of one or more space-separated stage names; if not empty
            then the parameter will only be visible if any of the specified stages is visible
        - skipRows: number of rows to skip before displaying
        - startNewColumn: if True then display parameter in a new column (then skip skipRows before gridding)
        - ctrlColSpan: column span for data entry widget; if None then the value is computed
        - ctrlSticky: sticky for data entry widget
        - helpText: help text for entry widget; if None then a default is generated
        """
        ItemWdgSet.__init__(self,
            name = name,
            dispName = dispName,
        )
        self.defValue = defValue
        self.units = units
        self.paramWidth = paramWidth
        self.stateWidth = stateWidth
        self.trackCurr = bool(trackCurr)
        self.stageNameSet = frozenset(stageStr.split())
        self.skipRows = skipRows
        self.startNewColumn = startNewColumn
        self.ctrlColSpan = ctrlColSpan
        self.ctrlSticky = ctrlSticky
        if helpText is None:
            self.helpText = "Desired value for %s" % (self.name,)
        else:
            self.helpText = helpText
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
            keyVar = getattr(sopModel, keyVarName)
            keyVar.addCallback(self._keyVarCallback)

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
        if not self.controlWdg.winfo_ismapped():
            return ""
        if not self.controlWdg.getEnable():
            return ""
        strVal = self.controlWdg.getString()
        if not strVal:
            return ""
        return "%s=%s" % (self.name, strVal)

    def setEnable(self, doEnable):
        """Enable or disable the control widgets
        """
        self.controlWdg.setEnable(doEnable)
        self._doCallbacks()

    def _buildWdg(self, master, helpURL=None):
        """Build self.controlWdg and perhaps other widgets. Subclasses must override!
        
        A default self.nameWdg, self.statusWdg and self.unitsWdg are already created;
        you may use them, ignore them or replace them as desired.

        self.unitsWdg will be None if no units widget wanted
        """
        raise RuntimeError("%s._buildWg: need an implementation!" % (type(self).__name__,))

    def _buildWdgInfoList(self):
        """Build self.wdgInfoList. Subclasses may override, but the default will handle most cases.
        """
        controlColSpan = 1
        if not self.nameWdg:
            controlColSpan += 1
        if not self.unitsWdg:
            controlColSpan += 1
        
        if self.ctrlColSpan != None:
            # override default value
            controlColSpan = self.ctrlColSpan
            
        self.wdgInfoList = [
            (self.stateWdg, "w", 1),
        ]
        if self.nameWdg:
            self.wdgInfoList.append((self.nameWdg, "e", 1))
        self.wdgInfoList.append((self.controlWdg, self.ctrlSticky, controlColSpan))
        if self.unitsWdg:
            self.wdgInfoList.append((self.unitsWdg, "w", 1))

    def _keyVarCallback(self, keyVar):
        """Parameter keyword variable callback
        """
        if not keyVar.isCurrent:
            return
        self.defValue = keyVar[1]
        if self.trackCurr:
            self.controlWdg.setDefault(keyVar[0])

    def gridWdg(self, startingRow, startingCol):
        """Grid the widgets starting at the specified startingRow and startingCol
        
        Return the next startingRow and startingCol
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

    def regridWdg(self):
        for wdg, sticky, columnSpan in self.wdgInfoList:
            wdg.grid()

    def ungridWdg(self):
        for wdg, sticky, columnSpan in self.wdgInfoList:
            wdg.grid_remove()


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


class CountParameterWdgSet(BaseParameterWdgSet):
    """An object representing a count; the state shows N of M
    """
    def __init__(self, name, dispName=None, defValue=None, paramWidth=DefCountWidth,
        trackCurr=True, stageStr="", skipRows=0, startNewColumn=False, ctrlColSpan=None, ctrlSticky="w", helpText=None):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - defValue: default value for parameter
        - units: units of parameter (a string); if provided then self.unitsWdg is set to
            an RO.Wdg.StrLabel containing the string; otherwise None
        - trackCurrent: if True then display current value
        - stageStr: a string of one or more space-separated stage names; if not empty
            then the parameter will only be visible if any of the specified stages is visible
        - skipRows: number of rows to skip before displaying
        - startNewColumn: if True then display parameter in a new column (then skip skipRows before gridding)
        - ctrlColSpan: column span for data entry widget; if None then the value is computed
        - ctrlSticky: sticky for data entry widget
        - helpText: help text for entry widget; if None then a default is generated
        """
        if defValue != None: defValue = int(defValue)
        
        BaseParameterWdgSet.__init__(self,
            name = name,
            dispName = dispName,
            defValue = defValue,
            paramWidth = paramWidth,
            stateWidth = 4 + (2 * paramWidth), # room for "N of M"
            stageStr = stageStr,
            skipRows = skipRows,
            startNewColumn = startNewColumn,
            ctrlColSpan = ctrlColSpan,
            ctrlSticky = ctrlSticky,
            helpText = helpText,
        )

    def _buildWdg(self, master, helpURL=None):
        """Build self.controlWdg and perhaps other widgets.
        """
        self.controlWdg = RO.Wdg.IntEntry(
            master = master,
            callFunc = self.enableWdg,
            autoIsCurrent = True,
            width = self.paramWidth,
            defValue = self.defValue,
            helpText = self.helpText,
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
        if self.trackCurr:
            self.controlWdg.setDefault(currValue)

    @property
    def isDefault(self):
        """Does value of parameter match most current command?
        """
        if self.defValue == None:
            return not self.controlWdg.defValueStr
        return self.controlWdg.getNum() == self.defValue


class IntParameterWdgSet(BaseParameterWdgSet):
    """An object representing an integer parameter for a SOP command stage
    """
    def __init__(self, name, dispName=None, defValue=None, units=None, paramWidth=DefParamWidth,
        trackCurr=True, stageStr="", skipRows=0, startNewColumn=False, ctrlColSpan=None, ctrlSticky="w", helpText=None):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - defValue: default value for parameter
        - units: units of parameter (a string); if provided then self.unitsWdg is set to
            an RO.Wdg.StrLabel containing the string; otherwise None
        - trackCurrent: if True then display current value
        - stageStr: a string of one or more space-separated stage names; if not empty
            then the parameter will only be visible if any of the specified stages is visible
        - skipRows: number of rows to skip before displaying
        - startNewColumn: if True then display parameter in a new column (then skip skipRows before gridding)
        - ctrlColSpan: column span for data entry widget; if None then the value is computed
        - ctrlSticky: sticky for data entry widget
        - helpText: help text for entry widget; if None then a default is generated
        """
        if defValue != None:
            defValue = float(defValue)

        BaseParameterWdgSet.__init__(self,
            name = name,
            dispName = dispName,
            defValue = defValue,
            units = units,
            paramWidth = paramWidth,
            stateWidth = 0,
            trackCurr = trackCurr,
            stageStr = stageStr,
            skipRows = skipRows,
            startNewColumn = startNewColumn,
            ctrlColSpan = ctrlColSpan,
            ctrlSticky = ctrlSticky,
            helpText = helpText,
        )

    def _buildWdg(self, master, helpURL=None):
        """Build self.controlWdg and perhaps other widgets.
        """
        self.controlWdg = RO.Wdg.IntEntry(
            master = master,
            callFunc = self.enableWdg,
            autoIsCurrent = True,
            width = self.paramWidth,
            defValue = self.defValue,
            helpText = self.helpText,
            helpURL = helpURL,
        )


class FloatParameterWdgSet(BaseParameterWdgSet):
    """An object representing an floating point parameter for a SOP command stage
    """
    def __init__(self, name, dispName=None, defValue=None, units=None, paramWidth=DefParamWidth,
        trackCurr=True, stageStr="", skipRows=0, startNewColumn=False, ctrlColSpan=None, ctrlSticky="w", helpText=None,
        defFormat="%0.1f", epsilon=1.0e-5):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - defValue: default value for parameter
        - units: units of parameter (a string); if provided then self.unitsWdg is set to
            an RO.Wdg.StrLabel containing the string; otherwise None
        - trackCurrent: if True then display current value
        - stageStr: a string of one or more space-separated stage names; if not empty
            then the parameter will only be visible if any of the specified stages is visible
        - skipRows: number of rows to skip before displaying
        - startNewColumn: if True then display parameter in a new column (then skip skipRows before gridding)
        - ctrlColSpan: column span for data entry widget; if None then the value is computed
        - ctrlSticky: sticky for data entry widget
        - helpText: help text for entry widget; if None then a default is generated
        - defFormat default format used when converting numbers to strings
        - epsilon: values that match to within epsilon are considered identical
            for purposes of detecting isDefault
        """
        if defValue != None:
            defValue = float(defValue)

        BaseParameterWdgSet.__init__(self,
            name = name,
            dispName = dispName,
            defValue = defValue,
            units = units,
            paramWidth = paramWidth,
            stateWidth = 0,
            trackCurr = trackCurr,
            stageStr = stageStr,
            skipRows = skipRows,
            startNewColumn = startNewColumn,
            ctrlColSpan = ctrlColSpan,
            ctrlSticky = ctrlSticky,
            helpText = helpText,
        )
        self.defFormat = str(defFormat)
        self.epsilon = float(epsilon)

    def _buildWdg(self, master, helpURL=None):
        """Build self.controlWdg and perhaps other widgets.
        """
        self.controlWdg = RO.Wdg.FloatEntry(
            master = master,
            callFunc = self.enableWdg,
            autoIsCurrent = True,
            width = self.paramWidth,
            defValue = self.defValue,
            defFormat = self.defFormat,
            helpText = self.helpText,
            helpURL = helpURL,
        )

    @property
    def isDefault(self):
        """Does value of parameter match most current command?
        """
        if self.defValue == None:
            return not self.controlWdg.defValueStr
        return abs(self.controlWdg.getNum() - self.defValue) < self.epsilon


class StringParameterWdgSet(BaseParameterWdgSet):
    """An object representing a string parameter for a SOP command stage
    """
    def __init__(self, name, dispName=None, defValue=None, units=None, paramWidth=DefParamWidth,
        trackCurr=True, stageStr="", skipRows=0, startNewColumn=False, ctrlColSpan=None, ctrlSticky="w", helpText=None,
        partialPattern=None, finalPattern=None):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - defValue: default value for parameter
        - units: units of parameter (a string); if provided then self.unitsWdg is set to
            an RO.Wdg.StrLabel containing the string; otherwise None
        - trackCurrent: if True then display current value
        - stageStr: a string of one or more space-separated stage names; if not empty
            then the parameter will only be visible if any of the specified stages is visible
        - skipRows: number of rows to skip before displaying
        - startNewColumn: if True then display parameter in a new column (then skip skipRows before gridding)
        - ctrlColSpan: column span for data entry widget; if None then the value is computed
        - ctrlSticky: sticky for data entry widget
        - helpText: help text for entry widget; if None then a default is generated
        - partialPattern    a regular expression string which partial values must match
        - finalPattern  a regular expression string that the final value must match;
            if omitted, defaults to partialPattern
        """
        if defValue != None:
            defValue = str(defValue)

        BaseParameterWdgSet.__init__(self,
            name = name,
            dispName = dispName,
            defValue = defValue,
            units = units,
            paramWidth = paramWidth,
            stateWidth = 0,
            trackCurr = trackCurr,
            stageStr = stageStr,
            skipRows = skipRows,
            startNewColumn = startNewColumn,
            ctrlColSpan = ctrlColSpan,
            ctrlSticky = ctrlSticky,
            helpText = helpText,
        )
        self.partialPattern = partialPattern
        self.finalPattern = finalPattern

    def _buildWdg(self, master, helpURL=None):
        """Build self.controlWdg and perhaps other widgets.
        """
        self.controlWdg = RO.Wdg.StrEntry(
            master = master,
            callFunc = self.enableWdg,
            autoIsCurrent = True,
            defValue = self.defValue,
            width = self.paramWidth,
            partialPattern = self.partialPattern,
            finalPattern = self.finalPattern,
            helpText = self.helpText,
            helpURL = helpURL,
        )

    def getCmdStr(self):
        """Return a portion of a command string for this parameter
        
        Override the default behavior to quote the string value
        """
        strVal = self.controlWdg.getString()
        if not strVal:
            return ""
        return "%s=%s" % (self.name, RO.StringUtil.quoteStr(strVal))

    @property
    def isDefault(self):
        """Does value of parameter match most current command?
        """
        if self.defValue == None:
            return not self.controlWdg.defValueStr
        return self.controlWdg.getString() == self.defValue


class OptionParameterWdgSet(BaseParameterWdgSet):
    """An object representing a set of options
    """
    def __init__(self, name, dispName=None, defValue=None, trackCurr=True, stageStr="",
        skipRows=0, startNewColumn=False, ctrlColSpan=None, ctrlSticky="w", helpText=None,
        items=None):
        """Constructor
        
        Inputs:
        - name: name of parameter, as used in sop commands
        - dispName: displayed name (text for control widget); if None then use last field of name
        - defValue: default value for parameter
        - trackCurrent: if True then display current value
        - stageStr: a string of one or more space-separated stage names; if not empty
            then the parameter will only be visible if any of the specified stages is visible
        - skipRows: number of rows to skip before displaying
        - startNewColumn: if True then display parameter in a new column (then skip skipRows before gridding)
        - ctrlColSpan: column span for data entry widget; if None then the value is computed
        - ctrlSticky: sticky for data entry widget
        - helpText: help text for entry widget; if None then a default is generated
        - items: list of options
        """
        self.items = items
        BaseParameterWdgSet.__init__(self,
            name = name,
            dispName = dispName,
            defValue = defValue,
            trackCurr = trackCurr,
            stageStr = stageStr,
            skipRows = skipRows,
            startNewColumn = startNewColumn,
            ctrlColSpan = ctrlColSpan,
            ctrlSticky = ctrlSticky,
            helpText = helpText,
       )

    def _buildWdg(self, master, helpURL=None):
        """Build self.controlWdg and perhaps other widgets.
        """
        self.controlWdg = RO.Wdg.OptionMenu(
            master = master,
            items = self.items,
            callFunc = self.enableWdg,
            autoIsCurrent = True,
            defValue = self.defValue,
            helpText = self.helpText,
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
        if self.trackCurr:
            self.controlWdg.setDefault(currValue)


def formatSurveyStr(survey):
    """Format survey keyword data

    @param[in] surveyData: the value of guider.survey or sop.survey
        (a pair of strings, either of which may be None)
    """
    surveyStrList = []
    if survey[0] == None:
        surveyStrList.append("?")
    else:
        surveyStrList.append(survey[0])
    if survey[1] == None:
        surveyStrList.append("?")
    elif survey[1].lower() != "none":
        surveyStrList.append(survey[1])
    return "-".join(surveyStrList)



class PointingParameterWdgSet(OptionParameterWdgSet):
    """Parameter widgets for displaying the current pointing and selecting a pointing (A or B)
    """
    def __init__(self):
        """Constructor
        """
        OptionParameterWdgSet.__init__(self,
            name = "pointing",
            items = ("A", "B"),
            defValue = "A",
        )
    
    def build(self, master, callFunc=None, helpURL=None):
        OptionParameterWdgSet.build(self, master=master, callFunc=callFunc, helpURL=helpURL)
        self.nameWdg.configure(text = "")
        self.controlWdg.helpText = "Desired pointing"
        self.stateWdg.configure(width = 27, anchor = "w")
        self.stateWdg.grid_forget()
        self.stateWdg.grid(row=0, column=0, columnspan=2)
        self.spacerWdg = RO.Wdg.StrLabel(master = master, text=" ")
        self.spacerWdg.grid(row = 0, column = 9)
        self.sopSurveyWdg = RO.Wdg.StrLabel(
            master = master,
            helpText = "survey mode from sop, if different than guider",
            helpURL = helpURL,
        )
        self.sopSurveyWdg.grid(row = 0, column = 10)

        self.guiderModel = TUI.Models.getModel("guider")
        self.sopModel = TUI.Models.getModel("sop")
        self.guiderModel.cartridgeLoaded.addCallback(self._keyVarCallback)
        self.guiderModel.survey.addCallback(self._surveyCallback)
        self.sopModel.survey.addCallback(self._surveyCallback)

    def _keyVarCallback(self, keyVar):
        """Keyword variable callback
        Key("cartridgeLoaded",
        Int(name="cartridgeID", invalid=-1, help="Cartridge number"),
        Int(name="plateID", invalid=-1, help="Plate number"),
        String(name="pointing", invalid="?", help="The pointing being observed"),
        Int(name="fscanMJD", invalid=-1, help="MJD when the plate was mapped"),
        Int(name="fscanID", invalid=-1, help="Which of the mappings on fscanMJD we are using"),
        """
#        print "%s._keyVarCallback(keyVar=%s)" % (self, keyVar)
        if None in keyVar[0:3]:
            self.stateWdg.set("Cartridge ?  Plate ?  Ptg ?", keyVar.isCurrent)
            return
        cartridgeID, plateID, pointing = keyVar[0:3]
        self.controlWdg.setDefault(pointing, isCurrent = keyVar.isCurrent)
        stateStr = "Cartridge %s  Plate %s  Ptg %s" % (cartridgeID, plateID, pointing)
        self.stateWdg.set(stateStr, isCurrent = keyVar.isCurrent)

    def _surveyCallback(self, dumVar):
        """Callback for guider.survey and sop.survey
        """
        if self.guiderModel.survey[:] == self.sopModel.survey[:]:
            self.sopSurveyWdg.set("", severity=RO.Constants.sevNormal)
            return
        sopSurveyStr = formatSurveyStr(self.sopModel.survey)
        self.sopSurveyWdg.set(sopSurveyStr, isCurrent=self.sopModel.survey.isCurrent, severity=RO.Constants.sevWarning)

class LoadCartridgeCommandWdgSetSet(CommandWdgSet):
    """Guider load cartridge command widget set
    """
    def __init__(self):
        """Create a LoadCartridgeCommandWdgSet
        """
        CommandWdgSet.__init__(self,
            name = "loadCartridge",
            actor = "guider",
            canAbort = False,
            parameterList = (
                PointingParameterWdgSet(),
            )
        )

    def _makeCmdWdg(self, helpURL):
        """Build the command widgets

        Overridden to add a display of the kind of plate (from the guider's survey keyword)
        """
        col = CommandWdgSet._makeCmdWdg(self, helpURL)
        RO.Wdg.StrLabel( # spacer widget
            master = self.commandFrame,
            text = " ",
        ).grid(row = 0, column = col)
        col += 1
        self.surveyWdg = RO.Wdg.StrLabel(
            master = self.commandFrame,
            helpText = "survey mode from guider",
            helpURL = helpURL,
        )
        self.surveyWdg.grid(row = 0, column = col)
        col += 1

        guiderModel = TUI.Models.getModel("guider")
        guiderModel.survey.addCallback(self._surveyCallback)
        return col

    def _surveyCallback(self, survey):
        """Callback for the guider.survey and sop.survey keywords
        """
        surveyStrList = []
        if survey[0] == None:
            surveyStrList.append("?")
        else:
            surveyStrList.append(survey[0])
        if survey[1] == None:
            surveyStrList.append("?")
        elif survey[1].lower() != "none":
            surveyStrList.append(survey[1])
        surveyStr = "-".join(surveyStrList)
        self.surveyWdg.set(surveyStr, isCurrent=survey.isCurrent)
