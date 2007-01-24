#!/usr/bin/env python
"""Handles the bits set in a word such as a status word
"""

def getDescr(bitInfo, intVal):
    """Return information about the bits in an integer
    
    Inputs:
    - bitInfo   a sequence (list or tuple) of sequences:
        - bit number, 0 is the least significant bit
        - info: string describing the associated bit
    - intVal    an integer whose bits are to be described
    
    Returns:
    - infoList  a list of info strings, one for each bit that is set
        in intVal and has a corresponding entry in bitInfo.
        The returned info is in the same order as it appears in bitInfo.
    """
    return [info for bitNum, info in bitInfo if (1<<bitNum) & intVal]

if __name__ == "__main__":
    bitInfo = (
        (2, "Bit 2"),
        (1, "Bit 1"),
        (4, "Bit 4"),
        (3, "Bit 3"),
        (0, "Bit 0"),
    )
    
    print "starting test"
    for i in range(17):
        print i, getDescr(bitInfo, i)