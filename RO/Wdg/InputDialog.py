#!/usr/local/bin/python
"""Basic dialog class(es). The dialog's window is shown when the object is created
and destroyed when the user exits the dialog. The result is contained in dialog.result
and is None if the dialog is cancelled.

Warning: do not allow a menu to be posted in your dialog box under aqua Tk (on MacOS X).
This is due to tk bug 1101854 <https://sourceforge.net/tracker/?func=detail&atid=112997&aid=1101854&group_id=12997>

History:
2002-07-30 ROwen	Moved to the RO.Wdg module and renamed.
2003-04-24 ROwen	Removed "from Tkinter import *".
2004-05-18 ROwen	Stopped importing os; it wasn't used.
2004-08-11 ROwen	Define __all__ to restrict import.
2005-01-13 ROwen	Combined the apply and validate methods into setResult.
					The buttons method now receives the button's master as an argument.
					Buttons now have their own frame so you can pack or grid them as you prefer.
					The buttons method is now called before the body method. Also, the default buttons
					(OK and Cancel) are now RO.Wdg.Buttons. These changes allow one to add help text
					to the default buttons in the body method (by setting their helpText attribute).
					Modified to restore original focus and to generally work more like
					the example in Welch's Practical Programming in Tcl and Tk.
"""
__all__ = ['ModalDialogBase']

import Tkinter
import Button

class ModalDialogBase(Tkinter.Toplevel):
	"""Base class for modal dialogs.
	
	The result is returned in self.result
	
	You should subclass "body" and "setResult" and may subclass "buttons".
	"""

	def __init__(self, master = None, title = None):
		"""Create and display a modal dialog.
		"""
		Tkinter.Toplevel.__init__(self, master)
		self.resizable(False, False)

		if title:
			self.title(title)

		self.result = None
		
		self.doneVar = Tkinter.BooleanVar()
		
		# widget that had focus before this dialog opened
		self.prevFocus = self.focus_get() or master
		
		buttonFrame = Tkinter.Frame(self)
		self.buttons(master = buttonFrame)
		buttonFrame.pack(side="bottom")

		bodyFrame = Tkinter.Frame(self)
		# create dialog body and save widget that should
		# initially get focus in this dialog
		self.initialFocus = self.body(master = bodyFrame)
		if not self.initialFocus:
			self.initialFocus = self
		bodyFrame.pack(side="bottom")
		
		self.protocol("WM_DELETE_WINDOW", self.close)

		self.geometry("+%d+%d" % (master.winfo_rootx()+50,
								  master.winfo_rooty()+50))

		self.initialFocus.focus_set()

		# According to Welch, grab_set may fail if the dialog is not fully visible
		# But wait_visible may also fail. We can safely ignore these errors;
		# it's just a best-effort attempt to grab (make the dialog box modal).
		try:
			self.wait_visibility()
		except TclError, e:
			pass
		try:
			self.grab_set()
		except TclError:
			pass

		self.update_idletasks() # solves a few problems on MacOS X

		self.wait_variable(self.doneVar)

		try:
			self.grab_release()
		except TclError:
			pass

		if self.prevFocus:
			self.prevFocus.focus_set()

		self.destroy()

	# construction hooks

	def body(self, master):
		"""Create body of dialog, e.g. text entry area.
		Return the widget that should have the initial focus.
		Override (unless you want a blank area).
		"""
		pass

	def buttons(self, master):
		"""Create the standard "OK" and "Cancel" buttons.
		Override if you want something else.
		"""
		
		self.okWdg = Button.Button(master, text="OK", width=6, command=self.ok, default="active")
		self.okWdg.pack(side="left")
		self.cancelWdg = Button.Button(master, text="Cancel", width=6, command=self.close)
		self.cancelWdg.pack(side="left")

		self.bind("<KeyPress-Return>", self.ok)
		self.bind("<KeyPress-Escape>", self.close)

	def ok(self, event=None):
		"""OK button pressed. If data is valid, call apply and close dialog.
		If data is not valid, return focus to initial input widget and do NOT close dialog.
		"""
		try:
			self.setResult()
		except ValueError:
			self.initialFocus.focus_set() # put focus back to initial input widget
			return
			
		self.close()

	def close(self, event=None):
		"""Close the dialog.
		"""
		self.doneVar.set(True)

	# command hooks

	def setResult(self):
		"""Set self.result based on supplied data.
		
		Raise ValueError if the data is not valid.
		
		Called if "OK" pressed. Subclasses should override.
		"""
		self.result = "OK"


if __name__ == "__main__":
	class TestDialog(ModalDialogBase):
		def body(self, master):
	
			Tkinter.Label(master, text="Name:").grid(row=0)
			Tkinter.Label(master, text="Password:").grid(row=1)
	
			self.e1 = Tkinter.Entry(master)
			self.e2 = Tkinter.Entry(master, show="*")
	
			self.e1.grid(row=0, column=1)
			self.e2.grid(row=1, column=1)
			return self.e1 # initial focus
	
		def setResult(self):
			first = self.e1.get()
			second = self.e2.get()
			self.result = (first, second)
	
	def doDialog():
		d = TestDialog(root, "User Info")
		l["text"] = "Result: %s" % (d.result,)
		print d.result
			
	root = Tkinter.Tk()
	e = Tkinter.Entry(root)
	e.pack()
	l = Tkinter.Label(root)
	l.pack()
	b = Tkinter.Button(root, text="Dialog", command=doDialog)
	b.pack()
	e.focus_set()

	root.mainloop()
