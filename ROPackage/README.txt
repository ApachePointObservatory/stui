Various utilities written, adapted or borrowed by Russell Owen

Prerequisites:
- Python 2.3 with Tkinter
- numpy
- pyfits (for RO.DS9 only)

Note: version 2.1 is the first version to use numpy
instead of numarray and Numeric.

Installation:

The usual technique works:
% python setup.py install

Or if you don't have sufficient permissions, try this:
% python setup.py build
% sudo python setup.py install

Notes:
- Written with cross-platform portability in mind (with one known exception, see next item). It has been written on MacOS X and has been tested on some flavors of unix and on Windows.
- Written in pure python (at least for now). I may add compiled extensions at some point.
- This code is provided "as is". Much of the code is quite well tested and is used daily, but some of it is not.
- I cannot provide much technical support, but am always happy to receive bug reports and would be interested to learn of your enhancements.

License:
All code is released under the GNU General Public License <http://www.gnu.org/copyleft/gpl.html> unless otherwise noted (see the individual
code modules for such notes). One notable exception is the Astro package, which is based on an extensive body of work by Pat Wallace and as such has a license that requires payment for commercial use.

Russell Owen
Astronomy Dept
University of Washington
PO Box 351580
Seattle, WA 98195-1580
rowen@u.washington.edu
