"""
! OffMag is used when computing offsets from pairs of positions,
! which is done to compute rotator angle and also to correct drift scan
! rate for refraction.
!   2nd position = 1st position + offset of size sys__OffMag on the sky
!   (when drift scanning, offset is along the direction of motion)
! There are several ways to look at accuracy:
! - if sys__OffMag is too large, systematic errors are introduced
!   by certain transformations (not including rotation).
!   The only test of this I've found so far is
!   tsph:[.test]NullSphCC  for appgeo<->apptopo conversions
!   with altitudes near -90 (i.e. very unrealistic).
! - if sys__OffMg is too small, accuracy of angle determination suffers.
!   I believe the optimal value is about 1e-5 radians (0.0006 deg),
!   because the system has 15 digits of accuracy, and determining angle
!   is basically two subtractions -- nearby points before transformation
!   compared to nearby points after. NullAxeCC tests seem to bear this out;
!   0.01 deg results in 1/10th the angle error of 0.1 deg
!   and 0.001 deg results in 1/10th the angle error of 0.01 deg,
!   but 0.0001 deg is much worse.
"""
OffMag = 0.001