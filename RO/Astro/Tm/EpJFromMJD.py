#!/usr/bin/env python
from RO.Astro import llv

def epJFromMJD (mjd):
    """
    Converts Modified Julian Date to Julian epoch.
    
    Inputs:
    - mjd   Modified Julian Date (JD - 2400000.5)
    
    Returns:
    - epj   Julian epoch.
    
    History:
    2002-08-06 R Owen Just a more memorable name for llv.epj.
    """
    return llv.epj(mjd)
