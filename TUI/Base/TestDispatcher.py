#!/usr/bin/env python
"""Dispatch data for testing purposes

History:
2009-04-21 ROwen
2009-07-09 ROwen    Bug fix: test code was sending SlewEnds instead of SlewEnd.
                    Modified dispatch to dispatch each item separately, thereby
                    allowing dataList to contain multiple instances of the same keyword.
                    Modified to not print each dispatched message since the dispatcher already does this.
"""
import TUI.Models.TUIModel

class TestDispatcher(object):
    """Dispatch a set of data at regular intervals
    """
    def __init__(self, actor, cmdID = 11, msgCode = "i", delay=2.0):
        """Create a tester with a given set of data
        
        Inputs:
        - actor: default name of actor
        - cmdID: default command ID
        - msgCode: default message code; one of :>iwef! (opscore.actor.keyvar.AllCodes)
        - delay: default delay
        """
        self.actor = actor
        self.cmdID = int(cmdID)
        self.msgCode = str(msgCode)
        self.tuiModel = TUI.Models.TUIModel.Model(True)
        self.dispatcher = self.tuiModel.dispatcher
        self.dataSet = None
        self.cmdr = self.tuiModel.getCmdr()
        self.delay = float(delay)

    def dispatch(self, dataList, cmdr=None, cmdID=None, actor=None, msgCode=None):
        """Dispatch a list of data imemdiately
        
        Inputs:
        - dataList: a collection of key=value strings, for example:
            ("AxePos=-342.563, 38.625, 5.4", "TCCPos=-342.563, 38.625, 5.0")
        - cmdr: commander (program.username); defaults to me
        - actor: name of actor
        - cmdID: command ID (an integer)
        - msgCode: message code; one of :>iwef! (opscore.actor.keyvar.AllCodes)
        """
        if cmdr == None:
            cmdr = self.cmdr
        if cmdID == None:
            cmdID = self.cmdID
        if actor == None:
            actor = self.actor
        if msgCode == None:
            msgCode = self.msgCode
        for dataItem in dataList:
            replyStr = "%s %s %s %s %s" % (cmdr, cmdID, actor, msgCode, dataItem)
            self.dispatcher.dispatchReplyStr(replyStr)
    
    def runDataSet(self, dataSet):
        """Dispatch a sequence of data, with a fixed pause between each entry.

        Inputs:
        - dataSet: a collection of data; each element of which is a collection of key=value strings
          for example:
            (
                ("AxePos=-342.563, 38.625, 5.4", "TCCPos=-342.562, 38.624, 5.5"),
                ("AxePos=-341.230, 39.023, 5.3", "TCCPos=-341.231, 39.024, 5.4"),
            )
        """
        dataDictSet = [dict(delay=self.delay, dataList=dataList) for dataList in dataSet]
        self._dispatchIter(iter(dataDictSet))

    def runDataDictSet(self, dataDictSet):
        """Dispatch a sequence of data dicts

        Inputs:
        - dataDictSet: a collection of data dicts, each of which may contain any of these keys:
            - dataList: a list of key=value strings, for example:
                (
                    ("AxePos=-342.563, 38.625, 5.4", "TCCPos=-342.562, 38.624, 5.5"),
                    ("AxePos=-341.230, 39.023, 5.3", "TCCPos=-341.231, 39.024, 5.4"),
                )
            - delay: time to wait for next item (sec)
            - msgCode: one of >iwef!: (opscore.actor.keyvar.AllCodes)
            - cmdID: command ID (an int)
            - cmdr: program_name.user_name
        """
        for item in dataDictSet:
            item.setdefault("delay", self.delay)
        self._dispatchIter(iter(dataDictSet))
    
    def _dispatchIter(self, dataDictIter):
        """Dispatch and iterator over dataDictSet; see runDataDictSet for details
        """
        try:
            dataDict = dataDictIter.next()
            delay = dataDict.pop("delay")
        except StopIteration:
            print "Test finished"
            return
        self.dispatch(**dataDict)
        self.tuiModel.reactor.callLater(delay, self._dispatchIter, dataDictIter)


if __name__ == "__main__":
    tccTester = TestDispatcher(actor="tcc", delay=0.5)
    
    # this could just as easily be the first element of animDataSet,
    # but it demonstrates the fact that you might wish to initially dispatch
    # one set of data and then wait for the user to push a button to dispatch the animated data
    initialData = (
        "AxePos=-340.009, 45, NaN",
        "AzStat=-340.009, 0.0, 4565, 0x801",
        "AltStat=45.0, 0.0, 4565, 0x801",
    )
    
    tccTester.dispatch(initialData)

    animDataSet = (
        (   # enable stop buttons
            "AxePos=-340.009, 45, NaN",
            "AzStat=-340.009, 0.0, 4565, 0",
            "AltStat=45.0, 0.0, 4565, 0",
        ),
        (   # slew
            "ObjName='test object with a long name'",
            "ObjSys=FK5, 2000.0",
            "ObjNetPos=120.123450, 0.000000, 4494436859.66000, -2.345670, 0.000000, 4494436859.66000",
        ),
        (
            "AxePos=-348.121, 43.432, NaN",
            "TCCPos=-342.999, 38.623, NaN",
        ),
        (   # slew ends
            "SlewEnd",
            "AxisCmdState=Tracking, Tracking, Halted",
            "AxisErrCode='','', NoRestart",
            "AxePos=-342.974, 38.645, 10.0",
            "TCCPos=-342.974, 38.645, NaN",
        ),
    )
    tccTester.runDataSet(animDataSet)
    
    tccTester.tuiModel.reactor.run()
