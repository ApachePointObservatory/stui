#!/usr/bin/env python
"""Sends commands (of type RO.KeyVariable.CmdVar) and dispatches replies
to key variables (RO.KeyVariable.KeyVar and subclasses).

History:
2002-11-25 ROwen    First version with history.
                    Modified TypeDict to include meaning (in addition to category).
                    Added AllTypes.
2002-12-13 ROwen    Modified to work with the MC.
2003-03-20 ROwen    Added actor to logged commands.
2003-03-26 ROwen    Prevented infinite repeat of failed refresh requests, whether
                    cmd failed or cmd succeeded but did not refresh the keyVar;
                    added ignoreFailed flag to refreshAllVar
                    
2003-05-08 ROwen    Modified to use RO.CnvUtil.
2003-06-09 ROwen    Modified to look up commands purely by command ID, not by actor;
                    this allows us to detect some hub rejections of commands.
2003-06-11 ROwen    Modified to make keyword dispatching case-blind;
                    bug fix in dispatch; refreshKey sometimes referenced before set.
2003-06-18 ROwen    Modified to print a full traceback for unexpected errors.
2003-06-25 ROwen    Modified to handle message data as a dict.
2003-07-10 ROwen    Added makeMsgDict and used it to improve
                    logging and reporting of errors.
2003-07-16 ROwen    Modified to use KeyVar.refreshTimeLim
2003-08-13 ROwen    Moved TypeDict and AllTypes to KeyVariable to remove
                    a circular dependency.
2003-10-10 ROwen    Modified to use new RO.Comm.HubConnection.
2003-12-17 ROwen    Modified KeyVar to support the actor "keys",
                    which is used to refresh values from a cache,
                    to save querying the original actor:
                    - keywords from keys.<actor> are treated as if from <actor>
                    - uses KeyVar.refreshInfo to handle refresh commands.
2004-01-06 ROwen    Modified to use KeyVar.hasRefreshCmd and keyVar.getRefreshInfo
                    instead of keyVar.refreshInfo.
2004-02-05 ROwen    Modified logMsg to make it easier to use; \n is automatically appended
                    and typeCategory can be derived from typeChar.
2004-06-30 ROwen    Added abortCmdByID method to KeyDispatcher.
                    Modified for RO.Keyvariable.KeyCommand->CmdVar.
2004-07-23 ROwen    When disconnected, all pending commands time out.
                    Improved variable refresh and command variable timeout handling
                    to better allow other tasks to run: eliminated the use of
                    update_idletasks in favor of scheduling a helper function
                    that works through an iterator and reschedules itself
                    until the iterator is exhausted, then schedules the main task.
                    If a refresh command fails, the message is now printed to the log, not stderr.
                    Added _replyCmdVar to centralize sending messages to cmdVars
                    and handling completion of commands.
                    If a command ID is already in use, the next ID is assigned;
                    this allows a command to never finish without causing other problems later.
2004-08-13 ROwen    Bug fix: abortCmdByID could report a bug when none existed.
2004-09-08 ROwen    Made NullLogger.addOutput output to stderr instead of discarding the data.
2004-10-12 ROwen    Modified to not keep refreshing keyvars when not connected.
2005-01-05 ROwen    Improved documentation for logMsg.
2005-06-03 ROwen    Bug fix: _isConnected was not getting set properly
                    if connection was omitted. It may also have not been
                    set correctly for real connections in special cases.
                    Bug fix: the test code had a typo; it now works.
2005-06-08 ROwen    Changed KeyDispatcher, NullLogger and StdErrLogger to new style classes.
2005-06-16 ROwen    Modified logMsg to take severity instead of typeChar.
2006-05-01 ROwen    Bug fix: if a message could not be parsed, logging the error failed
                    (due to logging in a way that involved parsing the message again).
2006-10-25 ROwen    Overhauled logging:
                    - Replaced logger argument with logFunc.
                    - Replaced setLogger method with setLogFunc
                    - Modified logMsg method to support the new log function:
                      - Removed typeCategory and msgID arguments.
                      - Added actor and cmdr arguments.
                    Modified to log commands using the command target as the actor, not TUI.
2008-04-29 ROwen    Fixed reporting of exceptions that contain unicode arguments.
2009-01-06 ROwen    Improved some doc strings.
"""
import sys
import time
import traceback
import RO.Alg
import RO.CnvUtil
import RO.Constants
import RO.KeyVariable
import RO.Comm.HubConnection
import RO.ParseMsg
import RO.StringUtil

# intervals (in milliseconds) for various background tasks
_RefreshIntervalMS = 1000 # time interval between variable refresh checks (msec)
_TimeoutIntervalMS = 1300 # time interval between checks for command timeout checks (msec)

_CmdNumWrap = 1000 # value at which user command ID numbers wrap

def stdErrLogFunc(msgStr, severity=None, actor=None, cmdr=None):
    sys.stderr.write("%s %s %s %s\n" % (cmdr, actor, severity, msgStr))

class _NullRoot(object):
    def after(self, *args, **kargs):
        pass
    def after_cancel(self, *args, **kargs):
        pass
    def update(self):
        pass
    def update_idletasks(self):
        pass

class KeyDispatcher(object):
    """
    A keyword dispatcher sets keyword variables based on keyword/value data.
    
    Inputs:
    - name: used as the actor when the dispatcher reports errors
    - tkWdg: any Tk widget (used for "after" and "after_cancel" events);
      if omitted, KeyVariables do not self-update
    - connection: an RO.Conn.HubConnection object or similar;
      if omitted, an RO.Conn.HubConnection.NullConnection is used,
      which is useful for testing.
    - logFunc: a function that logs a message. Argument list must be:
        (msgStr, severity, actor, cmdr)
        where the first argument is positional and the others are by name
    """
    def __init__ (self,
        name="KeyDispatcher",
        tkWdg = None,
        connection = None,
        logFunc = None,
    ):
        self.name = name
        self.tkWdg = tkWdg or _NullRoot()
        
        self._isConnected = False

        # keyVarListDict keys are (actor, keyword) tuples and values are lists of KeyVariables
        self.keyVarListDict = {}
        
        # cmdDict keys are command ID and values are KeyCommands
        self.cmdDict = {}
        
        # refreshCmdDict contains info about pending refresh commands;
        # it is used to avoid issuing multiple identical commands
        # and to verify that the command successfully refreshes the keyVar.
        # keys are (actor, command string)
        # values are:
        # - keyVar if pending
        # - None if succeeded
        # - False if the command failed
        # Note: if the command succeeds but its keyVar is not refreshed
        # then a warning is printed and the keyVar's refresh command is nulled
        self.refreshCmdDict = {}
        
        # IDs of various scheduled callbacks
        self._checkCmdID = None
        self._checkRemCmdID = None
        self._refreshAllID = None
        self._refreshRemID = None
        
        if connection:
            self.connection = connection
            self.connection.addReadCallback(self.doRead)
            self.connection.addStateCallback(self.updConnState)
        else:
            self.connection = RO.Comm.HubConnection.NullConnection()
        self._isConnected = self.connection.isConnected()
        self.userCmdIDGen = RO.Alg.IDGen(1, _CmdNumWrap)
        self.refreshCmdIDGen = RO.Alg.IDGen(_CmdNumWrap + 1, 2 * _CmdNumWrap)
        
        self.setLogFunc(logFunc)        
        
        # if a Tk tkWdg supplied, start background tasks (refresh variables and check command timeout)
        if tkWdg:
            self.refreshAllVar()
            self.checkCmdTimeouts()
        
        # exhibit the bug that shows up Tcl/Tk 8.4.15
#        s = tkWdg.tk.call("tk_chooseColor")
#        print "s=%r" % (s,)
#        sys.exit(1)
    
    def abortCmdByID(self, cmdID):
        """Abort the command with the specified ID.
        
        Issue the command specified by cmdVar.abortCmdStr, if present.
        Report the command as failed.
        
        Has no effect if the command was never dispatched (cmdID == None)
        or has already finished.
        """
        if cmdID == None:
            return

        cmdVar = self.cmdDict.get(cmdID)
        if not cmdVar:
            return

        # check isDone
        if cmdVar.isDone():
            return
        
        # if relevant, issue abort command, with no callbacks
        if cmdVar.abortCmdStr and self._isConnected:
            abortCmd = RO.KeyVariable.CmdVar(
                cmdStr = cmdVar.abortCmdStr,
                actor = cmdVar.actor,
            )
            self.executeCmd(abortCmd)
            
        # report command as aborted
        errMsgDict = self.makeMsgDict (
            cmdID = cmdVar.cmdID,
            dataStr = "Aborted; Actor=%r; Cmd=%r" % (
                cmdVar.actor, cmdVar.cmdStr),
        )
        self._replyCmdVar(cmdVar, errMsgDict)

    def add (self, keyVar):
        """
        Adds a keyword variable to the list.

        Inputs:
        - keyVar: the keyword variable; typically of class RO.KeyVariable
          but can be any object that:
          - has property: keyword (a string)
          - has method "set" with arguments:
            - valueTuple (positional): a tuple of one or more values for the keyword
              the values may be strings, even if another type is expected
            - keyword (by name): the keyword
            - msgDict (by name): the full message dictionary
        """
        dictKey = (keyVar.actor, keyVar.keyword.lower())
        # get list of keyVars, adding it if not already present
        keyList = self.keyVarListDict.setdefault(dictKey, [])
        # append new keyVar to the list
        keyList.append(keyVar)

    def checkCmdTimeouts (self):
        """Check all pending commands for timeouts"""
#       print "RO.KeyDispatcher.checkCmdTimeouts()"
        
        # cancel pending update, if any
        if self._checkCmdID:
            self.tkWdg.after_cancel(self._checkCmdID)
        if self._checkRemCmdID:
            self.tkWdg.after_cancel(self._checkRemCmdID)
        
        # iterate over a copy of the values
        # so we can modify the dictionary while checking command timeouts
        cmdVarIter = iter(self.cmdDict.values())
        self._checkRemCmdTimeouts(cmdVarIter)

    def _checkRemCmdTimeouts(self, cmdVarIter):
        """Helper function for checkCmdTimeouts.
        Check the remaining command variables in cmdVarIter.
        If a timeout is found, time out that one command
        and schedule myself to run again shortly
        (thereby giving other events a chance to run).

        Once the iterator is exhausted, schedule
        my parent function checkCmdTimeouts to run
        at the usual interval later.
        """
#       print "RO.KeyDispatcher._checkRemCmdTimeouts(%s)" % cmdVarIter
        try:
            errMsgDict = None
            currTime = time.time()
            for cmdVar in cmdVarIter:
                # if cmd still exits (i.e. has not been deleted for other reasons)
                # check if it has a time limit and has timed out
                if not self.cmdDict.has_key(cmdVar.cmdID):
                    continue
                if not self._isConnected:
                    errMsgDict = self.makeMsgDict (
                        cmdID = cmdVar.cmdID,
                        dataStr = "Aborted; Actor=%r; Cmd=%r; Text=\"disconnected\"" % (
                            cmdVar.actor, cmdVar.cmdStr),
                    )
                    # no connection, so cannot send abort command
                    cmdVar.abortCmdStr = ""
                    break
                elif cmdVar.maxEndTime and (cmdVar.maxEndTime < currTime):
                    # time out this command
                    errMsgDict = self.makeMsgDict (
                        cmdID = cmdVar.cmdID,
                        dataStr = "Timeout; Actor=%r; Cmd=%r" % (
                            cmdVar.actor, cmdVar.cmdStr),
                    )
                    break
            if errMsgDict:
                self._replyCmdVar(cmdVar, errMsgDict)
    
                # schedule myself to run again shortly
                # (thereby giving other time to other events)
                # continuing where I left off
                self._checkRemCmdID = self.tkWdg.after(1, self._checkRemCmdTimeouts, cmdVarIter)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            sys.stderr.write ("RO.KeyDispatcher._checkRemCmdTimeouts failed\n")
            traceback.print_exc(file=sys.stderr)

        # finished checking all commands in the current cmdVarIter;
        # schedule a new checkCmdTimeouts at the usual interval
        self._checkCmdID = self.tkWdg.after(_TimeoutIntervalMS, self.checkCmdTimeouts)
        
    def updConnState(self, conn):
        """If connection state changes, update refresh variables.
        """
        wasConnected = self._isConnected
        self._isConnected = conn.isConnected()

        if wasConnected != self._isConnected:
            self.tkWdg.after(50, self.refreshAllVar)
    
    def dispatch (self, msgDict):
        """
        Updates the appropriate entries based on the supplied message data.

        Inputs:
        - msgDict: message dictionary. Required fields:
          - cmdr: name of commander that triggered the message (string)
          - cmdID: command ID that triggered the message (int)
          - actor: the actor that generated the message (string)
          - type: message type (character)
          - data: dict of keyword: data_tuple entries;
            data_tuple is always a tuple, even if it contains one or zero values
        """
#       print "dispatching", msgDict
        
        # extract user number, command number and data dictionary; die if absent
        cmdr  = msgDict["cmdr"]
        cmdID   = msgDict["cmdID"]
        actor = msgDict["actor"]
        msgType  = msgDict["type"]
        dataDict = msgDict["data"]

        # handle keywords
        # note: keywords from actor keys.<actor>
        # should be handled as if from <actor>
        if actor.startswith("keys."):
            keyActor = actor[5:]
        else:
            keyActor = actor
        for keywd, valueTuple in dataDict.iteritems():
            dictKey = (keyActor, keywd.lower())
            keyVarList = self.keyVarListDict.get(dictKey, [])
            for keyVar in keyVarList:
                try:
                    keyVar.set(valueTuple, msgDict = msgDict)
                except (SystemExit, KeyboardInterrupt):
                    raise
                except:
                    traceback.print_exc(file=sys.stderr)

        # if you are the commander for this message,
        # execute the command callback (if any)
        if cmdr == self.connection.cmdr:
            # get the command for this command id, if any
            cmdVar = self.cmdDict.get(cmdID, None)
            if cmdVar != None:
                # send reply but don't log (that's already been done)
                self._replyCmdVar(cmdVar, msgDict, doLog=False)
                    
    def doRead (self, sock, msgStr):
        """Reads, parses and dispatches a message from the hub"""
        # parse message; if it fails, log it as an error
        try:
            msgDict = RO.ParseMsg.parseHubMsg(msgStr)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            self.logMsg(
                msgStr = "CouldNotParse; Msg=%r; Text=%r" % (msgStr, RO.StringUtil.strFromException(e)),
                severity = RO.Constants.sevError,
            )
            return
        
        # log message
        self.logMsgDict(msgDict)
        
        # dispatch message
        try:
            self.dispatch(msgDict)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            sys.stderr.write("Could not dispatch: %r\n" % (msgDict,))
            traceback.print_exc(file=sys.stderr)
                
    def executeCmd (self, cmdVar):
        """Executes the command (of type RO.KeyVariable.CmdVar) by performing the following tasks:
        - Sets the command number
        - Sets the start time
        - Puts the command on the keyword dispatcher queue
        - Issues the command to the server

        Inputs:
        - cmdVar: the command, of class RO.KeyVariable.CmdVar
            
        Note:
        - we always increment cmdID since every command must have a unique command ID
          (even commands that go to different actors); this simplifies the
          dispatcher code and also makes the hub's life easier
          (since it can report certain kinds of failures using actor=hub).
        """
        if not self._isConnected:
            errMsgDict = self.makeMsgDict(
                dataStr = "Failed; Actor=%r; Cmd=%r; Text=\"not connected\"" % (
                    cmdVar.actor, cmdVar.cmdStr),
            )
            self._replyCmdVar(cmdVar, errMsgDict)
            return
        
        while True:
            if cmdVar.isRefresh:
                cmdID = self.refreshCmdIDGen.next()
            else:
                cmdID = self.userCmdIDGen.next()
            if not self.cmdDict.has_key(cmdID):
                break
        self.cmdDict[cmdID] = cmdVar
        cmdVar._setStartInfo(self, cmdID)
    
        try:
            fullCmd = "%d %s %s" % (cmdVar.cmdID, cmdVar.actor, cmdVar.cmdStr)
            self.connection.writeLine (fullCmd)
            self.logMsg (
                msgStr = fullCmd,
                actor = cmdVar.actor,
            )
#           print "executing:", fullCmd
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            errMsgDict = self.makeMsgDict(
                cmdID = cmdVar.cmdID,
                dataStr = "WriteFailed; Actor=%r; Cmd=%r; Text=%r" % (
                    cmdVar.actor, cmdVar.cmdStr, RO.StringUtil.strFromException(e)),
            )
            self._replyCmdVar(cmdVar, errMsgDict)
        
    def logMsg (self,
        msgStr,
        severity = RO.Constants.sevNormal,
        actor = "TUI",
        cmdr = None,
    ):
        """Writes a message to the log.
        On error, prints message to stderr and returns normally.
        
        Inputs:
        - msgStr: message to display; a final \n is appended
        - severity: message severity (an RO.Constants.sevX constant)
        - actor: name of actor
        - cmdr: commander; defaults to self
        """
        if not self.logFunc:
            return

        try:
            self.logFunc(
                msgStr,
                severity = severity,
                actor = actor,
                cmdr = cmdr,
            )
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            sys.stderr.write("Could not log: %r; severity=%r; actor=%r; cmdr=%r\n" % \
                (msgStr, severity, actor, cmdr))
            traceback.print_exc(file=sys.stderr)
    
    def logMsgDict (self, msgDict):
        try:
            typeChar = msgDict["type"].lower()
            severity = RO.KeyVariable.TypeDict[typeChar][1]
            self.logMsg(
                msgStr = msgDict["msgStr"],
                severity = severity,
                actor = msgDict["actor"],
                cmdr = msgDict["cmdr"],
            )
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            sys.stderr.write("Could not log message dict:\n%r\n" % (msgDict,))
            traceback.print_exc(file=sys.stderr)
        
    def makeMsgDict (self,
        cmdr = None,
        cmdID = 0,
        actor = None,
        type = "f",
        dataStr = "",
    ):
        """Generate a hub message based on the supplied data.
        Useful for reporting internal errors.
        """
        if cmdr == None:
            cmdr = self.connection.cmdr
        if actor == None:
            actor = self.name

        headerStr = "%s %d %s %s" % (
            cmdr,
            cmdID,
            actor,
            type,
        )
        msgStr = " ".join((headerStr, dataStr))
        try:
            return RO.ParseMsg.parseHubMsg(msgStr)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            sys.stderr.write("Could not make message dict from %r; error: %s" % (msgStr, e))
            traceback.print_exc(file=sys.stderr)
            msgDict = RO.ParseMsg.parseHubMsg(headerStr)
            msgDict["msgStr"] = msgStr
            msgDict["data"] = {}
            return msgDict
    
    def refreshAllVar (self, ignoreFailed=False, startOver=False):
        """Examines all keywords, looking for ones that need updating
        and issues the appropriate refresh commands.

        Inputs:
        - ignoreFailed: refresh even if an earlier attempt failed
        - startOver: list all vars as bad and then reload
        """
#       print "RO.KeyDispatcher.refreshAllVar"

        # cancel pending update, if any
        if self._refreshAllID:
            self.tkWdg.after_cancel(self._refreshAllID)
        if self._refreshRemID:
            self.tkWdg.after_cancel(self._refreshRemID)
    
        if (not self._isConnected) or startOver:
            # clear the refresh command dict
            # and invalidate all keyVars
            # (leave pending refresh commands alone; they will time out)
            self.refreshCmdDict = {}
            for keyVarList in self.keyVarListDict.values():
                for keyVar in keyVarList:
                    keyVar.setNotCurrent()

            # schedule a new refreshAllVar at the usual interval
            if self._isConnected:
                self._refreshAllID = self.tkWdg.after(_RefreshIntervalMS, self.refreshAllVar)

        elif self._isConnected:
            # iterate over a copy of the values
            # so we can modify the dictionary while checking command timeouts
            keyVarListIter = iter(self.keyVarListDict.values())
            self._refreshRemVars(keyVarListIter, ignoreFailed)

    def _refreshRemVars(self, keyVarListIter, ignoreFailed):
        """Helper function for refreshAllVar. Plow through a keyVarList iterator
        until a refresh command is found that is wanted, issue it,
        then schedule a call for myself for asap.
        
        Each element should be a list of 1 or more RO.KeyVariable.KeyVar objects
        that shares a common actor and keyword (and thus should be updatable
        with the same refresh command).

        Once the iterator is exhausted, schedule
        my parent function refreshAllVar to run
        at the usual interval later.
        """
#       print "RO.KeyDispatcher._refreshRemVars(%s)" % keyVarListIter
        try:
            if not self._isConnected:
                # schedule parent function asap and bail out
                self._refreshAllID = self.tkWdg.after(1, self.refreshAllVar)
                return
                
            # refresh all variables
            for keyVarList in keyVarListIter:
                for keyVar in keyVarList:
                    if not keyVar.isCurrent() and keyVar.hasRefreshCmd():
                        # refreshInfo is (actor, cmdStr, timeLim)
                        # and refreshCmdDict keys are (actor, cmdStr)
                        cmdState = self.refreshCmdDict.get(keyVar.getRefreshInfo()[0:2], None)
                        if cmdState == None or (ignoreFailed and cmdState == False):
                            self.refreshOneVar(keyVar)
                            
                            # schedule myself to run again shortly
                            # (thereby giving other time to other events)
                            # continuing where I left off but with a new actor, keyword combo
                            # (since the current one has presumably now been handled)
                            self._refreshRemID = self.tkWdg.after(1, self._refreshRemVars, keyVarListIter, ignoreFailed)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            sys.stderr.write ("RO.KeyDispatcher.refreshAllVar failed:\n")       
            traceback.print_exc(file=sys.stderr)

        # finished checking all commands in the current keyVarListIter;
        # schedule a new refreshAllVar at the usual interval
        self._refreshAllID = self.tkWdg.after(_RefreshIntervalMS, self.refreshAllVar)
            
    def refreshOneVar (self, keyVar):
        """Refreshes one keyVariable.
        """
        if not keyVar.hasRefreshCmd():
            return
#       print "refreshOneVar(%s) with %s" % (keyVar, keyVar.getRefreshInfo())
        actor, cmdStr, timeLim = keyVar.getRefreshInfo()
        cmdVar = RO.KeyVariable.CmdVar (
            actor = actor,
            cmdStr = cmdStr,
            timeLim = timeLim,
            isRefresh = True,
        )
        self.refreshCmdDict[(actor, cmdStr)] = keyVar
        self.executeCmd(cmdVar)
    
    def remove (self, keyVar):
        """
        Removes the specified keyword variable,
        returning whatever was removed, or None if keyVar not found.
        See also "add".

        Inputs:
        - keyVar: the keyword variable to remove

        Returns:
        - keyVar, if present, None otherwise.
        """
        dictKey = (keyVar.actor, keyVar.keywd.lower())
        varList = self.keyVarListDict.get(dictKey, [])
        if keyVar in varList:
            varList.remove(keyVar)
            return keyVar
        else:
            return None
    
    def _replyCmdVar(self, cmdVar, msgDict, doLog=True):
        """Send a message to a command variable and optionally log it.

        If the command is done, delete it from the command dict.
        If the command is a refresh command and is done,
        update the refresh command dict accordingly.
        
        Inputs:
        - cmdVar    command variable (RO.KeyVariable.CmdVar)
        - msgDict   message to send
        """
        if doLog:
            self.logMsgDict(msgDict)
        cmdVar.reply(msgDict)
        if cmdVar.isDone() and cmdVar.cmdID != None:
            try:
                del (self.cmdDict[cmdVar.cmdID])
            except KeyError:
                sys.stderr.write("KeyDispatcher bug: tried to delete cmd %s=%s but it was missing\n" % \
                    (cmdVar.cmdID, cmdVar))

            if cmdVar.isRefresh:
                # refresh command finished; update refresh command dict
                refreshKey = (cmdVar.actor, cmdVar.cmdStr)
                if cmdVar.lastType == ":":
                    # command succeeded;
                    # remove command from refresh command dict
                    # if associated keyVar not updated, complain and delete its refresh command
                    keyVar = self.refreshCmdDict.get(refreshKey)
                    if keyVar == None:
                        return

                    self.refreshCmdDict[refreshKey] = None
                    if not keyVar.isCurrent():
                        keyVar.refreshCmd = None
                        errMsgDict = self.makeMsgDict(
                            cmdID = cmdVar.cmdID,
                            actor = None,
                            type = "w",
                            dataStr = "RefreshFailed; Actor=%r; Keyword=%r; Cmd=%r; Text=\"deleting refresh command\"" % (keyVar.actor, keyVar.keyword, cmdVar.cmdStr),
                        )       
                        self.logMsgDict(errMsgDict)
                else:
                    # command failed, mark it false in the refresh command dict
                    self.refreshCmdDict[refreshKey] = False

    def setLogFunc (self, logFunc=None):
        """Sets the log output device, or clears it if none specified.
        
        The function must take the following arguments: (msgStr, severity, actor, cmdr)
        where the first argument is positional and the others are by name
        """
        self.logFunc = logFunc
    

if __name__ == "__main__":
    print "\nTesting RO.KeyDispatcher\n"
    import time, RO.KeyVariable

    kdb = KeyDispatcher()

    def showVal(valueList, isCurrent, keyVar):
        print "keyVar %s.%s = %r, isCurrent = %s" % (keyVar.actor, keyVar.keyword, valueList, isCurrent)

    # scalars
    varList = (
        RO.KeyVariable.KeyVar(
            converters = str,
            keyword="StringKey",
            actor="test",
            refreshCmd = "refresh stringkey",
            dispatcher=kdb,
        ),
        RO.KeyVariable.KeyVar(
            converters = RO.CnvUtil.asInt,
            keyword="IntKey",
            actor="test",
            refreshCmd = "refresh intkey",
            dispatcher=kdb,
        ),
        RO.KeyVariable.KeyVar(
            converters = RO.CnvUtil.asFloatOrNone,
            keyword="FloatKey",
            actor="test",
            refreshCmd = "refresh floatkey",
            dispatcher=kdb,
        ),
        RO.KeyVariable.KeyVar(
            converters = RO.CnvUtil.asBool,
            keyword="BooleanKey",
            actor="test",
            refreshCmd = "refresh boolkey",
            dispatcher=kdb,
        ),
        RO.KeyVariable.KeyVar(
            nval = 2,
            converters = (str, RO.CnvUtil.asInt),
            keyword="KeyList",
            actor="test",
            refreshCmd = "refresh keylist str,int combo",
            dispatcher=kdb,
        ),
    )

    for var in varList:
        var.addCallback(showVal)
    
    # command callback
    def cmdCall(msgType, msgDict, cmdVar):
        print "command callback for actor=%s, cmdID=%d, cmdStr=%r called with code '%s'" % (cmdVar.actor, cmdVar.cmdID, cmdVar.cmdStr, msgType)
    
    # command
    cmdVar = RO.KeyVariable.CmdVar(
        cmdStr = "THIS IS A SAMPLE COMMAND",
        actor="test",
        callFunc=cmdCall,
        callTypes = RO.KeyVariable.DoneTypes,
    )
    kdb.executeCmd(cmdVar)
    cmdID = cmdVar.cmdID

    dataDict = {
        "StringKey": ("hello",),
        "IntKey": (1,),
        "IntKey": ("badIntValue",),
        "FloatKey": (1.23456789,),
        "BooleanKey": ("T",),
        "KeyList": ("three", 3),
        "Coord2Key": (45.0, 0.1, 32.1, -0.1, time.time()),
    }

    msgDict = {
        "cmdr":"me",
        "cmdID":cmdID-1,
        "actor":"wrongActor",
        "type":":",
        "data":dataDict,
    }
    print "\nDispatching message with wrong actor; nothing should happen"
    kdb.dispatch(msgDict)

    msgDict = {
        "cmdr":"me",
        "cmdID":cmdID-1,
        "actor":"test",
        "type":":",
        "data":{},
    }
    print "\nDispatching message with wrong cmdID and no data; command callback should not be called"
    kdb.dispatch(msgDict)

    msgDict = {
        "cmdr":"me",
        "cmdID":cmdID,
        "actor":"wrongActor",
        "type":":",
        "data":{},
    }
    print "\nDispatching message with wrong actor and no data; command callback should not be called"
    kdb.dispatch(msgDict)

    msgDict = {
        "cmdr":"me",
        "cmdID":cmdID,
        "actor":"test",
        "type":":",
        "data":dataDict,
    }
    print "\nDispatching message correctly; all should work:"
    kdb.dispatch(msgDict)
    
    print "\nTesting keyVar refresh"
    kdb.refreshAllVar()
