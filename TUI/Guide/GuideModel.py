#!/usr/bin/env python
"""Model for guide cameras.

Warning: the config stuff will probably be modified.

2005-01-28 ROwen    preliminary; has all existing keywords, but there will be more
                    and "star" will probably change to include ellipticity.
2005-02-23 ROwen    added expTime and thresh.
2005-03-14 ROwen    overhauled for new keywords
2005-03-30 ROwen    overhauled again for new keywords files and star keywords.
2005-04-11 ROwen    Renamed to GuideModel from GCamModel (because an actor is named gcam).
2005-04-13 ROwen    Bug fix: was refreshing all keywords. Was refreshing nonexistent keyword time.
2005-04-20 ROwen    Removed expTime; get from FITS header instead.
                    Added default exposure time and bin factor to camInfo.
                    Tweaked description of fs...Thresh keywords, since they now
                    also apply to centroid.
2005-06-08 ROwen    Added noStarsFound and starQuality.
2005-06-10 ROwen    Added playing of sound cues.
                    Renamed noStarsFound to noGuideStar.
                    Modified starQuality to accept additional values.
2005-06-17 ROwen    Guide start/stop sounds only play if the state has changed.
                    Thus one can quietly ask for guide status.
2005-06-23 ROwen    Modified to not play NoGuideStar sound unless the keyword is "genuine".
                    This is mostly paranoia since it's not auto-refreshed anyway.
2005-06-27 ROwen    Changed default bin factor from 3 to 1 for the DIS and Echelle slitviewers.
2005-07-08 ROwen    Modified for http download:
                    - Changed ftpLogWdg to downloadWdg.
                    - Removed imageRoot.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2005-10-24 ROwen    Lowered default min exposure time to 0 sec.
2006-03-28 ROwen    Added "nfocus" actor.
                    Added guideMode keyword.
                    Bug fix: fsActRadMult was listening for fsDefRadMult.
2006-04-14 ROwen    Added locGuideMode.
                    Play a sound when locGuideMode changes while guiding.
2006-05-18 ROwen    Added measOffset and actOffset.
                    Added support for predicted position for star="g"...
                    Added support for NaN in star values.
2006-05-22 ROwen    Changed the default exposure time from 10 to 5 seconds
                    by request of the obs specs.
2006-03-03 ROwen    Added imSize to gcamInfo. This may be a temporary hack,
                    since it would be better to get the info from the hub.
2007-01-29 ROwen    Bug fix: guiding sound cues were not always played because
                    "starting" and perhaps "stopping" states were not always sent.
2007-06-05 ROwen    Added "sfocus" actor.
2008-02-04 ROwen    Added locGuideStateSummary.
2008-03-14 ROwen    Added tcam actor.
2008-03-17 ROwen    Bug fix: tcam was not listed as a slitviewer.
2008-03-25 ROwen    PR 744: changed default nfocus exposure time to 6 seconds.
2008-04-01 ROwen    Bug fix: _updLocGuideStateSummary mis-handled a mode of None.
2008-04-22 ROwen    Added expState.
2008-04-23 ROwen    Get expState from the cache (finally) but null out the times.
                    Modified expState so durations can be None or 0 for unknown (was just 0).
2008-07-24 ROwen    Fixed CR 851: changed tcam default bin factor to 2 (from 1).
2009-03-27 ROwen    Modified to use new keyVar callbacks.
2009-07-17 ROwen    Modified to use opscore dictionary and keyvars.
"""
__all__ = ['getModel']

import opscore.protocols.keys as protoKeys
import opscore.protocols.types as protoTypes
import opscore.actor.keyvar as actorKeyvar
import opscore.actor.model as actorModel
import RO.CnvUtil
import RO.KeyVariable
import TUI.TUIModel
import TUI.PlaySound

class _GCamInfo:
    """Exposure information for a camera
    
    Inputs:
    - min/maxExpTime: minimum and maximum exposure time (sec)
    """
    def __init__(self,
        imSize,
        minExpTime = 0.0,
        maxExpTime = 3600,
        defBinFac = 1,
        defExpTime = 5,
    ):
        self.imSize = imSize
        self.minExpTime = float(minExpTime)
        self.maxExpTime = float(maxExpTime)
        self.defBinFac = defBinFac
        self.defExpTime = defExpTime

# dictionary of guide camera information
# keys are gcam actor name (and so must be lowercase)
_GCamInfoDict = {
    "gcam": _GCamInfo(
        imSize = (1024, 1024),
        defBinFac = 2,
    ),
    "ecam": _GCamInfo(
        imSize = (512, 512),
    ),
}

# cache of guide camera models; each entry is guide camera actor: model
_modelDict = {}

def Model(actor):
    global _modelDict
    model = _modelDict.get(actor)
    if not model:
        model = _Model(actor)
        _modelDict[actor] = model
    return model

class _Model (actorModel.Model):
    def __init__(self, actor):
        self.actor = actor
        self._isGuiding = None

        self.gcamInfo = _GCamInfoDict[self.actor]
        
        self.tuiModel = TUI.TUIModel.Model()
        
        actorModel.Model.__init__(self, actor)
 
        # synthetic keywords
        self.locGuideMode = actorKeyvar.KeyVar(
            self.actor,
            protoKeys.Key("locGuideMode", protoTypes.String(),
                help="""like guideMode, but restricted to one of:
field, boresight, manual, "" or None
and lowercase is guaranteed""",
                doCache = False,
            ),
        )

        self.locGuideStateSummary = actorKeyvar.KeyVar(
            self.actor,
            protoKeys.Key("locGuideStateSummary", protoTypes.String(),
                help = """Summary of state of guide actor; one of: on, off, starting, stopping, manual
    where manual means guide state = on and guide mode = manual
    """,
                doCache = False,
            ),
        )

        self.ftpSaveToPref = self.tuiModel.prefs.getPrefVar("Save To")
        downloadTL = self.tuiModel.tlSet.getToplevel("TUI.Downloads")
        self.downloadWdg = downloadTL and downloadTL.getWdg()
       
        self.expState.addCallback(self._expStateCallback)
        self.guideMode.addCallback(self._guideModeCallback)
        self.guideState.addCallback(self._guideStateCallback)
    
    def _updLocGuideStateSummary(self):
        """Compute new local guide mode summary"""
        guideState = self.guideState[0]
        gsCurr = self.guideState.isCurrent
        if guideState == None:
            return
        if guideState.lower() != "on":
            self.locGuideStateSummary.set((guideState,), isCurrent = gsCurr)
            return
        
        guideMode = self.locGuideMode[0]
        gmCurr = self.locGuideMode.isCurrent
        if guideMode == "manual":
            self.locGuideStateSummary.set((guideMode,), isCurrent = gsCurr and gmCurr)
        else:
            self.locGuideStateSummary.set((guideState,), isCurrent = gsCurr)
    
    def _guideModeCallback(self, keyVar):
        """Set locGuideMode and play "Guide Mode Changed" as appropriate.
        """
        guideMode = keyVar[0]
        if not guideMode:
            self.locGuideMode.set((None,), isCurrent = keyVar.isCurrent)
            return
            
        gmLower = guideMode.lower()
        if gmLower not in ("boresight", "field", "manual", None):
            return

        if gmLower and keyVar.isCurrent:
            guideState  = self.guideState[0]
            gsIsCurrent = self.guideState.isCurrent
            locGuideMode = self.locGuideMode[0]
            lgmIsCurrent = self.locGuideMode.isCurrent
            if guideState and gsIsCurrent and \
                locGuideMode and lgmIsCurrent and \
                (gmLower != locGuideMode) and \
                (guideState.lower() == "on"):
                TUI.PlaySound.guideModeChanges()

        self.locGuideMode.set((gmLower,), keyVar.isCurrent)
    
        self._updLocGuideStateSummary()
        
    def _expStateCallback(self, keyVar):
        """Set the durations to None (unknown) if data is from the cache"""
        if keyVar.isGenuine:
            return
        modValues = list(keyVar.valueList)
        modValues[2] = None
        modValues[3] = None
        keyVar.valueList = tuple(modValues)
    
    def _guideStateCallback(self, keyVar):
        if not keyVar.isCurrent:
            if not self.tuiModel.dispatcher.connection.isConnected():
                self._isGuiding = None
            return
        
        gsLower = keyVar[0].lower()

        if gsLower in ("starting", "on"):
            if self._isGuiding != True:
                TUI.PlaySound.guidingBegins()
            self._isGuiding = True
        elif gsLower == "stopping":
            if self._isGuiding != False:
                TUI.PlaySound.guidingEnds()
            self._isGuiding = False
    
        self._updLocGuideStateSummary()

def modelIter():
    for actor in _GCamInfoDict.iterkeys():
        yield Model(actor)


if __name__ == "__main__":
#    getModel("ecam")
    getModel("gcam")
