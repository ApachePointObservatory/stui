##########################################################
#  Tcl/Tk program for SDSS Telescope position monitor
#  Originally by Dennis Nicklaus nicklaus@fnal.gov    Feb. 1998
#

###########################################################
# Initialization

set missing_color slateGray
set neutral_color gray

# if a bit has this value, then that means the value is:
set BAD_POLARITY 0;			# bad
set INTERMEDIATE_POLARITY -1;		# unknown
set GOOD_POLARITY 1;			# good
set IGNORE_POLARITY 2;			# good, and !IGNORE is good too

###########################################################
# Make a couple buttons to do neat things.
###########################################################

proc set_update_rate {{parent ""}} {
   if [winfo exists .set_rate] { destroy .set_rate }
   
   toplevel .set_rate -class transient
   wm title .set_rate "Set Update Rate"
   
   if {$parent != ""} {
      set x [expr int([winfo rootx $parent]+[winfo width $parent]/2)]
      set y [expr int([winfo rooty $parent]+[winfo height $parent]/2)]
      wm geometry .set_rate +$x+$y
   }
   #
   # Header
   #
   pack [frame .set_rate.top] .set_rate.top -expand 1 -fill x
   
   label .set_rate.top.label -text "Update Interval(s)"
   frame .set_rate.top.fill
   button .set_rate.top.ok -text accept \
       -command "if {\$update_rate == 0} {incr update_rate}
		 schedule readMCPValues  {} \$update_rate
		 schedule graphicEngineMcp {} \$update_rate
	  	 destroy .set_rate"
   button .set_rate.top.cancel -text cancel -command "destroy .set_rate"
   
   pack .set_rate.top.ok .set_rate.top.cancel .set_rate.top.label \
       -side left
   pack .set_rate.top.fill -before .set_rate.top.label \
       -side left  -expand 1 -fill x
   #
   # Scale
   #
   global readMCPValuesDelay update_rate
   set update_rate [expr 1e-3*$readMCPValuesDelay]

   set len 12;				# length of scale in cm
   scale .set_rate.scale -from 0 -to 50 \
       -length ${len}c -orient horizontal \
       -tickinterval 10 -sliderlength [expr 0.25*$len]c \
       -variable update_rate -command ""
   pack .set_rate.scale
}
   
###############################################################################
#
# Here's the proc to load (or reload) an interlock specification, as given
# in interlocks.tcl
#
proc read_interlock_logic {{file interlocks.tcl}} {
   foreach symb [list \
		     analog_watch_list \
		     bicolor_status_list \
		     big_button_status_args \
		     derived_big_list \
		     keydisplays \
		     topdogs \
		     latchdisplays \
		     instchange_status_list \
		    ] {
      global $symb
      if [info exists $symb] {
	 if [info exists ${symb}(.window)] {
	    set win [set ${symb}(.window)];# save the window
	 }

	 unset $symb

	 if [info exists win] {
	    set ${symb}(.window) $win
	    unset win
	 }
      }
   }

   uplevel #0 [list source $file]
}

proc reload_interlock_logic {{win ""}} {
   global interlock_logic_file

   set file [prompt_user "Interlock Logic" "File: " $interlock_logic_file $win]

   if {$file == ""} {
      return "";
   }
   set interlock_logic_file $file
      
   if [file exists $interlock_logic_file] {
      read_interlock_logic $interlock_logic_file
   } else {
      dialog "Interlock Logic" "File $interlock_logic_file doesn't exist"
   }
}

proc read_tpm_dump {{win ""}} {
   global tpm_dump_file

   if ![info exists tpm_dump_file] {
      set tpm_dump_file ""
   }
   
   set tpm_dump_file \
       [prompt_user "TPM Dump File" "Dump File: " $tpm_dump_file $win]

   if {$tpm_dump_file == ""} {
      return "";
   }

   if [catch { startInterlocks -file $tpm_dump_file } msg] {
      dialog "Bad TPM Dump file" $msg $win
   }
}

###########################################################
# Set up a derived parameter.  We are given:
# 	newvar: the new parameter name to create
#	derived_from_name: The parameter whose value drives this one
#	comparison_list: simple logical expression, when appended
#		to the value of derived_from_name gives the
#		expression which sets the new value.
#		For example, {< 99}.
#       conversion_function:  A function to convert "derived_from_name" 
#  		into the units that are compared with here. (typically to convert
#		into engineering units from raw D/A counts.
#		Enter a 0 if no conversion is required.
# We add to a global list of all these derived parameters so that
# they may be derived when new parameter values are read in.
# We also create the new parameter name in the global arrays.
# This function is run at setup time during reading of the logic
# interlocks description file.
###########################################################
proc MORE_THINGS { newvar derived_from_name comparison_list function_or_0 \
		       {descrip ""}} {
   global derived_big_list interlockDescriptions
   
   lappend derived_big_list [list $newvar [expand_abbrev $derived_from_name] \
				 $function_or_0 \
				 [concat {$source_value} $comparison_list] ]

   if {$descrip != ""} {
      set interlockDescriptions($newvar) $descrip
   }
}
###########################################################
# Run each of the specials we've set up through MORE_THINGS.
# This function is the processing partner to the setup
# which is done in MORE_THINGS.  This is called each
# time new parameter values are read in to update the
# derived values.
# Works off the global list that was setup by all the calls
# to MORE_THINGS.
###########################################################
proc Special_Derivations { } {
   global derived_big_list
   global BAD_POLARITY
   global GOOD_POLARITY
   global mcpData
   
   foreach aupair $derived_big_list {
      set target [lindex $aupair 0]
      set source [lindex $aupair 1]
      if [info exists mcpData($source)] {
	 set source_value $mcpData($source)
      } else {
	 global $source
	 if [info exists $source] {
	    set source_value [set $source]
	 } else {
	    error "Value for Special_Derivations $source doesn't exist"
	 }
      }
      set convert_function [lindex $aupair 2]
      if {$convert_function != 0} {
	 set source_value [$convert_function $source_value]
      }
      
      if [lindex $aupair 3] {
	 set value $GOOD_POLARITY
      } else {
	 set value $BAD_POLARITY
      }
      set mcpData($target) $value
   }
}

###########################################################
# Procedure to read the latest values 
###########################################################

proc readMCPValues {{file ""}} {
   global mcpData mcpDerivedData
   global GOOD_POLARITY BAD_POLARITY

   if {[info commands mcpIsOpen] == ""} {
      error "Cannot open the MCP's UDP socket"
   }

   if ![mcpIsOpen] {
      mcpOpen
   }

   if [catch {set values [mcpReadPacket -nocheck -timeout 0.1]} msg] {
      echo "Error reading MCP packet: $msg"
      return -code error -errorinfo $msg
   }

   #
   # Write file if so desired
   #
   if {$file != ""} {
      set fd [open $file w];
      puts $fd $values
      close $fd
   }
   #
   # Set data array, and clear derived values
   #
   array set mcpData $values
   if [info exists mcpDerivedData] {
      unset mcpDerivedData;		# array of cached derived values
   }

   PostReadProcessing
}

###########################################################
# Extra processing to compute derived values after the Read.
###########################################################
proc PostReadProcessing {  } {
  global mcpData

#  A few specially-made status bits derived  from other quantities.
   Special_Derivations

#  Even more special things -- converting to actual units.
   global altpos1 azpos1 rotpos1
   global cw1pos cw2pos cw3pos cw4pos

   set mcpData(azcomputed:val) [az2marcs $mcpData(azpos1:val) 2]
   set mcpData(altcomputed:val) [az2marcs $mcpData(altpos1:val) 3]
   set mcpData(rotcomputed:val) [az2marcs $mcpData(rotpos1:val) 1]

   loop i 1 5 {
      set mcpData(cw${i}pos_in:val) \
	  [format "%.3f" [expr $mcpData(cw${i}pos:val) / (2048*0.7802)]]
      set mcpData(cw${i}pos_volts:val) \
	  [format "%.3f" [expr $mcpData(cw${i}pos:val) / 2048.0]]
   }

   # convert to engineering units the analog values which we are watching.
   convert_heathens
}

###########################################################
# A function to convert from counts that we get for 
# alt, az, and rotator positions to degrees (& milliarcseconds).
# If the "type" argument, type=1 means rot.  type=2 means AZ, type=3 means ALT
# RETURNS a formatted string showing position in deg, min, arcs, and
# milliarcseconds.

proc az2marcs { counts type} {
   #
   # These numbers come from the MCP, e.g.
   #   echo [expr 3600*1e3/[lindex [mcpPut tel1 axis.status] 0]]
   # for Azimuth
   #
   if {$type == 1} {			# Rotator
      set milliarcsecond_per_count 21.315785266649378
   } elseif {$type == 2} {		# Azimuth
      set milliarcsecond_per_count 14.01671040629539
   } else {				# Altitude
      set milliarcsecond_per_count 14.00914485839475
   }
   
   if { $counts < 0 } {
      set sign "-"
      set counts [expr 0 - $counts]
   } else {
      set sign "+"
   }
   
   set deg [expr ($counts*$milliarcsecond_per_count)/(60*60*1000)]
   set ideg [expr int($deg)]
   
   set min [expr 60*($deg - int($deg))]
   set imin [expr int($min)]
   
   set sec [expr 60*($min - int($min))]

   if {[format %05.2f $sec] >= 60.0} {
      set sec [expr $sec - 60.0]
      incr imin 1
      if {$imin >= 60} {
	 incr imin -60
	 incr ideg
      }
   } elseif {$sec < -60.0} {
      set sec [expr $sec + 60.0]
      incr imin -1
      if {$imin < 0} {
	 incr imin 60
	 incr ideg -1
      }
   } 

   return [format "%s%03d:%02d:%05.2f" $sign $ideg $imin $sec]
}

###########################################################
# WATCHSLOPES is typically invoked from the logic setup file.
# It gives us the name of each "analog" field we are to watch, along
# with the conversion constants needed to turn the reading into engineering units.
#
# The expected set of $args here is a set of lists. Each of the sub
# lists contains parameter name, then either 1 or 2 more arguments.
# If 2 more arguments are present, they are interpreted as
# slope (m)  and intercept (b) to convert to
# engineering units by applying an mX+b transformation.
# If 1 more argument is present, it is interpreted as a function name,
# which takes one 
# So, we have three frames, side by side, equal numbers of rows in each.
# Frame .f.l has the label.
# Frame .f.v has the raw (unconverted) value (from the A/D input)
# Frame .f.convert has the converted value
###########################################################

proc WATCHSLOPES { args } {
   global analog_watch_list
   
   if [info exists analog_watch_list] {
      return
   }

   set analog_watch_list [expand_abbrev_list $args]
}

###########################################################
# convert_heathens steps through the same list of arguments
# that was passed to WATCHSLOPES and then saved as a global variable.
# In  WATCHSLOPES we set a Tk label attached to a  -textvariable global.
# Here we update the value of that textvariable to get the new converted
# value displayed.
# See WATCHSLOPES for description of the format and meaning of analog_watch_list.
###########################################################

proc convert_heathens {  } {
   global mcpData analog_watch_list

   foreach paramset $analog_watch_list {
	set param [lindex $paramset 0]
  	if {[info exists mcpData($param)] } {
		set temp $mcpData($param)
	} else {
		set temp 0
	}

	set type [llength $paramset]
	if { $type == 3 } {
#		Two additional items after parameter name are interpreted as
#		slope and intercept for linear transformation
		set mval  [lindex $paramset 1]
		set bval  [lindex $paramset 2]
		if [regexp {:val$} $param] {
		   set nparam $param
		} else {
		   set nparam "$param:val"
		}
		set mcpData($nparam) \
		    [format "%.3f" [expr $temp * $mval + $bval]]
	} else {
#		Single extra item is interpreted as a Tcl function name to call
#		which will return the converted value.
		if { $type == 2 } {
			set function  [lindex $paramset 1]
			set mcpData($param:val) [format "%.3f" \
							[$function $temp]]
		}
	}
   }
}
