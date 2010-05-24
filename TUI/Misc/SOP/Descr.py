"""Objects that describe the basics of commands, stages and parameters
Used to paint the GUI
"""
from BasicWdg import *

def getCommandList():
    return (
        # sop doCalibs [narc=N] [nbias=N] [ndark=N] [nflat=N] [arcTime=FF.F]
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
        CommandWdgSet(
            name = "doCalibs",
            dispName = "Do Calibs",
            stageList = (
                StageWdgSet(
                    name = "calibs",
                    parameterList = (
                        IntParameterWdgSet(
                            name = "narc",
                            dispName = "Num Arc",
                        ),
                        IntParameterWdgSet(
                            name = "nbias",
                            dispName = "Num Bias",
                        ),
                        IntParameterWdgSet(
                            name = "ndark",
                            dispName = "Num Dark",
                        ),
                        IntParameterWdgSet(
                            name = "nflat",
                            dispName = "Num Flat",
                        ),
                        FloatParameterWdgSet(
                            name = "arcTime",
                            dispName = "Arc Time",
                            startNewColumn = True,
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "darkTime",
                            dispName = "Dark Time",
                            skipRows = 1,
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "flatTime",
                            dispName = "Flat Time",
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "guiderFlatTime",
                            dispName = "Guider Flat Time",
                            units = "sec",
                        ),
                    ),
                ),
            ),
        ),

        # sop gotoField [arcTime=FF.F] [flatTime=FF.F] [guiderFlatTime=FF.F]
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
        CommandWdgSet(
            name = "gotoField",
            dispName = "Go To Field",
            stageList = (
                StageWdgSet(
                    name = "slew",
                ),
                StageWdgSet(
                    name = "hartmann",
                ),
                StageWdgSet(
                    name = "calibs",
                    parameterList = (
                        FloatParameterWdgSet(
                            name = "arcTime",
                            dispName = "Arc Time",
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "flatTime",
                            dispName = "Flat Time",
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "guiderFlatTime",
                            dispName = "Guider Flat Time",
                            units = "sec",
                        ),
                    ),
                ),
                StageWdgSet(
                    name = "guider",
                ),
            ),
        ),
    )
