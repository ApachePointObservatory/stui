#!/usr/local/bin/python
"""Tkinter utilities

History:
2004-10-08 ROwen
2004-10-12 ROwen	Modified getWindowingSystem to handle versions of Tk < ~8.4
"""
__all__ = ['colorOK', 'getWindowingSystem', 'WSysAqua', 'WSysX11', 'WSysWin']

import Tkinter
import RO.OS

# windowing system constants
WSysAqua = "aqua"
WSysX11 = "x11"
WSysWin = "win32"

# internal globals
g_wdg = None
g_winSys = None

def colorOK(colorStr):
	"""Return True if colorStr is a valid tk color, False otherwise.
	"""
	global g_wdg
	if not g_wdg:
		g_wdg = Tkinter.Frame()

	try:
		g_wdg["bg"] = colorStr
	except Tkinter.TclError:
		return False
	return True

def getWindowingSystem():
	"""Return the Tk window system.
	
	Returns one of:
	- WSysAqua: the MacOS X native system
	- WSysX11: the unix windowing system
	- WSysWin: the Windows windowing system
	Other values might also be possible.
	
	Please don't call this until you have started Tkinter with Tkinter.Tk().
	
	Warning: windowingsystem is a fairly recent tk command;
	if it is not available then this code does its best to guess
	but will not guess aqua.
	"""
	global g_wdg, g_winSys

	if not g_winSys:
		g_wdg = Tkinter.Frame()
		try:
			g_winSys = g_wdg.tk.call("tk", "windowingsystem")
		except Tkinter.TclError:
			# windowingsystem not supported; take a best guess
			if RO.OS.PlatformName == "win":
				g_winSys = "win32"
			else:
				g_winSys = "x11"

	return g_winSys
