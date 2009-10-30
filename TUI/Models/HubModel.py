#!/usr/bin/env python
"""An object that models the current state of the Hub.

It contains instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

2004-07-22 ROwen
2004-08-25 ROwen    Added users (a new hub keyword) and commented out commanders.
2005-07-08 ROwen    Added httpRoot.
2006-03-30 ROwen    Added user.
2009-04-01 ROwen    Modified to use opscore.actor.model.
2009-10-30 ROwen    Moved from TUI.HubModel to TUI.Models.HubModel.
                    Added methods getBaseURL and getFullURL.
"""
__all__ = ["Model"]

import urlparse
import opscore.actor.model as actorModel

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        _theModel = _Model()
    return _theModel

class _Model (actorModel.Model):
    def __init__(self):
        actorModel.Model.__init__(self, "hub")
    
    def getBaseURL(self):
        """Return base URL for image download or None if unknown
        """
        host, hostRootDir = self.httpRoot[0:2]
        if None in (host, hostRootDir):
            return None
        return "http://%s%s" % (host, hostRootDir)

    def getFullURL(self, path):
        """Return full URL for path (relative to base URL), or None if base URL unknown
        """
        baseURL = self.getBaseURL()
        if baseURL == None:
            return
        return urlparse.urljoin(baseURL, path)
