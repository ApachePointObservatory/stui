#!/usr/local/bin/python
"""Tkinter utilities

History:
2004-10-08 ROwen
2004-10-12 ROwen	Modified getWindowingSystem to handle versions of Tk < ~8.4
2005-06-17 ROwen	Added getButtonNumbers.
2005-07-06 ROwen	Added tkCallback
"""
__all__ = ['colorOK', 'getWindowingSystem', 'tkCallback', 'WSysAqua', 'WSysX11', 'WSysWin']

import Tkinter
import RO.OS

# windowing system constants
WSysAqua = "aqua"
WSysX11 = "x11"
WSysWin = "win32"

# internal globals
g_tkWdg = None
g_winSys = None

def colorOK(colorStr):
	"""Return True if colorStr is a valid tk color, False otherwise.
	"""
	tkWdg = _getTkWdg()

	try:
		tkWdg["bg"] = colorStr
	except Tkinter.TclError:
		return False
	return True

def getButtonNumbers():
	"""Return the button numbers corresponding to
	the left, middle and right buttons.
	"""
	winSys = getWindowingSystem()
	if winSys == WSysAqua:
		return (1, 3, 2)
	else:
		return (1, 2, 3)
	
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
	global g_winSys
	
	if not g_winSys:
		tkWdg = _getTkWdg()
		try:
			g_winSys = tkWdg.tk.call("tk", "windowingsystem")
		except Tkinter.TclError:
			# windowingsystem not supported; take a best guess
			if RO.OS.PlatformName == "win":
				g_winSys = "win32"
			else:
				g_winSys = "x11"

	return g_winSys

def tkCallback(func):
	"""Convert a python function or object method into a tk callback.
	"""
	tkWdg = _getTkWdg()
	tkFuncName = "cb%d" % id(func)
	return tkWdg.tk.createcommand(tkFuncName, func)

def _getTkWdg():
	"""Return a Tk widget"""
	global g_tkWdg
	if not g_tkWdg:
		g_tkWdg = Tkinter.Frame()
	return g_tkWdg
