#!/usr/local/bin/python
"""Constants for the RO package, especially RO.Wdg.

Supplies the following constants:

For widgets displaying data differently depending on state:
- Normal
- Warning
- Error

Functions to get and set the base url (prefix) for url help
(these are not imported with from ... import *
since they are mainly used internally to RO.Wdg):
- _joinHelpURL
- _setHelpURLBase

History:
2004-08-11 ROwen	Split out from RO.Wdg.Label and RO.Wdg.CtxMenu.
					Add st_ prefix to state constants.
2004-09-02 ROwen	Moved to RO.Constants to solve circular import problems.
"""
__all__ = ['st_Normal', 'st_Warning', 'st_Error']

import urlparse

# state constants
st_Normal = 0
st_Warning = 1
st_Error = 2

# Call setHelpURLBase if you want to specify URLs relative to a base
_HelpURLBase = ""
_gotHelpURLBase = False

def _joinHelpURL(urlSuffix=""):
	"""Prepend the help url base and return the result.
	If urlSuffix is "" then return the help url base.
	"""
	global _HelpURLBase, _gotHelpURLBase
	_gotHelpURLBase = True
	return urlparse.urljoin(_HelpURLBase, urlSuffix)

def _setHelpURLBase(urlBase):
	"""Set the base url for help urls.
	May only be called before getHelpURLBase is called
	(i.e. before any widgets are created that use url help).
	"""
	global _HelpURLBase, _gotHelpURLBase
	if _gotHelpURLBase:
		raise RuntimeError("helpURL already requested; cannot change it now.")

	if urlBase.endswith("/"):
		_HelpURLBase = urlBase
	else:
		_HelpURLBase = urlBase + "/"
