r"""
Interface for viewing images with the ds9 image viewer.
Loosely based on XPA, by Andrew Williams.

For more information, see the XPA Access Points section
of the ds9 reference manual (under Help in ds9).

WARNING: this module is not fully with Windows using ds9 3.0.3 with xpa 2.1.5.
There appears to be a bug in ds9 or xpa that makes showArray inoperable.
Symptoms suggest that the array data is undergoing newline translation.
See <http://www.astro.washington.edu/rowen/ds9andxpa.html> for more information.

Requirements:

*** Unix Requirements
- ds9 and xpa must be installed somewhere on your $PATH

*** MacOS X Requirements
- The ds9 MacOS X application (ds9.app) in ~/Applications or /Applications
  or the ds9 unix application somewhere on the $PATH
- if xpa is not yet part of the ds9 MacOS X application bundle,
  then xpaget, etc. must be installed as unix executables somewhere on the path.
  Currently if you download the darwin binaries, simply put xpaget, etc.
  somewhere on your path; /usr/local/bin is traditional,
  but you may have to create it and and modify your .login to include it on $PATH.

*** Windows Requirements
- Mark Hammonds pywin32 package: <http://sourceforge.net/projects/pywin32/>
- ds9 installed in the default directory C:\Program Files\ds9\
  (the default location)
- xpa installed in either the default directory C:\Program Files\xpa\
  or in C:\Program Files\ds9\
- Mark Hammonds pywin32 package: <http://sourceforge.net/projects/pywin32/>
- ds9 installed in the default directory C:\Program Files\ds9\
  (the default location)
- xpa installed in either the default directory C:\Program Files\xpa\
  or in C:\Program Files\ds9\

Extra Keyword Arguments:
Many commands take additional keywords as arguments. These are sent
as separate commands after the main command is executed.
Useful keywords for viewing images include: scale, orient and zoom.
See the XPA Access Points section of the ds9 reference manual
for more information. Note that the value of each keyword
is sent as an unquoted string. If you want quotes, provide them
as part of the value string.

Template Argument:
The template argument allows you to specify which copy of ds9
or which other software you wish to command via xpa.
One common use is to have multiple copies of ds9 on your own machine
(often necessary because ds9 only has one window, grr).
If you launch ds9 with the -title command-line option then you can
send commands to that ds9 by using that title as the template.
See the XPA documentation for other uses for template, such as talking
to ds9 on a remote host.

For a list of local servers try % xpaget xpans

History:
2004-04-15 ROwen	First release.
2004-04-20 ROwen	showarry improvements:
					- Accepts any array whose values can be represented as signed ints.
					- Bug fix: x and y dimensions were swapped (#@$@# numarray)
2004-04-29 ROwen	Added xpaset function.
2004-05-05 ROwen	Added DS9Win class and moved the showXXX functions to it.
					Added function xpaget.
					Added template argument to xpaset.
2004-10-15 ROwen	Bug fix: could only communicate with one ds9;
					fixed by specifying port=0 when opening ds9.
2004-11-02 ROwen	Improved Mac compatibility (now looks in [~]/Applications).
					Made compatible with Windows, except showArray is broken;
					this appears to be a bug in ds9 3.0.3.
					loadFITSFile no longer tests the file name's extension.
					showArray now handles most array types without converting the data.
					Eliminated showBinFile because I could not get it to work;
					this seems to be an bug or documentation bug in ds9.
					Changed order of indices for 3-d images from (y,x,z) to (z,y,x).
2004-11-17 ROwen	Corrected a bug in the subprocess version of xpaget.
					Updated header comments for big-fixed version of subprocess.
2004-12-01 ROwen	Bug fix in xpaset: terminate data with \n if not already done.
					Modified to use subprocess module (imported from RO.Future
					if Python is old enough not to include it).
					Added __all__.
2004-12-13 ROwen	Bug fix in DS9Win.__init__; the 2004-12-01 code was missing
					the code that waited for DS9 to launch.
"""
__all__ = ["xpaget", "xpaset", "DS9Win"]
import numarray as num
import os
import time
import RO.OS
try:
	import subprocess
except ImportError:
	import RO.Future.subprocess as subprocess

_DS9Exec = "ds9"	# path to ds9 executable; "ds9" if can be found automatically
_XPADir = None		# dir for xpa executables; None if they can be found automatically
if RO.OS.PlatformName == "win":
	import win32api

	def _getWinPath():
		# verify that ds9, xpaget and xpaset are all installed in this dir:
		progRoot = "C:\\Program Files\\"
		
		# make sure ds9 is where we expect it to be
		ds9Path = progRoot + "ds9\\ds9.exe"
		if not os.path.exists(ds9Path):
			raise RuntimeError("Could not find %s" % ds9Path)

		# look for xpaget in progRoot\xpa\ and progRoot\ds9\
		for subdir in ("xpa", "ds9"):
			xpaDir = progRoot + subdir + "\\"
			if os.path.exists(xpaDir + "xpaget.exe"):
				break
		else:
			raise RuntimeError("Could not find xpa in %s\\xpa\\ or %s\\ds9\\" % (progRoot,))

		return ds9Path, xpaDir
	
	_DS9Exec, _XPADir = _getWinPath()

elif RO.OS.PlatformName == "mac":
	for appRoot in ("~/Applications", "/Applications"):
		appPath = appRoot + "/ds9.app/"
		if not os.path.exists(appPath):
			continue
		
		if os.path.exists(appPath + "ds9"):
			_DS9Exec = appPath + "ds9"
		if os.path.exists(appPath + "xpaget"):
			_XPADir = appPath

#print "_DS9Exec = %r\n_XPADir = %r" % (_DS9Exec, _XPADir)

_ArrayKeys = ("dim", "dims", "xdim", "ydim", "zdim", "bitpix", "skip", "arch")
_DefTemplate = "ds9"

_OpenCheckInterval = 0.2 # seconds
_MaxOpenTime = 10.0 # seconds

def xpaget(cmd, template=_DefTemplate):
	"""Executes a simple xpaget command:
		xpaset -p <template> <cmd>
	returning the reply.
	
	Inputs:
	- cmd		command to execute; may be a string or a list
	- template	xpa template; can be the ds9 window title
				(as specified in the -title command-line option)
				host:port, etc.

	Raises RuntimeError if anything is written to stderr.
	"""
	fullCmd = 'xpaget %s %s' % (template, cmd,)
#	print fullCmd

	p = subprocess.Popen(
		args = fullCmd,
		shell = True,
		stdin = subprocess.PIPE,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE,
		cwd = _XPADir,
	)
	try:
		p.stdin.close()
		errMsg = p.stderr.read()
		if errMsg:
			raise RuntimeError('%r failed: %s' % (fullCmd, errMsg))
		return p.stdout.read()
	finally:
		p.stdout.close()
		p.stderr.close()


def xpaset(cmd, data=None, dataFunc=None, template=_DefTemplate):
	"""Executes a simple xpaset command:
		xpaset -p <template> <cmd>
	or else feeds data to:
		xpaset <template> <cmd>
		
	The command must not return any output for normal completion.
	
	Inputs:
	- cmd		command to execute
	- data		data to write to xpaset's stdin; ignored if dataFunc specified.
				If data[-1] is not \n then a final \n is appended.
	- dataFunc	a function that takes one argument, a file-like object,
				and writes data to that file. If specified, data is ignored.
				Warning: if a final \n is needed, dataFunc must supply it.
	- template	xpa template; can be the ds9 window title
				(as specified in the -title command-line option)
				host:port, etc.
	
	Raises RuntimeError if anything is written to stdout or stderr.
	"""
	if data or dataFunc:
		fullCmd = 'xpaset %s %s' % (template, cmd)
	else:
		fullCmd = 'xpaset -p %s %s' % (template, cmd)
#	print fullCmd

	p = subprocess.Popen(
		args = fullCmd,
		shell = True,
		stdin = subprocess.PIPE,
		stdout = subprocess.PIPE,
		stderr = subprocess.STDOUT,
	)
	try:
		if dataFunc:
			dataFunc(p.stdin)
		elif data:
			p.stdin.write(data)
			if data[-1] != '\n':
				p.stdin.write('\n')
		p.stdin.close()
		reply = p.stdout.read()
		if reply:
			raise RuntimeError("%r failed: %s" % (fullCmd, reply.strip()))
	finally:
		p.stdin.close() # redundant
		p.stdout.close()


def _computeCnvDict():
	"""Compute array type conversion dict.
	Each item is: unsupported type: type to which to convert.
	
	ds9 supports UInt8, Int16, Int32, Float32 and Float64.
	"""
	
	cnvDict = {
		num.Int8: num.Int16,
		num.UInt16: num.Int32,
		num.UInt32: num.Float32,	# ds9 can't handle 64 bit integer data
		num.Int64: num.Float64,
	}

	if hasattr(num, "UInt64="):
		cnvDict[num.UInt64] = num.Float64

	return cnvDict

_CnvDict = _computeCnvDict()
_FloatTypes = (num.Float32, num.Float64)
_ComplexTypes = (num.Complex32, num.Complex64)


def _expandPath(fname, extraArgs=""):
	"""Expand a file path and protect it such that spaces are allowed.
	Inputs:
	- fname		file path to expand
	- extraArgs	extra arguments that are to be appended
				to the file path
	"""
	filepath = os.path.abspath(os.path.expanduser(fname))
	# if windows, change \ to / to work around a bug in ds9
	filepath = filepath.replace("\\", "/")
	# quote with "{...}" to allow ds9 to handle spaces in the file path
	return "{%s%s}" % (filepath, extraArgs)


def _formatOptions(kargs):
	"""Returns a string: "key1=val1,key2=val2,..."
	(where keyx and valx are string representations)
	"""
	arglist = ["%s=%s" % keyVal for keyVal in kargs.iteritems()]
	return '%s' % (','.join(arglist))


def _splitDict(inDict, keys):
	"""Splits a dictionary into two parts:
	- outDict contains any keys listed in "keys";
	  this is returned by the function
	- inDict has those keys removed (this is the dictionary passed in;
	  it is modified by this call)
	"""
	outDict = {}
	for key in keys:
		if inDict.has_key(key):
			outDict[key] = inDict.pop(key)
	return outDict	


class DS9Win:
	"""An object that talks to a particular window on ds9
	
	Inputs:
	- template:	window name (see ds9 docs for talking to a remote ds9)
	- doOpen: open ds9 using the desired template, if not already open;
			MacOS X warning: opening ds9 requires ds9 to be on your PATH;
			this may not be true by default;
			see the module documentation above for workarounds.
	"""
	def __init__(self, template=_DefTemplate, doOpen=True):
		self.template = str(template)
		if doOpen:
			self.doOpen()
	
	def doOpen(self):
		"""Open the ds9 window (if necessary).
		"""
		if self.isOpen():
			return

		subprocess.Popen(
			executable = _DS9Exec,
			args = ('ds9', '-title', self.template, '-port', "0"),
			cwd = _XPADir,
		)

		startTime = time.time()
		while True:
			try:
				time.sleep(_OpenCheckInterval)
				xpaget('mode', self.template)
				break
			except RuntimeError:
				if time.time() - startTime > _MaxOpenTime:
					raise RuntimeError('Could not open ds9 window %r' % self.template)
	
	def isOpen(self):
		"""Return True if this ds9 window is open
		and available for communication, False otherwise.
		"""
		try:
			self.xpaget('mode')
			return True
		except RuntimeError:
			return False

	def showArray(self, arr, **kargs):
		"""Display a 2-d or 3-d grayscale integer numarray arrays.
		3-d images are displayed as data cubes, meaning one can
		view a single z at a time or play through them as a movie,
		that sort of thing.
		
		Inputs:
		- arr: a numarray array; must be 2-d or 3-d:
			2-d arrays have index order (y, x)
			3-d arrays are loaded as a data cube index order (z, y, x)
		kargs: see Extra Keyword Arguments in the module doc string for information.
		Keywords that specify array info (see doc for showBinFile for the list)
		are ignored, because array info is determined from the array itself.
		
		Data types:
		- UInt8, Int16, Int32 and floating point types sent unmodified.
		- All other integer types are converted before transmission.
		- Complex types are rejected.
	
		Raises ValueError if arr's elements are not some kind of integer.
		Raises RuntimeError if ds9 is not running or returns an error message.
		"""
		if not hasattr(arr, "type") or not hasattr(arr, "astype"):
			# create an array of the appropriate type
			# then check if it can safely be changed to int32
			arr = num.array(arr)
		
		if arr.type() in _ComplexTypes:
			raise TypeError("ds9 cannot handle complex data")

		ndim = arr.getrank()
		if ndim not in (2, 3):
			raise RuntimeError("can only display 2d and 3d arrays")
		dimNames = ["z", "y", "x"][3-ndim:]

		# if necessary, convert array type
		cnvType = _CnvDict.get(arr.type())
		if cnvType:
#			print "converting array from %s to %s" % (arr.type(), cnvType)
			arr = arr.astype(cnvType)
		
		# compute bits/pix; ds9 uses negative values for floating values
		bitsPerPix = arr.itemsize() * 8
		if arr.type() in _FloatTypes:
			# array is float; use negative value
			bitsPerPix = -bitsPerPix
	
		# remove array info keywords from kargs; we compute all that
		_splitDict(kargs, _ArrayKeys)

		# generate array info keywords; note that numarray
		# 2-d images are in order [y, x]
		# 3-d images are in order [z, y, x]
		arryDict = {}
		for axis, size in zip(dimNames, arr.getshape()):
			arryDict["%sdim" % axis] = size
		
		arryDict["bitpix"] = bitsPerPix
		xpaset(
			cmd = 'array [%s]' % (_formatOptions(arryDict),),
			dataFunc = arr.tofile,
			template = self.template,
		)
		
		for keyValue in kargs.iteritems():
			self.xpaset(cmd=' '.join(keyValue))

# showBinFile is commented out because it is broken with ds9 3.0.3
# (apparently due to a bug in ds9) and because it wasn't very useful
#	def showBinFile(self, fname, **kargs):
#		"""Display a binary file in ds9.
#		
#		The following keyword arguments are used to specify the array:
#		- xdim		# of points along x
#		- ydim		# of points along y
#		- dim		# of points along x = along y (only use for a square array)
#		- zdim		# of points along z
#		- bitpix	number of bits/pixel; negative if floating
#		- arch	one of bigendian or littleendian (intel)
#		
#		The remaining keywords are extras treated as described
#		in the module comment.
#
#		Note: integer data must be UInt8, Int16 or Int32
#		(i.e. the formats supported by FITS).
#		"""
#		arryDict = _splitDict(kargs, _ArrayKeys)
#		if not arryDict:
#			raise RuntimeError("must specify dim (or xdim and ydim) and bitpix")
#
#		arrInfo = "[%s]" % (_formatOptions(arryDict),)
#		filePathPlusInfo = _expandPath(fname, arrInfo)
#
#		self.xpaset(cmd='file array "%s"' % (filePathPlusInfo,))
#		
#		for keyValue in kargs.iteritems():
#			self.xpaset(cmd=' '.join(keyValue))
	
	def showFITSFile(self, fname, **kargs):
		"""Display a fits file in ds9.
		
		Inputs:
		- fname	name of file (including path information, if necessary)
		kargs: see Extra Keyword Arguments in the module doc string for information.
		Keywords that specify array info (see doc for showBinFile for the list)
		must NOT be included.
		"""
		filepath = _expandPath(fname)
		self.xpaset(cmd='file "%s"' % filepath)

		# remove array info keywords from kargs; we compute all that
		arrKeys = _splitDict(kargs, _ArrayKeys)
		if arrKeys:
			raise RuntimeError("Array info not allowed; rejected keywords: %s" % arrKeys.keys())
		
		for keyValue in kargs.iteritems():
			self.xpaset(cmd=' '.join(keyValue))

	def xpaget(self, cmd):
		"""Execute a simple xpaget command and return the reply.
		
		The command is of the form:
			xpaset -p <template> <cmd>
		
		Inputs:
		- cmd		command to execute
	
		Raises RuntimeError if anything is written to stderr.
		"""
		return xpaget(cmd=cmd, template=self.template)
	

	def xpaset(self, cmd, data=None, dataFunc=None):
		"""Executes a simple xpaset command:
			xpaset -p <template> <cmd>
		or else feeds data to:
			xpaset <template> <cmd>
			
		The command must not return any output for normal completion.
		
		Inputs:
		- cmd		command to execute
		- data		data to write to xpaset's stdin; ignored if dataFunc specified
		- dataFunc	a function that takes one argument, a file-like object,
					and writes data to that file. If specified, data is ignored.
		
		Raises RuntimeError if anything is written to stdout or stderr.
		"""
		return xpaset(cmd=cmd, data=data, dataFunc=dataFunc, template=self.template)
