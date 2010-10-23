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
"""
import time
import collections
import RO.AddCallback
import RO.Constants
import TUI.Version

__all__ = ["LogEntry", "LogSource"]

class LogEntry(object):
    """Data for one log entry
    
    Fields include:
    - unixTime: date (unix seconds) that LogEntry was created
    - taiTimeStr: TAI time as a string HH:MM:SS at which LogEntry was created
    - msgStr: the message string
    - actor: actor who sent the reply or to whom the command was sent
    - severity: one of the RO.Constants.sevX constants
    - cmdr: commander ID
    - tags: a list of strings used as tags in a Tk Text widget; see LogSource for the standard tags
    """
    def __init__(self,
        msgStr,
        severity=RO.Constants.sevNormal,
        actor = TUI.Version.ApplicationName,
        cmdr = None,
        tags = (),
    ):
        self.unixTime = time.time()
        self.taiTimeStr = time.strftime("%H:%M:%S", time.gmtime(self.unixTime -  - RO.Astro.Tm.getUTCMinusTAI()))
        self.msgStr = msgStr
        self.actor = actor
        self.severity = severity
        self.cmdr = cmdr
        self.tags = tags

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
    def __new__(cls, dispatcher, maxEntries=10000):
        """Construct the singleton LogSource if not already constructed
        
        Inputs:
        - dispatcher: an instance of opscore.actor.cmdkeydispatcher.CmdKeyVarDispatcher
        - maxEntries: the maximum number of entries saved (older entries are removed)
        """
        if hasattr(cls, 'self'):
            return cls.self

        cls.self = object.__new__(cls)
        self = cls.self

        RO.AddCallback.BaseMixin.__init__(self)
        self.entryList = collections.deque()
        self.lastEntry = None
        self.maxEntries = int(maxEntries)
        self.dispatcher = dispatcher
        self.dispatcher.setLogFunc(self.logMsg)
        return self
        
    def __init__(self, *args, **kargs):
        pass

    def logEntryFromLogMsg(self,
        msgStr,
        severity=RO.Constants.sevNormal,
        actor = TUI.Version.ApplicationName,
        cmdr = None,
    ):
        """Create a LogEntry from log message information.
        
        Inputs:
        - msgStr: message to display; a final \n is appended
        - severity: message severity (an RO.Constants.sevX constant)
        - actor: name of actor; defaults to TUI
        - cmdr: commander; defaults to self
        """
        # strip keys. from keys.<actor>
        if actor and actor.startswith("keys."):
            actor = actor[5:]

        # demote severity of normal messages from cmds actor to debug
        if actor == "cmds" and severity == RO.Constants.sevNormal:
            severity = RO.Constants.sevDebug

        # get default cmdr dynamically since it might change each time user connects to hub
        if cmdr == None:
            cmdr = self.dispatcher.connection.getCmdr()

        tags = []
        if cmdr:
            tags.append(self.CmdrTagPrefix + cmdr.lower())
        if actor:
            tags.append(self.ActorTagPrefix + actor.lower())
        return LogEntry(msgStr, severity=severity, actor=actor, cmdr=cmdr, tags=tags)

    def logMsg(self,
        msgStr,
        severity=RO.Constants.sevNormal,
        actor = TUI.Version.ApplicationName,
        cmdr = None,
    ):
        """Add a log message to the repository.
        
        Warning: this function is designed as a callback from the dispatcher and only affects LogSource
        and its clients (mostly log windows). The public function to log messages is tuiModel.logMsg.
        
        Inputs:
        - msgStr: message to display; a final \n is appended
        - severity: message severity (an RO.Constants.sevX constant)
        - actor: name of actor; defaults to TUI
        - cmdr: commander; defaults to self
        """
        self.lastEntry = self.logEntryFromLogMsg(msgStr, severity=severity, actor=actor, cmdr=cmdr)
        self.entryList.append(self.lastEntry)
        if len(self.entryList) > self.maxEntries:
            self.entryList.popleft()
        self._doCallbacks()
