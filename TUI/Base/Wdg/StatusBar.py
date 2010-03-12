"""Specialization of RO.Wdg.StatusBar that uses opscore.actor.keyvar instead of RO.KeyVariable

History:
2009-04-01 ROwen
2010-03-10 ROwen    Updated for RO.Wdg.StatusBar changes 2010-03-05.
2010-03-12 ROwen    Changed to use Models.getModel.
"""
__all__ = ['StatusBar']

import RO.Constants
import RO.Wdg
import opscore.actor.keyvar
import TUI.Models

class StatusBar(RO.Wdg.StatusBar):
    """Version of StatusBar that handles opscore commands
    """
    def __init__(self,
        master,
        playCmdSounds = False,
        summaryLen = 10,
        helpURL = None,
        helpText = None,
        width = 20,
    **kargs):
        """Create a StatusBar
    
        Inputs:
        - master        master (parent) widget
        - playCmdSounds if true, play "Command Done", "Command Failed" sounds
                        when a command started by doCmd succeeds or fails.
                        if true and these prefs aren't available or are available but aren't sounds,
                        prints a warning to stderr.
        - summaryLen    maximum number of characters of command to show, excluding final "..."
        - helpURL       URL for on-line help
        - helpText      Warning: if specified then the status bar will NOT display
                        help text and entry errors. This is typically only used if you have
                        more than one status bar in a window, in which case one should show
                        help and the others should have helpText strings.
        - width         desired width in average-sized characters
        
        Note: you may specify the following, but the defaults are generally what you want:
        - dispatcher    an opscore.actor.CmdKeyVarDispatcher; if omitted, then obtained from TUI model
        - prefs         a RO.Prefs.PrefSet of preferences; if omitted then obtained from TUI model;
                        uses "Command Done" and "Command Failed" sounds if playCmdSounds True, else ignored.
        """
        tuiModel = TUI.Models.getModel("tui")
        kargs.setdefault("dispatcher", tuiModel.dispatcher)
        kargs.setdefault("prefs", tuiModel.prefs)
        RO.Wdg.StatusBar.__init__(self,
            master = master,
            playCmdSounds = playCmdSounds,
            summaryLen = summaryLen,
            helpURL = helpURL,
            helpText = helpText,
            width = width,
        **kargs)
    
    def doCmd(self, cmdVar, cmdSummary=None):
        """Execute the given command and display progress reports
        for command start warnings and command completion or failure.
        """
        self.clear()

        self.cmdVar = cmdVar
        self.cmdMaxSeverity = RO.Constants.sevNormal
        self.cmdLastWarning = None
        if cmdSummary == None:
            if len(self.cmdVar.cmdStr) > self.summaryLen + 3:
                cmdSummary = self.cmdVar.cmdStr[0:self.summaryLen] + "..."
            else:
                cmdSummary = self.cmdVar.cmdStr
        self.cmdSummary = cmdSummary
    
        if self.dispatcher:
            cmdVar.addCallback(self._cmdVarCallback, opscore.actor.keyvar.AllCodes)
            self.setMsg("%s started" % self.cmdSummary)
            self.dispatcher.executeCmd(self.cmdVar)
        else:
            # note: this is the older format callback
            self._cmdCallback(
                msgType = "f",
                msgDict = dict(type = "f", msgStr = "No dispatcher", dataStart = 0),
            )

    def _cmdVarCallback(self, cmdVar):
        lastReply = cmdVar.lastReply
        dataDict = {}
        if lastReply:
            keywords = lastReply.keywords
            msgStr = lastReply.string
            dataStart = 0
            for keywd in lastReply.keywords:
                if keywd.name.lower() == "text":
                    dataDict["text"] = keywd.values[0]
                    break
        else:
            msgStr = ""
            dataStart = 0
        lastCode = cmdVar.lastCode
        msgDict = dict(
            type = lastCode,
            data = dataDict,
            msgStr = msgStr,
            dataStart = dataStart,
        )
        self._cmdCallback(msgType=lastCode.lower(), msgDict=msgDict)
