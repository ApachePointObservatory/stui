Various utilities written, adapted or borrowed by Russell Owen

Prerequisites:
- Python (2.3 or later) with Tkinter
- numpy
- pyfits (for RO.DS9 only)

Note: RO version 2.1 is the first version to use numpy instead of numarray and Numeric.

Installation:

The usual technique works:
% python setup.py install

Or if you don't have sufficient permissions, try this:
% python setup.py build
% sudo python setup.py install

Notes:
- Written with cross-platform portability in mind. It has been written on
   MacOS X and has been tested on some flavors of unix and on Windows.
- The code is presently pure python, though that may not always be so.
- This code is provided "as is". Much of the code is quite well tested
  and is used daily, but some is not.
- I cannot provide much technical support but am always happy to receive
  bug reports and patches.

License:
All code is released under the GNU General Public License
<http://www.gnu.org/copyleft/gpl.html> unless otherwise noted (see the
individual code modules for such notes). One notable exception is RO.Astro,
which contains some algorithms developed by Patrik Wallace and requires
payment for commercial use.

Russell Owen
Astronomy Dept
University of Washington
PO Box 351580
Seattle, WA 98195-1580
rowen@u.washington.edu
