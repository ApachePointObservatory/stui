import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("alerts", delay=1.0)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    'activeAlerts=mcp.foo, mcp.needIack, boss.tooWarm',
    'disabledAlertRules="(mcp.foo, serious)"',
    'alert=mcp.needIack, warn, "True", enabled, ack',
    'alert=boss.tooWarm, critical, "30C", enabled, noack',
)

AnimDataSet = (
    (
    'alert=mcp.foo, serious, "disabled alert", disabled, noack',
    ),
    (
    'alert=boss.tooWarm, critical, "20C", enabled, ack',
    ),
    (
    'alert=boss.tooWarm, ok, "", enabled, ack',
    ),
    (
    'disabledAlertRules',
    ),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
