#!/usr/bin/env python
"""Play each of the standard sounds for TUI.

Gets the sounds from TUI preferences.

2003-04-28 ROwen    Minimal implementation.
2003-10-30 ROwen    Added msgReceived.
2003-11-24 ROwen    Moved to TUI.Sounds; changed to use sound prefs.
2003-12-03 ROwen    Added exposureBegins, exposureEnds, guidingBegins, guidingEnds. 
2003-12-09 ROwen    Modified to import TUI.Models.TUIModel when it's used; this
                    allows TUI.Sounds to be imported before TUI.Models.TUIModel.
2004-05-18 ROwen    Stopped importing RO.Wdg; it wasn't used.
2005-08-02 ROwen    Moved from Sounds/PlaySounds.py -> PlaySound.py
2006-04-14 ROwen    Added guideModeChanges.
2006-10-24 ROwen    Added logHighlightedText.
2009-07-23 ROwen    Added seriousAlert.
2009-08-11 ROwen    Added support for Play Sounds preference.
2009-09-02 ROwen    Changed seriousAlert to alert(severity).
                    Added support for "Warning Alert" and "Critical Alert" sound cues.
                    Changed _playSound to play nothing if name is None.
2009-09-17 ROwen    Bug fix: played critical alert for warning alert due to key being "warning" instead of "warn".
                    Also changed the sound for invalid keys to Serious Alert from Critical Alert.
"""
import TUI.Models.TUIModel

_Prefs = None
_PlaySoundsPref = None

def _playSound(name):
    if name == None:
        return
    global _Prefs, _PlaySoundsPref
    if _Prefs == None:
        _Prefs = TUI.Models.TUIModel.Model().prefs
        _PlaySoundsPref = _Prefs.getPrefVar("Play Sounds")
    if _PlaySoundsPref.getValue():
        _Prefs.getPrefVar(name).play()

def axisHalt():
    _playSound("Axis Halt")

def axisSlew():
    _playSound("Axis Slew")

def axisTrack():
    _playSound("Axis Track")

def cmdDone():
    _playSound("Command Done")

def cmdFailed():
    _playSound("Command Failed")

def exposureBegins():
    _playSound("Exposure Begins")

def exposureEnds():
    _playSound("Exposure Ends")

def guidingBegins():
    _playSound("Guiding Begins")

def guideModeChanges():
    _playSound("Guide Mode Changes")

def guidingEnds():
    _playSound("Guiding Ends")

def msgReceived():
    _playSound("Message Received")

def noGuideStar():
    _playSound("No Guide Star")

def logHighlightedText():
    _playSound("Log Highlighted Text")

# dictionary of alert severity character: name of associated alert sound
# alert severities are Info, Warn, Serious, Critical
# sevChar is the first letter of the severity cast to lowercase
_AlertSeveritySoundNameDict = dict(
    info = None,
    warn = "Warning Alert",
    serious = "Serious Alert",
    critical = "Critical Alert",
)

def alert(severity):
    """Play an alert sound cue
    
    Inputs:
    - severity: alert severity: one of Info, Warning, Serious, Critical (not case sensitive)
        
    Warning:
    - if the severity is unrecognized then plays the critical alert sound cue.
    """
    soundName = _AlertSeveritySoundNameDict.get(severity.lower(), "Serious Alert")
    _playSound(soundName)
