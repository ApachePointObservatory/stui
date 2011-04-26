import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("apogeeql", delay=0.5)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    "dspload=\"APOGEE.lod\"; arrayPower=\"off\"; exposureState=\"done\",1,1; exposureMode=\"sutr\",2",
    "dspFiles=\"APOGEE.lod\"; exposureModeInfo=\"sutr\",2,20000",
    "ditherPosition=11.476510067114093; ditherLimits=1.0,19.0; ditherStepPosition=13685; ditherIndexer=On",
    "ttPosition=2250.033203125,22.49785156249999,-0.012402343749954525; ttStepPosition=2339.975,2159.9921875,2250.0828125 ; ttLimits=0.5,3.5; ttIndexer=On",
    "vacuumThreshold=10E-6; vacuumLimits=0E0,1E3; vacuumInterval=300",
    "vacuum=NaN; vacuumAlarm=0",
    "tempNames=\"DETPOLE_TOP\",\"DETPOLE_BASE\",\"TENT_TOP\",\"CP_MIDDLE\",\"GETTER\",\"TempBrd\",\"L_SOUTH\",\"L_NORTH\",\"LS-Camera2\",\"LS-Camera1\",\"LS-DetectorC\",\"LS-DetectorB\",\"CAM_AFT\",\"CAM_MIDDLE\",\"CAM_FWD\",\"VPH\",\"RADSHIELD_E\",\"COLLIMATOR\",\"CP_CORNER\",\"CP_HANGERS\"; tempInterval=300",
    "tempMin=0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0; tempMax=350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350,350; tempThresholds=400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400,400",
    "temps=458.143,456.804,454.774,455.889,457.6,295.678,457.342,456.295,0,0,0,0,458.407,457.2,455.573,457.096,456.096,458.915,455.631,455.341; tempAlarms=0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0",

    "ln2Level=5",
    "ln2Limits=20, 100",
    "ln2Alarm=0",
)
MainQLDataList = (
    "exposureData=1001, 1, 00000113, 600.0, 5, 30.0,  0.0, 28.2,  600, 28.2",
    "exposureData=1001, 2, 00000114, 600.0, 5, 30.0,  0.5, 28.2, 1200, 39.9",
    "exposureData=1001, 3, 00000115, 600.0, 5, 30.0, -0.5, 28.2, 1800, 48.8",
    "exposureData=1001, 4, 00000116, 600.0, 5, 30.0,  0.5, 28.2, 2400, 56.4",
    "exposureData=1001, 5, 00000117, 600.0, 5, 30.0, -0.5, 28.2, 3000, 63.1",
    "exposureData=1001, 6, 00000118, 600.0, 5, 30.0,  0.5, 28.2, 3600, 69.1",
    "snrH12Target=30",
    "utrData=6, 1, 10, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6",
    "utrData=6, 2, 15, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6",
    "utrData=6, 3, 20, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6",
    "utrData=6, 4, 24, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6",
    "utrData=6, 5, 28, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6",
    "snrAxisRange=14, 32",
)

AnimDataSet = (
    (
    ),
)

def start():
    print "dispatch MainQLDataList"
    testDispatcher.dispatch(MainDataList, actor="apogee")
    testDispatcher.dispatch(MainQLDataList, actor="apogeeql")
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
