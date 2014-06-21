#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("sop", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "version=1.4",
    'bypassNames=boss, ff_lamp, ffs, gcamera, hgcd_lamp, ne_lamp, uv_lamp, wht_lamp', 
    'bypassed=1, 0, 0, 0, 0, 1, 0, 1', 
    'gotoFieldStages="slew", "hartmann", "calibs", "guider", "cleanup"',
    'doBossCalibsStages="bias", "dark", "flat", "arc", "cleanup"',
    'doBossScience_nExp=3, 3',
    'doMangaSequenceStages="expose", "calibs", "dither"',
    'doMangaSequenceState="idle","OK","idle","idle","idle"',
    'doMangaSequence_count=3,3',
    'doMangaSequence_dithers="NSE","NSE"',
    'doMangaSequence_expTime=900.0,900.0',
    'doMangaSequence_arcTime=4.0,4.0',
    'doMangaSequence_ditherSeq=NSENSENSE,0,0',
    'doApogeeScienceStages="doApogeeScience"',
    'doApogeeScienceState="done","OK","idle"',
    'doApogeeScience_ditherSeq="ABBA","ABBA"',
    'doApogeeScience_seqCount=2,2',
    'doApogeeScience_expTime=500.0,500.0',
    'doApogeeScience_sequenceState="ABBAABBA",8',
    'doApogeeScience_comment="",""',
    'doApogeeDomeFlatStages="domeFlat"',
    'doApogeeDomeFlatState="done","gang connector is not at the cartridge!","done"',
    'doApogeeSkyFlatsStages="doApogeeSkyFlats"',
    'doMangaDitherStages="expose", "dither"',
    'gotoFieldStages="slew","hartmann","calibs","guider"',
    'doCalibsState="done","OK","done"',
    'doScienceState="done","OK","done"',
    'gotoFieldState="done","OK","off","done","done","done"',
    'doCalibs_nArc=2, 5',
    'doCalibs_arcTime=5.0, 6.0',
    'gotoField_guiderTime=5, 10',
    'gotoGangChange_alt=30.0, 45.0',
    'doApogeeScience_comment="test comment", ""',
)

dataSet = (
    (
    'surveyCommands=gotoField, doCalibs, gotoInstrumentChange',
    'gotoFieldStages="hartmann","guider"',
    'gotoFieldState="done","OK","done","done"',
    ),
    (
    'surveyCommands=gotoStow, gotoField, doScience, doCalibs, gotoInstrumentChange',
    'gotoFieldStages="slew","hartmann","calibs","guider"',
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
