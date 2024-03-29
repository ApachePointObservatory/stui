import TUI.Models.TUIModel
import TUI.TUIMenu.AboutWindow
import TUI.TUIMenu.ConnectWindow
import TUI.TUIMenu.DownloadsWindow
import TUI.TUIMenu.LogWindow
import TUI.TUIMenu.PreferencesWindow
import TUI.TUIMenu.PythonWindow
import TUI.TUIMenu.UsersWindow
import TUI.Inst.APOGEE.APOGEEWindow
# import TUI.Inst.APOGEEQL.APOGEEQLWindow
import TUI.Inst.BOSS.BOSSWindow
# import TUI.Inst.Guide.FocusPlotWindow
# import TUI.Inst.Guide.GuideWindow
import TUI.Inst.GuideMonitor.BOSSMonitorWindow
# import TUI.Inst.GuideMonitor.FluxMonitorWindow
# import TUI.Inst.GuideMonitor.FocusMonitorWindow
# import TUI.Inst.GuideMonitor.GuideMonitorWindow
# import TUI.Inst.GuideMonitor.ScaleMonitorWindow
# import TUI.Inst.GuideMonitor.SeeingMonitorWindow
import TUI.Misc.Alerts.AlertsWindow
import TUI.Misc.Interlocks.InterlocksWindow
import TUI.Misc.MCP.MCPWindow
import TUI.Misc.MessageWindow
import TUI.TCC.FiducialsWdg.FiducialsWindow
import TUI.TCC.FocalPlaneWindow
import TUI.TCC.FocusWindow
import TUI.TCC.MirrorStatusWindow
import TUI.TCC.NudgerWindow
import TUI.TCC.OffsetWdg.OffsetWindow
import TUI.TCC.SkyWindow
import TUI.TCC.SlewWdg.SlewWindow
import TUI.TCC.StatusWdg.StatusWindow


def loadAll():
    tuiModel = TUI.Models.TUIModel.Model()
    tlSet = tuiModel.tlSet
    TUI.TUIMenu.AboutWindow.addWindow(tlSet)
    TUI.TUIMenu.ConnectWindow.addWindow(tlSet)
    TUI.TUIMenu.DownloadsWindow.addWindow(tlSet)
    TUI.TUIMenu.LogWindow.addWindow(tlSet)
    TUI.TUIMenu.PreferencesWindow.addWindow(tlSet)
    TUI.TUIMenu.PythonWindow.addWindow(tlSet)
    TUI.TUIMenu.UsersWindow.addWindow(tlSet)
    TUI.Inst.APOGEE.APOGEEWindow.addWindow(tlSet)
    # TUI.Inst.APOGEEQL.APOGEEQLWindow.addWindow(tlSet)
    TUI.Inst.BOSS.BOSSWindow.addWindow(tlSet)
    # TUI.Inst.Guide.FocusPlotWindow.addWindow(tlSet)
    # TUI.Inst.Guide.GuideWindow.addWindow(tlSet)
    TUI.Inst.GuideMonitor.BOSSMonitorWindow.addWindow(tlSet)
    # TUI.Inst.GuideMonitor.FluxMonitorWindow.addWindow(tlSet)
    # TUI.Inst.GuideMonitor.FocusMonitorWindow.addWindow(tlSet)
    # TUI.Inst.GuideMonitor.GuideMonitorWindow.addWindow(tlSet)
    # TUI.Inst.GuideMonitor.ScaleMonitorWindow.addWindow(tlSet)
    # TUI.Inst.GuideMonitor.SeeingMonitorWindow.addWindow(tlSet)
    TUI.Misc.Alerts.AlertsWindow.addWindow(tlSet)
    TUI.Misc.Interlocks.InterlocksWindow.addWindow(tlSet)
    TUI.Misc.MCP.MCPWindow.addWindow(tlSet)
    TUI.Misc.MessageWindow.addWindow(tlSet)
    TUI.TCC.FiducialsWdg.FiducialsWindow.addWindow(tlSet)
    TUI.TCC.FocalPlaneWindow.addWindow(tlSet)
    TUI.TCC.FocusWindow.addWindow(tlSet)
    TUI.TCC.MirrorStatusWindow.addWindow(tlSet)
    TUI.TCC.NudgerWindow.addWindow(tlSet)
    TUI.TCC.OffsetWdg.OffsetWindow.addWindow(tlSet)
    TUI.TCC.SkyWindow.addWindow(tlSet)
    TUI.TCC.SlewWdg.SlewWindow.addWindow(tlSet)
    TUI.TCC.StatusWdg.StatusWindow.addWindow(tlSet)
