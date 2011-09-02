"""Objects that describe the basics of commands, stages and parameters
Used to paint the GUI

History:
2010-05-27 ROwen    Reordered the commands and added gotoInstrumentChange.
2011-07-05 ROwen    Added doApogeeScience and gotoGangChange.
                    Added "(BOSS)" to the button names for the doScience and doCalibs commands.
2011-07-11 ROwen    Added comment parameter to doApogeeScience and alt parameter to gotoGangChange.
"""
from CommandWdgSet import *

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

        # Usage: sop doApogeeScience [expTime=FF.F] [ditherSeq=SSS] [seqCount=N] [stop]   
        #                 [abort=] [comment=SSS]   
        #    
        # Take a sequence of dithered APOGEE science frames, or stop or modify a running   
        # sequence.   
        # Arguments:   
        # 	abort                               Abort a command   
        # 	comment                             comment for headers   
        # 	ditherSeq                           dither positions for each sequence. e.g. AB   
        # 	expTime                             Exposure time   
        # 	seqCount                            number of times to launch sequence   
        # 	stop                                no help   
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
                        StringParameterWdgSet(
                            name = "comment",
                            defValue = "",
                            units = None,
                            trackCurr = False,
                            ctrlColSpan = 10,
                            ctrlSticky = "ew",
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

        # Usage: sop doApogeeSkyFlats [expTime=FF.F] [ditherSeq=SSS] [stop] [abort=]
        #
        # RUSSELL WARNING: I am guessing a bit because sop help didn't show this command.
        #    
        # Take a sequence of dithered APOGEE sky flats, or stop or modify a running sequence.   
        # Arguments:   
        # 	abort                               Abort a command   
        # 	ditherSeq                           dither positions for each sequence. e.g. AB   
        # 	expTime                             Exposure time   
        # 	stop                                no help   
        CommandWdgSet(
            name = "doApogeeSkyFlats",
            stageList = (
                StageWdgSet(
                    name = "doApogeeSkyFlats",
                    parameterList = (
                        StringParameterWdgSet(
                            name = "ditherSeq",
                            defValue = "AB",
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

        # Usage: sop doScience [expTime=FF.F] [nexp=N] [abort] [stop] [test]   
        #    
        # Take a set of science frames   
        # Arguments:   
        # 	abort                               Abort a command   
        # 	expTime                             Exposure time   
        # 	nexp                                Number of exposures to take   
        # 	stop                                no help   
        # 	test                                Assert that the exposures are not expected to be meaningful   
        CommandWdgSet(
            name = "doScience",
            dispName = "Do (BOSS) Science",
            stageList = (
                StageWdgSet(
                    name = "doScience",
                    parameterList = (
                        CountParameterWdgSet(
                            name = "nExp",
                            defValue = 0,
                        ),
                        FloatParameterWdgSet(
                            name = "expTime",
                            startNewColumn = True,
                            units = "sec",
                        ),
                    ),
                ),
            ),
        ),
        
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
            dispName = "Do (BOSS) Calibs",
            stageList = (
                StageWdgSet(
                    name = "doCalibs",
                    parameterList = (
                        CountParameterWdgSet(
                            name = "nArc",
                            defValue = 0,
                        ),
                        CountParameterWdgSet(
                            name = "nBias",
                            defValue = 0,
                        ),
                        CountParameterWdgSet(
                            name = "nDark",
                            defValue = 0,
                        ),
                        CountParameterWdgSet(
                            name = "nFlat",
                            defValue = 0,
                        ),
                        FloatParameterWdgSet(
                            name = "arcTime",
                            startNewColumn = True,
                            units = "sec",
                        ),
                        FloatParameterWdgSet(
                            name = "darkTime",
                            skipRows = 1,
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
                    ),
                ),
            ),
        ),

        # Usage: sop gotoStow
        # 
        # Go to the gang connector change/stow position
        #
        # Is it a quirk of sop that a command with no stages has one stage named after the command?
        CommandWdgSet(
            name = "gotoStow",
            stageList = (
                StageWdgSet(
                    name = "gotoStow",
                ),
            ),
        ),

        # Usage: sop gotoGangChange [alt=FF.F] [abort] [stop]   
        #    
        # Go to the gang connector change position   
        # Arguments:   
        # 	abort                               Abort a command   
        # 	alt                                 what altitude to slew to   
        # 	stop                                no help   
        CommandWdgSet(
            name = "gotoGangChange",
            stageList = (
                StageWdgSet(
                    name = "slew",
                    parameterList = (
                        FloatParameterWdgSet(
                            name = "alt",
                            units = "deg",
                        ),
                    ),
                ),
            ),
        ),

        # Usage: sop gotoInstrumentChange
        # 
        # Go to the instrument change position
        CommandWdgSet(
            name = "gotoInstrumentChange",
            stageList = (
                StageWdgSet(
                    name = "gotoInstrumentChange",
                ),
            ),
        ),
    )
