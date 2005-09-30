"""Determine the application data directory for Windows.

Requires Mark Hammond's win32 extensions
<http://starship.python.net/crew/mhammond/win32/>.
Raises RuntimeError on import if win32 is not found.

Thanks to Mike C Fletcher for sample code showing how to use win32com.shell
and a pointer to Microsoft's documentation!

SHGetFolderPath is documented here:
<http://msdn.microsoft.com/library/default.asp?url=/library/en-us/shellcc/platform/shell/reference/functions/shgetfolderpath.asp>

The directory type constants are documented here:
<http://msdn.microsoft.com/library/default.asp?url=/library/en-us/shellcc/platform/shell/reference/enums/csidl.asp>

History:
2004-02-04 ROwen
2005-07-11 ROwen	Modified getAppSuppDirs to return None for nonexistent directories.
					Added getDocsDir.
2005-09-28 ROwen	Changed getPrefsDir to getPrefsDirs.
					Added getAppDirs.
					Removed unused import of _winreg
2005-09-30 ROwen	Raise ImportError (as getDirs expects), not RuntimeError
					if run on non-windows system.
"""
from win32com.shell import shell, shellcon
import pywintypes
import os

def getStandardDir(dirType):
	"""Return a path to the specified standard directory or None if not found.

	The path is in the form expected by the os.path module.
	
	Inputs:
	- dirType: one of CSID constants, as found in the win32com.shellcon module,
		such as CSIDL_APPDATA or CSIDL_COMMON_APPDATA.
		
	Note: in theory one can create the directory by adding CSILD_FLAG_CREATE
	to dirType, but in practice this constant is NOT defined in win32com.shellcon,
	so it is risky (you'd have to specify an explicit integer and hope it did not change).
	"""
	try:
		return shell.SHGetFolderPath(
			0, # hwndOwner (0=NULL)
			dirType,
			0, # hToken (0=NULL, no impersonation of another user)
			0  # dwFlag: want SHGFP_TYPE_CURRENT but it's not in shellcon; 0 seems to work
		)
	except pywintypes.com_error:
		return None

def getAppDirs():
	"""Return two paths: the user's private and shared applications directory.
	On Windows only the shared one exists.
	
	If a directory does not exist, its path is set to None.
	
	A typical return on English system is:
	[None
	C:\Program Files]
	"""
	path = getStandardDir(CSIDL_PROGRAM_FILES)
	return [None, path]

def getAppSuppDirs():
	"""Return two paths: the user's private and shared application support directory.
	
	If a directory does not exist, its path is set to None.
	
	A typical return on English system is:
	[C:\Documents and Settings\<username>\Application Data,
	C:\Documents and Settings\All Users\Application Data]
	"""
	retDirs = []
	for dirType in (shellcon.CSIDL_APPDATA, shellcon.CSIDL_COMMON_APPDATA):
		path = getStandardDir(dirType)
		retDirs.append(path)
	return retDirs

def getDocsDir():
	"""Return the path to the user's documents directory.

	Return None if the directory does not exist.

	A typical result on an English system is:
	C:\Documents and Settings\<username>\My Documents
	"""
	return getStandardDir(shellcon.CSIDL_PERSONAL)

def getPrefsDirs():
	"""Return two paths: the user's private and shared preferences directory.
	On Windows this is actually the application data directory.
	
	Return None if the directory does not exist.

	A typical return on English system is:
	[C:\Documents and Settings\<username>\Application Data,
	C:\Documents and Settings\All Users\Application Data]
	"""
	return getAppSuppDirs()


if __name__ == "__main__":
	print "Testing"
	print 'getAppDirs()     = %r' % getAppDirs()
	print 'getAppSuppDirs() = %r' % getAppSuppDirs()
	print 'getDocsDir()     = %r' % getDocsDir()
	print 'getPrefsDirs()   = %r' % getPrefsDirs()
