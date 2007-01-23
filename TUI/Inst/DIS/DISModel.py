#!/usr/local/bin/python
"""An object that models the current state of DIS.

Camera info is in pairs in order: blue, red

It contains instance variables that are KeyVariables
or sets of KeyVariables (the "ByGSID" items).
Most of these are directly associated
with status keywords and a few are ones that I generate.

The "ByGSID" items are _KeyVarByGSID objects. See code near the end
to see what methods this object has.
Each such entry also has a current entry that is a normal KeyVariable
that gives data for current turret position.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

The entities are approximately listed in the order in which
they appear in dis status output.

2003-03-04 ROwen    First version; will need overhaul when dis status output overhauled.
2003-03-05 ROwen    Modified for simplified KeyVariables.
2003-03-07 ROwen    Added current states for step and zerostep.
2003-03-17 ROwen    Added dispersions; adapted for expected final keyword names
2003-03-19 ROwen    Further adaptations for actual final keyword names.
2003-03-24 ROwen    Added getModel as the favored way to retrieve the model.
2003-03-31 ROwen    Mod. to change grating name "medium" to "med".
2003-05-08 ROwen    Modified to use RO.CnvUtil.
2003-06-09 ROwen    Renamed from Model; removed dispatcher arg from getModel.
2003-07-16 ROwen    Added _TimeLim; use it for refresh commands.
2003-10-15 ROwen    Renamed ccdWindow to ccdUBWindow and ccdWindowBinned to ccdWindow,
                    since binned is now the standard representation (alas).
                    Added bin, unbin, minCoord and maxCoord methods.
2003-12-04 ROwen    Modified to handle NaN in CCD info.
2003-12-17 ROwen    Modified to refresh using refreshKeys and to use KeyVarFact.
2004-01-06 ROwen    Modified to use KeyVarFactory.setKeysRefreshCmd;
                    added _KeyVarByGSIDFactory to simplify use of setKeysRefreshCmd;
                    removed file name entries because disExpose handles that.
2004-05-18 ROwen    Bug fix: unbin referred to unbinnedCoors instead of unbinnedCoords.
                    Stopped importing math and Tkinter; they weren't used.
2004-07-23 ROwen    Updated the module doc string.
2004-09-14 ROwen    Minor tweak to clearify a function and make pychecker happier.
2004-09-23 ROwen    Modified to allow callNow as the default for keyVars.
2005-01-05 ROwen    Corrected turretName to be None instead of ""
                    if turret position is None or unknown.
"""
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel

# reasonable time for fairly fast commands
# DIS can take a minute to read out; add some margin
_TimeLim = 80

# turret position info dictionary
# keys are turret position
# values are a tuple of:
# - grating set # (or None if not at a grating set)
# - descriptive string
_TurretPosDict = {
    1: (1, "grating set 1"),
    2: (2, "grating set 2"),
    3: (None, "mirrors"),
    4: (None, "change set 1"),
    5: (None, "change set 2"),
}
_TurretPosNames = [_TurretPosDict[ii+1][1] for ii in range(len(_TurretPosDict))]

_theModel = None

def getModel():
    global _theModel
    if _theModel == None:
        _theModel = _Model()
    return _theModel
        
class _Model (object):
    def __init__(self,
    **kargs):
        tuiModel = TUI.TUIModel.getModel()
        self.actor = "dis"
        self.dispatcher = tuiModel.dispatcher
        self._refreshKeys = ""  # get all keys; this value is used here and in _KeyVarByGSID
        self.timelim = _TimeLim
        
        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = 1,
            dispatcher = self.dispatcher,
        )

        self.filterNames = keyVarFact(
            keyword="filterNames",
            nval=2,
            description="list of filter names",
        )

        self.filterID = keyVarFact(
            keyword="filterID",
            converters=RO.CnvUtil.asInt,
            description="filter wheel position",
        )

        self.filterName = keyVarFact(
            keyword="filterName",
            description="current filter",
        )

        self.maskNames = keyVarFact(
            keyword="maskNames",
            nval = 5,
            description="list of mask names",
        )
        
        self.maskID = keyVarFact(
            keyword="maskID",
            converters=RO.CnvUtil.asInt,
            description="ID of current mask",
        )

        self.maskName = keyVarFact(
            keyword="maskName",
            description="current mask",
        )

        self.shutter = keyVarFact(
            keyword="shutter",
            description="shutter state",
        )

        self.detent = keyVarFact(
            keyword="detent",
            converters=RO.CnvUtil.asInt,
            description="turret detent force (?)",
        )
        
        keyVarFact.setKeysRefreshCmd()
        
        # turret position names are a constant and so are never sent by dis
        self.turretNames = keyVarFact(
            keyword="loc_turretNames",
            nval = 5,
            description="list of turret names",
            isLocal=True,
        )
        self.turretNames.set(_TurretPosNames)

        self.turretPos = keyVarFact(
            keyword="turretPos",
            converters=RO.CnvUtil.asInt,
            description="turret pos",
        )

        self.turretName = keyVarFact(
            keyword = "loc_turret",
            description="description of turret position",
            isLocal = True,
        )

        self.gratingSetID = keyVarFact(
            keyword = "loc_gratingSetID",
            converters=RO.CnvUtil.asInt,
            description="grating set ID",
            isLocal = True,
        )
        
        keyVarByGSIDFact = _KeyVarByGSIDFactory(
            keyVarFact = keyVarFact,
            gsIDVar = self.gratingSetID,
        )

        self.gratingsByGSID = keyVarByGSIDFact(
            keyword = "names",
            nval = 2,
            description = "grating names",
            converters = RO.CnvUtil.StrCnv(subsDict={"medium":"med"}),
        )
        self.gratings = self.gratingsByGSID.getCurrKeyVar()

        self.dispersionsByGSID = keyVarByGSIDFact(
            keyword = "dispersions",
            nval = 2,
            description = "dispersion in Angstroms/unbinned pixel",
            converters = RO.CnvUtil.asFloatOrNone,
        )
        self.dispersions = self.dispersionsByGSID.getCurrKeyVar()

        self.zeroStepsByGSID = keyVarByGSIDFact(
            keyword = "zerosteps",
            nval = 2,
            description = "grating position at lambda=0 (steps) blue, red",
            converters = RO.CnvUtil.asInt,
        )
        self.zeroSteps = self.zeroStepsByGSID.getCurrKeyVar()

        self.stepsByGSID = keyVarByGSIDFact(
            keyword = "steps",
            nval = 2,
            description = "current grating position (steps), blue, red",
            converters = RO.CnvUtil.asInt,
        )
        self.steps = self.stepsByGSID.getCurrKeyVar()

        self.cmdLambdasByGSID = keyVarByGSIDFact(
            keyword = "cmdLambdas",
            nval = 2,
            description = "commanded blue, red lambda (\u00c5ngstroms)",
            converters = RO.CnvUtil.asInt,
        )
        self.cmdLambdas = self.cmdLambdasByGSID.getCurrKeyVar()

        self.actLambdasByGSID = keyVarByGSIDFact(
            keyword = "actLambdas",
            nval = 2,
            description = "actual blue, red lambda (\u00c5ngstroms)",
            converters = RO.CnvUtil.asInt,
        )
        self.actLambdas = self.actLambdasByGSID.getCurrKeyVar()
        
        keyVarFact.setKeysRefreshCmd()

        self.ccdState = keyVarFact(
            keyword="ccdState",
            description="ccd state",
        )

        self.ccdBin = keyVarFact(
            keyword="ccdBin",
            nval = 2,
            converters=RO.CnvUtil.asIntOrNone,
            description="ccd binning",
        )
        
        self.ccdWindow = keyVarFact(
            keyword="loc_ccdWindow",
            nval = 4,
            converters=RO.CnvUtil.asIntOrNone,
            description="ccd window, binned: minX, minY, maxX, maxY (inclusive)",
            isLocal = True,
        )

        self.ccdUBWindow = keyVarFact(
            keyword="ccdUBWindow",
            nval = 4,
            converters=RO.CnvUtil.asIntOrNone,
            description="ccd window, unbinned: minX, minY, maxX, maxY (inclusive)",
        )

        self.ccdOverscan = keyVarFact(
            keyword="ccdOverscan",
            nval = 2,
            converters=RO.CnvUtil.asIntOrNone,
            description="ccd overscan",
        )

        self.ccdTemps = keyVarFact(
            keyword="ccdTemps",
            nval=2,
            converters=RO.CnvUtil.asFloatOrNone,
            description="temperature (C) of blue and red CCDs",
        )
        
        self.ccdHeaters = keyVarFact(
            keyword="ccdHeaters",
            nval=2,
            converters=RO.CnvUtil.asFloatOrNone,
            description="heater current (%) for blue, red CCD",
        )
        
        keyVarFact.setKeysRefreshCmd()
        
        # set up callbacks
        self.turretPos.addCallback(self.__updTurretPos)
        self.ccdBin.addCallback(self._updCCDWindow)
        self.ccdUBWindow.addCallback(self._updCCDWindow)

    def __updTurretPos(self, *args, **kargs):
        """Turret position has changed;
        Updates self.turretName and (if changed) the grating set ID
        (which in turn updates all self.xxxByGSID entries)
        """
        turretPos, isCurrent = self.turretPos.getInd(0)
#       print "__updTurretPos: turretPos = %s, isCurrent = %s" % (turretPos, isCurrent)
        newGratingSetID, turretName = _TurretPosDict.get(turretPos, (None, None))
#       print "__updTurretPos: gratingSetID = %r, turretName = %r" % (newGratingSetID, turretName)
        self.turretName.set((turretName,), isCurrent)
        if (newGratingSetID, isCurrent) != self.gratingSetID.getInd(0):
#           print "__updTurretPos: updating grating set ID"
            self.gratingSetID.set((newGratingSetID,), isCurrent)
    
    def _updCCDWindow(self, *args, **kargs):
        """Updated ccdWindow.
        
        Called by two different keyVars, so ignores the argument data
        and reads the keyVars directly.
        """
        binFac, binCurrent = self.ccdBin.get()
        ubWindow, windowCurrent = self.ccdUBWindow.get()
        isCurrent = binCurrent and windowCurrent
        try:
            bWindow = self.bin(ubWindow, binFac)
        except TypeError:
            # occurs if None is present in list of values
            bWindow = [None] * 4
        self.ccdWindow.set(bWindow, isCurrent)
    
    def bin(self, unbinnedCoords, binFac):
        """Converts unbinned to binned coordinates.
        
        The output is constrained to be in range for the given bin factor
        (if a dimension does not divide evenly by the bin factor
        then some valid unbinned coords are out of range when binned).

        Inputs:
        - unbinnedCoords: 2 or 4 coords
        
        If any element of binnedCoords or binFac is None, all returned elements are None.
        """
        assert len(unbinnedCoords) in (2, 4), "unbinnedCoords must have 2 or 4 elements; unbinnedCoords = %r" % unbinnedCoords
        assert len(binFac) == 2, "binFac must have 2 elements; binFac = %r" % binFac
            
        if None in unbinnedCoords or None in binFac:
            return (None,)*len(unbinnedCoords)
        
        binXYXY = binFac * 2

        # compute value ignoring limits
        binnedCoords = [1 + ((unbinnedCoords[ind] - 1) // int(binXYXY[ind]))
            for ind in range(len(unbinnedCoords))]
        
        # apply limits
        minBinXYXY = self.minCoord(binFac)*2
        maxBinXYXY = self.maxCoord(binFac)*2
        binnedCoords = [min(max(binnedCoords[ind], minBinXYXY[ind]), maxBinXYXY[ind])
            for ind in range(len(binnedCoords))]
#       print "bin: converted %r bin %r to %r" % (unbinnedCoords, binFac, binnedCoords)
        return binnedCoords
        
    def unbin(self, binnedCoords, binFac):
        """Converts binned to unbinned coordinates.
        
        The output is constrained to be in range (but such constraint is only
        needed if the input was out of range).
        
        A binned coordinate can be be converted to multiple unbinned choices (if binFac > 1).
        The first two coords are converted to the smallest choice,
        the second two (if supplied) are converted to the largest choice.
        Thus 4 coordinates are treated as a window with LL, UR coordinates, inclusive.

        Inputs:
        - binnedCoords: 2 or 4 coords; see note above
        
        If any element of binnedCoords or binFac is None, all returned elements are None.
        """
        assert len(binnedCoords) in (2, 4), "binnedCoords must have 2 or 4 elements; binnedCoords = %r" % binnedCoords
        assert len(binFac) == 2, "binFac must have 2 elements; binFac = %r" % binFac
        
        if None in binnedCoords or None in binFac:
            return (None,)*len(binnedCoords)

        binXYXY = binFac * 2
        subadd = (1, 1, 0, 0)
        
        # compute value ignoring limits
        unbinnedCoords = [((binnedCoords[ind] - subadd[ind]) * binXYXY[ind]) + subadd[ind]
            for ind in range(len(binnedCoords))]
            
        # apply limits
        minUnbinXYXY = self.minCoord()*2
        maxUnbinXYXY = self.maxCoord()*2
        unbinnedCoords = [min(max(unbinnedCoords[ind], minUnbinXYXY[ind]), maxUnbinXYXY[ind])
            for ind in range(len(unbinnedCoords))]
#       print "unbin: converted %r bin %r to %r" % (binnedCoords, binFac, unbinnedCoords)
        return unbinnedCoords
    
    def maxCoord(self, binFac=(1,1)):
        """Returns the maximum binned CCD coordinate, given a bin factor.
        """
        assert len(binFac) == 2, "binFac must have 2 elements; binFac = %r" % binFac
        return [(2048, 1028)[ind] // int(binFac[ind]) for ind in range(2)]

    def minCoord(self, binFac=(1,1)):
        """Returns the minimum binned CCD coordinate, given a bin factor.
        """
        assert len(binFac) == 2, "binFac must have 2 elements; binFac = %r" % binFac
        return (1, 1)


class _KeyVarByGSIDFactory:
    """A factory to produce _KeyVarByGSID objects.
    """
    def __init__(self, keyVarFact, gsIDVar):
        self._keyVarFact = keyVarFact
        self._gsIDVar = gsIDVar
    
    def __call__(self, keyword, description, converters, nval=1, isLocal=False, doCurr=True):
        """Return a _KeyVarByGSID object.
        
        Arguments are the same as _KeyVarByGSID, minus keyVarFact and gsIDVar.
        """
        return _KeyVarByGSID(
            keyVarFact = self._keyVarFact,
            gsIDVar = self._gsIDVar,
            keyword = keyword,
            description = description,
            converters = converters,
            nval = nval,
            isLocal = isLocal,
            doCurr = doCurr,
        )


class _KeyVarByGSID:
    def __init__(self, keyVarFact, gsIDVar, keyword, description, converters, nval=1, isLocal=False, doCurr=True):
        """Generates three keyVariables, one each for:
        - grating set 1
        - grating set 2
        - current grating set (optional), automatically updated from the other two
        
        The arguments are the same as for RO.KeyVariable.KeyVarFactory, plus:
        - keyVarFact: key variable factory with actor and dispatcher set
        - gsIDVar   grating set ID KeyVariable
        - doCurr: do generate a current grating set and automatically update it
        """
        self._gsIDVar = gsIDVar
        self._nullValueList = (None,)*nval
    
        self.keyVarDict = {}
        for gsid in (1,2):
            self.keyVarDict[gsid] = keyVarFact(
                keyword = "gset%d%s" % (gsid, keyword),
                nval = nval,
                description = "%s for grating set %d" % (description, gsid),
                converters = converters,
                isLocal = isLocal,
            )

        if doCurr:
            self.currKeyVar = keyVarFact(
                nval = nval,
                keyword = "%s" % (keyword,),
                description = "%s for current grating set" % (description,),
                converters = converters,
                isLocal = True,
            )
            for keyVar in self.keyVarDict.itervalues():
                keyVar.addCallback(self._updCurrKeyVar)
            gsIDVar.addCallback(self._updCurrKeyVar)
        else:
            self.currKeyVar = None
    
    def getKeyVarByID(self, gsID):
        """Returns the keyVar for the specified gsID,
        or None if GSID is invalid.
        """
        return self.keyVarDict.get(gsID)
    
    def getCurrKeyVar(self):
        """Returns the keyVar for the current grating set
        or None of none was generated.
        """
        return self.currKeyVar
    
    def getKeyVarSet(self):
        """Returns a tuple:
        - keyVar for guide set 1
        - keyvar for guide set 2
        - current keyVar
        """
        return (self.keyVarDict[1], self.keyVarDict[2], self.currKeyVar)
    
    def _updCurrKeyVar(self, *args, **kargs):
        gsID, gsIDCurr = self._gsIDVar.getInd(0)
        keyVar = self.getKeyVarByID(gsID)
        if keyVar == None:
            valueList = self._nullValueList
            valueIsCurrent = gsIDCurr
        else:
            valueList, keyVarIsCurrent = keyVar.get()
            valueIsCurrent = gsIDCurr and keyVarIsCurrent
            
        self.currKeyVar.set(valueList, valueIsCurrent)


if __name__ == "__main__":
    getModel()
