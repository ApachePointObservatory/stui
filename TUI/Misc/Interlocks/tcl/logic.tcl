##########################################################
#  Tcl/Tk program for SDSS Telescope Interlocks monitor
#  Originally written by Dennis Nicklaus nicklaus@fnal.gov    Feb. 1998
#
#  WHAT IT DOES:
# Draws very simple "logic diagrams" showing the interconnections of the bits
# This only shows 1-level-deep diagrams --- that is, it draws
# a simple AND or OR representation showing the one resulting bit,
# and all the bits which go into that one gate.
# 
# The tree of connections is set up by reading a file which defines them
# through a series of statements that just happen to also be tcl code. (defined below)
#
# A little rectangle represents each bit, with the color of the rectangle
# representing the status of the bit (red=bad, green=good, white = it is
# a virtual bit). "virtual bit" means that the value is formed by an
# intermediate result. Suppose we have [AND a b c "[OR d e]" ]
# The result of OR-ing 'd' and 'e' goes into the AND gate, but we don't
# have any one named, physical bit for the OR result, so this OR result
# becomes a virtual bit.
# Any bit (including especially virtual bits) which can be further 
# decomposed into a combination of other bits is "hot", meaning
# you can click on it, and the display changes to show the logic which
# goes into making that new bit.  As mentioned before, hot virtual
# bits have their rectangle shown in the color white. Hot, named, physical
# bits have a white outline on them to make them noticable.
#
# You can think of it as traversing a logic diagram tree, one level at a time.
# To go down the tree, you click on a hot bit. If you want to go back up
# the tree, you click on the result bit (at the top) and that takes you
# back up one level showing what that result bit fed into. (This is
# implemented as a simple stack, so there is NO concept of "fan-out" from
# any lower level bit at all.)
#
# The syntax of the definition file filled with statements as follows:
# <statement> :== [ RESULT <bitname> <logicombo> ]
# <bitname> :== any legal non-reserved tcl word, but hopefully the name 
#               of one of the bit fields read by sockmon.tcl's ReadNames 
# <logicombo> :== [ <logicop> {<bitname> | <nested_logicombo>} ]
# <logicop> :== AND | OR | NOT
# <nested_logicombo> :== " <logicombo> "  
# In the above definitions, the square brackets [] are literally
# required in the definition file.
# '|' is used here as indicating "or" (one or the other tokens are allowed)
# tokens are delimited by <token>.
# Items inside curly braces {} may be repeated any number of times.
# Line breaks matter! Thus if a definition statement takes multiple
# lines, you must escape the end-of-line with a backslash.
# Also, when you nest <logicombo>s, you must include the nested <logicombo> 
# inside double quotes due to the way tcl works.
# Here is an example:
# RESULT topcombo [AND a b c "[OR d e]" ]
# The equivalent C code is {topcombo = a && b && c && (d || e);}
#
# The implementation in TCL is actually quite simple: I just made
# up procedures named RESULT, AND, OR, NOT
#
#	WHAT ELSE IT DOES
# Besides these Logic diagrams, it the code here also maintains a
# canvas of those bits deemed "important", meaning we want to watch them
# more closely.  These will typically include the "RESULT" bits from the
# logic description input file. But there can also be other bits,
# grouped together in bunches also.  
# On this window, you can mouse on a interlock light to display info or
# a logic diagram about that bit, or you can mouse on a "word" (title
# of a interlock category) to show the names and status of all the 
# bits in that category at one time in the logic diagram window.

if ![info exists readMCPValuesDelay] {
   set readMCPValuesDelay 5000
}

proc startInterlocks {{toplevel ""} {update 0} {geom ""}} {
   global readMCPValuesDelay

   global exit_interlocks;		# exit when this is set
   global mcpData
   global readMCPValuesDelay;		# update interval, in ms

   if [info exists mcpData] {
      set cr_lava_lamp $mcpData(cr_lava_lamp)
      unset mcpData
   }
   array set mcpData [mcpGetFields]
   array set mcpData [list cr_lava_lamp $cr_lava_lamp]

   key_interlocks $toplevel $geom;	# actually pack window into toplevel

   set readMCPValuesDelay [expr int(1000*$update)]
      
   schedule readMCPValues {} $update
   after 1000;			# give the reader a chance
   schedule graphicEngineMcp {} $update
}

###############################################################################
#
# Read a Yanny param file of TPMABDATAs, as dumped from the tpm
#
proc read_TPMABDATA {file n} {
   global mcpData tpm_dmp_bits TPMABDATA_time
   
   if ![file readable $file] {
      error "I cannot read $file"
   }

   set ch [param2Chain $file ""]
   set nel [chainSize $ch]

   if {$n < 0 || $n > $nel - 1} {
      chainDestroy $ch genericDel
      error "Please specify a number in the range 0:[expr $nel - 1]"
   }

   set ab [chainElementGetByPos $ch $n]
   eval set TPMABDATA_time [exprGet $ab.time]

   set sch [schemaGetFromType TPMABDATA]

   foreach name [array names tpm_dmp_bits] {
      set val $tpm_dmp_bits($name)
      set el [lindex $val 0]
      set bit [lindex $val 1]

      if [keylget sch $el foo] {
	 set mcpData($name) [expr ([exprGet $ab.$el] & (1<<$bit)) ? 1 : 0]
      }
   }

   handleDel $ab; chainDestroy $ch genericDel
}

###############################################################################

###########################################################
# BIGAND describes one of the high-level summaries to watch.
# We make a button for the group , labelled with "newname."
# The arguments: newname is just a convenient descriptive name.
#   The remaining "args" has the names of all  the status bits that will be 
#   and-ed together to determine the color of the newname button.
#
# the name argument may not include whitespace.
#
# BIGOR is similar, except that its values are ORd together.
#
###########################################################
proc BIGAND {_arr name args} {
   upvar $_arr arr
   global bigand_arrays
   
   set bigand_arrays($_arr) 1
   set arr($name) [expand_abbrev_list $args]
}

proc BIGOR {_arr name args} {
   upvar $_arr arr
   global bigor_arrays
   
   set bigor_arrays($_arr) 1
   set arr($name) [expand_abbrev_list $args]
}

###########################################################
# HARDWARE_STATUS is called with the list of 
# on-off status bits. Here, being on or off isn't necessarily
# good or bad, it just tells which state a particular switch
# or brake or whatever is in.
# We create the necessary frames to display this info here also.
#
# Each list element of "args" is a list of 3 items.
# the first thing is just a name of the switch or whatever,
# We create a label using it.
# the second is a list of variable names. These are really just
# descriptive labels which are used for the colored-in buttons.
# The third and final thing on the sublist is a list of parameter
# status bit names that correspond (one-to-one) with the variable
# names in the 2nd item.
# So we make a set of buttons. The user sees them with the 
# provided varnames (2nd item), but each is attached to the
# corresponding status parameter name (3rd item)
#
# We set a variable, $_big_button_status_args,
# which contains ordered pairs of the button identifier 
# and the corresponding parameter name
###########################################################

proc HARDWARE_STATUS {_big_button_status_args args} {
   upvar $_big_button_status_args big_button_status_args
   global mcpData topdogs

   set args [expand_abbrev_list $args]
   set big_button_status_args $args
   #
   # Check parameter's validity
   #
   foreach one $args {
      set varnames [lindex $one 2]
      
      set counter -1
      foreach caption [lindex $one 1]  {
	 set thisvar_here [lindex $varnames [incr counter]] 
	 
	 if {![info exists mcpData($thisvar_here)] &&
	     ![info exists topdogs($thisvar_here)]} {
	    puts "ERROR, unknown parameter name in HARDWARE_STATUS: $thisvar_here"
	 }
	 VALUE_IS_USED $thisvar_here
      }
   }
}

###########################################################
# SPECIAL_BICOLOR is sort of a special case variation of HARDWARE_STATUS
# for when we have sensors for both on and off
#
# Each list element of "args" is a list of 3 items.
# the first thing is just a name of the switch or whatever, we create a
# label using it. The second is a pair of names for two mutually
# exclusive interlocks (e.g. brake on/ brake off); the third is the
# "official" interlock bit names.
###########################################################

proc SPECIAL_BICOLOR {_bicolor_status_list args} {
   upvar $_bicolor_status_list bicolor_status_list
   global mcpData

   if [info exist bicolor_status_list] {
      unset bicolor_status_list
   }

   foreach one [expand_abbrev_list $args] {
      set thisn [lindex $one 0]
      set varnames [lindex $one 2]
      
      foreach int $varnames {
	 if ![info exists mcpData($int)] {
	    error "Unknown name in SPECIAL_BICOLOR $thisn: $int"
	 }
      }
      
      lappend bicolor_status_list [list $thisn [lindex $one 1] $varnames]
   }
}

###############################################################################
#
# Save the names of fields that we are using, so as to be able to list
# the ones that we aren't
#
proc VALUE_IS_USED {name} {
   global value_is_used
   set value_is_used([expand_abbrev $name]) 1
}

###########################################################
# RESULT for parsing the interconnection definition file
# It stores the logic for any particular "topname" bit on
# a global array called topdogs.
#
# Fields may be specified with or without the leading "il__i1__il0__" strings;
# the topname need not exist in the MCP packets.
#
###########################################################

proc RESULT {topname biglist {descrip ""} {revision ""}} {
   global mcpData named_node pseudo_result topdogs
   
   if [expand_abbrev $topname name] {
      set pseudo_result($name) 1
   }

   set topdogs($name) [expand_abbrev_list $biglist]

   if ![info exists mcpData($name)] {
      set named_node($name) 1
   }

   if {$descrip != ""} {
      global interlockDescriptions
      set interlockDescriptions($name) $descrip
   }

   if {$revision != ""} {
      global interlockRevisions
      regsub -nocase {^rev(ision)? *: *} $revision "" revision
      set interlockRevisions($name) $revision
   }
}

#
# <alias> has the same logic as <real> (declared via e.g. RESULT <real> ...)
#
proc EQUIV {alias real {descrip ""}} {
   global mcpData named_node pseudo_result topdogs
   
   if [info exists pseudo_result($real)] {
      set pseudo_result($alias) $pseudo_result($real)
   }

   set topdogs($alias) $topdogs($real)

   if ![info exists mcpData($alias)] {
      set named_node($alias) 1
   }

   if {$descrip != ""} {
      global interlockDescriptions
      set interlockDescriptions($alias) $descrip
   }
}

#
# Return an expanded interlock field name.
#
# If _fullname is provided, set it to the expanded value and 
# return 1 if the name was indeed an abbreviation, and 0 otherwise
#
proc expand_abbrev {abbrev_name {_fullname ""}} {
   if {$_fullname != ""} {
      upvar $_fullname fullname
   }
   global mcpData

   if [regexp {^[0-9]*$} $abbrev_name] {# an integer
      set fullname $abbrev_name
      set status 0
   } elseif [info exists mcpData($abbrev_name)] {# the full name of a field
      set fullname $abbrev_name
      set status 0
   } else {
      if 1 {
	 set fullname $abbrev_name
	 set status 1
      } else {
	 echo "guessing at $abbrev_name's full name"
	 set guess [array names mcpData *__$abbrev_name]
	 switch [llength $guess] {
	    0 {				# neither an abbreviation nor a name
	       set fullname $abbrev_name
	       set status 1
	    }
	    1 {				# a unique abbreviation
	       set fullname $guess
	       set status 0
	    }
	    "default" {
	       error "$abbrev_name is not a unique abbreviation: $guess"
	    }
	 }
      }
   }
   if {$_fullname == ""} {
      return $fullname
   } else {
      return $status
   }      
}

#
# Given a list passed to e.g. RESULT, expand all abbreviations
#
proc expand_abbrev_list {abbrev_list} {
   set list ""

   foreach el $abbrev_list {
      if ![regexp { } $el] {		# no spaces; no more work
	 expand_abbrev $el full
	 lappend list $full
      } else {
	 lappend list [expand_abbrev_list $el]
      }
   }

   return $list
}

###########################################################
# Logic operations legal in the definition file.
###########################################################
proc AND {args} {
  set return [list AND $args]
}
proc NOT {args} {
  set return [list NOT $args]
}
proc OR {args} {
  set return [list OR $args]
}
###########################################################
# Implement a simple stack
###########################################################
proc Push { stack value } {
   upvar $stack S
   if ![info exists S(top)] {
      set S(top) 0
   }
   
   set S($S(top)) $value
   incr S(top)
}
proc Pop { stack } {
	upvar $stack S
	if ![info exists S(top)] {
		return {}
	}
	if {$S(top) == 0} {
		return {}
	} else {
		incr S(top) -1
		set x $S($S(top))
		unset S($S(top))
		return $x
	}
}

#
# Remove leading ??__ parts of interlock names
#
proc fix_name {name} {
#   regsub -all {([a-z][a-z0-9]+__)+} $name "" name

   return $name
}

###########################################################
# This is the primary diagram drawing function. Does the art.
###########################################################

proc Logic {{drawname ""}} {
  global canvas
  global BAD_POLARITY IGNORE_POLARITY GOOD_POLARITY colors
  global anondogs topdogs global logicstack logic_current_top

   if ![info exists canvas] {
      return
   }

   if {$drawname == "" && [info exists logic_current_top]} {
      set drawname $logic_current_top
   }

  set symbcolor black
  set notecolor white
  set linecolor white

   # Note that every item I draw on the canvas gets a "deleteme" tag
   # to make for easy erasing here.
   $canvas delete deleteme

  if [info exists topdogs($drawname)] {
     #   Remember what we are going to pop out to.
     if [info exists logic_current_top] {
	if {$drawname != $logic_current_top} {
	   Push logicstack $logic_current_top
	}
     }
     set logic_current_top $drawname
    
     #   Rip apart the logic combination list. Combine is the logic op.
     set combine [lindex $topdogs($drawname) 0]
     set pieces [lindex $topdogs($drawname) 1]
     
     #   Even if we are a PLC defined bit, follow
     # the logic in case any interlock bits are being ignored
     #
     set fillcolor [polarityToColor [param_status $combine $pieces]]
     #
     # Write name on canvas
     #
     set nsubcomp [llength $pieces]

     set x_gutter 5;			# x-spacing between subcomponents
     set y_gutter 10
     set rwide 10;			# size of subcomponents symbols
     set rhigh 10
     
     set symbsize 60;			# size of logical operator
     set symby 60;			# operator position
     set symbx [expr 30 + ($nsubcomp*($rwide + $x_gutter))/2]
     if {$symbx < $symbsize/2} {
	set symbx [expr $symbsize/2 + $y_gutter]
     }

     set label $drawname
     if [regexp {^NEST([0-9]+)(:([^:]+) :)?$} $drawname foo goo hoo label] {
	if [regexp {^(AND|OR|NOT) } $label] {
	   set label ""
	}
     }

     if {$label != ""} {
	incr symby 20
     }

     set startx 10;			# starting position for subcomponents
     set starty [expr $symby + $symbsize + 40]
     set textx 10
     set texty [expr $starty + $rhigh*2]
     
     $canvas configure -height [expr $starty + \
				    $nsubcomp*($rhigh + $y_gutter) + 20]

     if {$label != ""} {
	$canvas create text $symbx [expr $symby - $symbsize/2 - $rhigh*2] \
	    -fill $notecolor -tag deleteme -text $label -anchor w
     }

     #    Draw box for the result bit
     set glyph \
	 [$canvas create rect \
	      [expr $symbx - $rwide/2] [expr $symby - $symbsize/2 - $rhigh] \
	      [expr $symbx + $rwide/2] [expr $symby - $symbsize/2] \
	      -tag [list $drawname deleteme popoffsweetheart] -fill $fillcolor]

     $canvas bind $glyph <Button-1> "Logic_pop"
     if [regexp {^NEST} $drawname] {
	set drawname $label
     }
     $canvas bind $glyph <Button-3> "Describe $drawname {}"
     $canvas bind $glyph <Control-Button-1> "show_root_cause $drawname"

#   #######################################################
#   Now loop through each constituent bit and draw a box for each
#   #######################################################
    foreach val $pieces {
#     We check for "virtual bits" by looking for those identifiers which
#     are lists rather than simple bit names, because it'll be a list
#     something like [AND bitA bitB] instead of simply "bitC"
      unset glyph

      set val_name $val
      if {[info exists topdogs($val)] &&
	  ![regexp {^(true|false)$} $topdogs($val)]} {
	 set val $topdogs($val)
      }

      if {[llength $val] > 1} {
	 set op [lindex $val 0]
	 set elements [join [lreplace $val 0 0]]
	 set fillcolor [polarityToColor [param_status $op $elements]]
	 
	 set glyph [$canvas create rect $startx $starty \
			[expr $startx + $rwide] [expr $starty +$rhigh] \
			-fill $fillcolor \
			-tag [list NEST $val deleteme logicinfo_tag]]
	 $canvas bind $glyph <Button-1> "Logic_info2 \"NEST:$val_name : $val\""
	 $canvas bind $glyph <Control-Button-1> "show_root_cause $val_name"
	 
	 $canvas bind $glyph <Button-3> "bell"
      } else {
	 set fillcolor [Getfillcolor $val]
	 if {[info exists topdogs($val)] && [llength $topdogs($val)] > 1} {
	    set glyph [$canvas create rect $startx $starty \
			   [expr $startx + $rwide] [expr $starty +$rhigh] \
			   -fill $fillcolor \
			   -tag [list $val deleteme logicinfo_tag]]
	 } else {
	    # Just a plain bit; a leaf node. Draw as a circle if its value
	    # comes straight from the MCP, as a diamond if we calculate
	    # it from e.g. motor currents that the MCP gives us
	    if [from_udp_packet $val] {
	       set glyph [$canvas create oval $startx $starty \
			      [expr $startx + $rwide] [expr $starty +$rhigh]\
			      -fill $fillcolor \
			      -tag [list $val deleteme logicinfo_tag]]
	    } else {
	       set glyph \
		   [$canvas create poly \
			[expr $startx - 1] [expr $starty + $rhigh/2] \
			[expr $startx + $rwide/2] [expr $starty - 1] \
			[expr $startx + $rwide + 1] [expr $starty + $rhigh/2] \
			[expr $startx + $rwide/2] [expr $starty + $rhigh + 1] \
			-fill $fillcolor \
			-tag [list $val deleteme logicinfo_tag]]
	    }
	 }
	 $canvas bind $glyph <Button-1> "Logic_info2 $val"
	 $canvas bind $glyph <Control-Button-1> "show_root_cause $val"
	 
	 $canvas bind $glyph <Button-2> "toggle_mcpIgnoreValue $val"
	 $canvas bind $glyph <Button-3> "Describe $val {}"
      }
#      Draw the line connecting the box to the logic symbol.
      $canvas create line [expr $startx + $rwide/2] \
	  $starty $symbx $symby -fill $linecolor  -tag deleteme
      incr startx [expr $rwide + $x_gutter]
      $canvas create text $textx $texty -text [fix_name $val_name] \
	  -anchor w -fill $notecolor -tag deleteme

      incr texty [expr $rhigh + $y_gutter]
    }
     #
     # Finally Draw figure and name of logic operation; we do this last
     # so that it lies on top of the lines joining it to its children
     #
    switch -exact $combine {
      "AND" {
	$canvas create arc \
	    [expr $symbx - $symbsize/2] [expr $symby - $symbsize/2] \
	    [expr $symbx + $symbsize/2] [expr $symby + $symbsize/2] \
	    -start 0 -extent 180 -style pieslice -fill $symbcolor \
	    -tag deleteme
	$canvas create text $symbx $symby -text AND -anchor s \
	    -fill $notecolor -tag deleteme
      }
      "OR" {
	$canvas create poly \
	    $symbx [expr $symby - $symbsize/2] \
	    [expr $symbx - $symbsize/2] [expr $symby + $symbsize/2] \
	    [expr $symbx + $symbsize/2] [expr $symby + $symbsize/2] \
	    -fill $symbcolor -tag deleteme
	$canvas create text $symbx $symby -text OR -fill $notecolor \
	    -tag deleteme
      }
      "NOT" {
	$canvas create oval \
	    [expr $symbx - $symbsize/2.5] [expr $symby - $symbsize/2.5] \
	    [expr $symbx + $symbsize/2.5] [expr $symby + $symbsize/2.5] \
	    -fill $symbcolor -tag deleteme
	$canvas create text $symbx $symby -text NOT -fill $notecolor \
	    -tag deleteme
      }
    }
  } else {
     global bigand_arrays bigor_arrays

     set found_name 0
     foreach arr \
	 [concat [array names bigand_arrays] [array names bigor_arrays]] {
	global $arr
	if [info exists ${arr}($drawname)] {
	   Logic_nameshow2 $drawname
	   set found_name 1
	   break
	}
     }
     if !$found_name {
	puts "I don't know how to draw a logic diagram for $drawname"
     }
  }
}

###########################################################
# Redraw the currently shown logic diagram, without 
# changing the stack or anything.
###########################################################
proc Logic_redraw { } {
  global logic_current_top
  global global_nameshowing


  if [info exists logic_current_top] {
	set remember $logic_current_top
	unset logic_current_top
	Logic $remember
  } else {
	if [info exists global_nameshowing] {
	   Logic_nameshow2 $global_nameshowing
	}
  }
}

###########################################################
# Move up to the previous level. (pop the value off the 
# stack and redraw it if there was anything on the stack)
###########################################################
proc Logic_pop {} {
   global logicstack logic_current_top

   set a [Pop logicstack]
   if {[llength $a] > 0} {
      
      unset logic_current_top
      Logic $a
   }
}

###########################################################
# Procedure which takes an IL status bit and draws its
# logic decomposition. If it isn't decomposed, just 
# display its name and status.

proc Logic_info2 { thisguy { w 0 } {raise 0} {win ""} {forget_history 0}} {

  global state
  global topdogs
  global logicstack logic_current_top
  global nestcount

  if $forget_history {			# don't pop up above the
					# requested interlock when clicked on
     if [info exists logicstack] {
	unset logicstack
     }
     if [info exists logic_current_top] {
	unset logic_current_top
     }
  }

#  If it is a "virtual bit", it will have NEST as the first one of its tags,
#  followed by the logic function.  Otherwise, real bits simply have the 
#  bit name as the first one of their tags.
#  When we see a virtual bit, we create an entry for it in the "topdogs"
#  array named NESTnn just before calling the drawing function on it.
#  Can you spot the leakage? (Answer: I never unset the topdogs(NESTnn),
#  despite the fact that it is totally useless after we pop it back off the stack.)

  set need_canvas 1;			# do we need a logic display canvas?
  if [regexp {^NEST(:([^:]+) :)? +(.*)} $thisguy foo goo name rest] {
     if ![info exists nestcount] { set nestcount 0 }
     set thisguy [format "NEST%d:$name :" [incr nestcount]]
     set topdogs($thisguy) $rest
   } else {
      #     Pop up a name and value notification window for real bits. 
      #     who don't otherwise have a nested construct.
      if {![info exists topdogs($thisguy)] ||
	  [llength $topdogs($thisguy)] == 1} {
	 Describe $thisguy $win
	 set need_canvas 0
      }
   }
  if $need_canvas {
     set thisguy [expand_abbrev $thisguy]
     if [info exists topdogs($thisguy)] {
	make_canvas $raise
	
	Logic $thisguy
     }
  }
}

###########################################################
# Simple procedure to stick up a little note telling
# the full name and status of an individual status bit.
#
# We don't use a popup for speed, and so that the user doesn't
# have to decide to put it every time it's needed
###########################################################

proc Describe { thisguy {win ""} {extra ""}} {
   global interlockDescriptions interlockRevisions statusDescriptions
   global mcpData mcpIgnoreValue BAD_POLARITY tpm_dmp_bits

   if ![info exists mcpData($thisguy)] {
      set status "Unavailable from MCP"

      if {[info exists mcpIgnoreValue($thisguy)] &&
	  $mcpIgnoreValue($thisguy)} {
	 append status "
   Value ignored; will never trip interlock display"
      }

      global $thisguy
      if [info exists $thisguy] {
	 if {[set $thisguy] == $BAD_POLARITY} {
	    set status "Bad"
	 } else {
	    set status "OK"
	 }
	 append status " ([set $thisguy])"
      }
   } else {
      if [info exists statusDescriptions($thisguy)] {
	 set status [lindex $statusDescriptions($thisguy) $mcpData($thisguy)]
      } else {
	 if {$mcpData($thisguy) == $BAD_POLARITY} {
	    set status "Bad"
	 } else {
	    set status "OK"
	 }
      }
      
      if {[info exists mcpIgnoreValue($thisguy)] &&
	  $mcpIgnoreValue($thisguy)} {
	 append status "
   Value ignored; will never trip interlock display"
      }
      append status " ($mcpData($thisguy))"
   }

   if ![info exists tpm_dmp_bits($thisguy)] {
      set bit "??"
   } else {
      set bit $tpm_dmp_bits($thisguy)
      regsub {^tpm_AB} $bit {} bit
   }

   set descrip ""
   if [info exists $thisguy] {
      append descrip "(global variable)\n";
   }
   if [info exists interlockDescriptions($thisguy)] {
      append descrip $interlockDescriptions($thisguy)
   } elseif [info exists interlockDescriptions([fix_name $thisguy])] {
      append descrip $interlockDescriptions([fix_name $thisguy])
   } else {
      if ![from_udp_packet $thisguy] {
	 append descrip "(derived from analog inputs)\n"
      }
      append descrip "(unknown)"
   }
   if {$extra != ""} {
      append descrip "\n$extra"
   }

   set revision ""
   if [info exists interlockRevisions($thisguy)] {
      append revision "\nDrawing revision: $interlockRevisions($thisguy)"
   }
   #
   # pop up the help window
   #
   give_help $thisguy \
"Status: $status   Bit: $bit

$descrip
$revision
"
}

###########################################################
# Logic_nameshow2 is called when you already know the name
# of the BIGAND grouping instead of having to figure it out from the
# mouse position (as was done in a former implementation).
# In the logic diagram window, this draws a box for each of the bits
# for that group along with its name.
###########################################################
proc Logic_nameshow2 { thisleader {raise 0}} {
  global canvas topdogs
  global global_nameshowing
  global logicstack logic_current_top

  set notecolor white
  set rwide 10
  set rhigh 10

  set global_nameshowing $thisleader
  if [info exists logicstack(top)] {
     unset logicstack(top)
  }
  set logic_current_top $thisleader
  
  make_canvas $raise
   
  set starty 20
  $canvas delete deleteme
  $canvas create text 80 $starty -fill $notecolor -tag deleteme \
      -text $thisleader -anchor w
   set starty [expr $starty + 10]

   global bigand_arrays bigor_arrays
   foreach arr \
      [concat [array names bigand_arrays] [array names bigor_arrays]] {
      global $arr
      if [info exists ${arr}($thisleader)] {
	 set names [set ${arr}($thisleader)]
	 break
      }
   }
   
   foreach tname $names {
      set startx 10	 
      #
      #   Even if we are a PLC defined bit, follow
      # the logic in case any interlock bits are being ignored
      #
      if [info exists topdogs($tname)] {
	 set combine [lindex $topdogs($tname) 0]
	 set pieces [lindex $topdogs($tname) 1]

	 set fillcolor [polarityToColor [param_status $combine $pieces]]
      } else {
	 set fillcolor [Getfillcolor $tname]
      }
      set glyph [$canvas create rect $startx $starty \
		     [expr $startx + $rwide] [expr $starty +$rhigh] \
		     -fill $fillcolor \
		     -tag [list $tname deleteme logicinfo_tag]]
      $canvas bind $glyph <Button-1> "Logic_info2 $tname"
      $canvas bind $glyph <Control-Button-1> "show_root_cause $tname"
      $canvas bind $glyph <Button-3> "Describe $tname {}"

      set startx [expr $startx + $rwide + 2]
      $canvas create text \
		     $startx [expr $starty-$rhigh/3] -fill $notecolor \
		     -tag deleteme -text [fix_name $tname] -anchor nw
  
      incr starty [expr $rhigh + 10]
   }
  incr starty $rhigh
}

###############################################################################
#
# Tell me about the root cause of this item's unhappiness
#
proc show_root_cause {args} {
   global bigand_arrays bigor_arrays colors env root_causes

   if [info exists root_causes] {
      unset root_causes
   }

   if {[lavaLampStatus] != 1} {
      set root_causes(lavaLamp) "special"
   }
   #
   # Is args something like `rotator' that corresponds to a list of items?
   #
   if {[llength $args] == 1} {
      set name $args
      
      foreach arr [array names bigand_arrays] {
	 global $arr
	 if [info exists ${arr}($args)] {
	    set args [list AND [set ${arr}($args)]]
	    break
	 }
      }
      foreach arr [array names bigor_arrays] {
	 global $arr
	 if [info exists ${arr}($args)] {
	    set args [list OR [set ${arr}($args)]]
	    break
	 }
      }
   } else {
      set name ""
   }

   param_status [lindex $args 0] [lindex $args 1] 1
   #
   # OK, we know the root cause of any problems. Time to popup a window
   #
   if {[info commands winfo] != "" && ![winfo exists .mcp_root_causes]} {
      toplevel .mcp_root_causes
      wm title .mcp_root_causes "Root Causes of Problems"
      
      frame .mcp_root_causes.top

      pack [label .mcp_root_causes.top.label]
      pack .mcp_root_causes.top -expand 1 -fill x -pady 0
      #
      #
      # Buttons at bottom
      #
      frame .mcp_root_causes.bottom

      pack [button .mcp_root_causes.bottom.update -text "update" \
		-relief groove] -side left
      
      pack .mcp_root_causes.bottom -fill x
   }

   if [winfo exists .mcp_root_causes.vars] {
      destroy .mcp_root_causes.vars
   }
   wm deiconify .mcp_root_causes; raise .mcp_root_causes
   #
   # Manage update button
   #
   .mcp_root_causes.bottom.update configure -command "show_root_cause $name"
   #
   # List of items causing problems
   #
   frame .mcp_root_causes.vars

   set label "Root Causes of Problems"
   if {$name != ""} {
      append label " with $name"
   }
   .mcp_root_causes.top.label configure -text $label

   if ![info exists root_causes] {
      pack [label .mcp_root_causes.vars.text \
		-text "You don't have any problems"]
   } else {
      foreach el [lsort [array names root_causes]] {
	 if [regexp {^(spare_s1_c2|e_stop_byp_sw|s._c._bypass_sw)$} $el] {
	    continue;
	 }

	 frame .mcp_root_causes.vars._$el

	 if [info exists topdogs($el)] {
	    set bitmap square.bit
	 } else {
	    if [from_udp_packet $el] {
	       set bitmap circle.bit
	    } else {
	       set bitmap diamond.bit
	    }
	 }

	 label .mcp_root_causes.vars._$el.glyph \
	     -bitmap @$env(INTERLOCKS_DIR)/etc/$bitmap \
	     -fg [Getfillcolor $el] -bd 0
	 bind .mcp_root_causes.vars._$el.glyph <Button-1> "Logic_info2 $el"
	 bind .mcp_root_causes.vars._$el.glyph <Button-2> \
	     "toggle_mcpIgnoreValue $el;
	     .mcp_root_causes.vars._$el.glyph configure -fg \[Getfillcolor $el\]"
	 bind .mcp_root_causes.vars._$el.glyph <Button-3> "Logic_info2 $el"

	 label .mcp_root_causes.vars._$el.val -text $el
	 
	 pack .mcp_root_causes.vars._$el.glyph \
	     .mcp_root_causes.vars._$el.val \
	     -side left -fill y -anchor w
	 pack .mcp_root_causes.vars._$el -expand 1 -fill x
      }
   }
   
   pack .mcp_root_causes.vars -before .mcp_root_causes.bottom -expand 1 -fill x
}

###########################################################
#
# Decide which color a bit should be
# The argument is a parameter NAME
#
# If $desired is 0 or 1, set an element in root_causes to the
# name of the bit that prevents this routine from returning $desired
#
proc param_status1 {name {desired -1}} {
   global mcpData mcpDerivedData mcpIgnoreValue pseudo_result root_causes
   global BAD_POLARITY GOOD_POLARITY IGNORE_POLARITY
   global topdogs

   set verbose 1

   if {[info exists mcpIgnoreValue($name)] && $mcpIgnoreValue($name)} {
      return $IGNORE_POLARITY
   }

   if {![info exists topdogs($name)] && [info exists mcpData($name)]} {
      if {$desired >= 0 && $mcpData($name) != $desired} {
	 set root_causes($name) "mcpData"
      }
      
      return $mcpData($name)
   }
   
   if {[info exists pseudo_result($name)] || [info exists topdogs($name)]} {
      if ![info exists mcpDerivedData(name)] {
	 set op [lindex $topdogs($name) 0]
	 set pieces [lindex $topdogs($name) 1]
	 
	 set mcpDerivedData($name) [param_status $op $pieces $desired]
      }
      
      return $mcpDerivedData($name)
   }

   global $name

   if ![info exists $name] {
      if $verbose {
	 echo "param_status1: Requested field hasn't been defined: $name"
      }
      if {$desired >= 0} {
	 set root_causes($name) "undefined"
      }

      return $GOOD_POLARITY;
   }

   if {$desired >= 0 && [set name] != $desired} {
      set root_causes($name) "global"
   }

   return [set $name]
}

#
# Evaluate the expression "$op $what"; stop as soon as the result is known
# (unless we are after root_causes)
#
# If $desired is 0 or 1, set an element in root_causes to the
# name of the bit that prevents this routine from returning $desired
#
# If _ignored is passed, it's the name of a variable which should
# be set to the number of ignored bits in this op + what
#
proc param_status {op what {desired -1} {_ignored ""}} {
   global BAD_POLARITY IGNORE_POLARITY GOOD_POLARITY UNKNOWN_POLARITY
   global root_causes

   if {$_ignored != ""} {
      upvar $_ignored ignored;		# were any bits ignored?
   }
   if ![info exists ignored] {
      set ignored 0
   }

   if {$desired < 0 && $_ignored == ""} {
      set short_circuit 1
   } else {
      set short_circuit 0
   }

   if {[llength $what] == 0} {
      set nodeStatus [param_status1 $op $desired]
      if {$nodeStatus == $IGNORE_POLARITY} {
         incr ignored
      }
   } else {
      if {$desired == -1} {
	 ;				# OK, don't check anything
      } elseif {$op == "NOT"} {
	 set desired [expr $desired ? 0 : 1]
      } elseif {($desired == 0 && $op == "AND") ||
		($desired == 1 && $op == "OR")} {
	 #
	 # Oh dear. We have an AND that should return 0 (only
	 # a problem if _all_ the inputs are 1) or an OR that should
	 # return 1 (only a problem if _all_ the inputs are 0)
	 #
	 # So first find out what the node's status is, and then
	 # decide if we have to check whether each component matches
	 # our desires
	 #
	 set status [param_status $op $what -1 ignored]
	 if {$status == $desired || $ignored} {	# no need to check
	    return $status
	 }
      }
      
      set nodeStatus -1
      foreach val $what {
	 set status [param_status \
			 [lindex $val 0] [join [lreplace $val 0 0]] \
			 $desired ignored]
	 if {$status == $IGNORE_POLARITY} {
	    incr ignored
	 }

	 if {$nodeStatus < 0} {
	    set nodeStatus $status
	 } else {
	    switch -exact $op {
	       "AND" {
		  if {$nodeStatus == $IGNORE_POLARITY} {
		     if {$status == $BAD_POLARITY} {
			set nodeStatus $BAD_POLARITY
		     }
		  } elseif {$status == $IGNORE_POLARITY} {
		     if {$nodeStatus == $GOOD_POLARITY} {
			set nodeStatus $IGNORE_POLARITY
		     }
		  } else {
		     set nodeStatus [expr $nodeStatus && $status]
		  }
	       }
	       "OR" {
		  if {$nodeStatus == $IGNORE_POLARITY} {
		     if {$status == $GOOD_POLARITY} {
			set nodeStatus $GOOD_POLARITY
		     }
		  } elseif {$status == $IGNORE_POLARITY} {
		     if {$nodeStatus == $BAD_POLARITY} {
			set nodeStatus $IGNORE_POLARITY
		     }
		  } else {
		     set nodeStatus [expr $nodeStatus || $status]
		  }
	       }
	    }	
	 }
	 
	 if $short_circuit {
	    if {$op == "AND" && $nodeStatus == $BAD_POLARITY} {
	       break
	    } elseif {$op == "OR" && $nodeStatus == $GOOD_POLARITY} {
	       break
	    }
	 }
      }
   }

   if {$op == "NOT"} {
      switch -- $nodeStatus [list \
	 $BAD_POLARITY { set nodeStatus $GOOD_POLARITY } \
	 $GOOD_POLARITY { set nodeStatus $BAD_POLARITY } \
	 $IGNORE_POLARITY { set nodeStatus $IGNORE_POLARITY } \
      ]
   }
   
   return $nodeStatus
}

proc evaluate_logic {anybody} {
   global mcpData mcpDerivedData mcpIgnoreValue pseudo_result IGNORE_POLARITY

   set verbose 0
   
   if {[info exists mcpIgnoreValue($anybody)] && $mcpIgnoreValue($anybody)} {
      return $IGNORE_POLARITY
   }

   if [info exists pseudo_result($anybody)] {
      global topdogs
      
      if ![info exists mcpDerivedData($anybody)] {# not cached
	 if {[info exists mcpIgnoreValue($anybody)] &&
	     $mcpIgnoreValue($anybody)} {
	    set op $anybody; set pieces {}
	 } else {
	    set op [lindex $topdogs($anybody) 0]
	    set pieces [lindex $topdogs($anybody) 1]
	 }
	 
	 set mcpDerivedData($anybody) [param_status $op $pieces]
      }
      return $mcpDerivedData($anybody)
   }

   if [info exists mcpData($anybody)] {
      return $mcpData($anybody)
   }

   global $anybody

   if ![info exists $anybody] {
      if {$anybody == "lavaLamp"} {
	 return [lavaLampStatus]
      }
      if $verbose {
	 puts "    WARNING: Requested field hasn't been defined: $anybody"
      }
      
      return -1
   }

   return [set $anybody]
}

proc Getfillcolor {anybody} {
   return [polarityToColor [evaluate_logic $anybody]]
}

proc polarityToColor {polarity} {
   global BAD_POLARITY INTERMEDIATE_POLARITY IGNORE_POLARITY GOOD_POLARITY
   global colors missing_color
   
   switch -- $polarity \
       [list \
	    $BAD_POLARITY { set color $colors(led_bad) } \
	    $INTERMEDIATE_POLARITY { set color $colors(ignore) } \
	    $GOOD_POLARITY { set color $colors(led_ok) } \
	    $IGNORE_POLARITY { set color $colors(led_ignore) } \
	    default { set color $missing_color } \
	    ]

   return $color
}

###########################################################
# Change colors based on new values
# for the "lights" in the "MCP Interlocks" window.
###########################################################

proc update_bigand_status {win fields} {
   global BAD_POLARITY IGNORE_POLARITY GOOD_POLARITY colors
   
   set bigand_status $GOOD_POLARITY
   foreach tname $fields {
      set status [param_status1 $tname]
      if {$status == $BAD_POLARITY} {
	 set bigand_status $status
	 break
      }
   }
   $win configure -bg [polarityToColor $bigand_status]
}

proc update_bigor_status {win fields} {
   global BAD_POLARITY IGNORE_POLARITY GOOD_POLARITY colors
   
   set bigand_status $BAD_POLARITY
   foreach tname $fields {
      set status [param_status1 $tname]
      if {$status == $GOOD_POLARITY} {
	 set bigand_status $status
	 break
      }
   }
   $win configure -bg [polarityToColor $bigand_status]
}

proc update_bicolor {win type} {
   global mcpData
   global colors
   
   set int [lindex $type 0]
   set texts [lindex $type 1]
   set ints [lindex $type 2]
      
   loop i 0 2 {
      set val$i $mcpData([lindex $ints $i])
   }

   if {$val0} {
      if $val1 {		# shouldn't both be on
	 set color $colors(led_bad)
	 set text "Error"
      } else {
	 set color $colors(led_bad)
	 set text  [lindex $texts 0]
      }

      bind $win.$int.button <Button-1> "Logic_info2 [lindex $ints 0]" 
      bind $win.$int.button <Button-3> "Logic_info2 [lindex $ints 1]" 
   } else {
      if !$val1 {		# shouldn't both be on
	 set color $colors(ignore)
	 set text "neither"
      } else {
	 set color $colors(led_ok)
	 set text  [lindex $texts 1]
      }

      bind $win.$int.button <Button-1> "Logic_info2 [lindex $ints 1]" 
      bind $win.$int.button <Button-3> "Logic_info2 [lindex $ints 0]" 
   }
   
   $win.$int.button configure -bg $color -text $text
}

proc update_hardware_status {win type} {      
   global colors

   set name [lindex $type 0]
   
   loop i 0 [llength [lindex $type 1]] {
      set caption [lindex [lindex $type 1] $i]
      set int [lindex [lindex $type 2] $i]

      set color [Getfillcolor $int]
      
      set text $caption;		# may be a pair state1:state2
      if [regexp {^([^:]+):([^:]+)$} $text foo good_text bad_text] {
	 if {$color == $colors(led_ok)} {
	    set text $good_text
	 } else {
	    set text $bad_text
	 }
      }
      
      $win.$name.$caption configure -bg $color -text $text
   }
}

proc graphicEngineMcp {} {
   global colors mcpData mcp_main
   global bicolor_status_list bigand_arrays bigor_arrays
   global big_button_status_args keydisplays
   #
   # Are we still getting packets?
   #
   set ctime $mcpData(ctime)

   if {[clock seconds] - $ctime > 300} {
      set text_fg $colors(bad)
   } else {
      set text_fg $colors(ok)
   }

   global inst_ID_as_string inst_id_consistent
   set inst_ID_as_string [getInstrumentID]; set ID_fg "black"
   if {($inst_ID_as_string == 0 && ![latch_is_open primary 1]) ||
       !$inst_id_consistent} {
      set ID_fg "red"
   }

   if {[info commands winfo] == ""} {
      return;
   }
   
   global colors plcVersion_button plcVersion
   if [info exists plcVersion_button] {
      if [catch {set plcVersion "PLC: [plcVersion]"}] {
	 set plcVersion "PLC: ???"
      }
      
      if [regexp {\?\?\?|MISMATCH|NO(CVS|SVN):[^:]+:} $plcVersion] {
	 set fg $colors(bad)
      } else {
	 set fg $colors(ok)
      }
      $plcVersion_button configure -fg $fg
   }
   
   if {[info commands winfo] != "" &&
       ([info exists mcp_main] && [winfo exists $mcp_main.permits])} {
      foreach side "left right" {
	 $mcp_main.top.$side configure \
	     -text "Last Update:  [clock format $ctime -format "%H:%M:%S" -gmt 1]Z"
      }
      
      $mcp_main.top.left configure -fg $text_fg
      if [winfo exists .sys_status.values.middle._ID_val] {
	 .sys_status.values.middle._ID_val configure -fg $ID_fg
      }
      
      foreach _arr \
	  [concat [array names bigand_arrays] [array names bigor_arrays]] {
	 global $_arr
	 upvar 0 $_arr arr

	 if ![info exists arr(.window)] {
	    continue
	 }
	 
	 set base $arr(.window)
	 if ![winfo exists $base] {
	    continue
	 }
	 
	 foreach type [array names arr] {
	    if {$type == ".window"} {
	       continue
	    }
	    if [info exists bigand_arrays($_arr)] {
	       update_bigand_status $base.$type $arr($type)
	    } else {
	       update_bigor_status $base.$type $arr($type)
	    }
	 }
      }

      foreach type $big_button_status_args {
	 update_hardware_status $mcp_main.hwstat.right $type
      }

      foreach type $bicolor_status_list {
	 update_bicolor $mcp_main.hwstat.left $type
      }
   }

   # Now update the colors of the most recent logic diagram.
   # It is easier just to re-draw the most recent logic diagram rather than try
   # to figure out which rectangles there are which need their colors changed.
   if {[winfo exists .mcp_logic] && [winfo ismapped .mcp_logic]} {
      Logic_redraw
   }
   #
   # And the telescope status display.
   #
   if {[winfo exists .sys_status] && [winfo ismapped .sys_status]} {
      global msg_axis_state
      
      update_instrument_change
      foreach v "Alt Az Rot" {
	 if [bad_axis_state $v] {
	    set text_fg $colors(bad)
	 } else {
	    set text_fg $colors(ok)
	 }
	 .sys_status.values.middle._$v.txt configure -fg $text_fg

	 switch $v {
	    "Alt" { set name altitude }
	    "Az" { set name azimuth }
	    "Rot" { set name rotator }
	 }
	 update_bigand_status .sys_status.values.middle._$v.perm \
	     $keydisplays($name)
      }
   }
}

###########################################################
# Initialize global variables, create windows needed
###########################################################

proc key_interlocks {{toplevel ""} {geom ""}} {
   global canvas colors nestcount mcpData neutral_color mcp_main
   
   if {[info exists mcp_main] && [winfo exists $mcp_main]} {
      wm deiconify $mcp_main; raise $mcp_main
      return
   }

   if {$toplevel == ""} {
      toplevel .mcp_main

      if {$geom != ""} {
	 wm geometry .mcp_main $geom
      }
      wm title .mcp_main "MCP Interlocks"

      set mcp_main .mcp_main
   } else {
      set mcp_main $toplevel
   }

   frame $mcp_main.top
   
   global plcVersion_button plcVersion
   if ![info exists plcVersion] {
      set plcVersion ""
   }

   pack [label $mcp_main.top.left -text ""] -side left -expand 1 -anchor w
   pack [label $mcp_main.top.mplabel -text "Interlocks and Instruments"] \
       -side left
   set plcVersion_button [label $mcp_main.top.right -textvariable plcVersion]
   pack $plcVersion_button -side left -expand 1
   pack $mcp_main.top -expand 1 -fill x
   #
   # keydisplays is set in BIGAND, and is the major components (e.g. azimuth)
   #
   global keydisplays

   set keydisplays(.window) [frame $mcp_main.permits]
   pack $keydisplays(.window)
   
   foreach name [lsort [array names keydisplays]] {
      if {$name == ".window"} {
	 continue
      }
      button $mcp_main.permits.$name -text $name \
	  -background $colors(led_ok)
      bind $mcp_main.permits.$name <Control-Button-1> "show_root_cause $name"
      bind $mcp_main.permits.$name <Button-1> "Logic_nameshow2 $name 1"
      
      pack $mcp_main.permits.$name -side left -padx 10
   }
   #
   # bicolor_status_list is set in SPECIAL_BICOLOR, and is things like
   # the azimuth break
   #
   global bicolor_status_list
   set LABWIDE 20

   frame $mcp_main.hwstat
   label $mcp_main.hwstat.mainlabel -text "HARDWARE STATUS BITS"
   pack $mcp_main.hwstat.mainlabel
   pack $mcp_main.hwstat

   frame $mcp_main.hwstat.left
   foreach one $bicolor_status_list {
      set thisn [lindex $one 0]
      
      frame $mcp_main.hwstat.left.$thisn
      label $mcp_main.hwstat.left.$thisn.$thisn -text $thisn -width $LABWIDE
      pack $mcp_main.hwstat.left.$thisn.$thisn -side left -anchor w

      button $mcp_main.hwstat.left.$thisn.button -background $neutral_color
      pack $mcp_main.hwstat.left.$thisn.button -side top -anchor w

      pack $mcp_main.hwstat.left.$thisn -side top -anchor w
   }

   #
   # Select an instrument to change; position under SPECIAL_BICOLOR buttons
   #
   global instrument_changes
   foreach name [array names instrument_changes] {
      if {$name == ".window"} {
	 continue
      }
      
      regexp {^((install|remove)_)?(.*)} $name foo goo hoo name
      set instruments($name) 1
   }

   set instrument_changes(.window) \
       [frame $mcp_main.hwstat.left.bottom -relief flat]

   foreach name [lsort [array names instrument_changes]] {
      if {$name == ".window"} {
	 continue
      }

      button $instrument_changes(.window).$name -text $name \
	  -background $colors(led_ok)
      bind $instrument_changes(.window).$name <Control-Button-1> "show_root_cause $name"
      bind $instrument_changes(.window).$name <Button-1> "Logic_nameshow2 $name 1"
      
      pack $instrument_changes(.window).$name -side left -padx 10
   }

   pack $instrument_changes(.window) -anchor w -side bottom
   #
   # big_button_status_args is set in HARDWARE_STATUS, and the buttons
   # appear in the right-hand panel
   #
   global big_button_status_args
   frame $mcp_main.hwstat.right

   foreach one $big_button_status_args {
      set thisn [lindex $one 0]
      set varnames [lindex $one 2]
      
      frame $mcp_main.hwstat.right.$thisn
      label $mcp_main.hwstat.right.$thisn.$thisn -text $thisn -width $LABWIDE
      pack $mcp_main.hwstat.right.$thisn.$thisn -side left -anchor w
      set counter 0
      foreach caption [lindex $one 1]  {
	 set thisvar_here [lindex $varnames $counter] 
	 button $mcp_main.hwstat.right.$thisn.$caption -text $caption \
	     -background $colors(led_ok) \
	     -command "Logic_info2 $thisvar_here {} 1 {} 1"
	 bind $mcp_main.hwstat.right.$thisn.$caption <Button-2> \
	     "toggle_mcpIgnoreValue $thisvar_here"

	 pack $mcp_main.hwstat.right.$thisn.$caption -side left -anchor e
	 
	 incr counter
      }
      pack $mcp_main.hwstat.right.$thisn -side top -anchor w
   }

   pack $mcp_main.hwstat.left $mcp_main.hwstat.right -side left \
       -fill y -anchor n
   #
   # Buttons at bottom
   #
   frame $mcp_main.bottom

   pack [menubutton $mcp_main.bottom.server -text "Panels" -relief groove \
	     -menu $mcp_main.bottom.server.menu] -side left
   menu $mcp_main.bottom.server.menu
   $mcp_main.bottom.server.menu add command \
       -label "All Interlocks" -command show_mcp_interlocks
   $mcp_main.bottom.server.menu add command \
       -label "System Status" -command make_telescope
   $mcp_main.bottom.server.menu add command \
       -label "Ignored Interlocks" -command make_ignored_interlocks

   pack [frame $mcp_main.bottom.fill1] -expand 1 -fill x -side left
   
   pack [button $mcp_main.bottom.help -text "help" -relief groove \
	     -command "mcp_help $mcp_main"] -side left   

   pack $mcp_main.bottom -fill x
}

proc close_key_interlocks {} {
   global mcp_main
   
   if {[info exists mcp_main] && [winfo exists $mcp_main]} {
      destroy $mcp_main
   }
}

proc kill_key_interlocks {{unschedule 0}} {
   global exit_interlocks mcp_main

   set exit_interlocks 1;
   if {[info exists mcp_main] && [winfo exists $mcp_main]} {
      destroy $mcp_main
   }
   #
   # Do any of the other windows that use this data still exist?
   #
   if {!([winfo exists .sys_status] ||
	 [winfo exists .mcp_interlocks])} {
      set unschedule 1
   }

   if $unschedule {
      schedule readMCPValues 0 0;
      catch { mcpClose }
      schedule graphicEngineMcp 0 0
   }
}

#
# Is an field read directly from the udp packets?
#
proc from_udp_packet {what} {
   global mcp_interlock_fields
   
   if [info exists mcp_interlock_fields($what)] {
      return 1
   } else {
      return 0
   }
}

#
# This canvas is where we draw the logic diagrams.
#
proc make_canvas {{raise 0}} {
   global canvas

   if [winfo exists .mcp_logic] {
      if $raise {
	 wm deiconify .mcp_logic
	 raise .mcp_logic
      }
      wm geometry .mcp_logic "";	# allow window to resize itself, even
                                        # if it's been too big for the window

      return ""
   }      
 
   toplevel .mcp_logic
   wm title .mcp_logic "MCP Interlock Logic"
   frame .mcp_logic.frame
   set canvas ".mcp_logic.frame.c2"
   canvas $canvas -bg blue
   #
   # Add a scrollbar
   #
   scrollbar .mcp_logic.frame.scroll_x -orient horizontal \
       -command "$canvas xview"
   
   $canvas configure -xscrollcommand ".mcp_logic.frame.scroll_x set"
   $canvas configure -width 400 -height 300
   $canvas configure -scrollregion \
       "0 0 [expr 3*[$canvas cget -width]] [$canvas cget -height]"
   
   pack .mcp_logic.frame.scroll_x -side bottom -fill x -expand 1

   pack .mcp_logic.frame
   
   frame .mcp_logic.choose
   label .mcp_logic.choose.label -text "Show:"
   entry .mcp_logic.choose.entry -width 30 -textvariable chosen_interlock
   pack .mcp_logic.choose.label .mcp_logic.choose.entry -side left

   frame .mcp_logic.bottom

   button .mcp_logic.bottom.ignore -text "ignore" -relief groove \
		-command "make_ignored_interlocks .mcp_logic.bottom.ignore"
   button .mcp_logic.bottom.help -text "help" -relief groove \
       -command "mcp_help interlock_logic"
   pack .mcp_logic.bottom.ignore -side left

   pack [frame .mcp_logic.bottom.fill1] -expand 1 -fill x -side left
   
   pack .mcp_logic.bottom.help -side right
   
   pack $canvas .mcp_logic.choose .mcp_logic.bottom -fill x
}

#
# Handle the variable chosen_interlock, which deals with the
# entry at the bottom of the .mcp_logic
#
if ![info exists chosen_interlock] {
   set chosen_interlock ""
   trace variable chosen_interlock w show_interlock
}
proc show_interlock {name elem op} {
   global $name mcpData topdogs

   upvar 0 $name Name
   set Name [string trimleft [string trimright $Name]]
   if {$Name != ""} {
      if {![info exists topdogs($Name)] && ![info exists mcpData($Name)]} {
	 set guess [concat [array names topdogs *$Name] \
			[array names mcpData *$Name]]
	 if {[llength $guess] == 1} {
	    set Name $guess
	 }
      }
      Logic_info2 $Name 0 0 "" 1
   }
}

###############################################################################
#
# Check that the toplevel ("BIGAND") interlocks test every interlock
# that we know about, and that all specified interlocks actually exist
#
proc check_logic {{missing 1} {inconsistent 1} {unreachable 0}} {
   global missing_interlocks inconsistent_interlocks unused_interlocks

   if [info exists missing_interlocks] {
      unset missing_interlocks
   }
   if [info exists inconsistent_interlocks] {
      unset inconsistent_interlocks
   }
   #
   # get an array of all known interlocks.
   #
   if [info exists unused_interlocks] {
      unset unused_interlocks
   }
   array set unused_interlocks [mcpGetFields]
   
   foreach _arr "keydisplays instrument_changes" {
      global $_arr
      upvar 0 $_arr arr
      foreach name [array names arr] {
	 if {$name == ".window"} {
	    continue
	 }

	 foreach el $arr($name) {
	    check_logic1 $name $el
	 }
      }
   }
   #
   # Some interlocks are explicitly said to be used via VALUE_IS_USED,
   # mostly ones that record the state of the systems
   #
   global value_is_used
   foreach el [array names value_is_used] {
      if [info exists unused_interlocks($el)] {
	 unset unused_interlocks($el)
      }
   }
   
   #print_logic_coverage $missing $inconsistent $unreachable
}

#
# Print results of a check of the logic
#
proc print_logic_coverage {{missing 1} {inconsistent 1} {unreachable 0} \
			       {file "-"}} {
   global missing_interlocks inconsistent_interlocks unused_interlocks

   if {$file == "-"} {
      set fd stdout
   } else {
      set fd [open $file w]
   }
   
   if $inconsistent {
      set fmt "%-40s %-10s %-10s"
      puts $fd "\
The following interlocks values' disagree with those we expected:"
      puts $fd [format $fmt "interlock" "Calculated" "From MCP"]
      puts $fd [format $fmt "---------" "----------" "--------"]
      foreach i [lsort [array names inconsistent_interlocks]] {
	 puts $fd [eval format {$fmt} $i $inconsistent_interlocks($i)]
      }
      puts $fd ""
   }
   if $missing {
      set fmt "%-40s %s"
      puts $fd "\
The following interlocks are referenced, but are not provided by the MCP:"
      puts $fd [format $fmt "interlock" "where used"]
      puts $fd [format $fmt "---------" "----------"]
      foreach i [lsort [array names missing_interlocks]] {
	 puts $fd [format $fmt $i $missing_interlocks($i)]
      }
   }
   #
   # If desired, print all interlocks that are not reachable from the
   # key interlock buttons specified by BIGAND
   #
   if $unreachable {
      set fmt "%s"
      puts $fd "
The following are provided by the MCP but are not used by the key interlocks:"
      foreach i [lsort [array names unused_interlocks]] {
	 puts $fd [format $fmt $i unused_interlocks($i)]
      }
   }	 

   if {$fd != "stdout"} {
      close $fd
   }
}


proc check_logic1 {name what} {
   global missing_interlocks inconsistent_interlocks unused_interlocks
   global mcpData named_node pseudo_result topdogs

   global max_depth
   if {[info exists max_depth] && [incr max_depth] > 40} {
      set max_depth 0
      error \
	  "Too deep nesting (max $max_depth) -- possible interlock logic loop "
   }

   foreach comp $what {
      while [regexp {^([{}]+)(AND|NOT|OR)( |$)} $comp foo braces] {
	 set ncomp [eval concat $comp]
	 if {$ncomp == $comp} {
	    break;
	 }
	 set comp $ncomp
      }

      if [regexp {^(AND|NOT|OR)$} $comp] {
	 continue;
      }

      if {[llength $comp] > 1} {
	 check_logic1 $what $comp
      } else {
	 if [info exists unused_interlocks($comp)] {
	    unset unused_interlocks($comp)
	 }

	 if ![info exists topdogs($comp)] {
	    if [info exists mcpData($comp)] {# a valid leaf node
	       ;
	    } else {
	       if ![info exists mcpData($name)] {
		  set name "anon"
	       }

	       if {![info exists missing_interlocks($comp)] ||
		   [lsearch $missing_interlocks($comp) $name] < 0} {
		  lappend missing_interlocks($comp) $name
	       }
	    }
	 } else {
	    set tb $topdogs($comp)
	    check_logic1 $what $tb

	    set status [param_status [lindex $tb 0] [join [lreplace $tb 0 0]]]
	    if ![info exists pseudo_result($what)] {
	       if [info exists mcpData($comp)] {
		  set value $mcpData($comp)
		  if {$status != $value} {
		     set inconsistent_interlocks($comp) "$status $value"
		  }
	       } elseif [info exists named_node($comp)] {# a named non-terminal
		  ;
	       } else {
		  if {![info exists missing_interlocks($comp)] ||
		      [lsearch $missing_interlocks($comp) $name] < 0} {
		     lappend missing_interlocks($comp) $name
		  }
	       }
	    }
	 }
      }
   }

   if [info exists max_depth] {
      incr max_depth -1
   }
}

#
# Generate a display of all the interlocks that the MCP gives us.
# Start by destroying window if $restart is true
#
proc show_mcp_interlocks {{geom ""} {restart 0}} {
   global env colors mcpData topdogs
   global sort_interlocks_by_class show_interlocks_regexp

   if [winfo exists .mcp_interlocks] {
      if $restart {
	 if {$geom == "save"} {
	    set geom [winfo geometry .mcp_interlocks]
	 }
	 destroy .mcp_interlocks
      } else {
	 wm deiconify .mcp_interlocks; raise .mcp_interlocks
	 return
      }
   }

   toplevel .mcp_interlocks
   wm title .mcp_interlocks "MCP All Interlocks"

   if {$geom != ""} {
      wm geometry .mcp_interlocks $geom
   }
   #
   # Label at top
   #
   label .mcp_interlocks.top -text "All MCP Interlocks"
   pack .mcp_interlocks.top -fill x -expand 1
   #
   # Frame for all those interlocks.
   #
   frame .mcp_interlocks.main
   canvas .mcp_interlocks.main.canvas
   set canvas .mcp_interlocks.main.canvas

   set nrow_disp 16;			# number of rows and
   set ncol_disp 3;			#    columns to display at a time
   set nrow 50;				# number of items per column
   set ncol_max 10000;			# max number of columns, i.e. unlimited
   #
   # For debugging, it's faster to set these rather smaller...
   #
   if 0 {
      set ncol_max 3
      set nrow 10
   }

   set dx 200; set dy 25;		# size of objects on canvas

   set i -1
   set col 0

   if ![info exists sort_interlocks_by_class] {
      set sort_interlocks_by_class 1
   }
   
   if $sort_interlocks_by_class {
      set sort_interlock_proc sort_interlocks_by_class
   } else {
      set sort_interlock_proc sort_interlocks_by_name
   }

   set fields [lsort -command $sort_interlock_proc [array names mcpData]]

   if {[info exists show_interlocks_regexp] && $show_interlocks_regexp != ""} {
      set gfields {}
      foreach el $fields {
	 if [regexp $show_interlocks_regexp $el] {
	    lappend gfields $el
	 }
      }
      set fields $gfields
   }
   if {[llength $fields] < $nrow*$ncol_disp} {
      set nrow [expr [llength $fields]/$ncol_disp + 1]
   }
   if {$nrow < $nrow_disp} { set nrow $nrow_disp }

   foreach int $fields {
      if {[regexp {^(arrayName|CRC|serialNum|timeStamp)$} $int] ||
	  [regexp {(rack_[0-9]+_grp_[0-9]+_bit_?[0-9]+|spare.*|__unused_.*|:val)$} $int]} {
	 continue
      }
      
      incr i
      if {$i%$nrow == 0} {
	 if {$col >= $ncol_max} { break }

	 incr col
      }

      frame $canvas.$int -bd 0 -width $dy -height $dx
      if [info exists topdogs($int)] {
	 set bitmap square.bit
      } else {
	 if [from_udp_packet $int] {
	    set bitmap circle.bit
	 } else {
	    set bitmap diamond.bit
	 }
      }

      label $canvas.$int.symb -bitmap @$env(INTERLOCKS_DIR)/etc/$bitmap \
	  -bg [$canvas cget -bg] -fg gray -bd 0
      button $canvas.$int.b -text [fix_name $int] -bd 0

      foreach type "symb b" {
	 bind $canvas.$int.$type <Button-1> \
	     "Logic_info2 $int 0 1 $canvas.$int.$type 1"
	 bind $canvas.$int.$type <Button-2> \
	     "toggle_mcpIgnoreValue $int; update_mcp_interlocks"
	 bind $canvas.$int.$type <Button-3> \
	     "Describe $int $canvas.$int.$type"
      }


      pack $canvas.$int.symb -side left
      pack $canvas.$int.b -side left -anchor w -expand 1 -fill x

      $canvas create window [expr ($i/$nrow)*$dx] [expr $dy*($i%$nrow)] \
	     -window $canvas.$int -anchor nw
   }

   scrollbar .mcp_interlocks.main.scroll_y \
       -command ".mcp_interlocks.main.canvas yview"
   frame .mcp_interlocks.main.scroll_x_frame
   scrollbar .mcp_interlocks.main.scroll_x -orient horizontal \
       -command ".mcp_interlocks.main.canvas xview"

   .mcp_interlocks.main.canvas configure \
       -xscrollcommand ".mcp_interlocks.main.scroll_x set"
   .mcp_interlocks.main.canvas configure \
       -yscrollcommand ".mcp_interlocks.main.scroll_y set"
   .mcp_interlocks.main.canvas configure \
       -width [expr $ncol_disp*$dx] -height [expr $nrow_disp*$dy]
   .mcp_interlocks.main.canvas configure \
       -scrollregion "0 0 [expr $col*$dx] [expr $nrow*$dy]"

   pack .mcp_interlocks.main.scroll_y .mcp_interlocks.main.canvas \
       -side left -fill y

   pack .mcp_interlocks.main.scroll_x -side bottom \
       -after .mcp_interlocks.main.scroll_y -fill x -expand 1

   pack .mcp_interlocks.main -fill x -expand 1
   #
   # Button panel at bottom
   #
   frame .mcp_interlocks.bottom

   pack [button .mcp_interlocks.bottom.check -text "check" -relief groove \
	     -command "check_logic 0 0 0; update_mcp_interlocks; show_missing_interlocks"] \
       -side left

   if $sort_interlocks_by_class {
      set sort "sort by class"
   } else {
      set sort "sort by name"
   }

   pack [button .mcp_interlocks.bottom.sort -text $sort -relief groove \
	     -command {set sort_interlocks_by_class [expr 1-$sort_interlocks_by_class]; show_mcp_interlocks "save" 1}] \
       -side left

   pack [button .mcp_interlocks.bottom.grep -text "grep" -relief groove \
	     -command "grep_interlocks_and_redisplay .mcp_interlocks.bottom.grep"] -side left

   pack [button .mcp_interlocks.bottom.help -text "help" -relief groove \
	     -command "mcp_help .mcp_interlocks"] -side left   

   pack [frame .mcp_interlocks.bottom.fill1] -expand 1 -fill x -side left

   pack [frame .mcp_interlocks.bottom.fill2] -expand 1 -fill x -side left

   pack [button .mcp_interlocks.bottom.resize -text "resize" -relief groove]\
       -side left
   
   pack .mcp_interlocks.bottom -side bottom -fill x

   bind .mcp_interlocks.bottom.resize <Button-1> resize_interlocks_canvas
   #
   # If the user resized the window, resize the canvas
   #
   tkwait visibility .mcp_interlocks
   resize_interlocks_canvas
   #
   # Set the colours
   #
   update_mcp_interlocks
}

proc grep_interlocks_and_redisplay {{win ""}} {
   global show_interlocks_regexp

   if ![info exists show_interlocks_regexp] {
      set show_interlocks_regexp ""
   }

   set regexp [prompt_user "Interlock Pattern" "Regexp: " \
		   $show_interlocks_regexp $win]

   set show_interlocks_regexp $regexp

   show_mcp_interlocks "save" 1
}

#
# Resize the interlocks canvas
#
proc resize_interlocks_canvas {} {
   set geom [split [wm geometry .mcp_interlocks] {x+}]
   .mcp_interlocks.main.canvas configure \
       -width [expr [lindex $geom 0] - 40] \
       -height [expr [lindex $geom 1] - 110];
   wm geom .mcp_interlocks {}
}

#
# Sort the interlocks, with or without their il__... prefixes
#
proc sort_interlocks_by_class {a b} {
   return [string compare [fix_name $a] [fix_name $b]]
}

proc sort_interlocks_by_name {a b} {
   return [string compare $a $b]
}

#
# Update the colours of the mcp_interlocks panel
#
proc update_mcp_interlocks {} {
   global mcpData mcpIgnoreValue colors
   global inconsistent_interlocks unused_interlocks

   if ![winfo exists .mcp_interlocks] {
      return
   }

   set good [.mcp_interlocks cget -bg];	# good background colour
   
   foreach win [winfo children .mcp_interlocks.main.canvas] {
      regexp {([^.]*)$} $win foo int
      if {[info exists mcpIgnoreValue($int)] && $mcpIgnoreValue($int)} {
	 set color $colors(led_ignore)
      } elseif {![info exists mcpData($int)] || $mcpData($int) == ""} {
	 set color "gray"
      } elseif {$mcpData($int)} {
	 set color $colors(led_ok)
      } else {
	 set color $colors(led_bad)
      }
      
      $win.symb configure -fg $color

      if [info exists inconsistent_interlocks($int)] {
	 set color $colors(led_bad)
      } elseif [info exists unused_interlocks($int)] {
	 set color gray
      } else {
	 set color $good
      }
      $win.b configure -bg $color
   }
}

#
# Popup a display of interlocks that are referenced but not provided by the
# MCP
#
proc show_missing_interlocks {{geom ""} {verbose 0}} {
   global missing_interlocks

   if ![info exists missing_interlocks] {
      if $verbose {
	 echo "There are no known interlocks missing from mcpData"
      }
      return
   }

   if [winfo exists .mcp_missing_interlocks] {
      wm deiconify .mcp_missing_interlocks; raise .mcp_missing_interlocks
      destroy .mcp_missing_interlocks.main
   } else {
      toplevel .mcp_missing_interlocks
      wm title .mcp_missing_interlocks \
	  "Referenced Interlocks Absent from MCP Packets"

      if {$geom != ""} {
	 wm geometry .mcp_missing_interlocks $geom
      }
      #
      # Label at top
      #
      label .mcp_missing_interlocks.top \
	  -text "Referenced Interlocks Absent from MCP Packets"
      pack .mcp_missing_interlocks.top -fill x -expand 1
   }
   #
   # Frame for all those interlocks.
   #
   pack [frame .mcp_missing_interlocks.main] \
       -before .mcp_missing_interlocks.bottom

   foreach el [concat hdr [array names missing_interlocks]] {
      if {$el == "hdr"} {
	 set name "Interlock"
	 set where "Used Where"
      } else {
	 set name $el
	 set where $missing_interlocks($el)
      }
      pack [frame .mcp_missing_interlocks.main._$el]
      pack \
	  [label .mcp_missing_interlocks.main._$el.name \
	       -anchor w -text $name -width 30 -pady 0 -border 0] \
	  [label .mcp_missing_interlocks.main._$el.where \
	       -anchor w -text $where -border 0 -width 40 -pady 0] \
	  -side left

      if {$el == "hdr"} {
	 pack [frame .mcp_missing_interlocks.main.ln -height 3 -relief sunken]\
	     -expand 1 -fill x
      }
   }
}

###############################################################################
#
# Toggle (or set) mcpIgnoreValue($val)
#
proc toggle_mcpIgnoreValue {el {val -1}} {
   global mcpIgnoreValue

   if [info exists mcpIgnoreValue($el)] {
      if {$val < 0} {
	 set val [expr !$mcpIgnoreValue($el)]
      }
      set mcpIgnoreValue($el) $val
   } else {
      if {$val == -1} {
	 set val 1
      }
      set mcpIgnoreValue($el) $val
   }

   Logic; graphicEngineMcp;			# update display
}

###############################################################################
#
# Make a panel to show which interlocks are being ignored
#
# N.b geom can be the name of the parent window; useful for popups
#
proc make_ignored_interlocks {{geom ""}} {
   global colors mcpIgnoreValue

   if [catch {
   
   if [winfo exists .mcp_ignored] {
      if [winfo exists .mcp_ignored.vars] {
	 destroy .mcp_ignored.vars
      }
      wm deiconify .mcp_ignored; raise .mcp_ignored
   } else {
      toplevel .mcp_ignored
      
      if {$geom != ""} {
	 if [winfo exists $geom] {	# the name of the parent
	    set parent $geom
	    set x [expr int([winfo rootx $parent]+[winfo width $parent]/2)]
	    set y [expr int([winfo rooty $parent]+[winfo height $parent]/2)]
	    set geom +$x+$y
	 }
	 
	 wm geometry .mcp_ignored $geom
      }
      wm title .mcp_ignored "Ignored MCP Interlocks"

      frame .mcp_ignored.top

      pack [label .mcp_ignored.top.left -text ""] \
	  -side left -expand 1 -anchor w
      pack [label .mcp_ignored.top.mplabel -text "Ignored MCP Interlocks"] \
	  -side left
      pack [phantom_label .mcp_ignored.top.right ""] -side left -expand 1
      pack .mcp_ignored.top -expand 1 -fill x
      #
      # Helpful message
      #
      pack [label .mcp_ignored.text \
		-text "\
 Middle-button-click on an interlock bit
 to toggle ignoring that bit"]
      #
      # Buttons at bottom
      #
      frame .mcp_ignored.bottom

      global set_all_ignored_interlocks_text
      if ![info exists set_all_ignored_interlocks_text] {
	 set set_all_ignored_interlocks_text "set"
      }
      
      pack [button .mcp_ignored.bottom.set \
		-textvariable set_all_ignored_interlocks_text -relief groove \
		-command "set_all_ignored_interlocks"] -side left
      pack [button .mcp_ignored.bottom.refresh -text "refresh" -relief groove \
		-command "make_ignored_interlocks"] -side left
      
      pack .mcp_ignored.bottom -fill x
   }
   #
   # List of ignored variables
   #
   frame .mcp_ignored.vars

   foreach el [lsort [array names mcpIgnoreValue]] {
      frame .mcp_ignored.vars._$el
      button .mcp_ignored.vars._$el.del -text delete \
	  -command "unset mcpIgnoreValue($el); destroy .mcp_ignored.vars._$el"
      checkbutton .mcp_ignored.vars._$el.val -text $el \
	  -variable mcpIgnoreValue($el) \
	  -selectcolor $colors(led_ignore) -command graphicEngineMcp

      pack \
	  .mcp_ignored.vars._$el.del \
	  .mcp_ignored.vars._$el.val \
	  -side left -fill y -anchor w
      pack .mcp_ignored.vars._$el -expand 1 -fill x
   }
   
   pack .mcp_ignored.vars -before .mcp_ignored.bottom -expand 1 -fill x

   } err] {
      puts $err
   }
}

proc set_all_ignored_interlocks {} {
   global mcpIgnoreValue set_all_ignored_interlocks_text

   if {$set_all_ignored_interlocks_text == "set"} {
      set set_all_ignored_interlocks_text "unset"
      set val 1
   } else {
      set set_all_ignored_interlocks_text "set"
      set val 0
   }

   foreach el [array names mcpIgnoreValue] {
      set mcpIgnoreValue($el) $val
   }
}

###############################################################################
#
# Print an HTML file of all the descriptions
#
proc makeInterlockDoc {{file ""} {short 1} {nohtml 1}} {
   global interlockDescriptions

   if {$file == ""} {
      set fd stdout
   } else {
      set fd [open $file "w"]
   }

   set title "Interlock Bit Descriptions"
   if !$nohtml {
      puts $fd "
 <HTML>
 <TITLE>$title</TITLE>

 <H1>$title</H1>
 <TABLE>
 <TR> <TH align=left> Bit Name <TH align=left> Description </TR>
 "
   }

   foreach el [lsort [array names interlockDescriptions]] {
      if {$short && [regexp {[Ss]pare} "$el$interlockDescriptions($el)"]} {
	 continue;
      }
      if $nohtml {
	 puts $fd [format "%-20 %s" $el $interlockDescriptions($el)]
      } else {
	 puts $fd "<TR> <TD> $el <TD> $interlockDescriptions($el) </TR>";
      }
   }

   if !$nohtml {
      puts $fd "
 </TABLE>
 </HTML>
 "
   }

   if {$fd != "stdout"} {
      close $fd
   }

   return $file
}
