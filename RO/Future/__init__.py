"""These are modules from current Python that are backwards compatible
and are only imported if the user is using an older python.

Sample usage:
try:
	import foo
except ImportError:
	import RO.Future.foo as foo
	
WARNING: the version of subprocess supplied here is from
Python 2.4b1. It is NOT a release version. Do NOT use it yet.
It has several known bugs, especially on Windows.
	
See the individual modules for their license terms.
"""