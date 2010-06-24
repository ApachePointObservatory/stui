"""Source of log data for log windows
"""
import time
import collections
import RO.AddCallback
import RO.Constants
import TUI.Version
import TUI.Models

class LogEntry(object):
    def __init__(self,
        msgStr,
        severity=RO.Constants.sevNormal,
        actor = TUI.Version.ApplicationName,
        cmdr = None,
        tags = (),
    ):
        self.taiDate = time.time() - RO.Astro.Tm.getUTCMinusTAI()
        self.taiDateStr = time.strftime("%H:%M:%S", time.gmtime(self.taiDate))
        self.msgStr = msgStr
        self.actor = actor
        self.severity = severity
        self.cmdr = cmdr
        self.tags = tags

    def getStr(self):
        """Return log entry formatted for log window
        """
        return "%s %s\n" % (self.taiDateStr, self.msgStr)

class LogSource(RO.AddCallback.BaseMixin):
    ActorTagPrefix = "act_"
    CmdrTagPrefix = "cmdr_"
    def __init__(self, maxEntries=2000):
        RO.AddCallback.BaseMixin.__init__(self)
        self.entryList = collections.deque()
        self.maxEntries = int(maxEntries)
        self.dispatcher = TUI.Models.getModel("tui").dispatcher

    def logMsg(self,
        msgStr,
        severity=RO.Constants.sevNormal,
        actor = TUI.Version.ApplicationName,
        cmdr = None,
    ):
        # strip keys. from keys.<actor>
        if actor and actor.startswith("keys."):
            actor = actor[5:]

        # demote severity of normal messages from cmds actor to debug
        if actor == "cmds" and severity == RO.Constants.sevNormal:
            severity = RO.Constants.sevDebug
        severity = severity

        # get default cmdr dynamically since it might change each time user connects to hub
        if cmdr == None:
            cmdr = self.dispatcher.connection.getCmdr()

        tags = []
        if cmdr:
            tags.append(self.CmdrTagPrefix + cmdr.lower())
        if actor:
            tags.append(self.ActorTagPrefix + actor.lower())
    
        self.lastEntry = LogEntry(msgStr, severity=severity, actor=actor, cmdr=cmdr, tags=tags)
        self.entryList.append(self.lastEntry)
        if len(self.entryList) > self.maxEntries:
            self.entryList.popleft(0)
        self._doCallbacks()
