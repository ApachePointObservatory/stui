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
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
2016-06-01 EM       Changed getBaseURL to get httpHost  and httpPort from preferences
"""
__all__ = ["Model"]

import urllib
import opscore.actor.model as actorModel
import TUI.Models

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
        Prefs = TUI.Models.getModel("tui").prefs
        httpHost=Prefs.getPrefVar("httpHost").getValueStr()
        httpPort=Prefs.getPrefVar("httpPort").getValueStr()
        
        if httpHost.strip() == '':
            httpHost = host 
            #httpHost=Prefs.getPrefVar("httpHost").getDefValueStr()
            
        if httpPort.strip() == '':
            httpPort = Prefs.getPrefVar("httpPort").getDefValueStr() 

        if None in (httpHost, httpPort, hostRootDir):
            return None
             
        baseUrl="http://%s:%s%s" % (httpHost, httpPort, hostRootDir)
        return baseUrl

    def getFullURL(self, path):
        """Return full URL for path (relative to base URL), or None if base URL unknown
        """
        baseURL = self.getBaseURL()
        if baseURL is None:
            return
        return urllib.urljoin(baseURL, path)
