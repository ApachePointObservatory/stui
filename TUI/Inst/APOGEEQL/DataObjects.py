#!/usr/bin/env python
"""Basic objects for APOGEE support

History:
2011-04-04 ROwen
"""
class DataList(object):
    """Hold a sorted collection of unique data items
    """
    def __init__(self, sharedName, keyName):
        """Create a data list sorted by a specified key, with unique values for each key
        
        @param[in] sharedName: item attribute whose value is shared by all items;
            when an item is added with a new value for this attribute the list is reset
        @param[in] keyName: item attribute by which the items are sorted
        """
        self._sharedName = str(sharedName)
        self._keyName = str(keyName)
        self._sharedValue = None
        self._keyItemDict = dict()
    
    def addItem(self, item):
        """Add an item. If an item already exists with the same key then replace it.
        """
        sharedValue = getattr(item, self._sharedName)
        key = getattr(item, self._keyName)
        if sharedValue != self._sharedValue:
            self._keyItemDict = dict()
            self._sharedValue = sharedValue
        self._keyItemDict[key] = item
    
    def clear(self):
        """Clear all data
        """
        self._keyItemDict = dict()
    
    def getList(self):
        """Return the data as a sorted list
        """
        return [self._keyItemDict[k] for k in sorted(self._keyItemDict.keys())]
    
    def getSharedValue(self):
        """Get the shared value
        """
        return self._sharedName
        

class ExpData(object):
    """Convenient summary of exposureData keyword
    """
    def __init__(self, keyVar):
        """Construct an ExpData from a apogeeql exposureData keyVar
        """
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


class UTRData(object):
    """Convenient summary of utrData keyword: data about an up-the-ramp read
    """
    def __init__(self, keyVar):
        """Construct an ExpData from a apogeeql exposureData keyVar
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
