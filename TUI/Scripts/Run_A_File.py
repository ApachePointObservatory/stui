"""Run a file of commands.

Each line must consist of the actor followed by the command, e.g.:
tcc show time

Blank lines and lines beginning with # are ignored.

To do:
- Look for <TUIAdditions>/ScriptFiles and if found,
  use that as the starting directory. That will require
  a different file widget (one that can take a starting
  directory).

History:
2006-03-07 ROwen
"""
import Tkinter
import RO.Wdg

HelpURL = "Scripts/BuiltInScripts/RunAFile.html"

global g_file, g_fileWdg
g_file = None
g_fileWdg = None

def init(sr):
	"""Set up widgets to set input exposure time,
	drift amount and drift speed.
	"""
	global g_fileWdg

	Tkinter.Label(sr.master, text="File:").pack(side="left")
	g_fileWdg = RO.Wdg.FileWdg(
		master = sr.master,
		helpText = "file of commands",
		helpURL = HelpURL,
	)
	g_fileWdg.pack(side="left")

def run(sr):
	"""Execute the commands in the file.
	"""
	global g_fileWdg, g_file

	filePath = g_fileWdg.getPath()
	if not filePath:
		return
	g_file = file(filePath, 'rU')
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
