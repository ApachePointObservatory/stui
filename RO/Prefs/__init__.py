"""Application preferences.

Originally I had PrefWdg and PrefVar auto-loaded
but this lead to cylical import errors in PrefWdg
(PrefWdg uses RO.Wdg.Label which uses PrefVar)
"""
#from PrefWdg import *
#from PrefVar import *
__all__ = ["PrefVar", "PrefWdg"]
