#!/usr/local/bin/python
import RO.MathUtil
import RO.SysConst

def angSideAng (side_aa, ang_B, side_cc):
    """
    Solves a spherical triangle for two angles and the side connecting them,
    given the remaining quantities.
    
    Inputs:
    - side_aa   side  aa; range of sides:  [0, 180]
    - ang_B     angle b; range of angles: [0, 360)
    - side_cc   side  cc
    
    Returns a tuple containing:
    - ang_A     angle a
    - side_bb   side  bb
    - ang_C     angle c
    - zero_bb   if true, side bb is zero and angles a, c are undefined
    
    To Do:
    Some test cases fail (for unknown reasons) suggesting the math
    needs a bit of tweaking.
    
    Error Conditions:
    If the inputs are too small to allow computation, raises ValueError

    If side bb is too small, angles a and c cannot be computed;
    then "zero_bb" = true, side_bb = 0.0, ang_A = ang_C = 90.0.
    
    Warnings:
    Allowing angles in the 3rd and 4th quadrants is unusual.
    
    References:
    Selby, Standard Math Tables, crc, 15th ed, 1967, p161 (Spherical Trig.)
    
    History:
    2002-07-22 ROwen  Converted from TCC's sph_AngSideAng 1-6.
    """
    # +
    #  compute angles a and c using Napier's analogies
    # -
    #  compute sine and cosine of b/2, aa/2, and cc/2
    sin_h_B = RO.MathUtil.sind (ang_B * 0.5)
    cos_h_B = RO.MathUtil.cosd (ang_B * 0.5)
    sin_h_aa = RO.MathUtil.sind (side_aa * 0.5)
    cos_h_aa = RO.MathUtil.cosd (side_aa * 0.5)
    sin_h_cc = RO.MathUtil.sind (side_cc * 0.5)
    cos_h_cc = RO.MathUtil.cosd (side_cc * 0.5)

    #  compute sin((aa +/- cc) / 2) and cos((aa +/- cc) / 2)
    sin_h_sum_aacc  = sin_h_aa * cos_h_cc + cos_h_aa * sin_h_cc
    sin_h_diff_aacc = sin_h_aa * cos_h_cc - cos_h_aa * sin_h_cc
    cos_h_sum_aacc  = cos_h_aa * cos_h_cc - sin_h_aa * sin_h_cc
    cos_h_diff_aacc = cos_h_aa * cos_h_cc + sin_h_aa * sin_h_cc

    #  compute numerator and denominator, where tan((a +/- c) / 2) = num/den
    num1 = cos_h_B * cos_h_diff_aacc
    den1 = sin_h_B * cos_h_sum_aacc
    num2 = cos_h_B * sin_h_diff_aacc
    den2 = sin_h_B * sin_h_sum_aacc

    #  if numerator and denominator are too small
    #  to accurately determine angle = atan2 (num, den), give up
    if (((abs (num1) <= RO.SysConst.FAccuracy) and (abs (den1) <= RO.SysConst.FAccuracy))
        or ((abs (num2) <= RO.SysConst.FAccuracy) and (abs (den2) <= RO.SysConst.FAccuracy))):
        return (90.0, 0.0, 90.0, 1)

    #  compute (a +/- c) / 2, and use to compute angles a and c
    h_sum_AC = RO.MathUtil.atan2d (num1, den1)
    h_diff_AC = RO.MathUtil.atan2d (num2, den2)

#   print "sin_h_B, cos_h_B =", sin_h_B, cos_h_B
#   print "sin_h_aa, cos_h_aa =", sin_h_aa, cos_h_aa
#   print "sin_h_cc, cos_h_cc =",sin_h_cc, cos_h_cc
#   print "sin_h_diff_aacc, sin_h_sum_aacc =", sin_h_diff_aacc, sin_h_sum_aacc
#   print "num1, den1, num2, den2 =", num1, den1, num2, den2
#   print "h_sum_AC, h_diff_AC =", h_sum_AC, h_diff_AC

    ang_A = h_sum_AC + h_diff_AC
    ang_C = h_sum_AC - h_diff_AC

    if ang_A < 0.0:
        ang_A = ang_A + 360.0
    if ang_C < 0.0:
        ang_C = ang_C + 360.0

    # +
    #  compute side bb using one of two Napier's analogies
    #  (one is for bb - aa, one for bb + aa)
    # -
    #  preliminaries
    sin_h_A = RO.MathUtil.sind (ang_A * 0.5)
    cos_h_A = RO.MathUtil.cosd (ang_A * 0.5)
    sin_h_sum_BA  = sin_h_B * cos_h_A + cos_h_B * sin_h_A
    sin_h_diff_BA = sin_h_B * cos_h_A - cos_h_B * sin_h_A
    cos_h_sum_BA  = cos_h_B * cos_h_A - sin_h_B * sin_h_A
    cos_h_diff_BA = cos_h_B * cos_h_A + sin_h_B * sin_h_A

    #  numerator and denominator for analogy for bb - aa
    num3 = sin_h_cc * sin_h_diff_BA
    den3 = cos_h_cc * sin_h_sum_BA

    #  numerator and denominator for analogy for bb + aa
    num4 = sin_h_cc * cos_h_diff_BA
    den4 = cos_h_cc * cos_h_sum_BA

    #  compute side bb
    if abs (num3) + abs (den3) > abs (num4) + abs (den4):
        #  use Napier's analogy for bb - aa
        side_bb = 2.0 * RO.MathUtil.atan2d (num3, den3) + side_aa
    else:
        side_bb = 2.0 * RO.MathUtil.atan2d (num4, den4) - side_aa
    side_bb = RO.MathUtil.wrapPos (side_bb)

    return (ang_A, side_bb, ang_C, 0)


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing angSideAng"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (

        # case 1)  a = 180, deg, B = 10, deg, c -> a
        #          correct answers: A = 180, b = a - c, C = B = 10
        # Note: the third and fourth cases fail, though not badly
        # I'm not sure why they do worse than the original fortran sph_AngSideAng
        # clearly the code for this case could be optimized

        ((180, 10, 179.9999999999999), (90.0, 0.0, 90.0, 1)),
        ((180, 10, 179.999999999999), (90.0, 0.0, 90.0, 1)),
        ((180, 10, 179.99999999999), (180.0,  1.0E-011, 10.0, 0)),
        ((180, 10, 179.9999999999), (180.0,  1.0E-010, 10.0, 0)),
        ((180, 10, 179.9999), (180.0,  1.0E-04, 10.0, 0)),
        ((180, 10, 179.99), (180.0,  1.0E-02, 10.0, 0)),

        #  case 2) a = c = 90, B -> 0
        #          correct answers: A = C = 90, b = B

        ((90, 1e-13, 90), (90.0, 0.0, 90.0, 1)),
        ((90, 1e-12, 90), (90.0, 0.0, 90.0, 1)),

        # case 3) a = 180, B -> 0, c is a bit less than a
        #         correct answers: A = 180, b = a - c, C = B

        ((180,     0, 179.999999999999), (90.0, 0.0, 90.0, 1)),
        ((180, 1e-14, 179.999999999999), (90.0, 0.0, 90.0, 1)),
        ((180, 1e-13, 179.999999999999), (90.0, 0.0, 90.0, 1)),

        # case 4) a = 90, c small, B varies
        #         correct answers: A = 180, - B, C = small, b = a + c cos(B)

        ((90,   0, 1e-12), (180.0,  89.9999999999990, 0.0, 0)),
        ((90,  60, 1e-12), (120.0,  89.9999999999995, 8.739675649849232E-013, 0)),
        ((90, 120, 1e-12),  (60.0, 90.0000000000005, 8.704148513061227E-013, 0)),
        ((90, 180, 1e-12),   (0.0, 90.0000000000010, 0.0, 0)),

        # case 5) a = small, c = 90, B varies
        #         correct answers: C = 180, - B, A = small, b = c + a cos(B)

        ((1e-12,   0, 90), (0.0, 89.9999999999990, 180.0,  0)),
        ((1e-12,  60, 90), (8.739675649849232E-013, 89.9999999999995, 120.0,  0)),
        ((1e-12, 120, 90), (8.704148513061227E-013, 90.0000000000005, 60.0, 0)),
        ((1e-12, 180, 90), (0.0, 90.0000000000010, 0.0, 0)),

        # case 6) a = c = small, B varies
        #         correct answers: A = C = ?, b = ?

        ((1e-14, 90, 1e-14), (90.0, 0.0, 90.0, 1)),
        ((1e-13, 45, 1e-13), (90.0, 0.0, 90.0, 1)),
        ((1e-13, 90, 1e-13), (90.0, 0.0, 90.0, 1)),
        ((1e-12,  1, 1e-12), (90.0, 0.0, 90.0, 1)),
        ((1e-12, 30, 1e-12), (90.0, 0.0, 90.0, 1)),
        ((1e-12, 45, 1e-12), (90.0, 0.0, 90.0, 1)),

        # case 7) inputs that might cause side_bb < 0, (but should not)

        ((45, 1, 45), (89.6464421219342, 0.707102293688337, 89.6464421219342, 0)),
        ((45, -1, 45), (270.353557878066, 0.707102293688337, 270.353557878066, 0)),
        ((135, 1, 135), (90.3535578780658, 0.707102293688337, 90.3535578780658, 0)),
        ((135, -1, 135), (269.646442121934, 0.707102293688308, 269.646442121934, 0)),
    )
    for testInput, expectedOutput in testData:
        actualOutput = angSideAng(*testInput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-10):
            print "failed on input:", testInput
            print "expected output:", expectedOutput
            print "actual output:", actualOutput
            print
