#!/usr/local/bin/python
"""Open a URL in the user's default browser.

The URL is opened in a background thread.

History:
2004-10-05 ROwen
"""
__all__ = ["browseURL"]

import threading
import urlparse
import webbrowser

class _BrowseURLThread(threading.Thread):
	def __init__(self, url):
		threading.Thread.__init__(self)
		self.url = url
		self.setDaemon(True)

	def run(self):
		url = self.url
		try:
			webbrowser.open(url)
			return
		except (SystemExit, KeyboardInterrupt):
			raise
		except Exception, e:
			pass

		# failed! if this is a file URL with an anchor,
		# try again without the anchor
		urlTuple = urlparse.urlparse(url)
		if urlTuple[0] == "file" and urlTuple[-1] != '':
			urlTuple = urlTuple[0:-1] + ('',)
			url = urlparse.urlunparse(urlTuple)
			if not url:
				return
			try:
				webbrowser.open(url)
				return
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				pass

		# failed!
		print "could not open URL %r: %s %r" % (url, e, e)

def browseURL(url):
	newThread = _BrowseURLThread(url)
	newThread.start()