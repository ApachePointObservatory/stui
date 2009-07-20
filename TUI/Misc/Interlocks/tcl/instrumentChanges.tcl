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

   catch {				# needs a post v2_6_4 watcher
      if {[schedule list graphicEngineMcp 1] == 0} {# not scheduled
	 after 1000;				# give the reader a chance
	 schedule graphicEngineMcp {} $update
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
   # The floor
   #
   frame .sys_status.floor -height 0.5c -bg $colors(struct)
   pack .sys_status.floor -side bottom -fill x -expand 1
   pack propagate .sys_status.floor 0
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
   frame .sys_status.lift -width 7c -height 5c -bd 0
   pack .sys_status.lift -in .sys_status.left 
   pack propagate .sys_status.lift 0
   #
   # The doghouse
   #
   frame .sys_status.doghouse -width 4c -height 3.5c -bd 0
   pack .sys_status.doghouse \
       -side bottom -in .sys_status.right -padx 0.2c
   pack propagate .sys_status.doghouse 0
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
   # Latches and the camera/cartridge below the mirror cell
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
   foreach v "primary saddle prot" {
      global ${v}_rotator; set ${v}_rotator $cell.middle.$v
      pack_instrument [frame $cell.middle.$v -height 0.5c -bd 0]

      if {$v == "primary"} {
	 set n 3
      } else {
	 set n 2
      }
      make_latches $v $n $cell.left.latches.latches_$v 0.3c \
	  -anchor se -expand 1

      make_tbar $cell.middle rotator $v
   }
   #
   # Saddle-in-place switches
   make_latches saddle_in_use \
       2 $cell.right.latches 0.3c -anchor w -expand 1 
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

   set cart_width [make_cart lift_cart .sys_status.lift.bottom 5c]

   make_lift_plate 
   make_instrument_on_cart lift $inst_width .sys_status.lift.bottom
   #
   # Make a cart in the doghouse
   #
   pack [frame .sys_status.doghouse.top -height 0.2c \
	   -bd 0 -bg $colors(struct)] \
       -fill x
   pack [frame .sys_status.doghouse.door \
	     -width 0.2c -bd 2 -bg $colors(struct) -relief raised] \
       -fill y -side left
   bind13 .sys_status.doghouse.door \
	"describe_thing {Doghouse Door}"
   pack [frame .sys_status.doghouse.wall -width 0.2c \
	   -bd 0 -bg $colors(struct)] \
       -fill y -side right
   pack [frame .sys_status.doghouse.inside -bd 0] \
       -side right -fill both -expand 1

   pack [frame .sys_status.doghouse.inside.cart -bd 0] -expand 1 -anchor s

   set cart_width [make_cart doghouse_cart \
	   .sys_status.doghouse.inside.cart 3c]
   global doghouse_door; set doghouse_door .sys_status.doghouse.door

   make_instrument_on_cart doghouse $inst_width \
	.sys_status.doghouse.inside.cart
   #
   global movable_things
   if [info exists movable_things] {	# forget our old state
      unset movable_things
   }
   #
   # Umbilical tower. Change the height of the motor to move.
   #
   global umbilical_tower_height; set umbilical_tower_height 2c

   frame .sys_status.umbil -width 0.9c -height $umbilical_tower_height -bd 0
   pack propagate .sys_status.umbil 0
   pack .sys_status.umbil -after .sys_status.values \
       -fill y -expand 1 -anchor w
   
   pack [frame .sys_status.umbil.tower -bg $colors(struct) -bd 0] \
       -expand 1 -fill both -side left -padx 0.2c
   bind13 .sys_status.umbil.tower {describe_thing "umbilical tower"}
   pack [frame .sys_status.umbil.tower.slider -height 0.5c -bg black -bd 0] \
       -expand 1 -fill x -anchor s
   bind13 .sys_status.umbil.tower.slider {describe_thing "camera umbilical"}
   pack [frame .sys_status.umbil.tower.motor -height 0c \
	     -bg $colors(struct) -bd 0] -side bottom -anchor s
   #
   # Lava Lamp
   #
   set lava .sys_status.lava
   frame $lava -width 0.9c -height 1.5c -bd 0
   pack [frame $lava.lamp -bd 0 -width 0.4c -height 1.5c -bg gray] \
       -anchor w
   pack propagate $lava 0; pack propagate $lava.lamp 0
   pack [frame $lava.lamp.base -height 0.5c -bg black -relief raised] \
       [frame $lava.lamp.lava -height 0.5c -bg gray] \
       -fill x -side bottom
   pack $lava.lamp.base -anchor s
   pack $lava.lamp.lava -anchor n -expand 1

   bind13 $lava.lamp "describe_thing {Lava lamp}"
   bind13 $lava.lamp.base "describe_thing {Base of lava lamp}"
   bind13 $lava.lamp.lava "describe_thing {Lava lamp lava}"
   
   pack .sys_status.umbil $lava -after .sys_status.umbil \
       -side left -anchor se
   pack .sys_status.umbil  -anchor sw
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
   if {!([winfo exists $mcp_main] ||
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
# Make a latched and unlatched position for the tbars within the camera
#
proc make_tbar {base where comp} {
   set tbar $base.$comp.tbar

   if {$comp == "primary"} {
      global tbar_${where}_unlatched; set tbar_${where}_unlatched $tbar
      set bitname t_bar_xport_stat
   } elseif {$comp == "saddle"} {
      global tbar_${where}_latched; set tbar_${where}_latched $tbar
      set bitname t_bar_tel_stat
   }
   
   if [info exists bitname] {
      pack [frame $tbar -height 0.2c -width 0.2c]
      bind13 $tbar "Logic_info2 $bitname 0 1"
   }
}

proc tbars_latched {} {
   global mcpData
   
   if {$mcpData(t_bar_xport_stat) && !$mcpData(t_bar_tel_stat)} {
      return 1
   } elseif {!$mcpData(t_bar_xport_stat) && $mcpData(t_bar_tel_stat)} {
      return 0
   } else {
      return -1
   }
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

   foreach v "primary prot saddle" {
      global ${v}_$where; set ${v}_$where $inst.$v
      frame $inst.$v -height 0.5c -bd 0

      make_tbar $inst $where $v
   }
   pack [frame $inst.strut -bd 0 -width $width -height 0]
}

#
# Make the lift plate
#
proc make_lift_plate {} {
   global lift_plate inst_width colors
   
   set lift_plate [frame .sys_status.lift.plate -bd 0]
   pack [frame .sys_status.lift.plate.left -width 0.45c] \
       [frame .sys_status.lift.plate.middle -width $inst_width -height 0.4c \
	    -bd 2 -bg $colors(lift) -relief groove] \
       [frame .sys_status.lift.plate.right -width 0.45c] -side right
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
   show_doghouse
   show_lava
   #
   # What instrument's on the rotator?
   #
   if ![show_instrument_is_changed] { return }

   set current_instrument [instrument_type [getInstrumentID]]
   show_instrument $current_instrument rotator 1
   show_spec_corrector
   #
   # Where are the carts?
   #
   global movable_things

   if [cart_in_doghouse] {
      show_cart imager doghouse_cart s 1

      if {$current_instrument == "camera"} {
	 show_instrument camera doghouse 0
      } else {
	 show_instrument camera doghouse 1
      }
      
      if {![info exists movable_things(lift)] ||
	  $movable_things(lift) == "camera"} {
	 show_instrument camera lift 0
      }

      if {1 || [fiber_cart_position] <= 0} {
	 show_cart spectro lift_cart s 0
      }
      if [regexp {^[12]$} [fiber_cart_position] cart] {
	 if {$cart == 1} {
	    set anchor w
	 } else {
	    set anchor e
	 }
	 
	 show_cart spectro lift_cart $anchor 1
	 if {$current_instrument == "none"} {
	    show_instrument cartridge lift 1
	 } else {
	    show_instrument cartridge lift 0
	 }
      } else {
	 show_instrument cartridge lift 0
      }
   } else {
      show_instrument camera doghouse 0
      show_cart imager doghouse_cart s 0

      set pos s
      if {$current_instrument == "camera"} {
	 show_instrument camera lift 0
      } else {
	 show_instrument camera lift 1
      }

      if {!$mcpData(ops_cart_in_pos) && [lift_is_down]} {
	 set pos e
      } else {
	 set pos s
      }
      show_cart imager lift_cart $pos 1
   }
   #
   # Move the umbilical
   #
   global umbilical_tower_height
   
   .sys_status.umbil.tower.motor configure -height 0c
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
   } elseif {$where == "doghouse"} {
       set inst .sys_status.doghouse.inside.cart.inst
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
	 #
	 # The following is needed to ensure that the .middle frame becomes
	 # smaller when the saddle is unmapped. Grrr.
	 #
	 pack forget $inst.middle
	 pack $inst.middle -after $inst.left -side left -fill both -expand 1
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
      if [regexp {^(spec_corrector|prot)_} $v] {
	 set relief "raised"
      } else {
	 set relief "flat"
      }
      [set $v] configure -bg $color -relief $relief -bd 2
   }
}

proc show_instrument {what where show} {
   if {$show && $where == "lift"} {
      if [lift_is_down] {
	 show_lift down
      } else {
	 show_lift up
      }
   }

   global colors movable_things
   #
   # Tbar latches first
   #
   if $show {
      global tbar_${where}_latched tbar_${where}_unlatched

      set tbars_latched [tbars_latched]
      if {[info exists tbar_${where}_latched] &&
	  (![info exists movable_things(latches,$where)] ||
	   $movable_things(latches,$where) != "what,$tbars_latched")} {
	 if {$what == "camera"} {
	    switch -- $tbars_latched {
	       0 {
		  set latched_color $colors($what)
		  set unlatched_color $colors(tbars)
	       }
	       1 {
		  set latched_color $colors(tbars)
		  set unlatched_color $colors($what)
	       }
	       -1 {
		  set latched_color $colors(intermediate_latch)
		  set unlatched_color $colors(intermediate_latch)
	       }
	    }
	 } else {
	    set latched_color $colors($what)
	    set unlatched_color $colors($what)
	 }
	 [set tbar_${where}_latched] configure -bg $latched_color
	 [set tbar_${where}_unlatched] configure -bg $unlatched_color
	 set movable_things(latches,$where) $what,$tbars_latched
      }
   }
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
	     spec_corrector primary saddle prot
      }
      "spec_corrector" {
	 i_show_instrument rotator $show $colors(optics) spec_corrector
      }
      "camera" {
	 i_show_instrument $where $show $colors(camera) \
	     spec_corrector primary saddle prot

	 if $show {
	    global prot_$where; pack_instrument [set prot_$where]
	 }
      }
      {cartridge|engcam} {
	 i_show_instrument $where $show $colors($what) primary saddle

	 global prot_$where; pack forget [set prot_$where]
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

   loop m 1 4 {
      loop i 1 5 {
	 append sum $mcpData(inst_id${m}_$i)
      }
   }

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

proc show_lava {} {
   #
   # Status of lava lamp
   #
   global mcpData systemState

   if {[info exists mcpData(cr_lava_lamp)] && $mcpData(cr_lava_lamp)} {
      set lava_color red; set lamp_color white; set relief raised
   } else {
      set lava_color gray; set lamp_color gray; set relief flat
   }

   if ![info exists systemState(show_lava)] {
      set old NOT$lava_color
   } else {
      set old $systemState(show_lava)
   }
   set systemState(show_lava) $lava_color
   
   if ![string compare $systemState(show_lava) $old] {
      .sys_status.lava.lamp.lava configure -bg $lava_color -relief $relief
      .sys_status.lava.lamp configure -bg $lamp_color
   }
}

#
# Show the state of the latches
#
proc show_latches {} {
   global colors latches
   
   if ![show_latches_is_changed] { return }

   foreach v [list spec_corrector primary prot saddle \
		  slithead1 slithead_latch1 slithead2 slithead_latch2] {
      switch -regexp $v {
	 {slithead(_latch)?[12]} {
	    set n 1
	 }
	 {prot|saddle} {
	    set n 2
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
   # Now the sensors that check if the spectro corrector and
   # saddle are in
   #
   foreach v "spec_corrector saddle" {
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

#
# Show state of the doghouse
#
proc show_doghouse {} {
   global doghouse_door colors

   set bkgd [.sys_status.lift.top.left cget -bg]

   switch -- [doghouse_is_open] {
      "0" {
	 set color $colors(struct)
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
      
   $doghouse_door configure -bg $color
}

#
# Set the position of the instrument on the lift
#
proc show_lift {state} {
   global movable_things

   if [info exists movable_things(lift_pos)] {
      if {$movable_things(lift_pos) == $state} {
	 return
      }
   }
   set movable_things(lift_pos) $state

   switch $state {
      "up" { set where "bottom"; set after after }
      "down" { set where "top"; set after before}
      "default" { error "Unknown state: $state" }
   }
   
   pack forget .sys_status.lift.bottom.top .sys_status.lift.bottom.inst
   pack .sys_status.lift.bottom.inst
   pack .sys_status.lift.bottom.top \
       -$after .sys_status.lift.bottom.inst -side $where -expand 1 -fill y
}

#
# Show a cart
#
proc show_cart {type where anchor show} {
   global movable_things
   #
   # Are things unchanged?
   #
   if [info exists movable_things($where)] {
      if $show {
	 if {$movable_things($where) == "$type,$anchor"} {
	    return
	 }
      } else {
	 global lift_plate; pack forget $lift_plate
	 set movable_things($where) "unknown"
      }
   }

   if $show {
      set movable_things($where) $type,$anchor
   }
   
   if $show {
      set color "black"
      set relief "raised"
   } else {
      set color [.sys_status.lift.top.left cget -bg]
      set relief "flat"
   }

   switch $type {
      "imager" { set width 3c } 
      "spectro" { set width 5c } 
      "default" { error "Unknown cart type: $type" }
   }
   
   global $where; set cart [set $where]

   regsub {\.[^.]*$} $cart "" parent
   pack $parent -anchor $anchor
   
   $cart.platform configure -width $width
   bind13 $cart.platform "describe_thing {$type cart}"

   foreach w "platform wheels.left wheels.right" {
      $cart.$w configure -bg $color -relief $relief
   }
   #
   # If it's a spectro cart, move instrument to correct end
   #
   regsub {\.cart$} $cart ".inst" inst

   if {$type == "spectro"} {
      global inst_width

      if {$anchor == "w"} {
	 $inst.left configure -width $inst_width
	 $inst.right configure -width 1p
      } else {
	 $inst.left configure -width 1p
	 $inst.right configure -width $inst_width
      }
   } else {
      $inst.right configure -width 1p
      $inst.left configure -width 1p
   }

   show_lift_plate $cart $type $anchor $show
}

#
# Show the lift plate
#
proc show_lift_plate {cart type anchor show} {
   global lift_plate movable_things

   if ![regexp "lift" $cart] {
      return
   }

   #return;				# XXX

   if {$type == "spectro"} {
      if {$anchor == "w"} {
	 set anchor "e"
      } else {
	 set anchor "w"
      }
   }

   if [winfo ismapped $lift_plate] {
      if {![info exists movable_things(lift_plate)] ||
	  $movable_things(lift_plate) != [lift_is_down]} {
	 pack forget $lift_plate
      }
   }
   if $show {
      if [lift_is_down] {
	 pack $lift_plate -after $cart -side bottom -anchor $anchor
      } else {
	 pack $lift_plate -after .sys_status.lift.bottom.inst \
	     -side top -anchor $anchor
      }
   }
   set movable_things(lift_plate) [lift_is_down]
}
###############################################################################
#
# Deal with instrument IDs; set the globals inst_id# and inst_id_consistent
# based on the MCP fields
#
proc getInstrumentID {} {
   global mcpData

   global fake_lift; if [info exists fake_lift] { #return 0; }

   loop m 1 4 {
      global inst_id$m
      
      set inst_id$m 0
      loop i 1 5 {
	 set inst_id$m \
	     [expr ([set inst_id$m]<<1) + ($mcpData(inst_id${m}_$i)  ? 0 : 1)]
      }
   }

   global inst_id_consistent
   if {$inst_id1 == $inst_id2 && $inst_id1 == $inst_id3} {
      set inst_id_consistent 1
   } else {
      set inst_id_consistent 0
   }

   return $inst_id1
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
	       if [latch_is_open saddle 1] {
		  return "engcam"
	       } else {
		  return "camera"
	       }
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
# Is the doghouse door open?
#
proc doghouse_is_open {} {
   global mcpData
   
   return [expr $mcpData(dog_house_door_cls) ? 0 : 1]
}

#
# Is the given latch open?
#
proc latch_is_open {type i} {
   global mcpData

   switch -regexp $type {
      "saddle" {
	 set prefix "sad_latch$i"
      }
      "spec_corrector" {
	 set prefix "sec_latch$i"
      }
      "primary" {
	 set prefix "pri_latch$i"
      }
      "prot" {
	 set prefix "safety_latch$i"
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
# Is there a cart in the doghouse?
#
proc cart_in_doghouse {} {
   global fake_lift; if [info exists fake_lift] { #return 0;}
      
   global mcpData
   return $mcpData(ops_cart_in_house)
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

proc saddle_in_use {} {
   global mcpData
   set is_in 0
   loop i 1 3 {
      incr is_in [saddle_sensor $i]
   }

   switch $is_in {
      0 { return 0 }
      3 { return 1 }
      default { return -$is_in }
   }
}

proc saddle_sensor {i} {
   global mcpData

   if {$i == 1} {
      return [expr !$mcpData(sad_mount$i)];# wired backwards on purpose
   } else {
      return [expr  $mcpData(sad_mount$i)]
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
	 "prot" { set bitname "safety_latch${n}_cls" }
	 "spec_corrector" { set bitname "sec_latch${n}_cls" }
	 "spec_corrector_in_use" { set bitname "spec_lens${n}" }
	 "saddle" { set bitname "sad_latch${n}_cls" }
	 "saddle_in_use" { set bitname "sad_mount$n" }
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

loop m 1 4 {
   loop i 1 5 {
      VALUE_IS_USED inst_id${m}_$i
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
	    "doghouse" {
	       set mcpData(ops_cart_in_house) 1
	    }
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

   loop m 1 4 {
      loop i 1 5 {
	 set mcpData(inst_id${m}_$i) [expr ($n & (1 << (4 - $i))) ? 0 : 1]
      }
   }
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
