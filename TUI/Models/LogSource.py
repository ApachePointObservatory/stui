"""Source of log data for log windows

History:
2010-06-25 ROwen
2010-06-28 ROwen    Removed a statement that had no effect (thanks to pychecker).
2010-06-29 ROwen    Modified LogSource to take the dispatcher as a constructor argument
                    instead of importing the TUI model which is being constructed.
2010-07-20 ROwen    LogEntry:
                    - Changed taiDate to unixTime and taiDateStr to taiTimeStr
                    - Documented the fields
2010-08-26 ROwen    Increased default maximum log length from 2000 to 10000.
2011-01-18 ROwen    Increased default maximum log length from 10000 to 40000.
2011-02-02 ROwen    LogEntry now supports keywords to support changes to the new opscore dispatcher.
2011-06-13 ROwen    Added cmdID argument to LogEntry, LogSource.logEntryFromLogMsg and LogSource.logMsg.
2011-07-28 ROwen    Added cmdInfo and isKeys fields to LogEntry.
                    Generate new LogEntry messages when cmds keywords CmdQueued and CmdDone are seen.
2011-08-31 ROwen    Added support for the new completionCode field of the cmds.CmdDone keyword.
2012-12-07 ROwen    Modified to use RO.Astro.Tm clock correction to show correct time for timestamp
                    even if user's clock is keeping TAI or is drifting.
"""
import time
import collections

import opscore.protocols.messages
import opscore.actor.keyvar
import RO.AddCallback
import RO.Astro.Tm
import RO.Constants
import TUI.Models
import TUI.Version

__all__ = ["LogEntry", "LogSource"]

class CmdInfo(object):
    """Data for synthesized command messages
    """
    def __init__(self,
        uniqueCmdID,
        cmdr,
        cmdID,
        actor,
        cmdStr,
        myCmdr,
    ):
        """Inputs:
        - uniqueCmdID: unique cmdID assigned by hub
        - cmdr: commander
        - cmdID: command ID assigned by commander
        - actor: actor
        - cmdStr: command string for actor
        - myCmdr: my cmdr ID (used to set isMine and msgCmdID)
        
        Fields that are set include all of the above except myCmdr, plus:
        - isMine: True if I issued this command
        - msgCmdID: the command ID for the log message: cmdID if isMine, else 0
        """
        self.uniqueCmdID = uniqueCmdID
        self.cmdr = cmdr
        self.cmdID = cmdID
        self.actor = actor
        self.cmdStr = cmdStr
        self.isMine = (cmdr == myCmdr)
        
        if self.isMine:
            self.msgCmdID = self.cmdID
        else:
            self.msgCmdID = 0
    
    def __str__(self):
        return "%s %d %s %s" % (self.cmdr, self.cmdID, self.actor, self.cmdStr)


class LogEntry(object):
    """Data for one log entry
    
    Fields include:
    - unixTime: date (unix seconds) that LogEntry was created
    - taiTimeStr: TAI time as a string HH:MM:SS at which LogEntry was created
    - msgStr: the message string
    - actor: actor who sent the reply or to whom the command was sent
    - severity: one of the RO.Constants.sevX constants
    - cmdr: commander ID
    - cmdID: command ID (an integer)
    - keywords: parsed keywords (an opscore.protocols.messages.Keywords);
        warning: this is not KeyVars from the model; it is lower-level data
    - tags: a list of strings used as tags in a Tk Text widget; see LogSource for the standard tags
    """
    def __init__(self,
        msgStr,
        severity,
        actor,
        cmdr,
        cmdID,
        keywords,
        tags = (),
        cmdInfo = None,
    ):
        self.unixTime = time.time()
        currPythonSeconds = RO.Astro.Tm.getCurrPySec(self.unixTime)
        currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
        self.taiTimeStr = time.strftime("%H:%M:%S", currTAITuple)
        self.msgStr = msgStr
        self.actor = actor
        self.severity = severity
        self.cmdr = cmdr
        self.cmdID = int(cmdID)
        self.keywords = keywords
        self.tags = tags
        self.cmdInfo = cmdInfo
        self.isKeys = self.actor.startswith("keys") or (self.cmdInfo and self.cmdInfo.actor.startswith("keys"))

    def getStr(self):
        """Return log entry formatted for log window
        """
        return "%s %s\n" % (self.taiTimeStr, self.msgStr)


class LogSource(RO.AddCallback.BaseMixin):
    """Repository of messages from the dispatcher, designed for logging. A singleton.
    
    Supports callbacks via the standard interface (RO.AddCallback), including:
    - addCallback(func, callNow): register a callback function;
      whenever a log entry is added the function will be called with this LogSource as the sole argument
    
    Useful attributes:
    - entryList: an ordered collection of LogEntry objects
    - lastEntry: the last entry added; None until the first entry is added
    
    Each LogEntry has the following tags:
    - act_<LogEntry.actor>
    - cmdr_<LogEntry.cmdr>
    """
    ActorTagPrefix = "act_"
    CmdrTagPrefix = "cmdr_"
    def __new__(cls, dispatcher, maxEntries=40000):
        """Construct the singleton LogSource if not already constructed
        
        Inputs:
        - dispatcher: message dispatcher; an instance of opscore.actor.cmdkeydispatcher.CmdKeyVarDispatcher
        - maxEntries: the maximum number of entries saved (older entries are removed)
        """
        if hasattr(cls, 'self'):
            return cls.self

        cls.self = object.__new__(cls)
        self = cls.self

        RO.AddCallback.BaseMixin.__init__(self)
        self.entryList = collections.deque()
        # dictionary of hub unique command ID: CmdInfo
        # used to keep track of running commands so I can turn cmds.CmdDone into real information
        self.cmdDict = {}
        self.lastEntry = None
        self.maxEntries = int(maxEntries)
        self.dispatcher = dispatcher
        self.dispatcher.setLogFunc(self.logMsg)
        self.cmdsModel = TUI.Models.getModel("cmds")
        self.cmdsModel.CmdQueued.addCallback(self._cmdQueuedCallback)
        self.cmdsModel.CmdDone.addCallback(self._cmdDoneCallback)
        return self
        
    def __init__(self, *args, **kargs):
        pass

    def _cmdDoneCallback(self, keyVar):
        """Handle cmds cmdDone keyword

        Delete self.cmdDict entry (if present) and create a CmdDone log entry with cmdInfo.
        """
        if None in keyVar:
            return
        cmdInfo = self.cmdDict.pop(keyVar[0], None)
        if not cmdInfo:
            return

        completionCode = keyVar[1]
        if completionCode != None:
            completionCode = completionCode.upper()
        severity = opscore.actor.keyvar.MsgCodeSeverity.get(completionCode, RO.Constants.sevWarning)

        self.logMsg(
            msgStr = "CmdDone: %s" % (cmdInfo,),
            severity = severity,
            actor = "",
            cmdr = cmdInfo.cmdr,
            cmdID = cmdInfo.msgCmdID,
            cmdInfo = cmdInfo,
        )
    
    def _cmdQueuedCallback(self, keyVar):
        """Handle cmds cmdQueued keyword
        
        Create a self.cmdDict entry and a CmdStarted log entry with cmdInfo.
        """
        if None in keyVar:
            return
        cmdInfo = CmdInfo(
            uniqueCmdID = keyVar[0],
            cmdr = keyVar[2],
            cmdID = keyVar[3],
            actor = keyVar[4],
            cmdStr = keyVar[6],
            myCmdr = self.dispatcher.connection.getCmdr(),
        )

        self.cmdDict[cmdInfo.uniqueCmdID] = cmdInfo
        self.logMsg(
            msgStr = "CmdStarted: %s" % (cmdInfo,),
            severity = RO.Constants.sevNormal,
            actor = "",
            cmdr = cmdInfo.cmdr,
            cmdID = cmdInfo.msgCmdID,
            cmdInfo = cmdInfo,
        )

    def logEntryFromLogMsg(self,
        msgStr,
        severity=RO.Constants.sevNormal,
        actor = TUI.Version.ApplicationName,
        cmdr = None,
        cmdID = 0,
        keywords = None,
        cmdInfo = None,
    ):
        """Create a LogEntry from log message information.
        
        Inputs:
        - msgStr: message to display; a final \n is appended
        - severity: message severity (an RO.Constants.sevX constant)
        - actor: name of actor; defaults to TUI
        - cmdr: commander; defaults to self
        - cmdID: command ID (an integer)
        - keywords: parsed keywords (an opscore.protocols.messages.Keywords);
            warning: this is not KeyVars from the model; it is lower-level data
        - cmdInfo: CmdInfo object (only for synthesized command log entries)
        """
        # strip keys. from keys.<actor>
#         if actor and actor.startswith("keys."):
#             actor = actor[5:]

        # demote severity of normal messages from cmds actor to debug
        if actor == "cmds" and severity == RO.Constants.sevNormal:
            severity = RO.Constants.sevDebug

        # get default cmdr dynamically since it might change each time user connects to hub
        if cmdr == None:
            cmdr = self.dispatcher.connection.getCmdr()

        if keywords == None:
            keywords = opscore.protocols.messages.Keywords()

        tags = []
        if cmdr:
            tags.append(self.CmdrTagPrefix + cmdr.lower())
        if actor:
            tags.append(self.ActorTagPrefix + actor.lower())
        return LogEntry(
            msgStr = msgStr,
            severity = severity,
            actor = actor,
            cmdr = cmdr,
            cmdID = cmdID,
            tags = tags,
            keywords = keywords,
            cmdInfo = cmdInfo,
        )

    def logMsg(self,
        msgStr,
        severity=RO.Constants.sevNormal,
        actor = TUI.Version.ApplicationName,
        cmdr = None,
        cmdID = 0,
        keywords = None,
        cmdInfo = None,
    ):
        """Add a log message to the repository.
        
        Warning: this function is designed as a callback from the dispatcher and only affects LogSource
        and its clients (mostly log windows). The public function to log messages is tuiModel.logMsg.
        
        Inputs:
        - msgStr: message to display; a final \n is appended
        - severity: message severity (an RO.Constants.sevX constant)
        - actor: name of actor; defaults to TUI
        - cmdr: commander; defaults to self
        - cmdID: command ID (an integer)
        - keywords: parsed keywords (an opscore.protocols.messages.Keywords);
            warning: this is not KeyVars from the model; it is lower-level data
        - cmdInfo: CmdInfo object (only for synthesized command log entries)
        """
        self.lastEntry = self.logEntryFromLogMsg(
            msgStr = msgStr,
            severity = severity,
            actor = actor,
            cmdr = cmdr,
            cmdID = cmdID,
            keywords = keywords,
            cmdInfo = cmdInfo,
        )
        self.entryList.append(self.lastEntry)
        if len(self.entryList) > self.maxEntries:
            self.entryList.popleft()
        self._doCallbacks()
