import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp", delay=1.5)
tuiModel = testDispatcher.tuiModel

#    Key("azFiducialCrossing", 
#        Int(help="fiducial index"),
#        Float(units="deg", help="fiducial position"),
#        Int(units="ticks", help="error in expected position", invalid=99999),
#        Int(units="ticks", help="error in reported position")),
#     Key("azBadFiducial", Int(help="fiducial index"),
#         Float(units="deg", help="fiducial position")),

MainDataList = (
    "azFiducialCrossing=0, 10.0, 102, 106",
    "rotFiducialCrossing=5, 179.0, 153, 352",
    "altFiducialCrossing=2, 45.0, 53, 79",
)

AnimDataSet = (
    ("azFiducialCrossing=1, 25.0, 120, 234","azFiducialCrossing=1, 25.0, 120, 234","azFiducialCrossing=1, 25.0, 120, 234",),
    ("azFiducialCrossing=2, 45.0, 80, 76",),
    ("rotFiducialCrossing=4, 160.0, 35, 165",),
    ("azFiducialCrossing=1, 25.0, 1034, 1780", "azBadFiducial=1, 25.0"),
    ("altFiducialCrossing=2, 45.0, 10203, 30234",),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
