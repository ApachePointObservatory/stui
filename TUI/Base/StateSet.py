#!/usr/bin/env python
"""Keep track of named states in sorted order.
"""
import RO.AddCallback

class State(object):
    def __init__(self, name, severity, isCurrent, stateStr):
        self.name = name
        self.severity = int(severity)
        self.isCurrent = bool(isCurrent)
        self.stateStr = stateStr
    
    @property
    def values(self):
        return (self.name, self.severity, self.isCurrent, self.stateStr)
    
    def __getitem__(self, ind):
        return self.values[ind]
        
    def __eq__(self, rhs):
        return self.values == rhs.values

    def __str__(self):
        return "%s, %s, %s, %r" % (self.name, self.severity, self.isCurrent, self.stateStr)

    def __repr__(self):
        return "State(%s, %s, %s, %r)" % (self.name, self.severity, self.isCurrent, self.stateStr)


class StateSet(RO.AddCallback.BaseMixin):
    """A class to keep track of states of multiple devices
    
    Devices are ordered in importance and each state has an associated severity.
    States are sorted by severity first, then device order.
    
    Can call callback functions when the state changes.
    Callback functions may be specified at creation or via the addCallback method.
    """
    def __init__(self, devNames, callFunc):
        """Create a StateSet
        
        Inputs:
        - devNames: list of device names, highest priority first
        - callFunc: callback function or None if no function.
            The function will receive one argument: this StateSet.
        """
        RO.AddCallback.BaseMixin.__init__(self)
        
        # dict of device name: priority (larger is more important)
        self.priorityDict = {}
        numDevs = len(devNames)
        for ind, name in enumerate(devNames):
            self.priorityDict[name] = numDevs - ind
        # dict of device name: (severity, state)
        self.stateDict = {}
        if callFunc:
            self.addCallback(callFunc, callNow=False)
     
    def clearState(self, name):
        """Clear a state (a no-op if no state existed).
        
        If a state existed then callbacks are called.

        Raise ValueError if name unknown
        """
        if name not in self.priorityDict:
            raise ValueError("Unknown device %r" % (name,))
        clearedState = self.stateDict.pop(name, None)
        if clearedState:
            self._doCallbacks()
     
    def setState(self, name, severity, isCurrent=True, stateStr=""):
        """Set a state
        
        Inputs:
        - name: device name
        - severity: severity; an integer (larger is more severe)
        - isCurrent: is value current?; ignored if severity=None
        - stateStr: description of state; ignored if severity=None
        
        Raise ValueError if name unknown
        """
        if name not in self.priorityDict:
            raise ValueError("Unknown device %r" % (name,))
        self.stateDict[name] = State(name, severity, isCurrent, stateStr)
        self._doCallbacks()
    
    def getState(self, name):
        """Return state; return None if no state exists
                
        Raise ValueError if name unknown
        """
        if name not in self.priorityDict:
            raise ValueError("Unknown device %r" % (name,))
        self.stateDict.get(name)

    def getAllStates(self):
        """Return all states sorted by decreasing importance.
        """
        if not self.stateDict:
            return []
        sevList = []
        for state in self.stateDict.itervalues():
            sevList.append((state.severity, not state.isCurrent, self.priorityDict[state.name], state))
        sevList.sort()
        sevList.reverse()
        return [item[-1] for item in sevList]
   
    def getFirstState(self):
        """Return the most important state, or None if there are no states.
        """
        stateList = self.getAllStates()
        if not stateList:
            return None
        return stateList[0]


if __name__ == "__main__":
    print "Testing StateSet"
    nFailures = 0
    
    predState = (None, None, None)
    
    def setPredState(name, severity, isCurrent=True, stateStr=""):
        global predState
        if name == None:
            predState = None
        else:
            predState = State(name, severity, isCurrent, stateStr)

    def assertMainState(sd):
        global nFailures
        firstState = sd.getFirstState()
        if not firstState == predState:
            nFailures += 1
            print "Assertion failed: pred = %s != %s = worst" % (predState, firstState)
    
    sd = StateSet(("A", "B", "C"), assertMainState)
    setPredState("B", 1, True, "warning on B")
    sd.setState("B", 1, True, "warning on B")

    setPredState("A", 1, True, "warning on A") # A trumps B
    sd.setState("A", 1, True, "warning on A")

    setPredState("A", 1, True, "warning on A") # A trumps B and C
    sd.setState("C", 1, True, "warning on C")

    setPredState("B", 1, False, "warning on B") # not current trumps current
    sd.setState("B", 1, False, "warning on B")

    setPredState("C", 2, True, "error on C") # error trumps warning
    sd.setState("C", 2, True, "error on C")
    
    setPredState("B", 2, True, "error on B") # B trumps A
    sd.setState("B", 2, True, "error on B")

    setPredState("C", 2, True, "error on C") # restore prev condition: error trumps warning
    sd.setState("B", 1, False, "warning on B")

    setPredState("B", 1, False, "warning on B") # restore prev condition: not current trumps current
    sd.setState("C", 1, True, "warning on C")

    setPredState("A", 1, True, "warning on A") # restore prev condition: A trumps B and C
    sd.setState("B", 1, True, "warning on B")
    
    setPredState("B", 1, True, "warning on B") # restore prev condition: B trumps C
    sd.clearState("A")
    
    setPredState("C", 1, True, "warning on C") # warning on C is the only remaining condition
    sd.clearState("B")

    setPredState(None, None) # no conditions
    sd.clearState("C")

    if nFailures:
        print "%s failures" % (nFailures,)
    else:
        print "Passed"
