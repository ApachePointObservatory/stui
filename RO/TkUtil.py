#!/usr/local/bin/python
"""Tkinter utilities

History:
2004-10-08 ROwen
2004-10-12 ROwen	Modified getWindowingSystem to handle versions of Tk < ~8.4
2005-06-17 ROwen	Added getButtonNumbers.
2005-07-07 ROwen	Added TclFunc
"""
__all__ = ['colorOK', 'getWindowingSystem', 'TclFunc', 'WSysAqua', 'WSysX11', 'WSysWin']

import sys
import traceback
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

#class TkAdapter:
	#_tkWdg = None
	#def __init__(self):
		#if self._tkWdg == None:
			#self._tkWdg = self._getTkWdg()
		#self.funcDict = {}
	
	#def after(*args):
		#self._tkWdg.after(*args)

	#def register(self, func):
		#"""Register a function as a tcl function.
		#Returns the name of the tcl function.
		#Be sure to deregister the function when done
		#or delete the TkAdapter
		#"""
		#funcObj = TclFunc(func)
		#funcName = funcObj.tclFuncName
		#self.funcDict[funcName] = funcObj
		#return funcName
	
	#def deregister(self, funcName):
		#"""Deregister a tcl function.

		#Raise KeyError if function not found.
		#"""
		#func = self.funcDict.pop(funcName)
		#func.deregister()
	
	#def eval(self, *args):
		#"""Evaluate an arbitrary tcl expression and return the result"""
		#return self._tkWdg.tk.eval(*args)

	#def call(self, *args):
		#"""Call a tcl function"""
		#return self._tkWdg.tk.call(*args)

class TclFunc:
	"""Register a python function as a tcl function.
	Based on Tkinter's _register method (which, being private,
	I prefer not to use explicitly).
	
	If the function call fails, a traceback is printed.

	Deleting the object deregisters the function.
	"""
	tkApp = None
	def __init__(self, func, debug=False):
		if self.tkApp == None:
			self.tkApp = _getTkWdg().tk
		self.func = func
		self.tclFuncName = "py%s" % (id(self),)
		self.debug = bool(debug)
		try:
			self.tclFuncName += str(func.__name__)
		except AttributeError:
			pass
		if self.debug:
			print "registering tcl function", self.tclFuncName
		self.tkApp.createcommand(self.tclFuncName, self)
	
	def __call__(self, *args):
		try:
			self.func(*args)
		except (SystemExit, KeyboardInterrupt):
			raise
		except Exception, e:
			sys.stderr.write("tcl function %s failed: %s\n" % (self.tclFuncName, e))
			traceback.print_exc(file=sys.stderr)
		
	def deregister(self):
		"""Deregister callback and delete reference to python function.
		Safe to call if already deregistered.
		"""
		if self.debug:
			print "%r.deregister()" % (self,)
		if not self.func:
			if self.debug:
				print "already deregistered"
			return
		try:
			self.tkApp.deletecommand(self.tclFuncName)
		except Tkinter.TclError, e:
			if self.debug:
				print "deregistering failed: %r" % (e,)
			pass
		self.func = None
	
	def __del__(self):
		self.deregister()
	
	def __repr__(self):
		return "%s(%s)" % (self.__class__.__name__, self.tclFuncName)
	
	def __str__(self):
		return self.tclFuncName

def _getTkWdg():
	"""Return a Tk widget"""
	global g_tkWdg
	if not g_tkWdg:
		g_tkWdg = Tkinter.Frame()
	return g_tkWdg
