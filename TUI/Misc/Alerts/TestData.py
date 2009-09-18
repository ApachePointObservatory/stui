"""Simulated data from the alerts actor.

History:
- 2009-09-17 ROwen  Updated test data for changes to the alerts actor.
"""
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("alerts", delay=1.0)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    'activeAlerts=mcp.needIack, boss.tooWarm',
    'alert=mcp.needIack, warn, "True", enabled, noack, ""',
    'alert=boss.tooWarm, critical, "some really long text so that this alert will wrap onto the next line even using the default size window, which is pretty wide.", enabled, noack, ""',
    'disabledAlertRules="(mcp.foo, serious, alerts.cfg)"',
)

AnimDataSet = (
    (
    'alert=mcp.needIack, warn, "True", enabled, ack, "ssnedden.APO1"',
    ),
    (
    'activeAlerts=mcp.foo, mcp.needIack, boss.tooWarm',
    'alert=mcp.foo, serious, "disabled alert", disabled, noack, "ssnedden.APO1"',
    ),
    (
    'alert=boss.tooWarm, critical, "20C", enabled, ack, "ssnedden.APO1"',
    ),
    (
    'alert=boss.tooWarm, ok, "", enabled, ack, "ssnedden.APO1"',
    ),
    (
    'disabledAlertRules',
    ),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
