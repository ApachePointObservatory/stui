#!/usr/bin/env python
"""Parse APOGEE limit switch keywords

History:
2011-05-04 ROwen
2011-05-17 ROwen    Bug fix: assumed 6 values, so reported a problem when dither limits were OK.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import RO.Constants

def limitParser(keyVar):
    """Parse an APOGEE limit switch KeyVar
    
    Returns:
    * A list of limit data as single character strings ("0", "1" or "?")
    * severity: one of the following (tested in order)
      * RO.Constants.sevNormal if all limit switches off
      * RO.Constants.sevError if both the forward and reverse limit switch are on for any actuator
      * RO.Constants.sevWarning otherwise
    """
    severity = RO.Constants.sevNormal
    numActuators = len(keyVar) / 2
    limStrDict = {
        True: "1",
        False: "0",
    }
    limStrList = [limStrDict.get(val, "?") for val in keyVar]
    if limStrList != ["0"]*len(keyVar):
        if len([ind for ind in range(numActuators)
                if keyVar[ind*2] == True and keyVar[(ind*2)+1] == True]) > 0:
            severity = RO.Constants.sevError
        else:
            severity = RO.Constants.sevWarning
    return limStrList, severity


# nicer output but less direct than showing the limits directly and the complexity is probably not justified
#             if True in self.model.collLimitSwitch:
#                 # some switches have fired so treat ? the same as False
#                 currLimBools = [(val == True) for val in self.model.collLimitSwitch]
#                 limStrList = []
#                 for limName, limValPair, limSev in (
#                     ("Both", (True,  True),  RO.Constants.sevError),
#                     ("Rev", (True,  False), RO.Constants.sevWarning),
#                     ("Fwd", (False, True),  RO.Constants.sevWarning),
#                 ):
#                     actuatorList = [str(ind+1) for ind in range(3)
#                         if (currLimBools[ind*2], currLimBools[(ind*2)+1]) == limValPair]
#                     if actuatorList:
#                         limStrList.append("%s Lim %s" % (limName, " ".join(actuatorList)))
#                         severity = max(severity, limSev) 
#                     isCurrent = isCurrent and self.model.collLimitSwitch
#                 
#                 sumStr = ", ".join(limStrList)
#             elif None in self.model.collLimitSwitch:
#                 actuatorList = [str(ind+1) for ind in range(3) if
#                     self.model.collLimitSwitch[ind*2] == None
#                     or self.model.collLimitSwitch[(ind*2)+1] == None]
#                 sumStr = "Unknown Lim %s" % (" ".join(actuatorList))
#                 severity = RO.Constants.sevWarning
