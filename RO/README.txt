"""Various utilities written, adapted or borrowed by Russell Owen

Installation:
This package is written in pure python. To install, either:
- move RO to the standard location for libraries (.../lib/site-packages)
- put RO on your PYTHONPATH

Various components of this package require two other packages:
- Numeric (also called NumPy). In particular the Astro package makes heavy use of Numeric.
- Tkinter.

Caveats:
- This code requires Python 2.2.1 or later. It has been tested most extensively with Python 2.3.
- This code is written with cross-platform portability in mind (with one known exception, see next item). It has been written on MacOS X and has been tested on some flavors of unix. I have done no testing on any flavor of Windows.
- RO.Comm.TkSocket and classes that depend on it are not compatible with Windows, because it uses file events. I hope to fix this eventually.
- This code is being used for a major project of my own and one that is still under construction. As such it will change over time.
- Some code is not well tested.
- This code is provided "as is".
- I cannot provide technical support, but am always happy to receive bug reports and would also be interested to learn of your enhancements.

License:
All code is released under the GNU General Public License <http://www.gnu.org/copyleft/gpl.html> unless otherwise noted (see the individual
code modules for such notes). One notable exception is the Astro package, which is based on an extensive body of work by Pat Wallace and as such has a license that requires payment for commercial use.


Russell Owen
Astronomy Dept
University of Washington
PO Box 351580
Seattle, WA 98195-1580
owen@astro.washington.edu
"""
