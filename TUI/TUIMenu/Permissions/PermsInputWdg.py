#!/usr/local/bin/python
"""Specify what users from each program are allowed to do.

Note: the interface visible to the user uses the terms "add" and "delete"
because they are clear and succinct. However, the internal code use the
perms terminology "register" and "unregister" because they work
better in function calls when one might be toggling the state
and because the transition has to occur somewhere.

To do:
- Fix readonly toggle. It doesn't seem to handle lockout or the first program.
- Clean up this code.
- Mark the current user in some way (use a "good" color bg?).
- Consider some kind of warning for users that are connected but are NOT in the permissions list,
  for instance show them as deleted for non-read-only users? How for read-only users?
  Perhaps use a read background in both cases. Note that this makes the already-complicated logic
  even more hair-raising.

2003-12-19 ROwen	Preliminary version; html help is broken.
2003-12-29 ROwen	Implemented html help.
2004-07-22 ROwen	Updated for new RO.KeyVariable
2004-07-29 ROwen	Added read-only support.
2004-08-11 ROwen	Use modified RO.Wdg state constants with st_ prefix.
2004-09-03 ROwen	Modified for RO.Wdg.st_... -> RO.Constants.st_...
2004-11-16 ROwen	Modified for RO.Wdg.Label change.
2005-01-05 ROwen	Modified to use RO.Wdg.Label.setSeverity instead of setState.
					Modified to use Checkbutton autoIsCurrent instead of
					a separate changed indicator.
					Fixed and improved test code.
"""
import Tkinter
import RO.Constants
import RO.Alg
import RO.KeyVariable
import RO.Wdg
import TUI.TUIModel
import PermsModel

# first row for displaying program widgets
# the preceding rows are: title labels, title width frames,
# data width frames, lockout
# note: if no titleFrame then title info is displayed on the main frame
# otherwise some of these rows are not used in the main frame
_ProgBegRow = 2

_HelpPrefix = "TUIMenu/PermissionsWin.html#"

class PermsInputWdg(Tkinter.Frame):
	"""Inputs:
	- master		master widget
	- statusBar		status bar to handle commands.
	- titleFrame	a frame in which to place program names and lockout line;
		if omitted, the master is used.
	- readOnlyCallback	a function that is called when the readOnly state changes
		(note that it starts out True). The function receives one argument:
		isReadOnly: True for read only, False otherwise
	"""
	def __init__(self,
		master,
		statusBar,
		titleFrame = None,
		readOnlyCallback = None,
	):
		Tkinter.Frame.__init__(self, master)
		self._statusBar = statusBar
		self._titleFrame = titleFrame or self
		self._tuiModel = TUI.TUIModel.getModel()
		self._readOnlyCallback = readOnlyCallback

		self._actors = []
		self._progDict = {} # prog name: prog perms
		self._nextRow = _ProgBegRow
		self._readOnly = True
		
		self.permsModel = PermsModel.getModel()
		
		self.permsModel.actors.addCallback(self._updActors)
		self.permsModel.authList.addCallback(self._updAuthList)
		self.permsModel.lockedActors.addCallback(self._updLockedActors)
		self.permsModel.programs.addCallback(self._updPrograms)
		
		self._addTitle("", col = 0)

		self._lockoutWdg = _LockoutPerms(
			master = self._titleFrame,
			actors = self._actors,
			readOnly = self._readOnly,
			row = 1,
			statusBar = self._statusBar,
		)
		
		self._vertMeasWdg = Tkinter.Frame(self)
		self._vertMeasWdg.grid(row=_ProgBegRow, sticky="wns")
		
		statusBar.dispatcher.connection.addStateCallback(self.__connStateCallback)
	
	def getVertMeasWdg(self):
		"""A widget whose height is the height of one row of data.
		"""
		return self._vertMeasWdg

	def purge(self):
		"""Remove unregistered programs.
		"""
		knownProgs = self.permsModel.programs.get()[0]

		# use items instead of iteritems so we can modify as we go
		for prog, progPerms in self._progDict.items():
			if progPerms.isRegistered() or prog in knownProgs:
				continue
			progPerms.delete()
			del(self._progDict[prog])
	
	def sort(self):
		"""Sort existing programs.
		"""
		progNames = self._progDict.keys()
		progNames.sort()
		self._nextRow = _ProgBegRow
		for prog in progNames:
			progPerms = self._progDict[prog]
			progPerms.display(row=self._nextRow, actors=self._actors)
			self._nextRow += 1
	
	def __connStateCallback(self, conn):
		"""If the connection closes, clear all programs from the list.
		"""
		if self._progDict and not conn.isConnected():
			for prog, progPerms in self._progDict.items():
				progPerms.delete()
				del(self._progDict[prog])
	
	def _addProg(self, prog):
		"""Create and display a new program.
		
		Called when the hub informs this widget of a new program
		(to add a program send the suitable command to the hub,
		don't just call this method).
		"""
		prog = prog.upper()
		newProg = _ProgPerms(
			master = self,
			prog = prog,
			actors = self._actors,
			readOnly = self._readOnly,
			row = self._nextRow,
			statusBar = self._statusBar,
		)
		self._nextRow += 1
		self._progDict[prog] = newProg
	
	def _addTitle(self, text, col):
		"""Create and grid a title label and two associated
		width measuring frames (one in the title frame, one in the main frame).
		
		Inputs:
		- text	text for title
		- col	column for title
		"""
#		print "_addTitle(%r, %r)" % (text, col)
		strWdg = RO.Wdg.StrLabel(self._titleFrame, text=text)
		strWdg.grid(row=0, column=col)
		titleSpacer = Tkinter.Frame(self._titleFrame)
		titleSpacer.grid(row=1, column=col, sticky="ew")
		mainSpacer = Tkinter.Frame(self)
		mainSpacer.grid(row=2, column=col, sticky="ew")
		
		def dotitle(evt):
#			print "dotitle: titlewidth = %r, mainwidth = %r" % (
#				titleSpacer.winfo_width(), mainSpacer.winfo_width(),
#			)
			if titleSpacer.winfo_width() > mainSpacer.winfo_width():
				mainSpacer["width"] = titleSpacer.winfo_width()		
		titleSpacer.bind("<Configure>", dotitle)
		
		def domain(evt):
#			print "domain: titlewidth = %r, mainwidth = %r" % (
#				titleSpacer.winfo_width(), mainSpacer.winfo_width(),
#			)
			if mainSpacer.winfo_width() > titleSpacer.winfo_width():
				titleSpacer["width"] = mainSpacer.winfo_width()		
		mainSpacer.bind("<Configure>", domain)
		

	def _updActors(self, actors, isCurrent=True, **kargs):
		"""Perms list of actors updated.
		
		Add any that we didn't already know about.
		"""
#		print "%s._updActors(%r)" % (self.__class__, actors,)
		if not isCurrent:
			return

		if not self._actors:
			actors = list(actors)
			actors.sort()

		newActors = [actor for actor in actors if actor not in self._actors]
		if newActors:
			# display new actor labels and update self._actors
			for actor in newActors:
				self._actors.append(actor)
				col = len(self._actors)
				self._addTitle(actor, col)

			# set actors in lockout and each program
			self._lockoutWdg.setActors(self._actors)
			for progPerms in self._progDict.iteritems():
				progPerms.setActors(self._actors)

	def _updPrograms(self, programs, isCurrent=True, **kargs):
		"""Hub's list of registered programs updated.
		
		Delete old programs based on this info, but don't add new ones
		(instead, look for an authList entry for the new program,
		so we get auth info at the same time).
		"""
		if not isCurrent:
			return
#		print "_updPrograms(%r)" % (programs,)

		# raise program names to uppercase
		programs = [prog.upper() for prog in programs]

		if self._tuiModel.getProgID().upper() not in programs:
#			print "my prog=%s is not in programs=%s; currReadOnly=%s" % (prog, programs, self._readOnly)
			self._setReadOnly(True)

		# mark unregistered programs
		anyUnreg = False
		for prog, progPerms in self._progDict.iteritems():
			if prog not in programs:
				# mark progPerms as unregistered
				anyUnreg = True
				progPerms.setRegistered(False)
		
		# if read only, then automatically purge (if necessary) and sort
		if self._readOnly:
			if anyUnreg:
				self.purge()
			self.sort()
		
	def _setReadOnly(self, readOnly):
		"""Set read only state.
		"""
		if self._readOnly != readOnly:
			self._readOnly = readOnly
#			print "toggling readOnly to", self._readOnly
			self._lockoutWdg.setReadOnly(self._readOnly)
			for progPerms in self._progDict.itervalues():
				progPerms.setReadOnly(self._readOnly)
			if self._readOnlyCallback:
				self._readOnlyCallback(self._readOnly)
	
	def _updAuthList(self, progAuthList, isCurrent=True, **kargs):
		"""New authList received.
		
		progAuthList is:
		- program name
		- 0 or more actors
		"""
		if not isCurrent:
			return
#		print "_updAuthList(%r)" % (progAuthList,)
		
		prog = progAuthList[0].upper()
		authActors = progAuthList[1:]
	
		if prog == self._tuiModel.getProgID().upper():
			readOnly = "perms" not in authActors
#			print "prog=%s is me; readOnly=%s, currReadOnly=%s, actors=%s" % (prog, readOnly, self._readOnly, authActors)
			self._setReadOnly(readOnly)

		isNew = prog not in self._progDict
		if isNew:
			self._addProg(prog)

		progPerms = self._progDict[prog]
		progPerms.setRegistered(True)
		progPerms.setCurrActors(authActors)
	
	def _updLockedActors(self, lockedActors, isCurrent=True, **kargs):
		"""Hub's locked actor list updated.
		"""
		if not isCurrent:
			return
		
		self._lockoutWdg.setCurrActors(lockedActors)


class _LockoutPerms:
	"""Lockout permissions
	
	This class keeps track of locked actors,
	displays the info as a set of controls
	and responds to these controls by sending the appropriate commands.
	
	Inputs:
	- master	master widget
	- actors	a list of the currently known actors, in desired display order
	- row		row at which to grid display widgets
	- statusBar	object to handle commands (via doCmd)
	"""
	def __init__(self, master, actors, readOnly, row, statusBar, prog=""):
		self._master = master
		self._prog = prog
		self._readOnly = readOnly
		self._row = row
		self._statusBar = statusBar

		if self._prog:
			self._helpURL = _HelpPrefix + "ProgEntry"
		else:
			self._helpURL = _HelpPrefix + "Lockout"

		self._createNameWdg()

		# dictionary of actor: auth checkbutton entries
		self._actorWdgDict = RO.Alg.OrderedDict()
		self.setActors(actors)
		
		self.display(row=self._row, actors=actors)

	def delete(self):
		"""Cleanup
		"""
		wdgSet = self._actorWdgDict.values()
		if self._nameWdg != None:
			wdgSet.append(self._nameWdg)
		self._nameWdg = None
		self._actorWdgDict = RO.Alg.OrderedDict()
		for wdg in wdgSet:
			wdg.grid_forget()
			wdg.destroy()
		
	def display(self, row, actors):
		"""Display widgets in the specified row.
		If widgets are already displayed, they are first withdrawn.
		
		Raises ValueError if the list of actors does not match.
		"""
		# check actors
		if actors != self._actorWdgDict.keys():
			raise ValueError("cannot display entry %r; my actors %r != %r" % \
				(self._prog, self._actorWdgDict.keys(), actors))

	 	self._row = row
	 	self._nameWdg.grid_forget()
	 	self._nameWdg.grid(row=self._row, column=0, sticky="e")
	 	
		wdgSet = self._actorWdgDict.values()
		colSet = range(1, 1+len(wdgSet))
		for col, wdg in zip(colSet, wdgSet):
			wdg.grid_forget()
			wdg.grid(row=self._row, column=col)
	
	def setActors(self, actors):
		"""Set the list of actors.
		Once the object is created, the list can only be extended.

		Raises ValueError if actors is not an extension of the current list.
		"""
#		print "%s.setActors(%r)" % (self.__class__, actors)
		currActors = self._actorWdgDict.keys()
		currNumActors = len(currActors)
		if currActors != actors[:currNumActors]:
			raise ValueError("%r: new actors %r not an extension of existing %r" % (self, actors, currActors))

		newActors = actors[currNumActors:]
		for actor in newActors:	
			if actor in self._actorWdgDict:
				raise ValueError("%r: actor %r already exists" % (self, actor))
			
			self._actorWdgDict[actor] = _ActorWdg (
				master = self._master,
				prog = self._prog,
				actor = actor,
				readOnly = self._readOnly,
				command = self._actorCommand,
				helpURL = self._helpURL,
			)
		self.display(self._row, actors)
	
	def setCurrActors(self, currActors):
		"""Sets the list of actors that should be checked.
		
		Inputs:
		- currActors: list of actors that should be checked
		"""
#		print "%s.setCurrActors(%r)" % (self.__class__, currActors)
		for actor, wdg in self._actorWdgDict.iteritems():
			isAuth = actor in currActors
			wdg.set(isAuth)

		self._someActorsChecked(bool(currActors))
	
	def setReadOnly(self, readOnly):
		"""Update read only state.
		"""
#		print "_LockoutPerms.setReadOnly(%r)" % (readOnly,)
		readOnly = bool(readOnly)
		if self._readOnly != readOnly:
			for wdg in self._actorWdgDict.itervalues():
				wdg.setReadOnly(readOnly)

	def _actorCommand(self):
		"""Called when an actor button is pressed by hand.
		"""
#		print "%s._actorCommand()" % (self.__class__)
		
		actorList = [
			actor for actor, wdg in self._actorWdgDict.iteritems()
			if wdg.getBool()
		]
		cmdStr = 'setLocked %s' % (' '.join(actorList),)
		self._doCmd(cmdStr)
	
	def _someActorsChecked(self, someChecked):
		"""Show name as warning.
		Override in program subclass to do nothing.
		"""		
		if someChecked:
			self._nameWdg.setSeverity(RO.Constants.sevWarning)
		else:
			self._nameWdg.setSeverity(RO.Constants.sevNormal)
		
	def _cmdFailed(self, *args, **kargs):
		"""Called when a command fails; resets default state."""
		# handle name widget specially; it may not be an active control
		try:
			self._nameWdg.restoreDefault()
		except AttributeError:
			pass
		for wdg in self._actorWdgDict.itervalues():
			wdg.restoreDefault()

	def _createNameWdg(self):
		"""Create self._nameWdg.
		"""
		self._nameWdg = RO.Wdg.StrLabel (
			master = self._master,
			text = str(self),
			helpText = "lock out non-APO users",
			helpURL = self._helpURL,
		)
	
	def _doCmd(self, cmdStr):
		"""Execute a command.
		"""
		cmd = RO.KeyVariable.CmdVar(
			actor = "perms",
			cmdStr = cmdStr,
			callFunc = self._cmdFailed,
			callTypes = 'f!',
		)
		self._statusBar.doCmd(cmd)

	def __del__(self):
		self.delete()

	def __str__(self):
		return "Lockout"
	
	def __repr__(self):
		return "%s" % (self.__class__.__name__)


class _ProgPerms(_LockoutPerms):
	"""Permissions for one program.
	
	This class keeps track of the permissions,
	displays the info as a set of controls
	and responds to these controls by sending the appropriate commands.
	
	Inputs:
	- master	master widget
	- prog		program name
	- actors	a list of the currently known actors, in desired display order
	- row		row at which to grid display widgets
	- statusBar	object to handle commands (via doCmd)
	"""
	def __init__(self, master, prog, actors, readOnly, row, statusBar):
#		print "_ProgPerms(%r)" % (prog)
		_LockoutPerms.__init__(self,
			master = master,
			actors = actors,
			readOnly = readOnly,
			row = row,
			statusBar = statusBar,
			prog = prog
		)
	
	def isRegistered(self):
		"""Returns True if desired state is registered,
		False otherwise.
		"""
		return self._nameWdg.getRegInfo()[1]
	
	def setCurrActors(self, currActors):
#		print "_ProgPerms %s setCurrActors(%r)" % (self, currActors)
		_LockoutPerms.setCurrActors(self, currActors)
		self._nameWdg.setCanUnreg("perms" not in currActors)

	def setRegistered(self, isReg):
		"""Set registered or unregistered state.
		"""
#		print "%s %s.setRegistered(%r)" % (self._prog, self.__class__, isReg)
		self._nameWdg.setRegistered(isReg)
		for wdg in self._actorWdgDict.itervalues():
			wdg.setRegInfo(isReg, isReg)

	def _actorCommand(self):
		"""Called when an actor button is toggled.
		"""
#		print "%s._actorCommand()" % (self.__class__)
		
		actorList = [
			actor for actor, wdg in self._actorWdgDict.iteritems()
			if wdg.getBool()
		]
		cmdStr = 'set program=%s %s' % (self._prog, ' '.join(actorList))
		self._doCmd(cmdStr)

	def _createNameWdg(self):
		"""Create the name widget; a checkbutton
		that, when checked, unregisters the program.
		"""
		self._nameWdg = _ProgramWdg (
			master = self._master,
			prog = self._prog,
			command = self._progCommand,
			readOnly = self._readOnly,
			helpText = "Press to delete program %r" % (self._prog),
			helpURL = self._helpURL,
			width = 4,
		)
		self._nameWdg._actorWdg.addCallback(self._progCallFunc)
	
	def _progCommand(self):
		"""Called when the program name button is pushed by hand.
		Sends the appropriate command(s) to the hub.
		See also _progCallFunc, which controls actor enabling.
		"""		
#		print "%s._progCommand" % (self.__class__)
		doUnreg = self._nameWdg.getBool()
			
		# issue register or unregister command
		if doUnreg:
			cmdVerb = "unregister"
		else:
			cmdVerb = "register"
		cmdStr = '%s %s' % (cmdVerb, self._prog)
		self._doCmd(cmdStr)
	
		# if re-registering, restore permissions
		if not doUnreg:
			self._actorCommand()

	def _progCallFunc(self, wdg=None):
		"""Called when the program name button is toggled by any means.
		Sets enabled of actors.
		See also progCommand, which sends commands to the hub.
		"""
#		print "%s._progCallFunc" % (self.__class__)
		actReg, desReg = self._nameWdg.getRegInfo()
		
		# set enable of actor wdg
		for wdg in self._actorWdgDict.itervalues():
			wdg.setRegInfo(actReg, desReg)
	
	def setReadOnly(self, readOnly):
		"""Update read only state.
		"""
		readOnly = bool(readOnly)
		if self._readOnly != readOnly:
			self._nameWdg.setReadOnly(readOnly)
			for wdg in self._actorWdgDict.itervalues():
				wdg.setReadOnly(readOnly)

	def _someActorsChecked(self, someChecked):
		"""Do nothing in program class.
		"""
		pass
		
	def __str__(self):
		return self._prog
	
	def __repr__(self):
		return "%s(%s)" % (self.__class__.__name__, self._prog)

class _SettingsWdg(Tkinter.Frame):
	"""Widget to toggle a setting (actor permission or delete program).
	"""
	def __init__(self,
		master,
		prog,
		readOnly,
		helpURL = None,
	**kargs):
		Tkinter.Frame.__init__(self, master)
		self._prog = prog
		self._readOnly = readOnly
		
		self._actorWdg = RO.Wdg.Checkbutton (
			master = self,
			helpURL = helpURL,
			autoIsCurrent = True,
			isCurrent = False,
		**kargs)
		self._actorWdg.grid(row=0, column=1, sticky="w")
		self._actorWdg["disabledforeground"] = self._actorWdg["foreground"]
		
		self._saveActorInfo()
		self._setState()
		self._actorWdg.addCallback(self._doToggle)
	
	def _doToggle(self, *args, **kargs):
		pass
	
	def _saveActorInfo(self):
		"""Save actor settings that allow us to
		enable and disable the actor button appropriately.
		"""
		pass

	def getBool(self):
		"""Return the current value as a boolean.
		"""
		return self._actorWdg.getBool()
	
	def set(self, val):
		"""Set the current and default value.
		"""
		self._actorWdg.set(val)
		self._actorWdg.setDefault(val)
		self._setState()
	
	def _setState(self):
		pass
	
	def _setEnable(self, doEnable):
		self._actorWdg.setEnable(doEnable)
	
	def setReadOnly(self, readOnly):
		readOnly = bool(readOnly)
		if readOnly != self._readOnly:
			self._readOnly = readOnly
			self._setState()	
	
	def restoreDefault(self):
		self._actorWdg.restoreDefault()


class _ActorWdg(_SettingsWdg):
	"""Minimal widget to display a checkbutton and a changed indicator.
	
	This widget has 3 states:
	- read only: user can view permissions but not change anything
	- registered: program is registered and user can change settings
	- not exists: program unregistered so settings disabled
	(read only and unregistered is irrelevant since read only users
	only see registered programs)
	"""
	def __init__(self,
		master,
		actor,
		prog,
		readOnly,
		helpURL = None,
	**kargs):
		self._actor = actor
		self._actReg = True
		self._desReg = True
		_SettingsWdg.__init__(self,
			master = master,
			prog = prog,
			readOnly = readOnly,
			helpURL = helpURL,
		**kargs)
	
	def setReadOnly(self, readOnly):
		_SettingsWdg.setReadOnly(self, readOnly)
#		print "%s %s setReadOnly(%r)" % (self._prog, self._actor, readonly)
	
	def _doToggle(self, *args, **kargs):
		"""Checkbutton toggled; state may be transitional
		"""
		actState = self._actorWdg.getDefBool()
		desState = self._actorWdg.getBool()
		if actState == desState:
			self._setState()
			return

		if self._prog:
			if actState:
				self._actorWdg.helpText = "%s soon may not use %s" % (self._prog, self._actor) 
			else:
				self._actorWdg.helpText = "%s soon may use %s" % (self._prog, self._actor) 
		else:
			if actState:
				self._actorWdg.helpText = "%s will soon be available" % (self._actor,)
			else:
				self._actorWdg.helpText = "%s will soon be locked out" % (self._actor,)
	
	def _setState(self):
		"""State changed and not transiational; update widget appearance and help.
		"""
		isChecked = self.getBool()
#		print "%s %s _ActorWdg._setState; readOnly=%s; isChecked=%s, actReg=%s; desReg=%s" % \
#			(self._prog, self._actor, self._readOnly, isChecked, self._actReg, self._desReg)

		if self._readOnly:
			self._setEnable(False)
			
			if self._prog:
				if isChecked:
					self._actorWdg.helpText = "%s may use %s" % (self._prog, self._actor) 
				else:
					self._actorWdg.helpText = "%s may not use %s" % (self._prog, self._actor) 
			else:
				if isChecked:
					self._actorWdg.helpText = "%s is locked out" % (self._actor,)
				else:
					self._actorWdg.helpText = "%s is available" % (self._actor,)
			return

		if self._actReg and self._desReg:
			self._setEnable(True)
			if self._prog:
				if isChecked:
					self._actorWdg.helpText = "%s may use %s; click to change" % (self._prog, self._actor) 
				else:
					self._actorWdg.helpText = "%s may not use %s; click to change" % (self._prog, self._actor) 
			else:
				if isChecked:
					self._actorWdg.helpText = "%s is locked out; click to change" % (self._actor,)
				else:
					self._actorWdg.helpText = "%s is available; click to change" % (self._actor,)

		else:
			# program not registered or in transition, so user cannot change permissions
			self._setEnable(False)
			if not self._desReg:
				self._actorWdg.helpText = "Re-add %s to enable" % (self._prog)
			else:
				self._actorWdg.helpText = "%s being added; please wait" % (self._prog)

	def setRegInfo(self, actReg, desReg):
		actReg = bool(actReg)
		desReg = bool(desReg)
		if (self._desReg, self._actReg) != (desReg, actReg):
			self._actReg = actReg
			self._desReg = desReg
			self._setState()

class _ProgramWdg(_SettingsWdg):
	"""Widget for showing program name.
	When disabled, shows up as a label and help is gone.
	When enabled, shows up as a checkbutton with the text as the button
	(rather than text next to a separate checkbox).
	"""
	def __init__(self, *args, **kargs):
		# handle defaults and forced settings
		self._canUnreg = True # can program be unregistered? some are fixed
		kargs.setdefault("padx", 5)
		kargs.setdefault("padx", 2)
		kargs["indicatoron"] = False
		if kargs.get("prog"):
			kargs["text"] = kargs["prog"]
		_SettingsWdg.__init__(self, *args, **kargs)
		
	def _saveActorInfo(self):
		"""Save actor settings that allow us to
		enable and disable the actor button appropriately.
		"""
		self._enabledPadX = int(str(self._actorWdg["padx"]))
		self._enabledPadY = int(str(self._actorWdg["pady"]))
		self._borderWidth = int(str(self._actorWdg["borderwidth"]))
		self._disabledPadX = self._enabledPadX + self._borderWidth
		self._disabledPadY = self._enabledPadY + self._borderWidth
		
	def _setEnable(self, doEnable):
#		print "%s _ProgWdg._setEnable(%r)" % (self._prog, doEnable)
		_SettingsWdg._setEnable(self, doEnable)
		if doEnable:
			self._actorWdg.configure(
				padx = self._enabledPadX,
				pady = self._enabledPadY,
				borderwidth = self._borderWidth,
			)
		else:
			self._actorWdg.configure(
				padx = self._disabledPadX,
				pady = self._disabledPadY,
				borderwidth = 0,
			)
	
	def _doToggle(self, *args, **kargs):
		actState = self._actorWdg.getDefBool()
		desState = self._actorWdg.getBool()
		if actState == desState:
			self._setState()
			return
	
		if actState:
			self._actorWdg.helpText = "%s being added; click to delete" % (self._prog,)
		else:
			self._actorWdg.helpText = "%s being deleted; click to re-add" % (self._prog,)
		
	def getRegInfo(self):
		"""Returns actReg, desReg
		"""
		return (not self._actorWdg.getDefBool(), not self._actorWdg.getBool())
	
	def _setState(self):
		"""State changed; update widget appearance and help.
		"""
#		print "%s _ProgWdg._setState; readOnly=%s; isRegistered=%s, canUnreg=%s" % \
#			(self._prog, self._readOnly, self._isRegistered, self._canUnreg)
		if self._readOnly:
			self._setEnable(False)
			self._actorWdg.helpText = "Permissions for program %s" % (self._prog,)
			return
		
		if not self._canUnreg:
			self._setEnable(False)
			self._actorWdg.helpText = "%s is always added" % (self._prog,)
			return
		
		self._setEnable(True)
		actReg, desReg = self.getRegInfo()
		if actReg:
			self._actorWdg.helpText = "%s added; click to delete" % (self._prog,) 
		else:
			self._actorWdg.helpText = "%s deleted; click to re-add" % (self._prog,) 
	
	def setRegistered(self, isRegistered):
		self.set(not isRegistered)

	def setReadOnly(self, readOnly):
#		print "%s _ProgWdg.setReadOnly(%s)" % (self._prog, readOnly,)
		_SettingsWdg.setReadOnly(self, readOnly)
	
	def setCanUnreg(self, canUnreg):
		"""Indicate whether a program can be unregistered or is always registered.
		"""
		canUnreg = bool(canUnreg)
		if canUnreg != self._canUnreg:
			self._canUnreg = canUnreg
			self._setState()

if __name__ == "__main__":
	root = RO.Wdg.PythonTk()
	root.resizable(False, False)

	import TestData
	
	statusBar = RO.Wdg.StatusBar(
		master = root,
		dispatcher = TestData.dispatcher
	)
	
	testFrame = PermsInputWdg(
		master=root,
		statusBar = statusBar,
	)
	testFrame.pack()
	
	statusBar.pack(expand="yes", fill="x")
	
	def doReadOnly(but):
		readOnly = but.getBool()
		testFrame._setReadOnly(readOnly)

	def doNew(evt):
		wdg = evt.widget
		if not wdg.isOK():
			return

		progName = wdg.getString().upper()
		
		testFrame._addProg(progName)
		wdg.clear()
		wdg.focus_set()

	butFrame = Tkinter.Frame(root)
	
	Tkinter.Label(butFrame, text="Add:").pack(side="left", anchor="e")
	newEntryWdg = RO.Wdg.StrEntry (
		master = butFrame,
		partialPattern = r"^[a-zA-Z]{0,2}[0-9]{0,2}$",
		finalPattern = r"^[a-zA-Z][a-zA-Z][0-9][0-9]$",
		width = 4,
	)
	newEntryWdg.bind("<Return>", doNew)
	
	newEntryWdg.pack(side="left", anchor="w")

	Tkinter.Button(butFrame, text="Demo", command=TestData.animate).pack(side="left")
	
	RO.Wdg.Checkbutton(butFrame, text="Read Only", callFunc=doReadOnly).pack(side="left")
	
	butFrame.pack(anchor="w")

	TestData.start()

	root.mainloop()
