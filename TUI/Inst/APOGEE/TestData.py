import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("apogee", delay=5)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    "dspload=\"APOGEE.lod\"; arrayPower=?; dspFiles=\"APOGEE.lod\"",
    "exposureTypeList=Object, Dark, InternalFlat, QuartzFlat, DomeFlat, ArcLamp, Blackbody, SuperFlat, SuperDark",
    "collOrient=2250.033203125,22.49785156249999,-0.012402343749954525; collMount=2339.975,2159.9921875,2250.0828125",
    "collMountLimits=0.0, 5000.0; collIndexer=On; collLimitSwitch=true, false, true, false, false, false",
    "ditherNamedPositions=11.5, 12.0; ditherPosition=11.5, A; ditherLimits=1.0,19.0",
    "ditherIndexer=On; ditherLimitSwitch=true, false",
    "utrReadTime=10",
    "exposureState=Done, Object, 10, 00120014",
    "utrReadState=00120014, Done, 3, 3",
    "vacuumThreshold=10E-6; vacuumLimits=0E0,1E3; vacuumInterval=300",
    "vacuum=NaN; vacuumAlarm=0",
    "tempNames=\"DETPOLE_TOP\",\"DETPOLE_BASE\",\"TENT_TOP\",\"CP_MIDDLE\",\"GETTER\",\"TempBrd\",\"L_SOUTH\",\"L_NORTH\",\"LS-Camera2\",\"LS-Camera1\",\"LS-DetectorC\",\"LS-DetectorB\",\"CAM_AFT\",\"CAM_MIDDLE\",\"CAM_FWD\",\"VPH\",\"RADSHIELD_E\",\"COLLIMATOR\",\"CP_CORNER\",\"CP_HANGERS\"; tempInterval=300",
    "tempMin=0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0; tempMax=350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350; tempThresholds=400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400",
    "temps=458.143,456.804,454.774,455.889,457.6,295.678,457.342,456.295,0,0,0,0,458.407,457.2,455.573,457.096,456.096,458.915,455.631,455.341; tempAlarms=0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0",
    "ln2Level=5; ln2Limits=20, 100; ln2Alarm=0",
)

AnimDataSet = (
    (
        "exposureState=Exposing, Object, 10, 00120015",
        "utrReadState=00120015, Reading, 1, 3",
    ),
    (
        "ditherIndexer=Off",
    ),
    (
        "utrReadState=00120015, Reading, 2, 3",
        "ditherIndexer=On",
        "collIndexer=Off",
    ),
    (
        "utrReadState=00120015, Saving, 1, 3",
        "collIndexer=On",
        "tempAlarms=1,0,1,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0",
    ),
    (
        "utrReadState=00120015, Reading, 3, 3",
        "ln2Alarm=1",
        "tempAlarms=0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0",
    ),
    (
        "utrReadState=00120015, Saving, 2, 3",
        "ln2Alarm=0",
        "vacuumAlarm=1",
    ),
    (
        "utrReadState=00120015, Saving, 3, 3",
        "exposureState=Done, Object, 10, 00120015",
        "vacuumAlarm=0",
    ),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
