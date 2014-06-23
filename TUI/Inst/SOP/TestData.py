#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("sop", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "version=1.4",
    'bypassNames=boss, ff_lamp, ffs, gcamera, hgcd_lamp, ne_lamp, uv_lamp, wht_lamp', 
    'bypassed=1, 0, 0, 0, 0, 1, 0, 1', 

    'gotoFieldStages="slew", "hartmann", "calibs", "guider", "cleanup"',
    'gotoFieldState="done","OK","off","done","done","done","done"',
    'gotoField_arcTime=5, 7.6',
    'gotoField_flatTime=4.3, 5.1',
    'gotoField_guiderFlatTime=7.6, 3.9',
    'gotoField_guiderTime=5, 10',

    'doApogeeScienceStages="expose"',
    'doApogeeScienceState="done","OK","idle"',
    'doApogeeScience_ditherSeq="ABBA","ABBA"',
    'doApogeeScience_seqCount=2,2',
    'doApogeeScience_expTime=500.0,500.0',
    'doApogeeScience_sequenceState="ABBAABBA",8',
    'doApogeeScience_comment="a comment",""',

    'doBossScienceStages="expose"',
    'doBossScienceState="done","OK","idle"',
    'doBossScience_nExp=3, 3',
    'doBossScience_expTime=13.3, 10',

    'doMangaDitherStages="expose", "dither"',
    'doMangaDitherState="done","OK","done","done"',
    'doMangaDither_expTime=25.3,30',
    'doMangaDither_dithers="NS","NSE"',

    'doMangaSequenceStages="expose", "calibs", "dither"',
    'doMangaSequenceState="idle","OK","idle","idle","idle"',
    'doMangaSequence_count=3,3',
    'doMangaSequence_dithers="NSE","NSE"',
    'doMangaSequence_expTime=900.0,900.0',
    'doMangaSequence_arcTime=4.0,4.0',          # ignored
    'doMangaSequence_ditherSeq=NSENSENSE,0,0',  # ignored

    'gotoGangChangeStages="domeFlat", "slew"',
    'gotoGangChangeState="done","some text","done","done"',
    'gotoGangChange_alt=30.0, 45.0',    # ignored

    'gotoInstrumentChangeStages="slew"',
    'gotoInstrumentChangeState="done","a bit of text","done"',

    'doApogeeSkyFlatsStages="expose"',
    'doApogeeSkyFlatsState="done","some text","done"',
    'doApogeeSkyFlats_ditherSeq="A","AB"',
    'doApogeeSkyFlats_expTime="400","500"',

    'doApogeeDomeFlatStages="domeFlat"',
    'doApogeeDomeFlatState="done","gang connector is not at the cartridge!","done"',

    'doBossCalibsStages="bias", "dark", "flat", "arc", "cleanup"',
    'doBossCalibsState="done","some text","done","done","done","done","done"',
    'doBossCalibs_nBias=3, 4',
    'doBossCalibs_nDark=10, 7',
    'doBossCalibs_darkTime=31.2, 15',
    'doBossCalibs_nFlat=5, 5',
    'doBossCalibs_flatTime=22.3, 14',
    'doBossCalibs_guiderFlatTime=12.3, 13',
    'doBossCalibs_nArc=2, 5',
    'doBossCalibs_arcTime=5.0, 6.0',

    'gotoStowStages="slew"',
    'gotoStowState="done","a bit of text","done"',
)

dataSet = (
    (
    'surveyCommands=gotoField, doCalibs, gotoInstrumentChange',
    'gotoFieldStages="hartmann","guider","cleanup"',
    'gotoFieldState="done","OK","done","done","done"',
    ),
    (
    'gotoFieldStages="slew","calibs","cleanup"',
    'gotoFieldState="done","OK","done","done","done"',
    ),
    (
    'gotoFieldStages="slew","hartmann","cleanup"',
    'gotoFieldState="done","OK","done","done","done"',
    ),
    (
    'surveyCommands=gotoStow, gotoField, doScience, doCalibs, gotoInstrumentChange',
    'gotoFieldStages="slew","hartmann","calibs","cleanup"',
    'gotoFieldState="running","OK","off","running","pending","pending"',
    ),
    (
    'gotoFieldState="running","OK","off","running","running","pending"',
    ),
    (
    'gotoFieldState="running","OK","off","running","done","running"',
    ),
    (
    'gotoFieldState="failed","OK","off","done","done","failed"',
    ),
)

def start():
    testDispatcher.dispatch(dataList)

def animate():
    testDispatcher.runDataSet(dataSet)
