#!/usr/bin/env python
from RO.Astro import llv

def mjdFromEpJ (epj):
    """
    Converts Julian epoch to Modified Julian Date.
    
    Inputs:
    - epj   Julian epoch
    
    Returns:
    - mjd   Modified Julian Date (JD - 2400000.5).
    
    History:
    2002-08-06 R Owen Just a more memorable name for llv.epj2d.
    """
    return llv.epj2d(epj)
