#!/usr/local/bin/python
"""Calibrate the NICFPS Fabrey-Perot by taking data
over a range of X, Y and Z positions as specified in a file.

The file format is:
- Zero or more lines of X Y Z position data, in steps
  - values may be separated with any whitespace, but not commas
  - values must be integers
  - leading and trailing whitespace are ignored.
- Blank lines are ignored.
- Comments: lines whose first non-whitespace character is # are ignored.

The whole file is parsed before measurement begins;
any errors are reported and must be corrected.

History:
2004-12-16 ROwen
"""
import RO.Prefs
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Inst.NICFPS.NICFPSModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

# constants
InstName = "NICFPS"
HelpURL = "Scripts/BuiltInScripts/NICFPSCalibrate.html"

# global variables
g_expWdg = None
g_filePrefWdg = None
g_file = None

def init(sr):
	"""Create widgets.
	"""
	global g_expWdg, g_filePrefWdg
	
	sr.debug = False
	
	nicfpsModel = TUI.Inst.NICFPS.NICFPSModel.getModel()

	row=0
	
	# standard exposure status widget
	expStatusWdg = ExposeStatusWdg(sr.master, InstName)
	expStatusWdg.grid(row=row, column=0, sticky="news")
	row += 1

	# standard exposure input widget
	g_expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
	g_expWdg.numExpWdg.helpText = "# of exposures at each spacing"
	g_expWdg.grid(row=row, column=0, sticky="news")
	row += 1
	
	gr = g_expWdg.gridder
		
	# add file prefrence editor
	filePref = RO.Prefs.PrefVar.FilePrefVar("Input File")
	g_filePrefWdg = filePref.getEditWdg(g_expWdg)
	g_filePrefWdg.helpText = "file of x y z etalon positions"
	gr.gridWdg("Data File", g_filePrefWdg)
	
	if sr.debug:
		g_expWdg.timeWdg.set(3)
		g_expWdg.fileNameWdg.set("debugtest")
	
def run(sr):
	"""Take a calibration sequence.
	"""
	# get current NICFPS focal plane geometry from the TCC
	# but first make sure the current instrument
	# is actually NICFPS
	global g_expWdg, g_filePrefWdg, g_file
	
	expModel = TUI.Inst.ExposeModel.getModel(InstName)
	nicfpsModel = TUI.Inst.NICFPS.NICFPSModel.getModel()
	tccModel = TUI.TCC.TCCModel.getModel()

	if not sr.debug:
		currInstName = sr.getKeyVar(tccModel.instName)
		if not currInstName.lower().startswith(InstName.lower()):
			raise sr.ScriptError("%s is not the current instrument!" % InstName)
	
	# get exposure data and verify we have enough info to proceed
	numExp = g_expWdg.numExpWdg.getNum()
	expCmdPrefix = g_expWdg.getString()
	if not expCmdPrefix:
		return

	# get data file and parse it
	fileName = g_filePrefWdg["text"]
	if not fileName:
		raise sr.ScriptError("specify a calibration data file")

	g_file = file(fileName, 'rU')
	if not g_file:
		raise sr.ScriptError("could not open %r" % fileName)
	
	if sr.debug:
		print "Reading file %r" % (fileName,)
	
	# read the file in advance, so we know how many lines of data there are
	xyzList = []
	for rawLine in g_file:
		if sr.debug:
			print "Read:", rawLine,
		line = rawLine.strip()
		if not line:
			continue
		if line.startswith("#"):
			continue
		try:
			x, y, z = [int(val) for val in line.split(None, 3)]
		except StandardError:
			raise sr.ScriptError("could not parse %r" % rawLine)
		xyzList.append((x, y, z))
	
	g_file.close()
	g_file = None
	
	if sr.debug:
		print "xyzList =", xyzList
	
	numPositions = len(xyzList)
		
	totNumExp = numExp * numPositions

	for seqInd in range(numPositions):
		xyzPos = xyzList[seqInd]
		
		# Set etalon position one axis at a time
		sr.showMsg("Step %s of %s: set etalon x,y,z = %s " % (seqInd+1, numPositions, xyzPos))
		for axis, pos in zip(("x", "y", "z"), xyzPos):
			yield sr.waitCmd(
				actor = nicfpsModel.actor,
				cmdStr = "fp set%s %d" % (axis, pos),
			)

		# compute # of exposures & format expose command
		startNum = seqInd * numExp
		expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNumExp)
		
		# take exposure sequence
		sr.showMsg("Step %s of %s: expose at etalon x,y,z = %s" % (seqInd+1, numPositions, xyzPos))
		yield sr.waitCmd(
			actor = expModel.actor,
			cmdStr = expCmdStr,
		)

def end(sr):
	global g_file
	if g_file:
		g_file.close()