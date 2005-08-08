import TUI.TUIModel
import TUI.TUIMenu.AboutWindow
import TUI.TUIMenu.ConnectWindow
import TUI.TUIMenu.DownloadsWindow
import TUI.TUIMenu.LogWindow
import TUI.TUIMenu.Permissions.PermsWindow
import TUI.TUIMenu.PreferencesWindow
import TUI.TUIMenu.PythonWindow
import TUI.TUIMenu.UsersWindow
import TUI.Guide.DISSlitviewerWindow
import TUI.Guide.EchelleSlitviewerWindow
import TUI.Guide.NA2GuiderWindow
import TUI.Inst.DIS.DISWindow
import TUI.Inst.Echelle.EchelleWindow
import TUI.Inst.NICFPS.NICFPSWindow
import TUI.Misc.MessageWindow
import TUI.Misc.TrussLamps.TrussLampsWindow
import TUI.TCC.FocalPlaneWindow
import TUI.TCC.FocusWindow
import TUI.TCC.MirrorStatusWindow
import TUI.TCC.NudgerWindow
import TUI.TCC.OffsetWdg.OffsetWindow
import TUI.TCC.SkyWindow
import TUI.TCC.SlewWdg.SlewWindow
import TUI.TCC.StatusWdg.StatusWindow

def loadAll():
	tuiModel = TUI.TUIModel.getModel()
	tlSet = tuiModel.tlSet
	TUI.TUIMenu.AboutWindow.addWindow(tlSet)
	TUI.TUIMenu.ConnectWindow.addWindow(tlSet)
	TUI.TUIMenu.DownloadsWindow.addWindow(tlSet)
	TUI.TUIMenu.LogWindow.addWindow(tlSet)
	TUI.TUIMenu.Permissions.PermsWindow.addWindow(tlSet)
	TUI.TUIMenu.PreferencesWindow.addWindow(tlSet)
	TUI.TUIMenu.PythonWindow.addWindow(tlSet)
	TUI.TUIMenu.UsersWindow.addWindow(tlSet)
	TUI.Guide.DISSlitviewerWindow.addWindow(tlSet)
	TUI.Guide.EchelleSlitviewerWindow.addWindow(tlSet)
	TUI.Guide.NA2GuiderWindow.addWindow(tlSet)
	TUI.Inst.DIS.DISWindow.addWindow(tlSet)
	TUI.Inst.Echelle.EchelleWindow.addWindow(tlSet)
	TUI.Inst.NICFPS.NICFPSWindow.addWindow(tlSet)
	TUI.Misc.MessageWindow.addWindow(tlSet)
	TUI.Misc.TrussLamps.TrussLampsWindow.addWindow(tlSet)
	TUI.TCC.FocalPlaneWindow.addWindow(tlSet)
	TUI.TCC.FocusWindow.addWindow(tlSet)
	TUI.TCC.MirrorStatusWindow.addWindow(tlSet)
	TUI.TCC.NudgerWindow.addWindow(tlSet)
	TUI.TCC.OffsetWdg.OffsetWindow.addWindow(tlSet)
	TUI.TCC.SkyWindow.addWindow(tlSet)
	TUI.TCC.SlewWdg.SlewWindow.addWindow(tlSet)
	TUI.TCC.StatusWdg.StatusWindow.addWindow(tlSet)
