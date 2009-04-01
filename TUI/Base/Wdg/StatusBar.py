"""Specialization of RO.Wdg.StatusBar that uses opscore.actor.keyvar instead of RO.KeyVariable

History:
2009-04-01 ROwen
"""
__all__ = ['StatusBar']

import RO.Constants
import RO.Wdg
import opscore.actor.keyvar

class StatusBar(RO.Wdg.StatusBar):
    """Version of StatusBar that handles opscore commands
    """
    def doCmd(self, cmdVar, cmdSummary=None):
        """Execute the given command and display progress reports
        for command start warnings and command completion or failure.
        """
        self.clear()

        self.cmdVar = cmdVar
        if cmdSummary == None:
            if len(self.cmdVar.cmdStr) > self.summaryLen + 3:
                cmdSummary = self.cmdVar.cmdStr[0:self.summaryLen] + "..."
            else:
                cmdSummary = self.cmdVar.cmdStr
        self.cmdSummary = cmdSummary
    
        if self.dispatcher:
            cmdVar.addCallback(self._cmdVarCallback, ":wf!")
            self.setMsg("%s started" % self.cmdSummary)
            self.dispatcher.executeCmd(self.cmdVar)
        else:
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
        self._cmdCallback(msgType=lastCode, msgDict=msgDict)
