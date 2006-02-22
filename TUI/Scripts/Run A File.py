"""Run a file of commands.

Each line must consist of the actor followed by the command, e.g.:
tcc show time

Blank lines and lines beginning with # are ignored.

History:
2006-02-22 ROwen
"""
import Tkinter
import RO.Wdg
import RO.Prefs.PrefVar

HelpURL = "Scripts/BuiltInScripts/RunAFile.html"

global g_file, filePrefVar
g_file = None
g_fileNameVar = None

def init(sr):
	"""Set up widgets to set input exposure time,
	drift amount and drift speed.
	"""
	global g_fileNameVar

	Tkinter.Label(sr.master, text="File:").pack(side="left")
	filePrefVar = RO.Prefs.PrefVar.FilePrefVar(
		name = "File",
	)
	g_fileNameVar = Tkinter.StringVar()
	filePrefWdg = filePrefVar.getEditWdg(
		master = sr.master,
		var = g_fileNameVar,
	)
	filePrefWdg.pack(side="left")

def run(sr):
	"""Execute the commands in the file.
	"""
	global g_fileNameVar, g_file

	fileName = g_fileNameVar.get()
	if not fileName:
		return
	g_file = file(fileName, 'rU')
	for line in g_file:
		line = line.strip()
		if not line or line.startswith("#"):
			continue
		
		actor, cmdStr = line.split(None, 1)
		yield sr.waitCmd(
			actor = actor,
			cmdStr = cmdStr,
		)
		
def end(sr):
	"""If telescope moved, restore original boresight position.
	"""
	global g_file
	if g_file:
		g_file.close()
