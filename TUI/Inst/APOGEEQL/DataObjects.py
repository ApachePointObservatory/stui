#!/usr/bin/env python
"""Basic objects for APOGEE support

History:
2011-04-04 ROwen
2011-07-28 ROwen    Added fields nReads and deltaSNR to ExpData.
2011-08-31 ROwen    DataList: added support for multiple shared names.
                    Added new fields to ExpData and UTRData.
2011-09-31 ROwen    Reverted to requiring a single shared name; too much complexity for too little gain.
                    Added sharedValue attribute to ExpData and PredExpData.
                    Renamed arguments for DataList.__init__.
"""
class DataList(object):
    """Hold a sorted collection of unique data items
    """
    def __init__(self, sharedName, uniqueName):
        """Create a sorted data list
        
        @param[in] sharedName: name of item attribute whose value is shared by all items;
            the list is reset when an item is added with a new value for this attribute
        @param[in] uniqueName: name of item attribute by which the items are sorted;
            the list will contain unique values for this item.
        """
        self._sharedName = sharedName
        self._uniqueName = uniqueName
        self._sharedValue = None
        self._keyItemDict = dict() # dict of uniqueKey: data item
    
    def addItem(self, item):
        """Add an item. If an item already exists with the same uniqueName then replace it.
        
        Return True if the list was reset, False otherwise.
        """
        sharedValue = getattr(item, self._sharedName)
        uniqueKey = getattr(item, self._uniqueName)
        if sharedValue != self._sharedValue:
            self._keyItemDict = dict()
            self._sharedValue = sharedValue
        self._keyItemDict[uniqueKey] = item
    
    def clear(self):
        """Clear all data
        """
        self._keyItemDict = dict()
    
    def getList(self):
        """Return the data, sorted by uniqueName
        """
        return [self._keyItemDict[k] for k in sorted(self._keyItemDict.keys())]

# These might be wanted someday. Better yet, make an attribute that you set or get.
#     def getSharedValue(self):
#         """Get the shared value
#         """
#         return self._sharedValue
#     
#     def setSharedValue(self, sharedValue):
#         """Set shared value; clear the data list if sharedValue has changed
#         """
#         if self._sharedValue == sharedValue:
#             return
#         self._sharedValue = sharedValue
#         self.clear()
        

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
        # synthesized values
        self.sharedValue = (self.plateID, self.expType)
        self.uniqueKey = (self.isPred, self.expNum)


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
        # synthesized values
        self.sharedValue = (self.plateID, self.expType)
        self.uniqueKey = (self.isPred, self.expNum)


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
