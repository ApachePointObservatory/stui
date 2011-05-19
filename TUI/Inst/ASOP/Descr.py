"""Objects that describe the basics of commands, stages and parameters
Used to paint the GUI

History:
2010-05-27 ROwen  from SOP
2011-05-18 SBeland modified (slightly) for Apogee SOP (ASOP) with new sop actor commands
"""
from TUI.Inst.SOP.CommandWdgSet import *

def getCommandList():
    return (
        # guider loadcartridge command
        LoadCartridgeCommandWdgSetSet(),

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
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "flatTime",
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "guiderFlatTime",
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "guiderExpTime",
                            units = "sec",
                        ),
                    ),
                ),
                StageWdgSet(
                    name = "guider",
                ),
            ),
        ),

        # Usage: sop doApogeeScience [ditherSeq=S] [repeatSeq=N] [expTime=FF.F]
        # 
        # Take a set of science frames
        # Arguments:
        # 	expTime                             Exposure time
        # 	nexp                                Number of exposures to take
        CommandWdgSet(
            name = "doApogeeScience",
            stageList = (
                StageWdgSet(
                    name = "doApogeeScience",
                    parameterList = (
                        StringParameterWdgSet(
                            name = "ditherSeq",
                            defValue = "AB",
                        ),
                        CountParameterWdgSet(
                            name = "seqCount",
                            defValue = 3,
                        ),
                        FloatParameterWdgSet(
                            name = "expTime",
                            startNewColumn = True,
                            defValue = 500.0,
                            units = "sec",
                        ),
                    ),
                ),
            ),
        ),
        
        # sop doApogeeCalibs [ndark=N] [nflat=N] [nUNe=N] [nThArNe=N] 
        #          [darkTime=FF.F] [flatTime=FF.F] [UNeTime=FF.F] [ThArNeTime=FF.F]
        # 
        # Take a set of calibration frames
        # Arguments:
        # 	UNeTime                             Exposure time for UNe lamp 
        # 	ThArNeTime                          Exposure time for ThArNe lamp 
        # 	darkTime                            Exposure time for darks
        # 	flatTime                            Exposure time for flats
        # 	narc                                Number of arcs to take
        # 	ndark                               Number of darks to take
        # 	nflat                               Number of flats to take
#         CommandWdgSet(
#             name = "doApogeeCalibs",
#             stageList = (
#                 StageWdgSet(
#                     name = "doApogeeCalibs",
#                     parameterList = (
#                         CountParameterWdgSet(
#                             name = "nDark",
#                             defValue = 50,
#                         ),
#                         CountParameterWdgSet(
#                             name = "nFlat",
#                             defValue = 10,
#                         ),
#                         CountParameterWdgSet(
#                             name = "nUNe",
#                             defValue = 40,
#                         ),
#                         CountParameterWdgSet(
#                             name = "nThArNe",
#                             defValue = 40,
#                         ),
#                         FloatParameterWdgSet(
#                             name = "darkTime",
#                             units = "sec",
#                             startNewColumn = True,
#                         ),
#                         FloatParameterWdgSet(
#                             name = "flatTime",
#                             units = "sec",
#                         ),
#                         FloatParameterWdgSet(
#                             name = "UNeTime",
#                             units = "sec",
#                         ),
#                         FloatParameterWdgSet(
#                             name = "ThArNeTime",
#                             units = "sec",
#                         ),
#                     ),
#                 ),
#             ),
#         ),

        # Usage: sop gotoInstrumentChange
        # 
        # Go to the instrument change position
        CommandWdgSet(
            name = "gotoInstrumentChange",
            dispName = "Go To Instrument Change",
            stageList = (
                StageWdgSet(
                    name = "gotoInstrumentChange",
                ),
            ),
        ),
    )
