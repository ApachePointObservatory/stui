import itertools
import time
import Tkinter
import RO.AddCallback

class StageInfo(RO.AddCallback.BaseMixin):
    """An object that keeps track of the state of a stage
    """
    DoneStates = ("aborted", "done", "failed")
    def __init__(self, name, state=None, callFunc=None):
        RO.AddCallback.BaseMixin.__init__(self)

        self.name = name
        self.state = state
        self.text = ""
        self.totDuration = 0
        self.currDuration = 0

        # dictionary of stage name: StageInfo object
        self.stageInfoDict = RO.SeqUtil.OrderedDict()

        # dictionary of task name: TaskState object
        self.taskInfoDict = RO.SeqUtil.OrderedDict()
        
        if callFunc:
            self.addCallback(callFunc, callNow=False)

    def getSubstageInfo(self, nameList, doCreate=True):
        """Get the desired substage
        
        Inputs:
        - nameList: partial name as [substage name, sub-substage name,...]
        - doCreate: create the state if necessary
        """
        substageName = nameList[0]
        substage = self.stageInfoDict.get(substageName)
        if substage == None:
            if not doCreate:
                return None
            substage = StageInfo(substageName)
            substage.addCallback(self._stageCallback)
            self.stageInfoDict[substageName] = substage
        if len(nameList) > 1:
            return substage.getSubstage(nameList[1:], doCreate=True)
        return substage

    def getTaskInfo(self, taskName, doCreate=True):
        """Get the desired task info
        
        Inputs:
        - taskName: name of task
        - doCreate: create the task if necessary
        """
        taskInfo = self.taskInfoDict.get(taskName)
        if taskInfo == None:
            if not doCreate:
                return None
            taskInfo = TaskInfo(taskName)
            taskInfo.addCallback(self._taskCallback)
            self.taskInfoDict[substageName] = taskInfo
        return taskInfo

    def setState(self, newState, text=None, totDuration=None, currDuration=None):
        """Set the state of this item
        
        Inputs:
        - newState: desired state for object
        - text: new text; if None then left unchanged
        - totDuration: new total duration; if None then left unchanged
        - currDuration: new current duration; if None then left unchanged
        
        @raise RuntimeError if called after state is done
        """
        if self.isDone:
            raise RuntimeError("State=%s already done; cannot set state to %s" % (self.state, state))
        self.state = state
        if text != None:
            self.text = text
        if totDuration != None:
            self.totDuration = totDuration
        if currDuration != None:
            self.currDuration = currDuration
        
        if self.isDone:
            # terminate all subtasks and substages
            for taskState in self.taskInfoDict.values():
                if not taskState.isDone:
                    taskState.setState("done")
            for stageState in self.stageInfoDict.values():
                if not stageState.isDone:
                    stageState.setState("done")
        self._doCallbacks()
        self._removeAllCallbacks()

    @property
    def isDone(self):
        return self.state in self.DoneStates

class TaskInfo(StageInfo):
    """An object that keeps track of the state of a task
    
    So far this is identical to StageInfo, but specialize later if needed.
    """
    pass

class CommandInfo(StageInfo):
    """An object that keeps track of the state of a command and its stages and tasks.
    """
    def __init__(self, name, state=None):
        StageInfo.__init__(self, name, state=state)
    
    def commandStagesCallback(self, cmdStagesKey):
        """Process commandStages keyword by setting up all stages
        
        Raise RuntimeError if stages already exist and do not match new stages

        commandStages=<command>, <stage1>, <stage2>,...
        """
        if cmdStagesKey[0] != self.name:
            return
        newStageNames = cmdStagesKey[1:]
        if None in newStageNames:
            return

        if self.stageInfoDict:
            # compare existing stages and complain if they don't match
            currStageNames = self.stageInfoDict.keys()
            if len(currStageNames) != len(cmdStagesKey) - 1:
                raise RuntimeError("number of stages does not match")
            if currStageNames != cmdStagesKey[1:]:
                raise RuntimeError("Stage names don't match")
            return

        for stageName in newStageNames:
            self.stageInfoDict[stageName] = StageInfo(stageName)
        
    def commandStateCallback(self, cmdStateKey):
        """Process commandState keyword

        commandState=<command>, <stage1state>, <stage2state>,...
        """
        if cmdStateKey[0] != self.name:
            return
        stageStages = cmdStateKey[1:]
        if None in stageStates:
            return

        if len(stageStates) != len(self.stageInfoDict):
            raise RuntimeError("number of stages does not match")
        for stageStateObj, stageState in itertools.izip(self.stageStageDict, stageStates):
            stageStateObj.setState(stageState)

    def getStageInfo(self, name, doCreate=True):
        """Return a stageInfo object given a complete list of names
        
        Inputs:
        - name: dotted name of stage: command.stage.substage...
        - doCreate: if True then substages will be created if needed (but never stages)
        """
        nameList = name.split(".")
        if self.name != nameList[0]:
            return
        if len(nameList) == 1:
            return self

        # information about a state or substate
        # the state must exist, but substates will be created if necessary
        stageInfo = self.stageInfoDict.get(nameList[1])
        if stageInfo == None:
            raise RuntimeError("getStageInfo(%s) failed: command %s does not have a stage %s" % \
                (nameList, self.name, nameList[1]))
        if len(nameList) > 2:
            stageInfo = stageInfo.getSubstage(nameList[2:], doCreate=doCreate)
        return stageInfo
        
    def _stageStateCallback(self, stageStateKey):
        """Handle stageState keyword

        stageState=stage, state, fullDuration, timeUsed
        """
        stageInfo = self.getStageInfo(stageStateKey[0], doCreate=True)
        stageInfo.setState(stageStateKey[1:])

    def _taskStateCallback(self, taskStateKey):
        """Handle taskState keyword
        
        taskState=taskName,stageName,state,fullDuration,timeUsed,commentaryText
        
        The associated state must exist! It will not be created.
        """
        if None in taskName:
            return
        taskName, stageName, state, fullDuration, timeUsed, text = taskSTateKey[0:6]
        
        stageInfo = self.getStageInfo(stageName, doCreate=False)
        if not stageInfo:
            raise RuntimeError("Unknown stage %s" % (stageName,))
        taskInfo = stageInfo.getTask(taskName, doCreate=True)
        taskInfo.setState(state=state, fullDuration=fullDuration, timeUsed=timeUsed, text=text)
