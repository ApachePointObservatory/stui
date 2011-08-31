#!/usr/bin/env python
"""Basic objects for APOGEE support

History:
2011-04-04 ROwen
2011-07-28 ROwen    Added fields nReads and deltaSNR to ExpData.
2011-08-31 ROwen    DataList: added support for multiple shared names.
                    Added new fields to ExpData and UTRData.
"""
import RO.SeqUtil

class DataList(object):
    """Hold a sorted collection of unique data items
    """
    def __init__(self, sharedNames, keyName):
        """Create a data list sorted by a specified key, with unique values for each key
        
        @param[in] sharedNames: one or more item attributes whose value is shared by all items;
            the list is reset when an item is added with a new value for any of these attributes
        @param[in] keyName: item attribute by which the items are sorted
        """
        self._sharedNames = tuple(str(n) for n in RO.SeqUtil.asSequence(sharedNames))
        self._keyName = str(keyName)
        self._sharedValues = None
        self._keyItemDict = dict()
    
    def addItem(self, item):
        """Add an item. If an item already exists with the same key then replace it.
        
        Return True if the list was reset, False otherwise.
        """
        sharedValues = tuple(getattr(item, sn) for sn in self._sharedNames)
        key = getattr(item, self._keyName)
        if sharedValues != self._sharedValues:
            self._keyItemDict = dict()
            self._sharedValues = sharedValues
        self._keyItemDict[key] = item
    
    def clear(self):
        """Clear all data
        """
        self._keyItemDict = dict()
    
    def getList(self):
        """Return the data as a sorted list
        """
        return [self._keyItemDict[k] for k in sorted(self._keyItemDict.keys())]
    
    def getSharedValues(self):
        """Get the shared values
        """
        return self._sharedValues
    
    def setSharedValues(self, sharedValues):
        """Set shared values; clear the data list if sharedValues has changed
        """
        if self._sharedValues == sharedValues:
            return
        self._sharedValues = sharedValues
        self.clear()
        

class ExpData(object):
    """Convenient summary of exposureData keyword
    """
    def __init__(self, keyVar):
        """Construct an ExpData from an apogeeql exposureData keyVar
        """
        self.isPred = False
        self.plateID = keyVar[0]
        self.expNum = keyVar[1]
        self.expName = keyVar[2]
        self.expTime = keyVar[3]
        self.nReads = keyVar[4]
        self.snrGoal = keyVar[5]
        self.ditherPos = keyVar[6]
        self.snr = keyVar[7]
        self.netExpTime = keyVar[8]
        self.netSNR = keyVar[9]
        self.expType = keyVar[10]
        self.namedDitherPosition = keyVar[11]
        self.sortKey = (self.isPred, self.expNum)


class PredExpData(object):
    """Convenient summary of predictedExposureData keyword
    """
    def __init__(self, keyVar):
        """Construct an PredExpData from an apogeeql predictedExposureData keyVar
        """
        self.isPred = True
        self.plateID = keyVar[0]
        self.expNum = keyVar[1]
        self.expName = keyVar[2]
        self.expTime = keyVar[3]
        self.nReads = keyVar[4]
        self.snrGoal = keyVar[5]
        self.expType = keyVar[6]
        self.ditherPos = keyVar[7]
        self.namedDitherPosition = keyVar[8]
        self.sortKey = (self.isPred, self.expNum)


class UTRData(object):
    """Convenient summary of utrData keyword: data about an up-the-ramp read
    """
    def __init__(self, keyVar):
        """Construct an ExpData from an apogeeql exposureData keyVar
        """
        self.expNum = keyVar[0]
        self.readNum = keyVar[1]
        self.snr = keyVar[2]
        self.snrTotalLinFitCoeffs = keyVar[3:5]
        self.snrRecentLinFitCoeffs = keyVar[5:7]
        self.statusWord = keyVar[7]
        self.measDitherPos = keyVar[8]
        self.cmdDitherPos = keyVar[9]
        self.waveOffset = keyVar[10]
        self.expTimeEst = keyVar[11]
        self.numReadsToTarget = keyVar[12]
        self.nReads = keyVar[13]
        self.deltaSNR = keyVar[14]
        self.expType = keyVar[15]
        self.namedDitherPosition = keyVar[16]
