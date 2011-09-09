#!/usr/bin/env python
"""Basic objects for APOGEE support

History:
2011-04-04 ROwen
2011-07-28 ROwen    Added fields nReads and deltaSNR to ExpData.
2011-08-31 ROwen    DataList: added support for multiple shared names.
                    Added new fields to ExpData and UTRData.
2011-09-02 ROwen    DataList:
                    - Return to requiring a single shared name; multiple names were an unnecessary complication.
                    - Added sharedName, uniqueName and sharedValue properties to DataList.
                    - Renamed the constructor arguments.
                    - Improved the documentation.
                    ExpData and PredExpData:
                    - Added sharedValue attribute
                    - Renamed sortKey attribute to uniqueValue.
2011-09-09 ROwen    Removed isPred and uniqueValue attributes from ExpData and PredExpData.
"""
class DataList(object):
    """Hold a sorted collection of data items having the same value of one attribute and a unique value of another.
    """
    def __init__(self, sharedName, uniqueName):
        """Create a DataList
        
        @param[in] sharedName: name of data item attribute whose value will be the same for all items;
            the list is reset when an item is added with a new value for this attribute.
        @param[in] uniqueName: name of data item attribute whose value will be unique for all items;
            if an item is added with a duplicate unique value, the old item is replaced.
            Also used to sort the data returned by getList.
        """
        self._sharedName = sharedName
        self._uniqueName = uniqueName
        self._sharedValue = None
        self._itemDict = dict()    # dict of uniqueValue: data item
    
    def addItem(self, item):
        """Add a data item
        
        If an existing item has the same shared value, the existing item is replaced.
        If the item has a different shared value then the existing data items
        then the list is reset to contain only the newly added item.
        
        Return True if the list was reset, False otherwise.
        """
        sharedValue = getattr(item, self._sharedName)
        uniqueValue = getattr(item, self._uniqueName)
        didReset = False
        if sharedValue != self._sharedValue:
            self._itemDict = dict()
            self._sharedValue = sharedValue
            didReset = True
        self._itemDict[uniqueValue] = item
        return didReset
    
    def clear(self):
        """Clear the data list
        """
        self._itemDict = dict()
    
    def getList(self):
        """Return the data items as a list sorted by their unique values.
        """
        return [self._itemDict[k] for k in sorted(self._itemDict.keys())]
    
    @property
    def sharedName(self):
        """Get sharedName, as specified to the constructor
        """
        return self._sharedName
    
    @property
    def uniqueName(self):
        """Get uniqueName, as specified to the constructor
        """
        return self._uniqueName

    @property
    def sharedValue(self):
        """Get the current shared value
        """
        return self._sharedValue
    
    @sharedValue.setter # requires Python 2.6
    def sharedValue(self, sharedValue):
        """Set the shared value; clear the data list if sharedValue has changed
        """
        if self._sharedValue == sharedValue:
            return
        self._sharedValue = sharedValue
        self.clear()
    
    def __bool__(self):
        return bool(self._itemDict)
    
    def __len__(self):
        return len(self._itemDict)
        

class ExpData(object):
    """Convenient summary of exposureData keyword
    """
    def __init__(self, keyVar):
        """Construct an ExpData from an apogeeql exposureData keyVar
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
        self.expType = keyVar[10]
        self.namedDitherPosition = keyVar[11]
        
        # synthesized values
        self.sharedValue = (self.plateID, self.expType)


class PredExpData(object):
    """Convenient summary of predictedExposureData keyword
    """
    def __init__(self, keyVar):
        """Construct an PredExpData from an apogeeql predictedExposureData keyVar
        """
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
