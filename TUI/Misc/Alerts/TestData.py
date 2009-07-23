import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("alerts", delay=1.0)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    'alert=mcp.needIack, warn, "True", enabled, ack',
    'alert=boss.tooWarm, critical, "30C", enabled, noack',
    'disabledAlerts="(mcp.foo, serious)"',
)

AnimDataSet = (
    (
    'alert=boss.tooWarm, critical, "20C", enabled, ack',
    ),
    (
    'alert=boss.tooWarm, ok, "", enabled, ack',
    ),
    (
    'disabledAlerts',
    ),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
