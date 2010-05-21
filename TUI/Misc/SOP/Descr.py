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
    """
    def __init__(self, baseName, dispName=None, entryWdgClass=RO.Wdg.IntEntry, units=None, **entryKeyArgs):
        BaseDescr.__init__(self, baseName, dispName)
        self.entryWdgClass = entryWdgClass
        self.units = units
        self.entryKeyArgs = entryKeyArgs

# describe all SOP commands in display order
CommandDescrList = (
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
                    ),
                    ParamDescr(
                        baseName = "flatTime",
                        dispName = "Flat Time",
                        entryWdgClass = RO.Wdg.FloatEntry,
                    ),
                    ParamDescr(
                        baseName = "guiderFlatTime",
                        dispName = "Guider Flat Time",
                        entryWdgClass = RO.Wdg.FloatEntry,
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
