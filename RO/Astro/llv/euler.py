#!/usr/local/bin/python
import math
import Numeric

def euler (axisAngSet):
    """
    Form a rotation matrix from successive rotations
    about specified Cartesian axes.
    
    Inputs:
    - axisAngSet    a list of axis, angle lists, where:
      - axis is the index of the axis (0 for x, 1 for y, 2 for z)
      - angle is the angle of rotation (rad)
    
    Returns:
    - rMat          the rotation matrix as a 3x3 Numeric.array
     
    Rotation is via the right-hand rule. For example: a positive
    rotation about x is from y to z.
    
    Based on EULER by Pat Wallace.
    
    History:
    P.T.Wallace   Starlink   November 1988
    2002-07-11 ROwen  Extensively rewritten for Python.
    """
    # Initialise result matrix
    netRotMat = Numeric.identity(3)

    # Look at each character of axis string until finished
    for axis, ang in axisAngSet:

        # generate the rotation matrix
        sa = math.sin(ang)
        ca = math.cos(ang)
        if axis == 0:  # x axis
            currRotMat = Numeric.array([
                [  1,   0,   0],
                [  0,  ca,  sa],
                [  0, -sa,  ca],
            ])
    
        elif axis == 1:  # y axis
            currRotMat = Numeric.array([
                [ ca,   0, -sa],
                [  0,   1,   0],
                [ sa,   0,  ca],
            ])
    
        elif axis == 2: # z axis
            currRotMat = Numeric.array([
                [ ca,  sa,   0],
                [-sa,  ca,   0],
                [  0,   0,   1],
            ])

        else:
            raise RuntimeError, "unknown axis %s; must be one of 0, 1, 2" % (axis,)
        
        # Apply the current rotation (currRotMat x netRotMat)
        netRotMat = Numeric.matrixmultiply(currRotMat, netRotMat)

    return netRotMat
    
if __name__ == "__main__":
    print "testing euler"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument for euler
    # - the expected resulting matrix, to at least 5 digits after the decimal point
    testData = (
        (((0, 1), (1, 0), (2, 0)), (
            (   1.00000000000000     ,  0.000000000000000E+000,  0.000000000000000E+000),
            (  0.000000000000000E+000,  0.540302305868140     ,  0.841470984807897     ),
            (  0.000000000000000E+000, -0.841470984807897     ,  0.540302305868140     ),
        )),
        (((0, 0), (1, 1), (2, 0)), (
            (  0.540302305868140     ,  0.000000000000000E+000, -0.841470984807897     ),
            (  0.000000000000000E+000,   1.00000000000000     ,  0.000000000000000E+000),
            (  0.841470984807897     ,  0.000000000000000E+000,  0.540302305868140     ),
        )),
        (((0, 0), (1, 0), (2, 1)), (
            (  0.540302305868140     ,  0.841470984807897     ,  0.000000000000000E+000),
            ( -0.841470984807897     ,  0.540302305868140     ,  0.000000000000000E+000),
            (  0.000000000000000E+000,  0.000000000000000E+000,   1.00000000000000     ),
        )),
        (((0, 1), (1, 1), (2, 1)), (
            (  0.291926581726429     ,  0.837222414029987     ,  0.462425670056630     ),
            ( -0.454648713412841     , -0.303896654864527     ,  0.837222414029987     ),
            (  0.841470984807897     , -0.454648713412841     ,  0.291926581726429     ),
        )),
        (((2, 1), (1, 1), (0, 1)), (
            (  0.291926581726429     ,  0.454648713412841     , -0.841470984807897     ),
            ( -7.207501279569456E-002,  0.887749818317385     ,  0.454648713412841     ),
            (  0.953721166490512     , -7.207501279569462E-002,  0.291926581726429     ),
        )),
        (((1, 1), (2, 1), (0, 1)), (
            (  0.291926581726429     ,  0.841470984807897     , -0.454648713412841     ),
            (  0.462425670056630     ,  0.291926581726429     ,  0.837222414029987     ),
            (  0.837222414029987     , -0.454648713412841     , -0.303896654864527     ),
        )),
        (((0, -1), (1, -1), (0, -1)), (
            (  0.540302305868140     ,  0.708073418273571     ,  0.454648713412841     ),
            (  0.708073418273571     , -9.064711889071747E-002, -0.700296461629782     ),
            ( -0.454648713412841     ,  0.700296461629782     , -0.550344813022578     ),
        )),
    )
    for testInput, expectedOutput in testData:
        actualOutput = euler(testInput)
        if not Numeric.allclose(actualOutput, expectedOutput, atol=1e-15, rtol=1e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
