#!/usr/local/bin/python
"""Basic dialog class(es). The dialog's window is shown when the object is created
and destroyed when the user exits the dialog.

At the moment the modal feature of ModalDialogBase does not work on Mac or unix.
I'm not sure why.

History:
2002-07-30 ROwen	Moved to the RO.Wdg module and renamed.
2003-04-24 ROwen	Removed "from Tkinter import *".
2004-05-18 ROwen	Stopped importing os; it wasn't used.
2004-08-11 ROwen	Define __all__ to restrict import.
"""
__all__ = ['ModalDialogBase']

import Tkinter

class ModalDialogBase(Tkinter.Toplevel):
	"""Base class for modal dialogs. You must subclass "body" and "apply".
	You may subclass: buttonbox, validate"
	"""

	def __init__(self, master = None, title = None):
		"""Create and display a modal dialog"""

		Tkinter.Toplevel.__init__(self, master)
		if master:
			self.transient(master)

		if title:
			self.title(title)

		self.master = master

		self.result = None

		bodyFrame = Tkinter.Frame(self)
		self.initial_focus = self.body(master = bodyFrame)
		bodyFrame.pack(padx=5, pady=5)

		self.buttonbox()

		self.grab_set()

		if not self.initial_focus:
			self.initial_focus = self

		self.protocol("WM_DELETE_WINDOW", self.cancel)

		self.geometry("+%d+%d" % (master.winfo_rootx()+50,
								  master.winfo_rooty()+50))

		self.initial_focus.focus_set()

		self.wait_window(self)

	# construction hooks

	def body(self, master):
		"""Create body of dialog, e.g. text entry area.
		Return the widget that should have the initial focus.
		Override (unless you want a blank area)
		"""

		pass

	def buttonbox(self):
		"""Add the standard "OK" and "Cancel" buttons.
		Override if you want something else.
		"""
		
		box = Tkinter.Frame(self)

		w = Tkinter.Button(box, text="OK", width=10, command=self.ok, default="active")
		w.pack(side="left", padx=5, pady=5)
		w = Tkinter.Button(box, text="Cancel", width=10, command=self.cancel)
		w.pack(side="left", padx=5, pady=5)

		self.bind("<KeyPress-Return>", self.ok)
		self.bind("<KeyPress-Escape>", self.cancel)

		box.pack()

	#
	# standard button semantics

	def ok(self, event=None):
		"""OK button pressed. If data is valid, call apply and close dialog.
		If data is not valid, return focus to initial input widget and do NOT close dialog.
		"""

		if not self.validate():
			self.initial_focus.focus_set() # put focus back to initial input widget
			return

		self.withdraw()
		self.update_idletasks()

		self.apply()

		self.cancel()

	def cancel(self, event=None):
		"""Cancel button pressed. Leave self.result=None and close the dialog.
		"""
		self.close(event=event)

	def close(self, event=None):
		"""Close the dialog window and return the focus to the master window."""
		if self.master:
			self.master.focus_set()
		self.destroy()

	#
	# command hooks

	def validate(self):
		"""Called if "OK" is pressed. Return true if the data is valid, false otherwise.
		"""

		return 1 # override

	def apply(self):
		"""Called if "OK" pressed. Set self.result based on supplied data.
		Override this! (The default is simply to set the result to "OK".)
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
	
		def apply(self):
			first = self.e1.get()
			second = self.e2.get()
			self.result = (first, second)
	

	root = Tkinter.Tk()
	d = TestDialog(root)
	print d.result

