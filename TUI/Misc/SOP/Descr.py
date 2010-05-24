#!/usr/bin/env python
"""Objects that describe the basics of commands, stages and parameters
Used to paint the GUI
"""
import RO.Wdg

class BaseDescr(object):
    """Basic description of sop command, stage or parameter
    
    Attributes include:
    - fullName: dotted name of item (e.g. command.stage.substage)
    - baseName: last field of fullName
    - dispName: name for GUI display
    - descrList: sequence of descriptions of subordinate objects
    """
    def __init__(self, baseName, dispName=None, descrList=None):
        """Create a BaseDescr
        
        Inputs:
        - baseName: basic name (last field of full name)
        - dispName: name to use for display in the GUI; defaults to capitalized baseName
        - descrList: sequence of descriptions of subordinate objects
            (e.g. stages for a command, parameters for a stage)
            
        Warning: be sure to call _prependToFullName before using the results
        (but this cannot be done until the command is constructed)
        """
        self.baseName = baseName
        self.fullName = self.baseName
        if dispName == None:
            dispName = baseName.title()
        self.dispName = dispName
        self.descrList = descrList or ()
        self._addPrefixToFullName(self.baseName)

    def _addPrefixToFullName(self, prefix):
        """Add prefix to fullName
        """
        for descr in self.descrList:
            descr.fullName = "%s.%s" % (prefix, descr.fullName)
            descr._addPrefixToFullName(prefix)

class CommandDescr(BaseDescr):
    """Description of a sop command
    """
    def __init__(self, baseName, dispName=None, descrList=None, actor="sop"):
        BaseDescr.__init__(self, baseName, dispName, descrList)
        self.actor = actor

class StageDescr(BaseDescr):
    """Description of sop command stage
    """
    def __init__(self, baseName, dispName=None, defEnabled=True, descrList=None):
        BaseDescr.__init__(self, baseName, dispName, descrList)
        self.defEnabled = True

class ParamDescr(BaseDescr):
    """Description of sop command stage parameter
    
    Inputs:
    - baseName: base name of parameter
    - dispName: name to display for this parameter (if different than baseName.titlecase())
    - skipRows: number of rows to skip before displaying this parameter
    - startNewColumn: if True then start this parameter in a new column (and then skip skipRows)
    - entryWdgClass: class of RO.Wdg for the entry widget
    - all remaining keyword arguments are used sent to the entryWdgClass constructor
    """
    def __init__(self,
        baseName,
        dispName = None,
        skipRows = 0,
        startNewColumn = False,
        entryWdgClass = RO.Wdg.IntEntry,
        defValue = None,
        units = None,
    **entryKeyArgs):
        BaseDescr.__init__(self, baseName, dispName)
        self.entryWdgClass = entryWdgClass
        self.skipRows = skipRows
        self.startNewColumn = startNewColumn
        self.defValue = defValue
        self.units = units
        self.entryKeyArgs = entryKeyArgs

# describe all SOP commands in display order
CommandDescrList = (
# Usage: sop doCalibs [narc=N] [nbias=N] [ndark=N] [nflat=N] [arcTime=FF.F]
#          [darkTime=FF.F] [flatTime=FF.F] [guiderFlatTime=FF.F]
# 
# Take a set of calibration frames
# Arguments:
# 	arcTime                             Exposure time for arcs
# 	darkTime                            Exposure time for darks
# 	flatTime                            Exposure time for flats
# 	guiderFlatTime                      Exposure time for guider flats
# 	narc                                Number of arcs to take
# 	nbias                               Number of biases to take
# 	ndark                               Number of darks to take
# 	nflat                               Number of flats to take
    CommandDescr(
        baseName = "doCalibs",
        dispName = "Do Calibs",
        descrList = (
            StageDescr(
                baseName = "calibs",
                descrList = (
                    ParamDescr(
                        baseName = "narc",
                        dispName = "Num Arc",
                        entryWdgClass = RO.Wdg.IntEntry,
                    ),
                    ParamDescr(
                        baseName = "nbias",
                        dispName = "Num Bias",
                        entryWdgClass = RO.Wdg.IntEntry,
                    ),
                    ParamDescr(
                        baseName = "ndark",
                        dispName = "Num Dark",
                        entryWdgClass = RO.Wdg.IntEntry,
                    ),
                    ParamDescr(
                        baseName = "nflat",
                        dispName = "Num Flat",
                        entryWdgClass = RO.Wdg.IntEntry,
                    ),
                    ParamDescr(
                        baseName = "arcTime",
                        dispName = "Arc Time",
                        startNewColumn = True,
                        entryWdgClass = RO.Wdg.FloatEntry,
                        units = "sec",
                    ),
                    ParamDescr(
                        baseName = "darkTime",
                        dispName = "Dark Time",
                        skipRows = 1,
                        entryWdgClass = RO.Wdg.FloatEntry,
                        units = "sec",
                    ),
                    ParamDescr(
                        baseName = "flatTime",
                        dispName = "Flat Time",
                        entryWdgClass = RO.Wdg.FloatEntry,
                        units = "sec",
                    ),
                    ParamDescr(
                        baseName = "guiderFlatTime",
                        dispName = "Guider Flat Time",
                        entryWdgClass = RO.Wdg.FloatEntry,
                        units = "sec",
                    ),
                ),
            ),
        ),
    ),
# Usage: sop gotoField [arcTime=FF.F] [flatTime=FF.F] [guiderFlatTime=FF.F]
#           [noSlew] [noHartmann] [noCalibs] [noGuider] [abort]
# 
# Slew to the current cartridge/pointing
# Arguments:
# 	abort                               Abort a command
# 	arcTime                             Exposure time for arcs
# 	flatTime                            Exposure time for flats
# 	guiderFlatTime                      Exposure time for guider flats
# 	noCalibs                            Don't run the calibration step
# 	noGuider                            Don't start the guider
# 	noHartmann                          Don't make Hartmann corrections
# 	noSlew                              Don't slew to field
# 
# Slew to the position of the currently loaded cartridge. At the beginning of the
# slew all the lamps are turned on and the flat field screen petals are closed.
# When you arrive at the field, all the lamps are turned off again and the flat
# field petals are opened if you specified openFFS.
# 
    CommandDescr(
        baseName = "gotoField",
        dispName = "Go To Field",
        descrList = (
            StageDescr(
                baseName = "slew",
            ),
            StageDescr(
                baseName = "hartmann",
            ),
            StageDescr(
                baseName = "calibs",
                descrList = (
                    ParamDescr(
                        baseName = "arcTime",
                        dispName = "Arc Time",
                        entryWdgClass = RO.Wdg.FloatEntry,
                        units = "sec",
                    ),
                    ParamDescr(
                        baseName = "flatTime",
                        dispName = "Flat Time",
                        entryWdgClass = RO.Wdg.FloatEntry,
                        units = "sec",
                    ),
                    ParamDescr(
                        baseName = "guiderFlatTime",
                        dispName = "Guider Flat Time",
                        entryWdgClass = RO.Wdg.FloatEntry,
                        units = "sec",
                    ),
                ),
            ),
            StageDescr(
                baseName = "guider",
            ),
        ),
    ),
)

if __name__ == "__main__":
    print "SOP Commands"
    for command in CommandDescrList:
        print "Command fullName=%s, dispName=%s" % (command.fullName, command.dispName)
        for stage in command.descrList:
            print "  Stage fullName=%s, dispName=%s" % (stage.fullName, stage.dispName)
            for param in stage.descrList:
                print "    Pram fullName=%s, dispName=%s" % (param.fullName, param.dispName)
