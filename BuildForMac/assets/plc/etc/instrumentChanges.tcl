###############################################################################
#
# Control/Show the instrument change procedure
#
if ![info exists colors(optics)] {
   array set colors [list \
			 ok "black" \
			 bad "red" \
			 none   "" \
			 unknown "" \
			 struct "slateGray" \
			 optics "lightBlue" \
			 camera "slateGray" \
			 cartridge "gray" \
			 engcam "slateGray" \
			 tbars "black" \
			 bad_latch "red" \
			 open_latch "white" \
			 closed_latch "black" \
			 intermediate_latch "yellow" \
			 lift "gray" \
			]
}

proc make_telescope {{toplevel ""} {update 5} {geom ""}} {
   global colors

   catch {
      if {[schedule list graphicEngineMcp 1] == 0} {# not scheduled
	 after 1000;				# give the reader a chance
	 schedule graphicEngineMcp {} $update
      }
   }
   catch {
      if {[schedule list readMCPValues 1] == 0} {# not scheduled
	 after 1000;				# give the reader a chance
	 schedule readMCPValues {} $update
      }
   }
   
   if [winfo exists .sys_status] {
      wm deiconify .sys_status
      raise .sys_status
      
      return
   } else {
      global systemStatus
      if [info exists systemStatus] {
	 unset systemStatus;		# invalidate cache
      }
   }

   toplevel .sys_status
   wm title .sys_status "System Status"

   wm protocol .sys_status WM_DELETE_WINDOW {
      close_telescope
   }

   if {$geom != ""} {
      wm geometry .sys_status $geom
   }
   #
   # First a set of frames:
   #
   # A couple of frames to provide padding around the sides and top
   #
   pack [frame .sys_status.tstrut -height 0.5c] 
   pack [frame .sys_status.lstrut -width 0.5c] -side left
   #
   # Control buttons
   #
   frame .sys_status.bottom
   pack .sys_status.bottom -side bottom -fill x -expand 1
   #
   # Frames to pack the telescope, the lift, etc.
   #
   frame .sys_status.left  -bd 0 -width 7c
   frame .sys_status.right -bd 0 -width 4c
   pack .sys_status.left .sys_status.right -side left -fill y
   #
   # The telescope
   #
   frame .sys_status.telescope -bd 0 -bg $colors(struct)
   pack .sys_status.telescope -in .sys_status.left
   #
   # The lift space
   #
   frame .sys_status.lift -width 7c -height 2c -bd 0
   pack .sys_status.lift -in .sys_status.left 
   pack propagate .sys_status.lift 0
   #
   # The space-formerly-occupied-by-the-doghouse
   #
   frame .sys_status.doghouse -width 3c -height 0c -bd 0
   pack .sys_status.doghouse -side bottom -in .sys_status.right -padx 0.2c
   #
   # Space for values to the right of the telescope
   #
   pack [frame .sys_status.values] \
       -after .sys_status.doghouse -side top -fill both -expand 1
   #
   # Layout the telescope
   #
   # Main body of telescope
   #
   pack [frame .sys_status.telescope.main -bd 0] -expand 1 -fill x

   frame .sys_status.telescope.main.left -width 0.2c -bg $colors(struct)
   frame .sys_status.telescope.main.middle -bd 0
   frame .sys_status.telescope.main.right -width 0.2c -bg $colors(struct)
   pack .sys_status.telescope.main.left \
       .sys_status.telescope.main.right -fill y -side right
   pack .sys_status.telescope.main.middle \
       -after .sys_status.telescope.main.left \
       -fill both -expand 1 -side right
   #
   # Flat field/calibration screen and permit
   #
   frame .sys_status.telescope.main.middle.leaves -bd 0
   pack .sys_status.telescope.main.middle.leaves -fill x
   loop i 1 9 {
      frame .sys_status.telescope.main.middle.leaves.leaf$i \
	  -height 0.3c -bd 2 -relief raised
      pack .sys_status.telescope.main.middle.leaves.leaf$i \
	  -expand 1 -fill both -side left
      bind13 .sys_status.telescope.main.middle.leaves.leaf$i \
	  "describe_thing {leaf $i}"
   }
   
   pack [frame .sys_status.telescope.main.right.ff_perm \
	     -height 0.2c -width 0.2c -bg $colors(intermediate_latch) -bd 0] \
	-anchor n -expand 1 -fill x
   bind13 .sys_status.telescope.main.right.ff_perm \
	"Logic_info2 ff_screen_open_pmt 0 1"
   #
   # Top end and telescope tube
   #
   pack [frame .sys_status.telescope.main.middle.topend -bd 0] \
       -fill x -expand 1
   pack [frame .sys_status.telescope.main.middle.topend.secondary \
	     -width 2c -height 2c -bg $colors(struct)]
   bind13 .sys_status.telescope.main.middle.topend.secondary \
	"describe_thing {Secondary}"
   pack [frame .sys_status.telescope.main.middle.main -height 5c -bd 0] \
       -fill x
   #
   # Calibration lamps
   #
   foreach type "wht uv ne hgcd ff" {
      pack [frame .sys_status.telescope.main.middle.$type -bd 0] \
	  -expand 1 -fill x
      loop i 1 5 {
	 frame .sys_status.telescope.main.middle.$type.l$i \
	     -bd 2 -relief raised
	 bind13 .sys_status.telescope.main.middle.$type.l$i \
	     "describe_thing {$type lamp $i}"
      }
      frame .sys_status.telescope.main.middle.$type.m \
	  -width 5.2c -height 0.5c -bd 0
      
      pack \
	  .sys_status.telescope.main.middle.$type.l1 \
	  .sys_status.telescope.main.middle.$type.l2 \
	  .sys_status.telescope.main.middle.$type.m \
	  .sys_status.telescope.main.middle.$type.l3 \
	  .sys_status.telescope.main.middle.$type.l4 \
	  -side left -expand 1 -fill both
   }
   #
   # Mirror and Correctors
   #
   set cell .sys_status.telescope.cell
   
   pack [frame $cell -bd 0 -bg $colors(struct)] -fill x
   
   frame $cell.left -bd 0 -width 2.5c -height 1c -bg $colors(struct)
   frame $cell.middle -bd 0 -width 2c
   pack propagate $cell.middle 0
   frame $cell.right -bd 0 -width 2.5c -height 1c -bg $colors(struct)
   pack $cell.left $cell.middle $cell.right -expand 1 -fill both -side left

   foreach which "left right" {
      pack propagate $cell.$which 0
      bind13 $cell.$which "describe_thing {Primary}"
   }
   global inst_width; set inst_width 2c
   pack [frame $cell.middle.common_corrector -height 0.5c \
	     -width $inst_width -bg $colors(optics)] \
	-anchor n -expand 1 -fill x -pady 0.05c
   bind13 $cell.middle.common_corrector "describe_thing {Common Corrector}"
   #
   # Spec guider
   #
   set guider $cell.left.guider
   frame $guider -bd 3 -bg gray -width 1c -height 0.5c
   bind13 $guider "describe_thing {Spectrograph Guider}"

   global spec_corrector_rotator;
   set spec_corrector_rotator $cell.middle.spec_corrector
   pack_instrument [frame $spec_corrector_rotator \
	   -height 0.5c -bd 2 -relief raised]
   bind13 $spec_corrector_rotator "describe_thing {Second Corrector}"
   # The guider's Packed with the latches in a few lines

   make_latches spec_corrector 3 $cell.left.latches 0.3c -anchor se -expand 1 
   # these are actually the spec corrector sensors
   make_latches spec_corrector_in_use \
	2 $cell.right.latches 0.3c -anchor sw -expand 1 
   pack $guider $cell.left.latches -anchor sw \
       -anchor se -side right
   pack $guider -padx 0.07c -pady 0.07c
   #
   # Latches and the cartridge below the mirror cell
   #
   set cell .sys_status.lift.top
   
   pack [frame $cell -bd 0] -fill both

   frame $cell.left -bd 0 -width 2.5c -height 1c
   frame $cell.middle -bd 2 -relief flat
   bind13 $cell.middle "describe_thing {Instrument on rotator}"
   frame $cell.right -bd 0 -width 2.5c

   pack $cell.left  -fill y -side left -anchor w
   pack $cell.middle -after $cell.left -expand 1 -fill both -side left
   pack $cell.right -fill y -side left -anchor e

   foreach which "left right" {
      pack propagate $cell.$which 0
   }

   pack [frame $cell.left.latches -bd 0] -anchor e

   global primary_rotator; set primary_rotator $cell.middle.primary
   pack_instrument [frame $cell.middle.primary -height 0.5c -bd 0]
   make_latches primary 3 $cell.left.latches.latches_primary 0.3c -anchor se -expand 1
   #
   # Frame to right of intrument
   #
   pack [frame $cell.right.latches -bd 0]
   #
   # The spectrographs below the mirror cell
   #
   pack [frame $cell.left.spec -bd 0] \
       -anchor nw -before $cell.left.latches -side left
   pack [frame $cell.right.spec -bd 0] \
       -anchor ne -before $cell.right.latches -side right
   loop i 1 3 {
      if {$i == 1} {			# spec1
	 set spec $cell.left.spec.spec
	 set anchor nw
	 set side left
      } else {				# spec2
	 set spec $cell.right.spec.spec
	 set anchor ne
	 set side right
      }
      
      frame $spec -bg cyan -width 1.4c -height 1c -relief raised
      bind13 $spec "describe_thing {Spectrograph $i}"
      pack $spec -padx 0.07c -anchor $anchor -side $side
      pack propagate $spec 0

      pack [frame $spec.door$i -bd 2 -width 0.6c -height 0.2c] \
	      -anchor s -side bottom
      bind13 $spec.door$i "describe_thing {Spectrograph $i Slit Door}"

      global slitdoors; set slitdoors($i) $spec.door$i

      make_latches slithead$i 1 $spec.slithead$i 0.3c \
	  -anchor s -expand 1 -side top
      make_latches slithead_latch$i 1 $spec.slithead_latch$i 0.3c \
	  -anchor s -expand 1 -side left
   }
   #
   # Carts and instrument lift
   #
   frame .sys_status.lift.bottom -bd 0
   pack .sys_status.lift.bottom -anchor s -expand 1 -fill y

   make_lift_plate 

   #
   # Update the picture
   #
   update_instrument_change
   #
   # Useful Facts to the right of the tube
   #
   pack [frame .sys_status.values.middle] -padx 0.01c -fill both -expand 1

   foreach v "ID Az Alt Rot" {
      pack [frame .sys_status.values.middle._$v] -anchor w

      if [regexp {Alt|Az|Rot} $v] {
	 switch $v {
	    "Alt" { set name altitude }
	    "Az" { set name azimuth }
	    "Rot" { set name rotator }
	 }
	 pack [frame .sys_status.values.middle._$v.perm \
		   -height 0.2c -width 0.2c -bg $colors(led_ok)] -side left
	 bind13 .sys_status.values.middle._$v.perm "Logic_nameshow2 $name 1"
      }
      pack [label .sys_status.values.middle._$v.txt -text "$v: "] \
	  -anchor w
      
      switch -regexp $v {
	 {^(Alt|Az|Rot)$} {
	    set var mcpData([string tolower $v]computed:val)
	 }
	 {^ID$} {
	    set var inst_ID_as_string
	 }
	 "default" {
	    error "Unknown entity to display: $v"
	 }
      }

      global $var; if ![info exists $var] { set $var "???" }
	    
      pack [label .sys_status.values.middle._${v}_val -textvariable $var] \
	  -anchor w
   }
}

proc close_telescope {} {
   global mcp_main

   if [winfo exists .sys_status] {
      destroy .sys_status
   }

   global systemState
   unset systemState
   #
   # Do any of the other windows that use this data still exist?
   #
   if {!(([info exists mcp_main] && [winfo exists $mcp_main]) ||
	 [winfo exists .mcp_interlocks])} {
      #schedule readMCPValues 0 0
      schedule graphicEngineMcp 0 0
   }
}

#
# Bind an action to buttons 1 and 3
#
proc bind13 {win command} {
   foreach b "1 3" {
      bind $win <Button-$b> $command
   }
}

#
# Utility function to pack (part of) an instrument
#
proc pack_instrument {win} {
   pack $win -side top -expand 1 -fill x -padx 0.07c
}

#
# Make the frames for the latches
#
proc make_latches {name n frame size args} {
   global colors latches
   frame $frame -bd 0
   eval pack $frame $args

   loop i 1 [expr $n + 1] {
      set latches($name,$i) "$frame.latch$i"

      frame $latches($name,$i) \
	  -height $size -width $size -bg $colors(led_ok) -relief raised
      pack $latches($name,$i) -side left
      bind13 $latches($name,$i) "describe_thing {${name} latch $i}"
   }
}

#
# Make a set of frames for a cart
#
proc make_cart {name parent width} {
   global $name; set $name $parent.cart

   set cart $parent.cart
   pack [frame $cart -bd 0] -side bottom -anchor s
   
   pack [frame $cart.platform -height 0.4c -width $width] \
       -fill x -expand 1 -side top
   pack [frame $cart.wheels -bd 0] -anchor s -fill x -expand 1 -side bottom

   frame $cart.wheels.left -height 0.4c -width 0.4c
   frame $cart.wheels.middle -height 0.4c -width 1.0c
   frame $cart.wheels.right -height 0.4c -width 0.4c
   pack $cart.wheels.left $cart.wheels.middle $cart.wheels.right \
       -side right -expand 1
   foreach w "platform wheels.left wheels.right" {
      $cart.$w configure -bg black -relief raised
   }
   bind13 $cart.platform "describe_thing {Imager cart}"

   return [$cart.platform cget -width]
}

proc make_instrument_on_cart {where width base} {
   set top [frame $base.top]
   
   pack [frame $base.inst -bd 0] \
       -after $base.cart -side bottom -anchor s
   pack $top -before $base.inst -side top -fill y -expand 1

   set left [frame $base.inst.left -width 1p]
   set inst [frame $base.inst.middle]
   set right [frame $base.inst.right -width 1p]

   pack $left $right -side left -anchor s
   pack $inst -before $right -side left -anchor s

   global spec_corrector_$where; set spec_corrector_$where $inst.spec_corrector
   frame $inst.spec_corrector -height 0.5c -bd 2 -relief raised

   foreach v "primary" {
      global ${v}_$where; set ${v}_$where $inst.$v
      frame $inst.$v -height 0.5c -bd 0
   }
   pack [frame $inst.strut -bd 0 -width $width -height 0]
}

#
# Make the lift plate
#
proc make_lift_plate {} {
   global lift_plate inst_width colors
   
   set lift_plate [frame .sys_status.lift.plate -bd 0 -width $inst_width -height 0.4c \
	    -bd 2 -bg $colors(lift) -relief groove]
   pack $lift_plate

   bind13 $lift_plate "describe_thing {Lift plate}"
}

###############################################################################
#
# Update the telescope/instrument change display.
# This could be scheduled, e.g.
#   schedule update_instrument_change {} 10
# but this is usually done for you by graphicEngineMcp
#
proc update_instrument_change {} {
   global mcpData

   show_lamps;
   show_latches
   show_slitdoors
   show_lift_plate
   #
   # What instrument's on the rotator?
   #
   if ![show_instrument_is_changed] { return }

   set current_instrument [instrument_type [getInstrumentID]]
   show_instrument $current_instrument rotator 1
   show_spec_corrector
}

#
# Procs to show the state of various moving parts
#
# Draw the spectroscopic corrector, cartridge, and engineering/imaging camera
#
proc i_show_instrument {where show color args} {
   if {$where == "rotator"} {
       set inst .sys_status.lift.top
   } elseif {$where == "lift"} {
       set inst .sys_status.lift.bottom.inst
   } else {
      if $show {
	 error "Unknown instrument location: $where"
      } else {
	 return
      }
   }

   if {$show == 0} {
      foreach v $args {
	 set v ${v}_$where
	 global $v; pack forget [set $v]
      }
      if {$args != "spec_corrector"} {
	 global movable_things
	 if [info exists movable_things(corrector_cell)] {
	    unset movable_things(corrector_cell)
	 }
	 
	 $inst.middle configure -height 1 -relief flat
      }
      return
   }

   if {$args != "spec_corrector"} {
      $inst.middle configure -relief raised
   }
   
   foreach v $args {
      set v ${v}_$where
      global $v
      pack_instrument [set $v]
      if [regexp {^spec_corrector_} $v] {
	 set relief "raised"
      } else {
	 set relief "flat"
      }
      [set $v] configure -bg $color -relief $relief -bd 2
   }
}

proc show_instrument {what where show} {
   global colors movable_things
   #
   # Are things unchanged?
   #
   if [info exists movable_things($where)] {
      if $show {
	 if {$movable_things($where) == "$what"} {
	    return
	 }
      } else {
	 if {$movable_things($where) != "$what"} {
	    if {$movable_things($where) != "none"} {
	       show_instrument $movable_things($where) $where 0
	       set movable_things($where) "none"
	    }
	    
	    return
	 }
	 set movable_things($where) "none"
      }
   }
   if $show {
      set movable_things($where) $what
   } else {
      set movable_things($where) "none"
   }

   switch -regexp $what {
      "none" {
	 i_show_instrument $where 0 "" \
	     spec_corrector primary
      }
      "spec_corrector" {
	 i_show_instrument rotator $show $colors(optics) spec_corrector
      }
      {cartridge|engcam} {
	 i_show_instrument $where $show $colors($what) primary
      }
      "unknown" {
	 ;				# we don't know what to do
      }
   }

   if $show {
      set movable_things($where) $what
   }
}

proc show_spec_corrector {} {
   if {[instrument_type [getInstrumentID]] != "camera"} {
      set in_use [spec_corrector_in_use]
      switch -- $in_use {		# deal with inconsistency
	 -1 { set in_use 0 }
	 -2 { set in_use 1 }
      }
      show_instrument spec_corrector corrector_cell $in_use
   }
}

#
# Return 1 if show_instrument has changed
#
proc show_instrument_is_changed {} {
   global mcpData systemState

   set csum ""

   append csum $mcpData(spec_lens1)
   append csum $mcpData(spec_lens2)
   append csum $mcpData(inst_lift_dn)
   append csum $mcpData(t_bar_xport_stat)
   append csum $mcpData(t_bar_tel_stat)
   append csum $mcpData(fiber_cart_pos1)
   append csum $mcpData(fiber_cart_pos2)
   append csum $mcpData(ops_cart_in_pos)
   append csum $mcpData(ops_cart_in_house)

   append sum [getInstrumentID]

   if ![info exists systemState(show_inst)] {
      set old NOT$csum
   } else {
      set old $systemState(show_inst)
   }
   set systemState(show_inst) $csum

   return [string compare $systemState(show_inst) $old]
}

#
# Show the show of the comparison lamps and screen
#
proc show_lamps {} {
   global colors

   if ![show_lamps_is_changed] { return }

   set off [.sys_status.telescope cget -bg];# lamp is off
   set open [.sys_status cget -bg];	# leaf is open
   #
   # Do the lamps themselves first
   #
   foreach type "ff hgcd ne uv wht" {
      switch $type {
	 "ff" {
	    set color "ivory"
	 }
	 "hgcd" {
	    set color "cyan"
	 }
	 "ne" {
	    set color "red"
	 }
	 "uv" {
	    set color "violet"
	 }
	 "wht" {
	    set color "white"
	 }
	 "default" {
	    error "Unknown lamp type: $type"
	 }
      }

      loop i 1 5 {
	 if [lamp_is_on $type $i] {
	    set lcolor $color
	    lappend leaf_color $color
	 } else {
	    set lcolor $off
	 }
	 .sys_status.telescope.main.middle.$type.l$i configure -bg $lcolor
      }
   }
   #
   # Now the leaves of the screen
   #
   # Just for fun, get the colour of the screen "right" if both lamps are on
   #
   if ![info exists leaf_color] {
      set color $off
   } else {
      if {[lsearch $leaf_color "white"] >= 0} {
	 set color "white"
      } else {
	 if {[lsearch $leaf_color "cyan"] >= 0 &&
	     [lsearch $leaf_color "red"] >= 0} {
	    set color "orchid"
	 } else {
	    set color [lindex $leaf_color 0]
	 }
      }
   }
   
   loop i 1 9 {
      switch -- [leaf_is_open $i enabled] {
	 "0" {
	    set lcolor $color
	 }
	 "1" {
	    set lcolor $open
	 }
	 "2" {
	    set lcolor $colors(ignore)
	 }
	 "default" {
	    set lcolor $colors(led_bad)
	 }
      }

      if $enabled {
	 set relief "raised"
      } else {
	 set relief "flat"
      }

      .sys_status.telescope.main.middle.leaves.leaf$i \
	  configure -bg $lcolor -relief $relief
   }

   if [leaf_is_open permit] {
      set lcolor $colors(led_ok)
   } else {
      set lcolor $colors(led_bad)
   }
   .sys_status.telescope.main.right.ff_perm configure -bg $lcolor
}

#
# Return 1 if show_lamps has changed
#
proc show_lamps_is_changed {} {
   global mcpData systemState

   set csum ""
   foreach type "ff hgcd ne" {
      loop i 1 5 {
	 append csum $mcpData(${type}_${i}_stat)
      }
   }

   foreach type "uv wht" {
      append csum $mcpData(im_ff_${type}_on_pmt)
   }

   loop i 1 9 {
      append csum $mcpData(leaf_${i}_closed_stat)
      append csum $mcpData(leaf_${i}_open_stat)
   }

   append csum $mcpData(ff_screen_open_pmt)

   if ![info exists systemState(show_lamps)] {
      set old NOT$csum
   } else {
      set old $systemState(show_lamps)
   }
   set systemState(show_lamps) $csum

   return [string compare $systemState(show_lamps) $old]
}

#
# Show the state of the latches
#
proc show_latches {} {
   global colors latches
   
   if ![show_latches_is_changed] { return }

   foreach v [list spec_corrector primary \
		  slithead1 slithead_latch1 slithead2 slithead_latch2] {
      switch -regexp $v {
	 {slithead(_latch)?[12]} {
	    set n 1
	 }
	 "default" {
	    set n 3
	 }
      }

      loop i 1 [expr $n + 1] {
	 switch -- [latch_is_open $v $i] {
	    "0" {
	       set color $colors(closed_latch)
	    }
	    "1" {
	       set color $colors(open_latch)
	    }
	    "2" {
	       set color $colors(intermediate_latch)
	    }
	    "default" {
	       set color $colors(bad_latch)
	    }
	 }
	 
	 $latches($v,$i) configure -bg $color
      }
   }
   #
   # Now the sensors that check if the spectro corrector is in
   #
   foreach v "spec_corrector" {
      switch -- [${v}_in_use] {
	 "0" {
	    set consistent 1
	    set color $colors(open_latch)
	 }
	 "1" {
	    set consistent 1
	    set color $colors(closed_latch)
	 }
	 "-1" {
	    set consistent 0
	    set majority 0
	 }
	 "-2" {
	    set consistent 0
	    set majority 1
	 }
      }
      
      if $consistent {
	 loop i 1 3 {
	    $latches(${v}_in_use,$i) configure -bg $color
	 }
      } else {
	 loop i 1 3 {
	    if {[${v}_sensor $i] == $majority} {
	       if {$majority == 0} {
		  set color $colors(open_latch)
	       } else {
		  set color $colors(closed_latch)
	       }
	    } else {
	       set color $colors(bad_latch)
	    } 

	    $latches(${v}_in_use,$i) configure -bg $color
	 }
      }
   }
}

#
# Return 1 if show_latches has changed
#
proc show_latches_is_changed {} {
   global mcpData systemState

   set csum ""

   append csum $mcpData(sad_latch1_cls)
   append csum $mcpData(sad_latch1_opn)
   append csum $mcpData(sad_latch2_cls)
   append csum $mcpData(sad_latch2_opn)

   append csum $mcpData(sec_latch1_cls)
   append csum $mcpData(sec_latch1_opn)
   append csum $mcpData(sec_latch2_cls)
   append csum $mcpData(sec_latch2_opn)
   append csum $mcpData(sec_latch3_cls)
   append csum $mcpData(sec_latch3_opn)

   append csum $mcpData(pri_latch1_cls)
   append csum $mcpData(pri_latch1_opn)
   append csum $mcpData(pri_latch2_cls)
   append csum $mcpData(pri_latch2_opn)
   append csum $mcpData(pri_latch3_cls)
   append csum $mcpData(pri_latch3_opn)

   append csum $mcpData(safety_latch1_cls)
   append csum $mcpData(safety_latch1_opn)
   append csum $mcpData(safety_latch2_cls)
   append csum $mcpData(safety_latch2_opn)

   append csum $mcpData(slit_head_1_in_place)
   append csum $mcpData(slit_head_2_in_place)
   append csum $mcpData(slit_head_door1_cls)
   append csum $mcpData(slit_head_door1_opn)
   append csum $mcpData(slit_head_door2_cls)
   append csum $mcpData(slit_head_door2_opn)
   append csum $mcpData(slit_head_latch1_ext)
   append csum $mcpData(slit_head_latch2_ext)

   if ![info exists systemState(show_latches)] {
      set old NOT$csum
   } else {
      set old $systemState(show_latches)
   }
   set systemState(show_latches) $csum

   return [string compare $systemState(show_latches) $old]
}


#
# Show the lift plate
#
proc show_lift_plate {} {
   global lift_plate

   if [lift_is_down] {
      pack forget $lift_plate
   } else {
      pack $lift_plate
   }
}

#
# Show the state of the spectrograph's doors
#
proc show_slitdoors {} {
   global slitdoors colors

   set bkgd [.sys_status.lift.top.left cget -bg]
   loop i 1 3 {
      switch -- [slitdoor_is_open $i] {
	 "0" {
	    set color cyan
	 }
	 "1" {
	    set color $bkgd
	 }
	 "2" {
	    set color $colors(intermediate_latch)
	 }
	 "default" {
	    set color $colors(bad_latch)
	 }
      }

      $slitdoors($i) configure -bg $color
   }
}

###############################################################################
#
# Deal with instrument IDs
#
proc getInstrumentID {} {
   global mcpData

   loop n 1 30 {			# really only need 18 at present
      if {[info exists mcpData(cartridge_$n)] && $mcpData(cartridge_$n)} {
	 return $n
      }
   }

   return 0
}

proc instrument_type {id} {
   switch -regexp $id {
      {^0$} {
	 if [latch_is_open primary 1] {
	    return "none"
	 } else {			# Guess
	    global fake_lift; if [info exists fake_lift] { return "none" }
	    if {![spec_corrector_in_use] &&
		![latch_is_open primary 1]} {
	       return "engcam"
	    } else {
	       return "cartridge"
	    }
	 }
      }
      {^14$} {
	 return "camera"
      }
      {^([1-9]|10)$} {
	 return "cartridge"
      }
      {^13$} {
	 return "engcam"
      }
      default {
	 return "unknown"
      }
   }
}

###############################################################################
#
# Procs to return information about the state of the telescope, as reported
# by the MCP
#
# return 1/0 if a given lamp is on/off1
#
proc lamp_is_on {type i} {
   global mcpData

   if [regexp {^(uv|wht)$} $type] {
      return $mcpData(im_ff_${type}_on_pmt)
   } else {
      return $mcpData(${type}_${i}_stat)
   }
}

#
# Return 0 or 1 if a flatfield screen is closed/open
# return 2 if indeterminate, and -1 for error
#
proc leaf_is_open {i {_enabled ""}} {
   global mcpData

   if {$i == "permit"} {
      return $mcpData(ff_screen_open_pmt)
   }

   if {$_enabled != ""} {
      upvar $_enabled enabled;		# is leaf enabled?

      if {$i <= 4} {
	 set enabled $mcpData(mcp_ff_screen_enable)
      } else {
	 set enabled $mcpData(mcp_ff_screen2_enabl)
      }
   }

   if $mcpData(leaf_${i}_closed_stat) {
      if $mcpData(leaf_${i}_open_stat) {
	 return -1;			# inconsistent
      } else {
	 return 0;			# closed
      }
   } else {
      if !$mcpData(leaf_${i}_open_stat) {
	 return 2;			# intermediate
      } else {
	 return 1;			# open
      }
   }
}

#
# Is something open?
#
proc something_is_open {prefix} {
   global mcpData

   if $mcpData(${prefix}_cls) {
      if $mcpData(${prefix}_opn) {
	 return -1;			# inconsistent
      } else {
	 return 0;			# closed
      }
   } else {
      if $mcpData(${prefix}_opn) {
	 return 1;			# open
      } else {
	 return 2;			# intermediate
      }
   }
}

#
# Is a slitdoor open?
#
proc slitdoor_is_open {i} {
   return [expr [something_is_open slit_head_door$i]]
}

#
# Is the given latch open?
#
proc latch_is_open {type i} {
   global mcpData

   switch -regexp $type {
      "spec_corrector" {
	 set prefix "sec_latch$i"
      }
      "primary" {
	 set prefix "pri_latch$i"
      }
      {slithead(_latch)?[12]} {
	 regexp {slithead(_latch)?([12])} $type foo latch i

	 if {$latch == ""} {
	    return [expr $mcpData(slit_head_${i}_in_place) ? 0 : 1]
	 } else {
	    return [expr $mcpData(slit_head_latch${i}_ext) ? 0 : 1]
	 }
      }
   }

   set is_open [something_is_open $prefix]

   return $is_open
}

#
# Where's the spectro cart? 0 => don't know (absent?), or position 1 or 2
#
proc fiber_cart_position {} {
   global mcpData

   global fake_lift; if [info exists fake_lift] { return 1; }

   loop i 1 3 {
      if $mcpData(fiber_cart_pos$i) {
	 set latch$i 0
      } else {
	 set latch$i $i
      }
   }
   
   if {$latch1 == 0} {
      if {$latch2 == 0} {
	 return 0
      } else {
	 return $latch2
      }
   } else {
      if {$latch2 == 0} {
	 return $latch1
      } else {
	 return -1
      }
   }   
}

#
# Return 1/0 according to if the spec_corrector is in the rotator. If the
# sensors are inconsistent, return -number_who_say_in
#
proc spec_corrector_in_use {} {
   global mcpData
   set is_in 0
   loop i 1 3 {
      incr is_in [spec_corrector_sensor $i]
   }

   switch $is_in {
      0 { return 0 }
      3 { return 1 }
      default { return -$is_in }
   }
}

proc spec_corrector_sensor {i} {
   global mcpData

   if {$i == 1} {
      return [expr !$mcpData(spec_lens$i)];# wired backwards on purpose
   } else {
      return [expr  $mcpData(spec_lens$i)]
   }
}

proc lift_is_down {} {
   global fake_lift; if [info exists fake_lift] { return 0; }

   global mcpData
   return $mcpData(inst_lift_dn);
}

###############################################################################
#
# Describe a thing such as a latch
#
proc describe_thing {what} {
   set extra "";			# extra information
   if {[regexp {^([^ ]*) +latch +([1-9])} $what foo type n]} {
      switch -- $type {
	 "primary" { set bitname "pri_latch${n}_cls" }
	 "spec_corrector" { set bitname "sec_latch${n}_cls" }
	 "spec_corrector_in_use" { set bitname "spec_lens${n}" }
	 "slithead1" { set bitname slit_head_1_in_place }
	 "slithead2" { set bitname slit_head_2_in_place }
	 "slithead_latch1" { set bitname slit_head_latch1_ext }
	 "slithead_latch2" { set bitname slit_head_latch2_ext }
      }
   } elseif {[regexp {^([^ ]*) +lamp +([1-9])} $what foo type n]} {
      if [regexp {^uv|wht$} $type] {
	 set bitname im_ff_${type}_on_pmt
      } else {
	 set bitname ${type}_${n}_stat
      }
   } elseif {[regexp {^leaf +([1-9])} $what foo n]} {
      set bitname leaf_${n}_open_stat
      leaf_is_open $n enabled
      if $enabled { set extra "(enabled)" } else { set extra "(disabled)" }
   } elseif {[regexp {^Spectrograph ([1-9]) Slit Door} $what foo n]} {
      set bitname slit_head_door${n}_opn
   }

   if [info exists bitname] {
      Describe $bitname "" $extra
   } else {
      give_help $what ""
   }
}

###############################################################################
#
# VALUE_IS_USED declares that we are indeed using the specified field
#
foreach type "ff hgcd ne" {
   loop i 1 5 {
      VALUE_IS_USED ${type}_${i}_stat
    }
}

loop i 1 3 {
   VALUE_IS_USED spec_lens$i 
}

###############################################################################
#
# Procs to fool the MCP, setting bits behind its back. Debugging only
#
proc set_screen {state} {
   global mcpData
   if {$state == "open"} {
      set closed 0; set open 1
   } else {
      set closed 1; set open 0
   }
   
   loop i 1 9 {
      set mcpData(leaf_${i}_closed_stat) $closed
      set mcpData(leaf_${i}_open_stat)   $open
   }
}

proc set_lamp {type i on} {
   global mcpData
   switch $on {
      "on" { set on 1 }
      "off" { set on 0 }
   }
   set mcpData(${type}_${i}_stat) $on
}

proc turn_off_lamps {} {
   foreach type "ff hgcd ne" {
      loop i 1 5 {
	 set_lamp $type $i 0
      }
   }
}

proc set_slitdoor {i open} {
   global mcpData
   switch $open {
      "open" { set open 1 }
      "closed" { set open 0 }
   }
   set mcpData(slit_head_door${i}_opn) $open
   set mcpData(slit_head_door${i}_cls) [expr !$open]
}

proc set_dogdoor {open} {
   global mcpData
   switch $open {
      "open" { set open 1 }
      "closed" { set open 0 }
   }
   set mcpData(dog_house_door_opn) $open
   set mcpData(dog_house_door_cls) [expr !$open]
}

proc set_cart {which where} {
   global mcpData
   
   switch $which {
      "imager" {
	 switch $where {
	    "lift" {
	       set mcpData(ops_cart_in_house) 0
	    }
	    "default" {
	       error "Unknown cart position: $where"
	    }
	 }
      }
	 
      "spectro" {
	 switch $where {
	    "pos1" {
	       set mcpData(cart_latch1_opn) 0
	       set mcpData(cart_latch2_opn) 1
	    }
	    "pos2" {
	       set mcpData(cart_latch1_opn) 1
	       set mcpData(cart_latch2_opn) 0
	    }
	    "shed" {
	       set mcpData(cart_latch1_opn) 0
	       set mcpData(cart_latch2_opn) 0
	    }
	    "default" {
	       error "Unknown cart position: $where"
	    }
	 }
      }
      "default" {
	 error "Unknown cart type: $what"
      }
   }
}

proc set_instrument_id {n} {
   global mcpData
   
   set mcpData("cartridge_$n") 1
}

proc set_spec_corrector {state} {
   global mcpData

   loop i 1 4 {
      set mcpData(spec_lens$i) $state
   }
}

proc set_camera {state} {
   set_spec_corrector 0
   set_instrument_id [expr $state ? 1 : 0]
}

proc set_cartridge {state} {
   set_spec_corrector $state
   set_instrument_id [expr $state ? 2 : 0]
}
