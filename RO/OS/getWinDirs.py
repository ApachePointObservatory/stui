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
"""
import _winreg # make sure this is Windows; raise ImportError if not
try:
	from win32com.shell import shell, shellcon
	import pywintypes
except ImportError:
	raise RuntimeError("Windows users must install the win32 package")
import os

def findFolder(dirType):
	"""Return a path to the specified standard directory or None if not found.

	The path is in the form expected by the os.path module.
	
	Inputs:
	- dirType: one of CSID constants, as found in the win32com.shellcon module,
		such as CSIDL_APPDATA or CSIDL_COMMON_APPDATA.
		
	Note: in theory one can create the folder by adding CSILD_FLAG_CREATE
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

def getPrefsDir():
	"""Return a path to the user's preferences folder
	(actually the user's Application Data folder).
	
	Returns None if the directory does not exist.
	"""
	return findFolder(shellcon.CSIDL_APPDATA)

def getAppSuppDirs():
	"""Return a list of paths to the user's and local (shared) application support folder.
	
	If a folder does not exist it is omitted; hence returns [] if nothing found.
	"""
	retDirs = []
	for dirType in (shellcon.CSIDL_APPDATA, shellcon.CSIDL_COMMON_APPDATA):
		path = findFolder(dirType)
		if path != None:
			retDirs.append(path)
	return retDirs


if __name__ == "__main__":
	print "Testing"
	print "prefs=", getPrefsDir()
	print "app supp=", getAppSuppDirs()
