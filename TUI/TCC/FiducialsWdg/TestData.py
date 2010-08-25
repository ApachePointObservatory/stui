import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp", delay=1.5)
tuiModel = testDispatcher.tuiModel

#    Key("azFiducialCrossing", 
#        Int(help="fiducial index"),
#        Float(units="deg", help="fiducial position"),
#        Int(units="ticks", help="error in expected position", invalid=99999),
#        Int(units="ticks", help="error in reported position")),
#    Key("altFiducialCrossing", 
#        Int(help="fiducial index"),
#        Float(units="deg", help="fiducial position"),
#        Int(units="ticks", help="error since last crossing", invalid=99999),
#        Int(units="ticks", help="error in reported position")),
#    Key("rotFiducialCrossing", 
#        Int(help="fiducial index"),
#        Float(units="deg", help="fiducial position"),
#        Int(units="ticks", help="error since last crossing", invalid=99999),
#        Int(units="ticks", help="error in reported position")), 

MainDataList = (
    "azFiducialCrossing=0, 10.0, 10203, 30234",
    "rotFiducialCrossing=5, 179.0, 10203, 30234",
    "altFiducialCrossing=2, 45.0, 10203, 30234",
)

AnimDataSet = (
    ("azFiducialCrossing=1, 25.0, 20123, 31346",),
    ("azFiducialCrossing=2, 45.0, 10203, 30234",),
    ("rotFiducialCrossing=4, 160.0, 10203, 30234",),
    ("azFiducialCrossing=1, 25.0, 20123, 31346",),
    ("altFiducialCrossing=2, 45.0, 10203, 30234",),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
