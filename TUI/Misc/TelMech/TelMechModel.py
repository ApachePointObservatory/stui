#!/usr/bin/env python
"""An object that models the current state of the enclosure controller.

Information about various devices in the telescope enclosure.
Devices are broken up into categories, e.g. Fans, Lights.
Information about each category of devices is stored as follows:
model.catDict is a dictionary whose keys are device categories
and values are CatInfo objects (described below) which contain
information about that category of device.

2004-12-27 ROwen
2005-08-15 ROwen    Bug fix: had stairs and outside lights swapped.
2005-09-23 ROwen    Made polling for status a refresh command
                    so it is more easily hidden in the log window.
2005-09-30 ROwen    Fixed order of fans.
2006-04-05 ROwen    Can disable polling by setting _StatusIntervalMS = 0 or None.
                    This is preparatory to switching to telmech, which will not need it at all.
                    Meanwhile it just helps me run from work.
2006-05-04 ROwen    Renamed from EnclosureModel to TelMechModel.
                    Modified to use the telmech actor.
                    As a result, there is now one keyword per device.
                    Removed polling for status.
                    Added catNameSingular to CatInfo.
2007-06-22 ROwen    Added the Eyelids category.
2007-06-26 ROwen    Added devState and devIsCurrent attributes to the CatInfo class.
2007-06-27 ROwen    Added covers and tertrot entries.
                    Modified stateToBoolOrNone to use ? as "unknown value".
2007-09-17 ROwen    Put the tertiary position names in order of increasing tertiary rotation angle.
"""
__all__ = ["getModel"]

import numpy
import RO.AddCallback
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel

# reasonable time for device toggle commands;
_TimeLim = 120

_theModel = None

def getModel():
    global _theModel
    if _theModel == None:
        _theModel = _Model()
    return _theModel

def stateToBoolOrNone(strVal):
    lowStrVal = strVal.lower()
    if lowStrVal in ("close", "off"):
        return False
    elif lowStrVal in ("open", "on"):
        return True
    elif lowStrVal == "?":
        return None
    else:
        raise ValueError("unknown state %r" % strVal)

def tertRotConverter(strVal):
    if strVal == "?":
        return None
    return str(strVal)

class CatInfo(RO.AddCallback.BaseMixin):
    """Information about a category of devices, e.g. Fans, Lights.
    
    Attributes:
    - catName: the name of the category
    - catNameSingular: the name of the category with the final "s" or "S" missing, if present.
    - devDict: an ordered dictionary of device name: boolean keyword variable
    - stateNames: a word describing the False and True state
    - verbNames: the verb used to command the False and True state;
        indeterminate if readOnly
    - readOnly: if True, this category of devices can be read
        but cannot be controlled
    - devState: numpy array representing the state of each device; values are 0, 1 or numpy.nan
    - devIsCurrent: numpy bool array representing the isCurrent of each device
    """
    def __init__(self, keyVarFact, catName, devNames, isReadOnly=False, isOpenShut=False, callFunc=None):
        RO.AddCallback.BaseMixin.__init__(self)
        self.catName = catName
        if catName.lower().endswith("s"):
            self.catNameSingular = catName[:-1]
        else:
            self.catNameSingular = catName
        
        self.devDict = RO.Alg.OrderedDict() # dict of device name: keyword variable
        self.devIndDict = {}    # dict of device name: index

        self.devState = numpy.zeros([len(devNames)], numpy.float)
        self.devIsCurrent = numpy.zeros([len(devNames)], numpy.bool)
        
        self.readOnly = isReadOnly
        if isOpenShut:
            self.stateNames = ("Closed", "Open")
            self.verbNames = ("Close", "Open")
        else:
            self.stateNames = ("Off", "On")
            self.verbNames = self.stateNames
        
        for ind, devName in enumerate(devNames):
            keyVar = keyVarFact(devName)
            self.devDict[devName] = keyVar
            self.devIndDict[devName] = ind
            keyVar.addIndexedCallback(self._updateDevState, callNow=False)
        
        if callFunc:
            self.addCallback(callFunc, callNow=False)
        
    def getStateStr(self, boolVal):
        """Returns a string representation of the state;
        one of:
        - "Off" or "Closed" if false
        - "On"  or "Open" if true
        """
        return self.stateNames[bool(boolVal)]
    
    def getVerbStr(self, boolVal):
        """Returns a the appropriate command verb
        for the specified date; one of:
        - "Off" or "Close" if false
        - "On"  or "Open" if true
        """
        return self.verbNames[bool(boolVal)]
    
    def _updateDevState(self, value, isCurrent, keyVar):
        """Update devState"""
        ind = self.devIndDict[keyVar.keyword]
        if value == None:
            value = numpy.nan
        self.devState[ind] = value
        self.devIsCurrent[ind] = isCurrent
        self._doCallbacks()

    
class _Model (object):
    def __init__(self,
    **kargs):
        tuiModel = TUI.TUIModel.getModel()
        self.actor = "telmech"
        self.dispatcher = tuiModel.dispatcher
        self._connection = tuiModel.getConnection()
        self.timeLim = _TimeLim
        self._pollID = None
        self._tkRoot = tuiModel.root
        
        self.__keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = stateToBoolOrNone,
            nval = 1,
            dispatcher = self.dispatcher,
        )
        
        self.catDict = {}

        self._addCat(
            catName = "Enable",
            devNames = (
                "Telescope",
            ),
        )
        self._addCat(
            catName = "Fans",
            devNames = (
                "IntExhaust",
                "TelExhaust",
                "Press",
            ),
        )
        self._addCat(
            catName = "Heaters",
            devNames = (
                "H4",
                "H8",
                "H12",
                "H16",
                "H20",
                "H24",
            ),
        )
        self._addCat(
            catName = "Lights",
            devNames = (
                "FHalides",
                "RHalides",
                "Incand",
                "Platform",
                "Catwalk", # was outside
                "Stairs",
                "Int_Incand",
                "Int_Fluor",
            ),
        )
        self._addCat(
            catName = "Louvers",
            devNames = (
                "LUp", "LMid", "LLow",
                "RUp", "RMid", "RLow",
                "Stairw",
                "LPit", "RPit",
            ),
            isOpenShut = True,
        )
        self._addCat(
            catName = "Shutters",
            devNames = (
                "Left",
                "Right",
            ),
            isReadOnly = True,
            isOpenShut = True,
        )
        self._addCat(
            catName = "Eyelids",
            devNames = (
                "NA2",
                "TR3",
                "BC2",
                "TR4",
                "NA1",
                "TR1",
                "BC1",
                "TR2",
            ),
            isOpenShut = True,
        )
        
        self.covers = self.__keyVarFact("covers")

        self.tertRot = self.__keyVarFact("tertRot", converters=tertRotConverter)

        self.__keyVarFact.setKeysRefreshCmd()
    
    def _addCat(self, catName, devNames, isReadOnly=False, isOpenShut = False):
        catInfo = CatInfo(
            keyVarFact = self.__keyVarFact,
            catName = catName,
            devNames = devNames,
            isReadOnly = isReadOnly,
            isOpenShut = isOpenShut,
        )
        self.catDict[catName] = catInfo


if __name__ == "__main__":
    getModel()
