#!/usr/local/bin/python

"""Take a series of NICFPS exposures at different focus positions to estimate best focus.



This script imports the standard NICFPS exposure widget

to allow the user to configure standard exposure options.



To do:

- Fail unless NICFPS is in imaging mode.



History:

2005-04-30 SBeland Copied/enhanced from NICFPS Dither script

2006-02-01 SBeland Modified to use full window mode to try to avoid the persistence

                   seen on the chip in window mode.

"""

import math

import numarray

import Tkinter

import Image

import RO.Wdg

import RO.Constants

import TUI.TCC.TCCModel

import TUI.Inst.ExposeModel

import TUI.Guide.GuideModel

from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg

from TUI.Inst.ExposeInputWdg import ExposeInputWdg

import matplotlib

matplotlib.use("TkAgg")

import pylab

from Tkconstants import *



from matplotlib.axes import Subplot

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from matplotlib.backends.backend_agg import FigureCanvasAgg

from matplotlib.figure import Figure







# constants

InstName = "NICFPS"

DefFocusStart = 0 # start focus position (microns)

DefFocusEnd   = 0 # last focus position (microns)

DefFocusInc = 25  # focus increment (microns)

DefFocusNPos = 6  # number of focus positions

OffsetWaitMS = 2000

HelpURL = "Scripts/BuiltInScripts/NICFPSFocus.html"

starXPos = 512  # initial pixel coordinate of star to measure

starYPos = 512



# global variables

g_expWdg = None

g_plotFitWdg = None

g_moveBestFocus = None

g_resultsLbl = None

search_radius = 50    # search radius in pixels

tccModel = None

nicfpsModel = None

current_nfs = 0





def init(sr):

    """The setup script; run once when the script runner

    window is created.

    """

    global InstName

    global g_expWdg

    global g_startFocusPosWdg

    global g_endFocusPosWdg

    global g_numFocusPosWdg

    global g_plotFitWdg, g_moveBestFocus

    global g_resultsLbl

    global g_starXPosWdg, g_starYPosWdg

    global tccModel, nicfpsModel, current_nfs



    tccModel = TUI.TCC.TCCModel.getModel()

    nicfpsModel = TUI.Inst.NICFPS.NICFPSModel.getModel()



    # get the current secondary focus position

    currFocus = sr.getKeyVar(tccModel.secFocus)

    #currFocus = -100

    DefFocusStart = currFocus - 100

    DefFocusEnd   = currFocus + 100

    DefFocusInc   = (DefFocusEnd - DefFocusStart) / (DefFocusNPos -1)

    micronStr = RO.StringUtil.MuStr + "m"



    row=0

    

    # standard exposure status widget

    expStatusWdg = ExposeStatusWdg(sr.master, InstName)

    expStatusWdg.grid(row=row, column=0, sticky="news")

    row += 1

    

    # standard exposure input widget

    g_expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")

    g_expWdg.numExpWdg.helpText = "# of exposures at each focus position"

    g_expWdg.grid(row=row, column=0, sticky="news")

    row += 1



    g_starXPosWdg = RO.Wdg.IntEntry(

        master = g_expWdg,

        minValue = 1,

        maxValue = 1024,

        defValue = starXPos,

        helpText = "X coordinate of star to measure",

        helpURL = HelpURL,

    )

    g_starYPosWdg = RO.Wdg.IntEntry(

        master = g_expWdg,

        minValue = 1,

        maxValue = 1024,

        defValue = starYPos,

        helpText = "Y coordinate of star to measure",

        helpURL = HelpURL,

    )

    g_expWdg.gridder.gridWdg("Star Pixel Position", g_starXPosWdg, g_starYPosWdg)

    row += 1



    g_startFocusPosWdg = RO.Wdg.IntEntry(

        master = g_expWdg,

        minValue = -2000,

        defValue = DefFocusStart,

        helpText = "First FOCUS position",

        helpURL = HelpURL,

    )

    g_expWdg.gridder.gridWdg("First Focus", g_startFocusPosWdg, micronStr)

    row += 1



    g_endFocusPosWdg = RO.Wdg.IntEntry(

        master = g_expWdg,

        maxValue = 2000,

        defValue = DefFocusEnd,

        helpText = "Last FOCUS position",

        helpURL = HelpURL,

    )

    g_expWdg.gridder.gridWdg("Last Focus", g_endFocusPosWdg, micronStr)

    row += 1



    g_numFocusPosWdg = RO.Wdg.IntEntry(

        master = g_expWdg,

        minValue = 3,

        defValue = DefFocusNPos,

        helpText = "Number of Focus Positions",

        helpURL = HelpURL,

    )

    g_expWdg.gridder.gridWdg("Number of Positions", g_numFocusPosWdg, "")

    row += 1



   # create the move to best focus checkbox

    g_moveBestFocus = RO.Wdg.Checkbutton(

        master = sr.master,

        text = "Move to Best Focus",

        defValue = True,

        relief = "flat",

        helpText = "Move to Best Focus when done",

        helpURL = HelpURL,

    )

    g_moveBestFocus.grid(row=row, column=0)

    row+=1



    # create the plotfwhm checkbox

    g_plotFitWdg = RO.Wdg.Checkbutton(

        master = sr.master,

        text = "Plot FWHM",

        defValue = True,

        relief = "flat",

        helpText = "Plot all FWHM when done",

        helpURL = HelpURL,

    )

    g_plotFitWdg.grid(row=row, column=0)

    row+=1



    g_resultsLbl = RO.Wdg.StrLabel(sr.master, anchor="w", text="")

    g_resultsLbl.grid(row=row, column=0)

    row += 1

   

def run(sr):

    """Take the series of focus exposures.

    """

    # get current NICFPS focal plane geometry from the TCC

    # but first make sure the current instrument

    # is actually NICFPS

    global InstName, OffsetWaitMS

    global g_expWdg

    global tccModel, nicfpsModel, current_nfs

    

    nfocusModel = TUI.Guide.GuideModel.getModel("nfocus")

    expModel = TUI.Inst.ExposeModel.getModel(InstName)



    currInstName = sr.getKeyVar(tccModel.instName)

    if not currInstName.lower().startswith(InstName.lower()):

        raise sr.ScriptError("%s is not the current instrument (%s)!" % (InstName,currInstName))



    # make sure we are in CDS mode for the focus script

    current_nfs = sr.getKeyVar(nicfpsModel.fowlerSamples) 

    yield sr.waitCmd(

        actor = "nicfps",

        cmdStr = "fowler nfs=1"

    )



    # exposure command without startNum and totNum

    # get it now so that it will not change if the user messes

    # with the controls while the script is running

    starXPos     = g_starXPosWdg.getNum()

    starYPos     = g_starYPosWdg.getNum()

    startPos     = g_startFocusPosWdg.getNum()

    endPos       = g_endFocusPosWdg.getNum()

    numPos       = g_numFocusPosWdg.getNum()

    incFocus     = float(endPos - startPos) / float(numPos -1)

    numExp       = g_expWdg.numExpWdg.getNum()

    expCmdPrefix = g_expWdg.getString()



    numExpTaken = 0

    numPosToGo = numPos



    # arrays for holding values as we take exposures

    FocusPos = numarray.zeros(numPos, "Float")

    FWHMval  = numarray.zeros(numPos, "Float")

    coeffs = numarray.zeros(numPos, "Float")

    weight = numarray.ones(numPos,"Float")

    

    for focNum in range(numPos):

        

        # move to new focus position

        focPos = int(startPos + round(focNum*incFocus))

        sr.showMsg("Moving Focus to %d " % focPos)

        yield sr.waitCmd(

            actor = "tcc",

            cmdStr = "set focus=%d" % (focPos),

        )

        yield sr.waitMS(OffsetWaitMS)



         

        # compute # of exposures & format expose command

        totNum = numExpTaken + (numPosToGo * numExp)

        startNum = numExpTaken + 1

        

        expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNum)

        

        # take exposure sequence

        sr.showMsg("Expose at focus position %d microns" % focPos)

        yield sr.waitCmd(

            actor = expModel.actor,

            cmdStr = expCmdStr,

        )



        root = sr.getKeyVar(expModel.files, ind=2)

        prog = sr.getKeyVar(expModel.files, ind=3)

        udir = sr.getKeyVar(expModel.files, ind=4)

        fname= sr.getKeyVar(expModel.files, ind=5)

        filename = "".join((root,prog,udir,fname))

        sr.showMsg("Looking for file: %s" % filename)



        # get the FWHM from the guide camera model

        sr.showMsg("Analyzing %s for FWHM" % filename)

        yield sr.waitCmd(

            actor = "nfocus",

            cmdStr = "centroid file=%s on=%d,%d radius=%d" % (filename,starXPos,starYPos,search_radius),

        )

        

        FWHMval[focNum] = sr.getKeyVar(nfocusModel.star,8)



        FocusPos[focNum] = focPos    #store the focal position for this exposure

        sr.showMsg("Exposure: %d,  Focus: %d,  FWHM:%0.1f" % (focNum,focPos, FWHMval[focNum]))

        # print "********************************************************************"

        # print "Exposure: %d,  Focus: %d,  FWHM:%0.1f" % (focNum,focPos, FWHMval[focNum])

        # print "********************************************************************"



        #decrement counters

        numExpTaken += numExp

        numPosToGo -= 1

        #and loop again...



    #Fit a curve to the data

    coeffs = polyfitw(FocusPos,FWHMval,weight, 2, 0)

    

    # find the best focus position

    finalFocPos = (-1.0*coeffs[1])/(2.0*coeffs[2])

    finalFocQuality = coeffs[0]+coeffs[1]*finalFocPos+coeffs[2]*finalFocPos*finalFocPos

    msg = "Estimated Best Focus Pos: %0.0f microns  (%0.1f pixels)" % (finalFocPos,finalFocQuality)

    g_resultsLbl["text"] = msg

    # print msg

    sr.showMsg("Estimated Best Focus Pos: %0.0f microns  (%0.1f pixels  %0.1f arcsec)" % (finalFocPos,finalFocQuality, finalFocQuality*0.273))





    ######################################################################

    # verify if the "Move to best Focus" has been checked

    movebest = g_moveBestFocus.getBool()

    if movebest:

       # to try to eliminate the backlash in the secondary mirror drive move back 1/2 the

       # distance between the start and end position from the finalFocPos

       focPos = finalFocPos - (endPos - startPos) / 2.0

       sr.showMsg("Moving Focus to %d " % focPos)

       yield sr.waitCmd(

           actor = "tcc",

           cmdStr = "set focus=%d" % (focPos),

       )

       yield sr.waitMS(OffsetWaitMS)



       # move to best position, take another image and measure the final FWHM at that focus position

       sr.showMsg("Moving Focus to %d " % finalFocPos)

       yield sr.waitCmd(

           actor = "tcc",

           cmdStr = "set focus=%d" % (finalFocPos),

       )

       yield sr.waitMS(OffsetWaitMS)



       # compute # of exposures & format expose command

       totNum = numExpTaken + 1

       startNum = numExpTaken + 1

       

       expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNum)

       

       # take exposure sequence

       sr.showMsg("Expose at focus position %d microns" % finalFocPos)

       yield sr.waitCmd(

           actor = expModel.actor,

           cmdStr = expCmdStr,

       )



       root = sr.getKeyVar(expModel.files, ind=2)

       prog = sr.getKeyVar(expModel.files, ind=3)

       udir = sr.getKeyVar(expModel.files, ind=4)

       fname= sr.getKeyVar(expModel.files, ind=5)

       filename = "".join((root,prog,udir,fname))

       sr.showMsg("Looking for file: %s" % filename)



       # get the FWHM from the guide camera model

       sr.showMsg("Analyzing %s for FWHM" % filename)

       yield sr.waitCmd(

           actor = "nfocus",

           cmdStr = "centroid file=%s on=%d,%d radius=%d" % (filename,starXPos,starYPos,search_radius),

       )

       

       finalFWHMval = sr.getKeyVar(nfocusModel.star,8)

       sr.showMsg("Final exposure Focus: %d,  FWHM:%0.1f (%0.1f arcsec)" % (finalFocPos, finalFWHMval, finalFWHMval*0.273))

       g_resultsLbl["text"] = "Final exposure Focus: %d,  FWHM:%0.1f (%0.1f arcsec)" % (finalFocPos, finalFWHMval, finalFWHMval*0.273)

 





    ######################################################################

    # verify if the "Plot FWHM" has been checked

    doplot = g_plotFitWdg.getBool()

    if doplot:



       # generate the data from the 2nd order fit

       x = numarray.arange(min(FocusPos),max(FocusPos),1)

       y = coeffs[0] + coeffs[1]*x + coeffs[2]*(x**2.0)



       # plot the data and the fit

       pylab.plot(FocusPos, FWHMval,'bo',x, y,'-k',linewidth=2)



       # ...and the chosen focus position in green

       print "finalFocPos=",finalFocPos

       print "finalFocQuality=",finalFocQuality

       pylab.plot([finalFocPos],[finalFocQuality],'go')



       # ...and the final focus position in red (if image taken there)

       if movebest:

            print "finalFWHMval=",finalFWHMval

            pylab.plot([finalFocPos],[finalFWHMval],'ro')



       pylab.xlabel('Focus Position (microns)')

       pylab.ylabel('FWHM (pixels)')

       if movebest:

          pylab.title('Best Focus at %0.0f (est.: %0.1f   measured: %0.1f pixels (%0.1f arcsec))' % (finalFocPos,finalFocQuality,finalFWHMval, finalFWHMval*0.273))

       else:

          pylab.title('Best Focus at %0.0f (est.: %0.1f pixels (%0.1f arcsec))' % (finalFocPos,finalFocQuality,finalFocQuality*0.273))

       pylab.grid(True)

       # pylab.draw()

       # we create a png file (only output with pylab) and convert it to gif with PIL, then load it to the canvas

       # this is a little convoluted but it works well (until i figure out how to draw to the canvas directly).

       infile='nicfps_focus.png'

       outfile='nicfps_focus.gif'

       pylab.savefig(infile,dpi=72)

       Image.open(infile).save(outfile)

       # clear the plot so that next time around it is clean

       pylab.clf()



       toplvl = Tkinter.Toplevel()

       toplvl.wm_title("NICFPS Focus Test")

       #print "got toplevel ", toplvl

       photo=Tkinter.PhotoImage(file=outfile)

       #print "got photo ", photo

       canvas=Tkinter.Canvas(toplvl,width=576,height=432)

       #print "got canvas"

       canvas.create_image(576,432,image=photo,anchor=SE)

       #print "got create_image"

       canvas.pack()

       mybutton=Tkinter.Button(toplvl, text="EXIT", command=toplvl.destroy)

       mybutton.pack() 



def end(sr):

    """If telescope moved, restore original boresight position.

    """

    global current_nfs



    yield sr.waitCmd(

        actor = "nicfps",

        cmdStr = "fowler nfs=%d" % current_nfs

    )





import Numeric

import LinearAlgebra



############################################################

def polyfitw(x, y, w, ndegree, return_fit=0):

   """

   Performs a weighted least-squares polynomial fit with optional error estimates.



   Inputs:

      x: 

         The independent variable vector.



      y: 

         The dependent variable vector.  This vector should be the same 

         length as X.



      w: 

         The vector of weights.  This vector should be same length as 

         X and Y.



      ndegree: 

         The degree of polynomial to fit.



   Outputs:

      If return_fit==0 (the default) then polyfitw returns only C, a vector of 

      coefficients of length ndegree+1.

      If return_fit!=0 then polyfitw returns a tuple (c, yfit, yband, sigma, a)

         yfit:  

            The vector of calculated Y's.  Has an error of + or - Yband.



         yband: 

            Error estimate for each point = 1 sigma.



         sigma: 

            The standard deviation in Y units.



         a: 

            Correlation matrix of the coefficients.



   Written by:   George Lawrence, LASP, University of Colorado,

                 December, 1981 in IDL.

                 Weights added, April, 1987,  G. Lawrence

                 Fixed bug with checking number of params, November, 1998, 

                 Mark Rivers.  

                 Python version, May 2002, Mark Rivers

   """

   n = min(len(x), len(y)) # size = smaller of x,y

   m = ndegree + 1         # number of elements in coeff vector

   a = Numeric.zeros((m,m),Numeric.Float)  # least square matrix, weighted matrix

   b = Numeric.zeros(m,Numeric.Float)    # will contain sum w*y*x^j

   z = Numeric.ones(n,Numeric.Float)     # basis vector for constant term



   a[0,0] = Numeric.sum(w)

   b[0] = Numeric.sum(w*y)



   for p in range(1, 2*ndegree+1):     # power loop

      z = z*x   # z is now x^p

      if (p < m):  b[p] = Numeric.sum(w*y*z)   # b is sum w*y*x^j

      sum = Numeric.sum(w*z)

      for j in range(max(0,(p-ndegree)), min(ndegree,p)+1):

         a[j,p-j] = sum



   a = LinearAlgebra.inverse(a)

   c = Numeric.matrixmultiply(b, a)

   if (return_fit == 0):

      return c     # exit if only fit coefficients are wanted



   # compute optional output parameters.

   yfit = Numeric.zeros(n,Numeric.Float)+c[0]   # one-sigma error estimates, init

   for k in range(1, ndegree +1):

      yfit = yfit + c[k]*(x**k)  # sum basis vectors

   var = Numeric.sum((yfit-y)**2 )/(n-m)  # variance estimate, unbiased

   sigma = Numeric.sqrt(var)

   yband = Numeric.zeros(n,Numeric.Float) + a[0,0]

   z = Numeric.ones(n,Numeric.Float)

   for p in range(1,2*ndegree+1):     # compute correlated error estimates on y

      z = z*x      # z is now x^p

      sum = 0.

      for j in range(max(0, (p - ndegree)), min(ndegree, p)+1):

         sum = sum + a[j,p-j]

      yband = yband + sum * z      # add in all the error sources

   yband = yband*var

   yband = Numeric.sqrt(yband)

   return c, yfit, yband, sigma, a




