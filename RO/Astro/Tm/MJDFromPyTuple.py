#!/usr/local/bin/python
import math
import RO.PhysConst

def mjdFromPyTuple(timeTuple):
	"""Converts a python time tuple to Modified Julian Date.
	Only the first six elements of the time tuple are used:
	- year: 4 digits
	- month: (1-12; 1=Jan)
	- day: day of month (1-31)
	- hour: hours (0-23)
	- minute: minutes (0-59)
	- sec: seconds (0-59.999...)
	Seconds may be floating point; all other entries must be integers
	or the floating point equivalent (nothing significant after the decimal point).
	"""
	year, month, day, hour, minute, sec = timeTuple[0:6]
	
	# I'm not sure where this algorithm came from
	# an alternate one is widely available on the web
	jd = (367.0 * year) \
		- math.floor(7.0 * (year + math.floor((month + 9.0) / 12.0)) / 4.0) \
		- math.floor(3.0 * (math.floor ((year + (month - 9.0) / 7.0) / 100.0) + 1.0) / 4.0) \
		+ math.floor(275.0 * month / 9.0) \
		+ day \
		+ 1721028.5
	
	return (jd - RO.PhysConst.JDMinusMJD) + (((((sec / 60.0) + minute) / 60.0) + hour) / 24.0)


if __name__ == "__main__":
	import RO.MathUtil
	print "testing mjdFromPyTuple"
	# dataList = tuples of year, month, Julian date, where
	# - JD is at noon on the specified year and month
	# - month is a number between 1 (Jan) and 12 (Dec)
	testData = (
		(1997,	1, 2450450.0),
		(1998,	1, 2450815.0),
		(1999,	1, 2451180.0),
		(2000,	1, 2451545.0),
		(1997,	2, 2450481.0),
		(1998,	2, 2450846.0),
		(1999,	2, 2451211.0),
		(2000,	2, 2451576.0),
		(1997,	3, 2450509.0),
		(1998,	3, 2450874.0),
		(1999,	3, 2451239.0),
		(2000,	3, 2451605.0),
		(1997,	4, 2450540.0),
		(1998,	4, 2450905.0),
		(1999,	4, 2451270.0),
		(2000,	4, 2451636.0),
		(1997,	5, 2450570.0),
		(1998,	5, 2450935.0),
		(1999,	5, 2451300.0),
		(2000,	5, 2451666.0),
		(1997,	6, 2450601.0),
		(1998,	6, 2450966.0),
		(1999,	6, 2451331.0),
		(2000,	6, 2451697.0),
		(1997,	7, 2450631.0),
		(1998,	7, 2450996.0),
		(1999,	7, 2451361.0),
		(2000,	7, 2451727.0),
		(1997,	8, 2450662.0),
		(1998,	8, 2451027.0),
		(1999,	8, 2451392.0),
		(2000,	8, 2451758.0),
		(1997,	9, 2450693.0),
		(1998,	9, 2451058.0),
		(1999,	9, 2451423.0),
		(2000,	9, 2451789.0),
		(1997, 10, 2450723.0),
		(1998, 10, 2451088.0),
		(1999, 10, 2451453.0),
		(2000, 10, 2451819.0),
		(1997, 11, 2450754.0),
		(1998, 11, 2451119.0),
		(1999, 11, 2451484.0),
		(2000, 11, 2451850.0),
		(1997, 12, 2450784.0),
		(1998, 12, 2451149.0),
		(1999, 12, 2451514.0),
		(2000, 12, 2451880.0),
	)
	for year, month, jd in testData:
		testInput = (year, month, 1, 12, 0, 0)
		expectedOutput = jd - RO.PhysConst.JDMinusMJD
		actualOutput = mjdFromPyTuple(testInput)
		if 0 != RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1e-15):
			print "failed on input:", testInput
			print "expected output:", expectedOutput
			print "actual output  :", actualOutput
