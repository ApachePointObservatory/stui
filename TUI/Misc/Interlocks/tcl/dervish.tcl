# -*- tcl -*-
#
# Don't typo when looking for an error trace (as the typo becomes the error trace!)
#
proc tb {} {
   global errorInfo
   puts $errorInfo
}

#
# Provide tclx's loop command
#
proc loop {_var start end delta {cmd "_None_"}} {
    upvar $_var var

    if {$cmd == "_None_"} {
       set cmd $delta
       set delta 1
    }
    
    set var $start

    if {$delta > 0} {
       while {[expr $var < $end]} {
	  uplevel $cmd
	  
	  set var [expr $var + $delta]
       }
    } else {
       while {[expr $var >= $end]} {
	  uplevel $cmd
	  
	  set var [expr $var + $delta]
       }
    }
}

#
# dervish's echo
#
proc echo {args} {
   puts $args
}

#
# and murmur, a logging command
#
proc murmur {args} {
   #puts $args
}

#------------------------------------------------------------------------------
#
# Robert Lupton's scheduler implementation of the after method 
#
#  if you have a proc foo that expects a scalar and a list as arguments,
#  and it should be run every 5s, you could say:
#
#       schedule foo "abcd {1 2}" 5
#
# to cancel it, use 
#
#       schedule foo "" 0
#
# The command
#	schedule list
# will list all scheduled tasks (schedule list will be more verbose);
#	schedule list task [quiet]
# returns that task's arguments and interval; if quiet is specified nothing is
# printed and 1/0 is returned according to whether the task is/isn't scheduled
#
proc schedule {procname {args ""} {delay 0}} {
    global after_$procname ${procname}Delay verbose scheduled
    global show_scheduled_errors

    if {$procname == "list"} {
       if {$args != ""} {
	  set cmd $args; global ${cmd}Delay
	  if {![info exists scheduled($cmd)] || ![info exists ${cmd}Delay]} {
	     if !$delay {	
		echo "Command $cmd is not currently scheduled"
	     }
	     return 0
	  }
	  if $delay {
	     return 1
	  } else {
	     return [list $scheduled($cmd) [expr 0.001*[set ${cmd}Delay]]]
	  }
       }
       
       if {$delay != 0} {
	  error "You cannot specify a delay with schedule list"
       }
	  
       set fmt "%-30s  %-30s  %4s"
       puts [format $fmt "command" "arguments" "interval (s)"]
       puts [format $fmt "-------" "---------" "------------"]

       foreach cmd [lsort [array names scheduled]] {
	  global ${cmd}Delay
	  
	  set arg [string trimleft $scheduled($cmd)]
	  if {"$arg" == ""} {
	     set arg "{}"
	  }

	  if {[string length $arg] > 30} {# insert some newlines
	     set alist [split $arg " "]
	     set arg ""; set line ""
	     loop i 0 [llength $alist] {
		if {[string length "$line"] > 30} {
		   append arg "$line\\\n[format [lindex $fmt 0] {}]         ";
		   set line ""
		}
		append line "[lindex $alist $i] "
	     }
	     append arg "$line"
	  }

	  puts [format $fmt  $cmd $arg \
		    [format "%.1f" [expr 0.001*[set ${cmd}Delay]]]]
       }
       if [info exists show_scheduled_errors] {
	  echo; echo "Errors will be popped up"
       } else {
	  echo; echo "Variable show_scheduled_errors is not set"
       }
       return
    }

    if {$delay < 0 && [set ${procname}Delay] != [expr -$delay*1000]} {
        # someone has set the delay to 0, so stop $procname
        set delay [set ${procname}Delay]
    }
    if {$delay > 3000} { echo "scheduler: delay is $delay, in seconds" }

    if {$delay >= 0} {
        set ${procname}Delay [expr int($delay*1000)]

        zap1After after_$procname;      # if we already have in event loop,
        # delete it. One is enough
        if {$delay == 0} {
	    murmur  "Stopping $procname"
	    if [info exists after_$procname] {unset after_$procname}
	    if [info exists scheduled($procname)] {unset scheduled($procname)}

            return 0
        } else {
            murmur  "Starting $procname"
        }
    }

    # do the work. Trap errors: the first time around, send error message 
    # to screen; otherwise only do so if show_scheduled_errors is set
    if {$delay < 0 || [info exists show_scheduled_errors]} {
        if [catch {eval $procname $args} msg] {
            murmur $msg
	   if [info exists show_scheduled_errors] {
	      tkerror "Error from scheduled job $procname in process [pid]: $msg"
	   }
        }
    } else {
        if [catch {eval $procname $args} msg] {
            murmur $msg
	    echo $msg
	    global errorInfo
	    echo $errorInfo
	    echo "$procname is scheduled, further errors sent to murmur"
        }
    }

    # reschedule this proc, i.e. put it back into the event loop.
    # A negative delay means that this is a re-schedule, so no messages
    # should be printed
    if {$delay > 0} {
        murmur  [format "Next $procname event loop pending in %d ms" [set ${procname}Delay]]

        set delay [expr -$delay]
        set scheduled($procname) $args;	# this is solely to allow use to list
       					# scheduled commands with their args
    }

    set after_$procname \
	[after [set ${procname}Delay] \
	     [list schedule $procname "$args" $delay]]

    return 0
}

#
# deletes the specified after command in the event loop.
#
proc zap1After { scheduled } {
    global verbose

    # 1st try the actual parameter specified
    global $scheduled
    if {[info exists $scheduled]} {
        if {[string length $scheduled]} {
            #murmur "Cancelling event loop: uplevel 0 after cancel [set $scheduled]"
            uplevel 0 after cancel [set $scheduled]
        }
        uplevel 0 unset $scheduled
        return 0
    }

    # Now try putting after_  before what was specified
    set scheduled "after_$scheduled"
    global $scheduled
    if {[info exists $scheduled]} {
        if {[string length $scheduled]} {
            #murmur "Cancelling event loop: uplevel 0 after cancel [set $scheduled]"
            uplevel 0 after cancel [set $scheduled]
        }
        uplevel 0 unset $scheduled
        return 0
    }

    # Nothing to delete, but that is not really an error condition
    regsub {after_after_} $scheduled "" name
    murmur "Can not find $name in the event loop, so can not delete it"
    return 0
}

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# colors for the various states of things
#
set colors(bad) red
set colors(ignore) yellow
set colors(ok) black
set colors(led_bad) red
set colors(led_ignore) yellow
set colors(led_ok) green
set colors(led_unknown) grey
foreach el [array names colors led_*] {
   set colors(big_$el) $colors($el)
}

#
# Set a colour;  useful from Tkinter.call, and performs keyword checking
#
proc setMcpColor {key value} {
   global colors

   if [info exists colors($key)] {
      set colors($key) $value
   } else {
      tk_messageBox -message "Unknown colour type $key; please use one of [array names colors]" -type ok
   }
}

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# Include machine generated procs to handle unpacking PLC bits into the mcpData array
#

proc set_B3_L0 {val} {
   global mcpData

   set mcpData(rot_mtr_iv_good) [expr ($val & (1 << 31)) != 0]
   set mcpData(alt_mtr_iv_good) [expr ($val & (1 << 30)) != 0]
   set mcpData(az_mtr_iv_good) [expr ($val & (1 << 29)) != 0]
   set mcpData(hgcd_lamp_on_request) [expr ($val & (1 << 28)) != 0]
   set mcpData(ne_lamp_on_request) [expr ($val & (1 << 27)) != 0]
   set mcpData(lift_speed_man_ovrid) [expr ($val & (1 << 26)) != 0]
   set mcpData(ilcb_led_on) [expr ($val & (1 << 25)) != 0]
   set mcpData(ff_screens_closed) [expr ($val & (1 << 24)) != 0]
   set mcpData(e_stop_flash_reset) [expr ($val & (1 << 23)) != 0]
   set mcpData(led_flash) [expr ($val & (1 << 22)) != 0]
   set mcpData(flip_flop_5) [expr ($val & (1 << 21)) != 0]
   set mcpData(flip_flop_4) [expr ($val & (1 << 20)) != 0]
   set mcpData(flip_flop_3) [expr ($val & (1 << 19)) != 0]
   set mcpData(flip_flop_2) [expr ($val & (1 << 18)) != 0]
   set mcpData(flip_flop_1) [expr ($val & (1 << 17)) != 0]
   set mcpData(flip_flop_0) [expr ($val & (1 << 16)) != 0]
   set mcpData(plc_cont_t_bar_latch) [expr ($val & (1 << 15)) != 0]
   set mcpData(mcp_cont_t_bar_latch) [expr ($val & (1 << 14)) != 0]
   set mcpData(plc_cont_slit_hd) [expr ($val & (1 << 11)) != 0]
   set mcpData(mcp_cont_slit_hd) [expr ($val & (1 << 10)) != 0]
   set mcpData(plc_cont_slit_dr) [expr ($val & (1 << 7)) != 0]
   set mcpData(mcp_cont_slit_dr) [expr ($val & (1 << 6)) != 0]
   set mcpData(e_stop_permit) [expr ($val & (1 << 5)) != 0]
   set mcpData(dn_inhibit_latch_4) [expr ($val & (1 << 4)) != 0]
   set mcpData(dn_inhibit_latch_3) [expr ($val & (1 << 3)) != 0]
   set mcpData(dn_inhibit_latch_2) [expr ($val & (1 << 2)) != 0]
   set mcpData(dn_inhibit_latch_1) [expr ($val & (1 << 1)) != 0]
   set mcpData(up_inhibit_latch) [expr ($val & (1 << 0)) != 0]
}


proc set_B3_L1 {val} {
   global mcpData

   set mcpData(img_cam_in_place) [expr ($val & (1 << 31)) != 0]
   set mcpData(undefined_2) [expr ($val & (1 << 30)) != 0]
   set mcpData(undefined_1) [expr ($val & (1 << 29)) != 0]
   set mcpData(undefined_3) [expr ($val & (1 << 28)) != 0]
   set mcpData(eng_cam_in_place) [expr ($val & (1 << 27)) != 0]
   set mcpData(cartridge_9) [expr ($val & (1 << 26)) != 0]
   set mcpData(cartridge_8) [expr ($val & (1 << 25)) != 0]
   set mcpData(cartridge_7) [expr ($val & (1 << 24)) != 0]
   set mcpData(cartridge_6) [expr ($val & (1 << 23)) != 0]
   set mcpData(cartridge_5) [expr ($val & (1 << 22)) != 0]
   set mcpData(cartridge_4) [expr ($val & (1 << 21)) != 0]
   set mcpData(cartridge_3) [expr ($val & (1 << 20)) != 0]
   set mcpData(cartridge_2) [expr ($val & (1 << 19)) != 0]
   set mcpData(cartridge_1) [expr ($val & (1 << 18)) != 0]
   set mcpData(no_inst_in_place) [expr ($val & (1 << 17)) != 0]
   set mcpData(disc_cable) [expr ($val & (1 << 16)) != 0]
}


proc set_B3_L2 {val} {
   global mcpData

   set mcpData(sad_not_in_place) [expr ($val & (1 << 31)) != 0]
   set mcpData(sad_in_place) [expr ($val & (1 << 30)) != 0]
   set mcpData(plc_cont_slit_dr_cls) [expr ($val & (1 << 29)) != 0]
   set mcpData(plc_cont_slit_dr_opn) [expr ($val & (1 << 28)) != 0]
   set mcpData(mcp_cont_slit_dr_os4) [expr ($val & (1 << 27)) != 0]
   set mcpData(mcp_cont_slit_dr_os3) [expr ($val & (1 << 26)) != 0]
   set mcpData(mcp_cont_slit_dr_os2) [expr ($val & (1 << 25)) != 0]
   set mcpData(mcp_cont_slit_dr_os1) [expr ($val & (1 << 24)) != 0]
   set mcpData(plc_t_bar_tel) [expr ($val & (1 << 23)) != 0]
   set mcpData(plc_t_bar_xport) [expr ($val & (1 << 22)) != 0]
   set mcpData(plc_cont_t_bar_osr) [expr ($val & (1 << 21)) != 0]
   set mcpData(mcp_cont_t_bar_osr) [expr ($val & (1 << 20)) != 0]
   set mcpData(plc_cont_slit_hd_osr) [expr ($val & (1 << 19)) != 0]
   set mcpData(plc_cont_slit_dr_osr) [expr ($val & (1 << 17)) != 0]
   set mcpData(lift_empty) [expr ($val & (1 << 15)) != 0]
   set mcpData(sad_latch_cls) [expr ($val & (1 << 14)) != 0]
   set mcpData(sad_latch_opn) [expr ($val & (1 << 13)) != 0]
   set mcpData(sec_latch_cls) [expr ($val & (1 << 12)) != 0]
   set mcpData(sec_latch_opn) [expr ($val & (1 << 11)) != 0]
   set mcpData(pri_latch_cls) [expr ($val & (1 << 10)) != 0]
   set mcpData(pri_latch_opn) [expr ($val & (1 << 9)) != 0]
   set mcpData(cartg_in_place) [expr ($val & (1 << 8)) != 0]
   set mcpData(cor_not_in_place) [expr ($val & (1 << 7)) != 0]
   set mcpData(cor_in_place) [expr ($val & (1 << 6)) != 0]
   set mcpData(plc_cont_slit_hd_lth) [expr ($val & (1 << 5)) != 0]
   set mcpData(plc_cont_slit_hd_unl) [expr ($val & (1 << 4)) != 0]
   set mcpData(mcp_cont_slit_hd_os4) [expr ($val & (1 << 3)) != 0]
   set mcpData(mcp_cont_slit_hd_os3) [expr ($val & (1 << 2)) != 0]
   set mcpData(mcp_cont_slit_hd_os2) [expr ($val & (1 << 1)) != 0]
   set mcpData(mcp_cont_slit_hd_os1) [expr ($val & (1 << 0)) != 0]
}


proc set_B3_L3 {val} {
   global mcpData

   set mcpData(speed_4) [expr ($val & (1 << 31)) != 0]
   set mcpData(speed_3) [expr ($val & (1 << 30)) != 0]
   set mcpData(speed_2) [expr ($val & (1 << 29)) != 0]
   set mcpData(speed_1) [expr ($val & (1 << 28)) != 0]
   set mcpData(lift_down_enable) [expr ($val & (1 << 27)) != 0]
   set mcpData(lift_up_enable) [expr ($val & (1 << 26)) != 0]
   set mcpData(lift_force_dn_enable) [expr ($val & (1 << 25)) != 0]
   set mcpData(lift_force_up_enable) [expr ($val & (1 << 24)) != 0]
   set mcpData(eng_cam_on_lift_comp) [expr ($val & (1 << 23)) != 0]
   set mcpData(eng_cam_on_lift) [expr ($val & (1 << 22)) != 0]
   set mcpData(cartg_on_lift_comp) [expr ($val & (1 << 21)) != 0]
   set mcpData(cartg_on_lift) [expr ($val & (1 << 20)) != 0]
   set mcpData(cam_on_lift_w_j_hok) [expr ($val & (1 << 19)) != 0]
   set mcpData(cam_on_lift_wo_j_hok) [expr ($val & (1 << 18)) != 0]
   set mcpData(cor_on_lift) [expr ($val & (1 << 17)) != 0]
   set mcpData(auto_mode_enable) [expr ($val & (1 << 16)) != 0]
   set mcpData(flex_io_fault) [expr ($val & (1 << 5)) != 0]
   set mcpData(empty_plate_on_lift) [expr ($val & (1 << 4)) != 0]
   set mcpData(eng_cam_up_in_place) [expr ($val & (1 << 3)) != 0]
   set mcpData(cor_up_in_place) [expr ($val & (1 << 2)) != 0]
   set mcpData(cartg_up_in_place) [expr ($val & (1 << 1)) != 0]
   set mcpData(img_cam_up_in_place) [expr ($val & (1 << 0)) != 0]
}


proc set_B3_L4 {val} {
   global mcpData

   set mcpData(lh_grt_17d5) [expr ($val & (1 << 31)) != 0]
   set mcpData(lh_lim_1d95_18d0) [expr ($val & (1 << 30)) != 0]
   set mcpData(lh_les_2d0) [expr ($val & (1 << 29)) != 0]
   set mcpData(lh_lim_18d0_22d2) [expr ($val & (1 << 28)) != 0]
   set mcpData(lh_lim_18d0_22d0) [expr ($val & (1 << 27)) != 0]
   set mcpData(lh_lim_18d0_20d99) [expr ($val & (1 << 26)) != 0]
   set mcpData(lh_lim_2d5_18d5) [expr ($val & (1 << 25)) != 0]
   set mcpData(lh_lim_18d0_22d75) [expr ($val & (1 << 24)) != 0]
   set mcpData(lh_lim_18d0_22d5) [expr ($val & (1 << 23)) != 0]
   set mcpData(lh_lim_18d0_21d74) [expr ($val & (1 << 22)) != 0]
   set mcpData(lh_lim_2d2_18d5) [expr ($val & (1 << 21)) != 0]
   set mcpData(lh_lim_18d0_23d0) [expr ($val & (1 << 20)) != 0]
   set mcpData(lh_lim_18d0_22d8) [expr ($val & (1 << 19)) != 0]
   set mcpData(lh_lim_18d0_21d89) [expr ($val & (1 << 18)) != 0]
   set mcpData(lh_les_18d5) [expr ($val & (1 << 17)) != 0]
   set mcpData(altitude_at_inst_chg) [expr ($val & (1 << 16)) != 0]
   set mcpData(lh_lim_20d0_21d89) [expr ($val & (1 << 15)) != 0]
   set mcpData(lf_les_350_3) [expr ($val & (1 << 14)) != 0]
   set mcpData(lf_les_150) [expr ($val & (1 << 13)) != 0]
   set mcpData(lf_les_200) [expr ($val & (1 << 12)) != 0]
   set mcpData(lf_les_450) [expr ($val & (1 << 11)) != 0]
   set mcpData(lf_les_350_2) [expr ($val & (1 << 10)) != 0]
   set mcpData(lf_les_1400) [expr ($val & (1 << 9)) != 0]
   set mcpData(lf_les_350) [expr ($val & (1 << 8)) != 0]
   set mcpData(lh_lim_2d0_20d0) [expr ($val & (1 << 7)) != 0]
   set mcpData(lh_lim_0d75_2d0) [expr ($val & (1 << 6)) != 0]
   set mcpData(lf_les_500) [expr ($val & (1 << 5)) != 0]
   set mcpData(lh_les_0d75) [expr ($val & (1 << 4)) != 0]
   set mcpData(lh_les_18d5_2) [expr ($val & (1 << 3)) != 0]
   set mcpData(lh_lim_18d0_22d3) [expr ($val & (1 << 2)) != 0]
   set mcpData(lh_lim_22d3_23d1) [expr ($val & (1 << 1)) != 0]
   set mcpData(lh_grt_23d1) [expr ($val & (1 << 0)) != 0]
}


proc set_B3_L5 {val} {
   global mcpData

   set mcpData(lh_lim_23d1_23d3) [expr ($val & (1 << 31)) != 0]
   set mcpData(lf_les_1100) [expr ($val & (1 << 30)) != 0]
   set mcpData(lh_lim_22d3_23d1_2) [expr ($val & (1 << 29)) != 0]
   set mcpData(lf_les_400_2) [expr ($val & (1 << 28)) != 0]
   set mcpData(lf_les_150_3) [expr ($val & (1 << 27)) != 0]
   set mcpData(lf_les_200_3) [expr ($val & (1 << 26)) != 0]
   set mcpData(lf_les_500_3) [expr ($val & (1 << 25)) != 0]
   set mcpData(lf_les_400) [expr ($val & (1 << 24)) != 0]
   set mcpData(lf_les_1700) [expr ($val & (1 << 23)) != 0]
   set mcpData(lh_lim_21d89_22d3) [expr ($val & (1 << 22)) != 0]
   set mcpData(lf_les_350_5) [expr ($val & (1 << 21)) != 0]
   set mcpData(lf_les_150_2) [expr ($val & (1 << 20)) != 0]
   set mcpData(lf_les_200_2) [expr ($val & (1 << 19)) != 0]
   set mcpData(lf_les_500_2) [expr ($val & (1 << 18)) != 0]
   set mcpData(lf_les_350_4) [expr ($val & (1 << 17)) != 0]
   set mcpData(lf_les_1650) [expr ($val & (1 << 16)) != 0]
   set mcpData(lf_grt_310_2) [expr ($val & (1 << 15)) != 0]
   set mcpData(lf_grt_220_2) [expr ($val & (1 << 14)) != 0]
   set mcpData(lf_grt_150_2) [expr ($val & (1 << 13)) != 0]
   set mcpData(lh_lim_20d0_21d89_2) [expr ($val & (1 << 12)) != 0]
   set mcpData(lf_grt_125) [expr ($val & (1 << 11)) != 0]
   set mcpData(lf_grt_0d0_2) [expr ($val & (1 << 10)) != 0]
   set mcpData(lf_grt_0d0) [expr ($val & (1 << 9)) != 0]
   set mcpData(lf_grt_310) [expr ($val & (1 << 8)) != 0]
   set mcpData(lf_grt_220) [expr ($val & (1 << 7)) != 0]
   set mcpData(lf_grt_1100) [expr ($val & (1 << 6)) != 0]
   set mcpData(lf_grt_150) [expr ($val & (1 << 5)) != 0]
   set mcpData(lh_lim_2d0_20d0_2) [expr ($val & (1 << 4)) != 0]
   set mcpData(lh_lim_0d75_3d0) [expr ($val & (1 << 3)) != 0]
   set mcpData(lf_grt_neg_125) [expr ($val & (1 << 2)) != 0]
   set mcpData(lh_les_0d75_2) [expr ($val & (1 << 1)) != 0]
   set mcpData(lf_les_800) [expr ($val & (1 << 0)) != 0]
}


proc set_B3_L6 {val} {
   global mcpData

   set mcpData(lh_lim_22d89_23d09) [expr ($val & (1 << 31)) != 0]
   set mcpData(lf_grt_950) [expr ($val & (1 << 30)) != 0]
   set mcpData(lh_lim_22d85_23d05) [expr ($val & (1 << 29)) != 0]
   set mcpData(lf_grt_1400) [expr ($val & (1 << 28)) != 0]
   set mcpData(lh_lim_21d8_22d15) [expr ($val & (1 << 27)) != 0]
   set mcpData(lh_lim_22d3_24d0) [expr ($val & (1 << 26)) != 0]
   set mcpData(lf_grt_125_3) [expr ($val & (1 << 25)) != 0]
   set mcpData(lf_grt_0d0_6) [expr ($val & (1 << 24)) != 0]
   set mcpData(lf_grt_0d0_5) [expr ($val & (1 << 23)) != 0]
   set mcpData(lf_grt_310_3) [expr ($val & (1 << 22)) != 0]
   set mcpData(lf_grt_220_3) [expr ($val & (1 << 21)) != 0]
   set mcpData(lf_grt_150_3) [expr ($val & (1 << 20)) != 0]
   set mcpData(lh_lim_21d89_22d3_2) [expr ($val & (1 << 19)) != 0]
   set mcpData(lf_grt_125_2) [expr ($val & (1 << 18)) != 0]
   set mcpData(lf_grt_0d0_4) [expr ($val & (1 << 17)) != 0]
   set mcpData(lf_grt_0d0_3) [expr ($val & (1 << 16)) != 0]
   set mcpData(spare_b3_13_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(im_ff_uv_on_req) [expr ($val & (1 << 14)) != 0]
   set mcpData(im_ff_wht_on_req) [expr ($val & (1 << 13)) != 0]
   set mcpData(alt_bump_dn_delay) [expr ($val & (1 << 12)) != 0]
   set mcpData(alt_bump_up_delay) [expr ($val & (1 << 11)) != 0]
   set mcpData(az_bump_ccw_delay) [expr ($val & (1 << 10)) != 0]
   set mcpData(az_bump_cw_delay) [expr ($val & (1 << 9)) != 0]
   set mcpData(lh_les_6d0_5) [expr ($val & (1 << 8)) != 0]
   set mcpData(lh_les_6d0_4) [expr ($val & (1 << 7)) != 0]
   set mcpData(lh_les_6d0_3) [expr ($val & (1 << 6)) != 0]
   set mcpData(lh_les_6d0_2) [expr ($val & (1 << 5)) != 0]
   set mcpData(lh_les_6d0_1) [expr ($val & (1 << 4)) != 0]
   set mcpData(lh_les_6d0) [expr ($val & (1 << 3)) != 0]
   set mcpData(lf_grt_750) [expr ($val & (1 << 2)) != 0]
   set mcpData(lh_lim_23d04_23d24) [expr ($val & (1 << 1)) != 0]
   set mcpData(lf_grt_950_1) [expr ($val & (1 << 0)) != 0]
}


proc set_B3_L7 {val} {
   global mcpData

   set mcpData(spare_b3_14_15) [expr ($val & (1 << 31)) != 0]
   set mcpData(spare_b3_14_14) [expr ($val & (1 << 30)) != 0]
   set mcpData(spare_b3_14_13) [expr ($val & (1 << 29)) != 0]
   set mcpData(spare_b3_14_12) [expr ($val & (1 << 28)) != 0]
   set mcpData(spare_b3_14_11) [expr ($val & (1 << 27)) != 0]
   set mcpData(spare_b3_14_10) [expr ($val & (1 << 26)) != 0]
   set mcpData(spare_b3_14_9) [expr ($val & (1 << 25)) != 0]
   set mcpData(spare_b3_14_8) [expr ($val & (1 << 24)) != 0]
   set mcpData(spare_b3_14_7) [expr ($val & (1 << 23)) != 0]
   set mcpData(spare_b3_14_6) [expr ($val & (1 << 22)) != 0]
   set mcpData(spare_b3_14_5) [expr ($val & (1 << 21)) != 0]
   set mcpData(spare_b3_14_4) [expr ($val & (1 << 20)) != 0]
   set mcpData(spare_b3_14_3) [expr ($val & (1 << 19)) != 0]
   set mcpData(spare_b3_14_2) [expr ($val & (1 << 18)) != 0]
   set mcpData(spare_b3_14_1) [expr ($val & (1 << 17)) != 0]
   set mcpData(spare_b3_14_0) [expr ($val & (1 << 16)) != 0]
   set mcpData(spare_b3_15_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(spare_b3_15_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(spare_b3_15_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(spare_b3_15_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(spare_b3_15_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(spare_b3_15_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(spare_b3_15_9) [expr ($val & (1 << 9)) != 0]
   set mcpData(spare_b3_15_8) [expr ($val & (1 << 8)) != 0]
   set mcpData(spare_b3_15_7) [expr ($val & (1 << 7)) != 0]
   set mcpData(spare_b3_15_6) [expr ($val & (1 << 6)) != 0]
   set mcpData(spare_b3_15_5) [expr ($val & (1 << 5)) != 0]
   set mcpData(spare_b3_15_4) [expr ($val & (1 << 4)) != 0]
   set mcpData(spare_b3_15_3) [expr ($val & (1 << 3)) != 0]
   set mcpData(spare_b3_15_2) [expr ($val & (1 << 2)) != 0]
   set mcpData(spare_b3_15_1) [expr ($val & (1 << 1)) != 0]
   set mcpData(spare_b3_15_0) [expr ($val & (1 << 0)) != 0]
}


proc set_B3_L8 {val} {
   global mcpData

   set mcpData(spare_b3_16_15) [expr ($val & (1 << 31)) != 0]
   set mcpData(spare_b3_16_14) [expr ($val & (1 << 30)) != 0]
   set mcpData(spare_b3_16_13) [expr ($val & (1 << 29)) != 0]
   set mcpData(spare_b3_16_12) [expr ($val & (1 << 28)) != 0]
   set mcpData(spare_b3_16_11) [expr ($val & (1 << 27)) != 0]
   set mcpData(spare_b3_16_10) [expr ($val & (1 << 26)) != 0]
   set mcpData(spare_b3_16_9) [expr ($val & (1 << 25)) != 0]
   set mcpData(spare_b3_16_8) [expr ($val & (1 << 24)) != 0]
   set mcpData(spare_b3_16_7) [expr ($val & (1 << 23)) != 0]
   set mcpData(spare_b3_16_6) [expr ($val & (1 << 22)) != 0]
   set mcpData(spare_b3_16_5) [expr ($val & (1 << 21)) != 0]
   set mcpData(spare_b3_16_4) [expr ($val & (1 << 20)) != 0]
   set mcpData(spare_b3_16_3) [expr ($val & (1 << 19)) != 0]
   set mcpData(spare_b3_16_2) [expr ($val & (1 << 18)) != 0]
   set mcpData(spare_b3_16_1) [expr ($val & (1 << 17)) != 0]
   set mcpData(spare_b3_16_0) [expr ($val & (1 << 16)) != 0]
   set mcpData(spare_b3_17_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(spare_b3_17_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(spare_b3_17_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(spare_b3_17_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(spare_b3_17_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(spare_b3_17_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(spare_b3_17_9) [expr ($val & (1 << 9)) != 0]
   set mcpData(spare_b3_17_8) [expr ($val & (1 << 8)) != 0]
   set mcpData(spare_b3_17_7) [expr ($val & (1 << 7)) != 0]
   set mcpData(spare_b3_17_6) [expr ($val & (1 << 6)) != 0]
   set mcpData(spare_b3_17_5) [expr ($val & (1 << 5)) != 0]
   set mcpData(spare_b3_17_4) [expr ($val & (1 << 4)) != 0]
   set mcpData(spare_b3_17_3) [expr ($val & (1 << 3)) != 0]
   set mcpData(spare_b3_17_2) [expr ($val & (1 << 2)) != 0]
   set mcpData(spare_b3_17_1) [expr ($val & (1 << 1)) != 0]
   set mcpData(spare_b3_17_0) [expr ($val & (1 << 0)) != 0]
}


proc set_B3_L9 {val} {
   global mcpData

   set mcpData(spare_b3_18_15) [expr ($val & (1 << 31)) != 0]
   set mcpData(spare_b3_18_14) [expr ($val & (1 << 30)) != 0]
   set mcpData(spare_b3_18_13) [expr ($val & (1 << 29)) != 0]
   set mcpData(spare_b3_18_12) [expr ($val & (1 << 28)) != 0]
   set mcpData(spare_b3_18_11) [expr ($val & (1 << 27)) != 0]
   set mcpData(spare_b3_18_10) [expr ($val & (1 << 26)) != 0]
   set mcpData(spare_b3_18_9) [expr ($val & (1 << 25)) != 0]
   set mcpData(spare_b3_18_8) [expr ($val & (1 << 24)) != 0]
   set mcpData(spare_b3_18_7) [expr ($val & (1 << 23)) != 0]
   set mcpData(spare_b3_18_6) [expr ($val & (1 << 22)) != 0]
   set mcpData(spare_b3_18_5) [expr ($val & (1 << 21)) != 0]
   set mcpData(spare_b3_18_4) [expr ($val & (1 << 20)) != 0]
   set mcpData(spare_b3_18_3) [expr ($val & (1 << 19)) != 0]
   set mcpData(spare_b3_18_2) [expr ($val & (1 << 18)) != 0]
   set mcpData(spare_b3_18_1) [expr ($val & (1 << 17)) != 0]
   set mcpData(spare_b3_18_0) [expr ($val & (1 << 16)) != 0]
   set mcpData(spare_b3_19_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(spare_b3_19_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(spare_b3_19_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(spare_b3_19_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(spare_b3_19_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(spare_b3_19_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(spare_b3_19_9) [expr ($val & (1 << 9)) != 0]
   set mcpData(spare_b3_19_8) [expr ($val & (1 << 8)) != 0]
   set mcpData(spare_b3_19_7) [expr ($val & (1 << 7)) != 0]
   set mcpData(spare_b3_19_6) [expr ($val & (1 << 6)) != 0]
   set mcpData(spare_b3_19_5) [expr ($val & (1 << 5)) != 0]
   set mcpData(spare_b3_19_4) [expr ($val & (1 << 4)) != 0]
   set mcpData(spare_b3_19_3) [expr ($val & (1 << 3)) != 0]
   set mcpData(spare_b3_19_2) [expr ($val & (1 << 2)) != 0]
   set mcpData(spare_b3_19_1) [expr ($val & (1 << 1)) != 0]
   set mcpData(spare_b3_19_0) [expr ($val & (1 << 0)) != 0]
}


proc set_B10_L0 {val} {
   global mcpData

   set mcpData(mcp_clamp_engage_cmd) [expr ($val & (1 << 31)) != 0]
   set mcpData(mcp_alt_brk_en_cmd) [expr ($val & (1 << 30)) != 0]
   set mcpData(mcp_alt_brk_dis_cmd) [expr ($val & (1 << 29)) != 0]
   set mcpData(mcp_az_brk_en_cmd) [expr ($val & (1 << 28)) != 0]
   set mcpData(mcp_az_brk_dis_cmd) [expr ($val & (1 << 27)) != 0]
   set mcpData(mcp_solenoid_engage) [expr ($val & (1 << 26)) != 0]
   set mcpData(mcp_pump_on) [expr ($val & (1 << 25)) != 0]
   set mcpData(mcp_lift_dn_4) [expr ($val & (1 << 24)) != 0]
   set mcpData(mcp_lift_dn_3) [expr ($val & (1 << 23)) != 0]
   set mcpData(mcp_lift_dn_2) [expr ($val & (1 << 22)) != 0]
   set mcpData(mcp_lift_dn_1) [expr ($val & (1 << 21)) != 0]
   set mcpData(mcp_lift_up_1) [expr ($val & (1 << 20)) != 0]
   set mcpData(mcp_lift_up_2) [expr ($val & (1 << 19)) != 0]
   set mcpData(mcp_lift_up_3) [expr ($val & (1 << 18)) != 0]
   set mcpData(mcp_lift_up_4) [expr ($val & (1 << 17)) != 0]
   set mcpData(mcp_lift_high_psi) [expr ($val & (1 << 16)) != 0]
   set mcpData(mcp_ff_screen_enable) [expr ($val & (1 << 15)) != 0]
   set mcpData(mcp_hgcd_lamp_on_cmd) [expr ($val & (1 << 14)) != 0]
   set mcpData(mcp_ne_lamp_on_cmd) [expr ($val & (1 << 13)) != 0]
   set mcpData(mcp_ff_lamp_on_cmd) [expr ($val & (1 << 12)) != 0]
   set mcpData(mcp_ff_scrn_opn_cmd) [expr ($val & (1 << 11)) != 0]
   set mcpData(mcp_slit_latch2_cmd) [expr ($val & (1 << 10)) != 0]
   set mcpData(mcp_slit_dr2_cls_cmd) [expr ($val & (1 << 9)) != 0]
   set mcpData(mcp_slit_dr2_opn_cmd) [expr ($val & (1 << 8)) != 0]
   set mcpData(mcp_slit_latch1_cmd) [expr ($val & (1 << 7)) != 0]
   set mcpData(mcp_slit_dr1_cls_cmd) [expr ($val & (1 << 6)) != 0]
   set mcpData(mcp_slit_dr1_opn_cmd) [expr ($val & (1 << 5)) != 0]
   set mcpData(mcp_umbilical_on_off) [expr ($val & (1 << 4)) != 0]
   set mcpData(mcp_umbilical_up_dn) [expr ($val & (1 << 3)) != 0]
   set mcpData(mcp_15deg_stop_ret_c) [expr ($val & (1 << 2)) != 0]
   set mcpData(mcp_15deg_stop_ext_c) [expr ($val & (1 << 1)) != 0]
   set mcpData(mcp_clamp_disen_cmd) [expr ($val & (1 << 0)) != 0]
}


proc set_B10_L1 {val} {
   global mcpData

   set mcpData(mcp_im_ff_uv_req) [expr ($val & (1 << 31)) != 0]
   set mcpData(mcp_im_ff_wht_req) [expr ($val & (1 << 30)) != 0]
   set mcpData(mcp_umbilical_fast) [expr ($val & (1 << 29)) != 0]
   set mcpData(mcp_ff_screen2_enabl) [expr ($val & (1 << 28)) != 0]
   set mcpData(mcp_ff_scrn2_opn_cmd) [expr ($val & (1 << 27)) != 0]
   set mcpData(mcp_inst_chg_alert) [expr ($val & (1 << 26)) != 0]
   set mcpData(mcp_inst_chg_prompt) [expr ($val & (1 << 25)) != 0]
   set mcpData(mcp_sad_latch_opn_cm) [expr ($val & (1 << 24)) != 0]
   set mcpData(mcp_sad_latch_cls_cm) [expr ($val & (1 << 23)) != 0]
   set mcpData(mcp_sec_latch_opn_cm) [expr ($val & (1 << 22)) != 0]
   set mcpData(mcp_sec_latch_cls_cm) [expr ($val & (1 << 21)) != 0]
   set mcpData(mcp_pri_latch_opn_cm) [expr ($val & (1 << 20)) != 0]
   set mcpData(mcp_pri_latch_cls_cm) [expr ($val & (1 << 19)) != 0]
   set mcpData(mcp_purge_cell_on) [expr ($val & (1 << 18)) != 0]
   set mcpData(mcp_t_bar_tel) [expr ($val & (1 << 17)) != 0]
   set mcpData(mcp_t_bar_xport) [expr ($val & (1 << 16)) != 0]
   set mcpData(velocity_trp_rst_in) [expr ($val & (1 << 0)) != 0]
}


proc set_I1_L0 {val} {
   global mcpData

   set mcpData(rack_0_grp_0_bit_15) [expr ($val & (1 << 31)) != 0]
   set mcpData(az_bump_ccw) [expr ($val & (1 << 30)) != 0]
   set mcpData(az_bump_cw) [expr ($val & (1 << 29)) != 0]
   set mcpData(rack_0_grp_0_bit_12) [expr ($val & (1 << 28)) != 0]
   set mcpData(ops_cart_in_pos) [expr ($val & (1 << 27)) != 0]
   set mcpData(fiber_cart_pos2) [expr ($val & (1 << 26)) != 0]
   set mcpData(fiber_cart_pos1) [expr ($val & (1 << 25)) != 0]
   set mcpData(inst_lift_low_force) [expr ($val & (1 << 24)) != 0]
   set mcpData(inst_lift_high_force) [expr ($val & (1 << 23)) != 0]
   set mcpData(inst_lift_man) [expr ($val & (1 << 22)) != 0]
   set mcpData(inst_lift_dn) [expr ($val & (1 << 21)) != 0]
   set mcpData(inst_lift_sw4) [expr ($val & (1 << 20)) != 0]
   set mcpData(inst_lift_sw3) [expr ($val & (1 << 19)) != 0]
   set mcpData(inst_lift_sw2) [expr ($val & (1 << 18)) != 0]
   set mcpData(inst_lift_sw1) [expr ($val & (1 << 17)) != 0]
   set mcpData(inst_lift_pump_on) [expr ($val & (1 << 16)) != 0]
   set mcpData(low_lvl_light_req) [expr ($val & (1 << 15)) != 0]
   set mcpData(rack_0_grp_1_bit_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(rack_0_grp_1_bit_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(rack_0_grp_1_bit_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(rack_0_grp_1_bit_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(rack_0_grp_1_bit_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(rack_0_grp_1_bit_9) [expr ($val & (1 << 9)) != 0]
   set mcpData(rack_0_grp_1_bit_8) [expr ($val & (1 << 8)) != 0]
   set mcpData(rack_0_grp_1_bit_7) [expr ($val & (1 << 7)) != 0]
   set mcpData(optical_bench_cls) [expr ($val & (1 << 6)) != 0]
   set mcpData(optical_bench_opn) [expr ($val & (1 << 5)) != 0]
   set mcpData(ops_cart_in_house) [expr ($val & (1 << 4)) != 0]
   set mcpData(dog_house_door_cls) [expr ($val & (1 << 3)) != 0]
   set mcpData(dog_house_door_opn) [expr ($val & (1 << 2)) != 0]
   set mcpData(dog_house_ccw_pad) [expr ($val & (1 << 1)) != 0]
   set mcpData(dog_house_cw_pad) [expr ($val & (1 << 0)) != 0]
}


proc set_I1_L1 {val} {
   global mcpData

   set mcpData(spare_i1_l1) [expr ($val & (1 << 31)) != 0]
}


proc set_I1_L2 {val} {
   global mcpData

   set mcpData(spare_i1_l2) [expr ($val & (1 << 31)) != 0]
}


proc set_I1_L3 {val} {
   global mcpData

   set mcpData(spare_i1_l3) [expr ($val & (1 << 31)) != 0]
}


proc set_I1_L4 {val} {
   global mcpData

   set mcpData(open_slit_doors) [expr ($val & (1 << 31)) != 0]
   set mcpData(close_slit_doors) [expr ($val & (1 << 30)) != 0]
   set mcpData(inst_chg_remove_sw) [expr ($val & (1 << 29)) != 0]
   set mcpData(inst_chg_install_sw) [expr ($val & (1 << 28)) != 0]
   set mcpData(man_mode_switch) [expr ($val & (1 << 27)) != 0]
   set mcpData(auto_mode_sw) [expr ($val & (1 << 26)) != 0]
   set mcpData(off_mode_sw) [expr ($val & (1 << 25)) != 0]
   set mcpData(iclb_leds_on_cmd) [expr ($val & (1 << 24)) != 0]
   set mcpData(sad_man_valve_cls) [expr ($val & (1 << 23)) != 0]
   set mcpData(sec_man_valve_cls) [expr ($val & (1 << 22)) != 0]
   set mcpData(inst_man_valve_cls) [expr ($val & (1 << 21)) != 0]
   set mcpData(ilcb_pres_good) [expr ($val & (1 << 20)) != 0]
   set mcpData(rot_pos_370_ccw) [expr ($val & (1 << 19)) != 0]
   set mcpData(rot_neg_190_cw) [expr ($val & (1 << 18)) != 0]
   set mcpData(rot_inst_chg_b) [expr ($val & (1 << 17)) != 0]
   set mcpData(rot_inst_chg_a) [expr ($val & (1 << 16)) != 0]
   set mcpData(rack_1_grp_1_bit_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(rack_1_grp_1_bit_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(rack_1_grp_1_bit_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(rack_1_grp_1_bit_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(rack_1_grp_1_bit_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(rack_1_grp_1_bit_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(rack_1_grp_1_bit_9) [expr ($val & (1 << 9)) != 0]
   set mcpData(rack_1_grp_1_bit_8) [expr ($val & (1 << 8)) != 0]
   set mcpData(rack_1_grp_1_bit_7) [expr ($val & (1 << 7)) != 0]
   set mcpData(rack_1_grp_1_bit_6) [expr ($val & (1 << 6)) != 0]
   set mcpData(rack_1_grp_1_bit_5) [expr ($val & (1 << 5)) != 0]
   set mcpData(rack_1_grp_1_bit_4) [expr ($val & (1 << 4)) != 0]
   set mcpData(tbar_latch_tel_cmd) [expr ($val & (1 << 3)) != 0]
   set mcpData(tbar_latch_xport_cmd) [expr ($val & (1 << 2)) != 0]
   set mcpData(slit_latch_lth_cmd) [expr ($val & (1 << 1)) != 0]
   set mcpData(slit_latch_unlth_cmd) [expr ($val & (1 << 0)) != 0]
}


proc set_I1_L5 {val} {
   global mcpData

   set mcpData(spare_i1_l5) [expr ($val & (1 << 31)) != 0]
}


proc set_I1_L6 {val} {
   global mcpData

   set mcpData(spare_i1_l6) [expr ($val & (1 << 31)) != 0]
}


proc set_I1_L7 {val} {
   global mcpData

   set mcpData(spare_i1_l7) [expr ($val & (1 << 31)) != 0]
}


proc set_I1_L8 {val} {
   global mcpData

   set mcpData(rack_2_grp_0_bit_15) [expr ($val & (1 << 31)) != 0]
   set mcpData(spec_autofill_on) [expr ($val & (1 << 30)) != 0]
   set mcpData(spec_lens2) [expr ($val & (1 << 29)) != 0]
   set mcpData(spec_lens1) [expr ($val & (1 << 28)) != 0]
   set mcpData(inst_id3_4) [expr ($val & (1 << 27)) != 0]
   set mcpData(inst_id3_3) [expr ($val & (1 << 26)) != 0]
   set mcpData(inst_id3_2) [expr ($val & (1 << 25)) != 0]
   set mcpData(inst_id3_1) [expr ($val & (1 << 24)) != 0]
   set mcpData(inst_id2_4) [expr ($val & (1 << 23)) != 0]
   set mcpData(inst_id2_3) [expr ($val & (1 << 22)) != 0]
   set mcpData(inst_id2_2) [expr ($val & (1 << 21)) != 0]
   set mcpData(inst_id2_1) [expr ($val & (1 << 20)) != 0]
   set mcpData(inst_id1_4) [expr ($val & (1 << 19)) != 0]
   set mcpData(inst_id1_3) [expr ($val & (1 << 18)) != 0]
   set mcpData(inst_id1_2) [expr ($val & (1 << 17)) != 0]
   set mcpData(inst_id1_1) [expr ($val & (1 << 16)) != 0]
   set mcpData(safety_latch2_cls) [expr ($val & (1 << 15)) != 0]
   set mcpData(safety_latch2_opn) [expr ($val & (1 << 14)) != 0]
   set mcpData(safety_latch1_cls) [expr ($val & (1 << 13)) != 0]
   set mcpData(safety_latch1_opn) [expr ($val & (1 << 12)) != 0]
   set mcpData(sec_latch3_cls) [expr ($val & (1 << 11)) != 0]
   set mcpData(sec_latch3_opn) [expr ($val & (1 << 10)) != 0]
   set mcpData(sec_latch2_cls) [expr ($val & (1 << 9)) != 0]
   set mcpData(sec_latch2_opn) [expr ($val & (1 << 8)) != 0]
   set mcpData(sec_latch1_cls) [expr ($val & (1 << 7)) != 0]
   set mcpData(sec_latch1_opn) [expr ($val & (1 << 6)) != 0]
   set mcpData(pri_latch3_cls) [expr ($val & (1 << 5)) != 0]
   set mcpData(pri_latch3_opn) [expr ($val & (1 << 4)) != 0]
   set mcpData(pri_latch2_cls) [expr ($val & (1 << 3)) != 0]
   set mcpData(pri_latch2_opn) [expr ($val & (1 << 2)) != 0]
   set mcpData(pri_latch1_cls) [expr ($val & (1 << 1)) != 0]
   set mcpData(pri_latch1_opn) [expr ($val & (1 << 0)) != 0]
}


proc set_I1_L9 {val} {
   global mcpData

   set mcpData(rack_2_grp_2_bit_15) [expr ($val & (1 << 31)) != 0]
   set mcpData(rack_2_grp_2_bit_14) [expr ($val & (1 << 30)) != 0]
   set mcpData(slit_head_2_in_place) [expr ($val & (1 << 29)) != 0]
   set mcpData(slit_head_latch2_ext) [expr ($val & (1 << 28)) != 0]
   set mcpData(slit_head_door2_cls) [expr ($val & (1 << 27)) != 0]
   set mcpData(slit_head_door2_opn) [expr ($val & (1 << 26)) != 0]
   set mcpData(slit_head_1_in_place) [expr ($val & (1 << 25)) != 0]
   set mcpData(slit_head_latch1_ext) [expr ($val & (1 << 24)) != 0]
   set mcpData(slit_head_door1_cls) [expr ($val & (1 << 23)) != 0]
   set mcpData(slit_head_door1_opn) [expr ($val & (1 << 22)) != 0]
   set mcpData(sad_mount2) [expr ($val & (1 << 21)) != 0]
   set mcpData(sad_mount1) [expr ($val & (1 << 20)) != 0]
   set mcpData(sad_latch2_cls) [expr ($val & (1 << 19)) != 0]
   set mcpData(sad_latch2_opn) [expr ($val & (1 << 18)) != 0]
   set mcpData(sad_latch1_cls) [expr ($val & (1 << 17)) != 0]
   set mcpData(sad_latch1_opn) [expr ($val & (1 << 16)) != 0]
}


proc set_I1_L10 {val} {
   global mcpData

   set mcpData(rack_2_grp_4_bit_15) [expr ($val & (1 << 31)) != 0]
   set mcpData(rack_2_grp_4_bit_14) [expr ($val & (1 << 30)) != 0]
   set mcpData(rack_2_grp_4_bit_13) [expr ($val & (1 << 29)) != 0]
   set mcpData(rack_2_grp_4_bit_12) [expr ($val & (1 << 28)) != 0]
   set mcpData(rack_2_grp_4_bit_11) [expr ($val & (1 << 27)) != 0]
   set mcpData(rack_2_grp_4_bit_10) [expr ($val & (1 << 26)) != 0]
   set mcpData(rack_2_grp_4_bit_9) [expr ($val & (1 << 25)) != 0]
   set mcpData(rack_2_grp_4_bit_8) [expr ($val & (1 << 24)) != 0]
   set mcpData(rack_2_grp_4_bit_7) [expr ($val & (1 << 23)) != 0]
   set mcpData(rack_2_grp_4_bit_6) [expr ($val & (1 << 22)) != 0]
   set mcpData(rack_2_grp_4_bit_5) [expr ($val & (1 << 21)) != 0]
   set mcpData(rack_2_grp_4_bit_4) [expr ($val & (1 << 20)) != 0]
   set mcpData(sec_mir_force_limits) [expr ($val & (1 << 19)) != 0]
   set mcpData(alt_bump_dn) [expr ($val & (1 << 18)) != 0]
   set mcpData(alt_bump_up) [expr ($val & (1 << 17)) != 0]
   set mcpData(purge_air_pressur_sw) [expr ($val & (1 << 16)) != 0]
}


proc set_I1_L11 {val} {
   global mcpData

   set mcpData(spare_i1_l11) [expr ($val & (1 << 31)) != 0]
}


proc set_I1_L12 {val} {
   global mcpData

   set mcpData(spare_i1_l12) [expr ($val & (1 << 31)) != 0]
   set mcpData(rack_3_grp_1_bit_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(rack_3_grp_1_bit_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(rack_3_grp_1_bit_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(rack_3_grp_1_bit_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(rack_3_grp_1_bit_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(rack_3_grp_1_bit_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(man_lift_dn_4) [expr ($val & (1 << 9)) != 0]
   set mcpData(man_lift_dn_3) [expr ($val & (1 << 8)) != 0]
   set mcpData(man_lift_dn_2) [expr ($val & (1 << 7)) != 0]
   set mcpData(man_lift_dn_1) [expr ($val & (1 << 6)) != 0]
   set mcpData(man_lift_up_4) [expr ($val & (1 << 5)) != 0]
   set mcpData(man_lift_up_3) [expr ($val & (1 << 4)) != 0]
   set mcpData(man_lift_up_2) [expr ($val & (1 << 3)) != 0]
   set mcpData(man_lift_up_1) [expr ($val & (1 << 2)) != 0]
   set mcpData(inst_lift_auto) [expr ($val & (1 << 1)) != 0]
   set mcpData(rack_3_grp_1_bit_0) [expr ($val & (1 << 0)) != 0]
}


proc set_I1_L13 {val} {
   global mcpData

   set mcpData(leaf_8_closed_stat) [expr ($val & (1 << 31)) != 0]
   set mcpData(leaf_8_open_stat) [expr ($val & (1 << 30)) != 0]
   set mcpData(leaf_7_closed_stat) [expr ($val & (1 << 29)) != 0]
   set mcpData(leaf_7_open_stat) [expr ($val & (1 << 28)) != 0]
   set mcpData(leaf_6_closed_stat) [expr ($val & (1 << 27)) != 0]
   set mcpData(leaf_6_open_stat) [expr ($val & (1 << 26)) != 0]
   set mcpData(leaf_5_closed_stat) [expr ($val & (1 << 25)) != 0]
   set mcpData(leaf_5_open_stat) [expr ($val & (1 << 24)) != 0]
   set mcpData(leaf_4_closed_stat) [expr ($val & (1 << 23)) != 0]
   set mcpData(leaf_4_open_stat) [expr ($val & (1 << 22)) != 0]
   set mcpData(leaf_3_closed_stat) [expr ($val & (1 << 21)) != 0]
   set mcpData(leaf_3_open_stat) [expr ($val & (1 << 20)) != 0]
   set mcpData(leaf_2_closed_stat) [expr ($val & (1 << 19)) != 0]
   set mcpData(leaf_2_open_stat) [expr ($val & (1 << 18)) != 0]
   set mcpData(leaf_1_closed_stat) [expr ($val & (1 << 17)) != 0]
   set mcpData(leaf_1_open_stat) [expr ($val & (1 << 16)) != 0]
   set mcpData(rack_3_grp_3_bit_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(rack_3_grp_3_bit_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(rack_3_grp_3_bit_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(rack_3_grp_3_bit_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(hgcd_4_stat) [expr ($val & (1 << 11)) != 0]
   set mcpData(hgcd_3_stat) [expr ($val & (1 << 10)) != 0]
   set mcpData(hgcd_2_stat) [expr ($val & (1 << 9)) != 0]
   set mcpData(hgcd_1_stat) [expr ($val & (1 << 8)) != 0]
   set mcpData(ne_4_stat) [expr ($val & (1 << 7)) != 0]
   set mcpData(ne_3_stat) [expr ($val & (1 << 6)) != 0]
   set mcpData(ne_2_stat) [expr ($val & (1 << 5)) != 0]
   set mcpData(ne_1_stat) [expr ($val & (1 << 4)) != 0]
   set mcpData(ff_4_stat) [expr ($val & (1 << 3)) != 0]
   set mcpData(ff_3_stat) [expr ($val & (1 << 2)) != 0]
   set mcpData(ff_2_stat) [expr ($val & (1 << 1)) != 0]
   set mcpData(ff_1_stat) [expr ($val & (1 << 0)) != 0]
}


proc set_I1_L14 {val} {
   global mcpData

   set mcpData(rack_3_grp_4_bit_15) [expr ($val & (1 << 31)) != 0]
   set mcpData(rack_3_grp_4_bit_14) [expr ($val & (1 << 30)) != 0]
   set mcpData(rack_3_grp_4_bit_13) [expr ($val & (1 << 29)) != 0]
   set mcpData(rack_3_grp_4_bit_12) [expr ($val & (1 << 28)) != 0]
   set mcpData(rack_3_grp_4_bit_11) [expr ($val & (1 << 27)) != 0]
   set mcpData(rack_3_grp_4_bit_10) [expr ($val & (1 << 26)) != 0]
   set mcpData(rack_3_grp_4_bit_9) [expr ($val & (1 << 25)) != 0]
   set mcpData(rack_3_grp_4_bit_8) [expr ($val & (1 << 24)) != 0]
   set mcpData(man_im_ff_uv_req) [expr ($val & (1 << 23)) != 0]
   set mcpData(man_im_ff_wht_req) [expr ($val & (1 << 22)) != 0]
   set mcpData(ff_man_cont_enable) [expr ($val & (1 << 21)) != 0]
   set mcpData(man_hgcd_lamp_on_cmd) [expr ($val & (1 << 20)) != 0]
   set mcpData(man_ne_lamp_on_cmd) [expr ($val & (1 << 19)) != 0]
   set mcpData(man_ff_lamp_on_cmd) [expr ($val & (1 << 18)) != 0]
   set mcpData(man_ff_scrn_en_cmd) [expr ($val & (1 << 17)) != 0]
   set mcpData(man_ff_scrn_opn_cmd) [expr ($val & (1 << 16)) != 0]
}


proc set_I1_L15 {val} {
   global mcpData

   set mcpData(spare_i1_l15) [expr ($val & (1 << 31)) != 0]
}


proc set_I2_L0 {val} {
   global mcpData

   set mcpData(spare) [expr ($val & (1 << 15)) != 0]
   set mcpData(wind_alt_perm) [expr ($val & (1 << 5)) != 0]
   set mcpData(wind_az_perm) [expr ($val & (1 << 4)) != 0]
   set mcpData(wind_alt1_fault) [expr ($val & (1 << 3)) != 0]
   set mcpData(wind_az3_fault) [expr ($val & (1 << 2)) != 0]
   set mcpData(wind_az2_fault) [expr ($val & (1 << 1)) != 0]
   set mcpData(wind_az1_fault) [expr ($val & (1 << 0)) != 0]
}


proc set_I2_L1 {val} {
   global mcpData

}


proc set_I2_L2 {val} {
   global mcpData

}


proc set_I2_L3 {val} {
   global mcpData

}


proc set_I2_L4 {val} {
   global mcpData

}


proc set_I2_L5 {val} {
   global mcpData

}


proc set_I2_L6 {val} {
   global mcpData

}


proc set_I2_L7 {val} {
   global mcpData

}


proc set_I3_L0 {val} {
   global mcpData

}


proc set_I3_L1 {val} {
   global mcpData

}


proc set_I3_L2 {val} {
   global mcpData

}


proc set_I3_L3 {val} {
   global mcpData

}


proc set_I4_L0 {val} {
   global mcpData

}


proc set_I4_L1 {val} {
   global mcpData

}


proc set_I4_L2 {val} {
   global mcpData

}


proc set_I4_L3 {val} {
   global mcpData

}


proc set_I5_L0 {val} {
   global mcpData

}


proc set_I5_L1 {val} {
   global mcpData

}


proc set_I5_L2 {val} {
   global mcpData

}


proc set_I5_L3 {val} {
   global mcpData

}


proc set_I6_L0 {val} {
   global mcpData

   set mcpData(mcp_watchdog_timer) [expr ($val & (1 << 31)) != 0]
   set mcpData(nw_fork_stop) [expr ($val & (1 << 30)) != 0]
   set mcpData(s_wind_stop) [expr ($val & (1 << 29)) != 0]
   set mcpData(w_lower_stop) [expr ($val & (1 << 28)) != 0]
   set mcpData(e_lower_stop) [expr ($val & (1 << 27)) != 0]
   set mcpData(s_lower_stop) [expr ($val & (1 << 26)) != 0]
   set mcpData(n_lower_stop) [expr ($val & (1 << 25)) != 0]
   set mcpData(w_rail_stop) [expr ($val & (1 << 24)) != 0]
   set mcpData(s_rail_stop) [expr ($val & (1 << 23)) != 0]
   set mcpData(n_rail_stop) [expr ($val & (1 << 22)) != 0]
   set mcpData(n_fork_stop) [expr ($val & (1 << 21)) != 0]
   set mcpData(n_wind_stop) [expr ($val & (1 << 20)) != 0]
   set mcpData(fiber_signal_loss) [expr ($val & (1 << 19)) != 0]
   set mcpData(spare_s1_c2) [expr ($val & (1 << 18)) != 0]
   set mcpData(cr_stop) [expr ($val & (1 << 17)) != 0]
   set mcpData(tcc_stop) [expr ($val & (1 << 16)) != 0]
   set mcpData(az_stow_3b) [expr ($val & (1 << 15)) != 0]
   set mcpData(wind_az_plc_perm_in) [expr ($val & (1 << 14)) != 0]
   set mcpData(az_plc_perm_in) [expr ($val & (1 << 13)) != 0]
   set mcpData(wind_az_mtr_perm_in) [expr ($val & (1 << 12)) != 0]
   set mcpData(az_mtr2_perm_in) [expr ($val & (1 << 11)) != 0]
   set mcpData(az_mtr1_perm_in) [expr ($val & (1 << 10)) != 0]
   set mcpData(az_mtr_ccw_perm_in) [expr ($val & (1 << 9)) != 0]
   set mcpData(az_mtr_cw_perm_in) [expr ($val & (1 << 8)) != 0]
   set mcpData(az_stow_3a) [expr ($val & (1 << 7)) != 0]
   set mcpData(wind_alt_plc_perm_in) [expr ($val & (1 << 6)) != 0]
   set mcpData(alt_plc_perm_in) [expr ($val & (1 << 5)) != 0]
   set mcpData(wind_alt_mtr_perm_in) [expr ($val & (1 << 4)) != 0]
   set mcpData(alt_mtr2_perm_in) [expr ($val & (1 << 3)) != 0]
   set mcpData(alt_mtr1_perm_in) [expr ($val & (1 << 2)) != 0]
   set mcpData(alt_mtr_dn_perm_in) [expr ($val & (1 << 1)) != 0]
   set mcpData(alt_mtr_up_perm_in) [expr ($val & (1 << 0)) != 0]
}


proc set_I7_L0 {val} {
   global mcpData

   set mcpData(az_stow_1b) [expr ($val & (1 << 31)) != 0]
   set mcpData(az_stow_1a) [expr ($val & (1 << 30)) != 0]
   set mcpData(alt_grt_18d6_limit_1) [expr ($val & (1 << 29)) != 0]
   set mcpData(az_109_131_limit_1) [expr ($val & (1 << 28)) != 0]
   set mcpData(bldg_on_alt) [expr ($val & (1 << 27)) != 0]
   set mcpData(alt_les_90d5_limit) [expr ($val & (1 << 26)) != 0]
   set mcpData(alt_locking_pin_out) [expr ($val & (1 << 25)) != 0]
   set mcpData(alt_grt_0d3_limit) [expr ($val & (1 << 24)) != 0]
   set mcpData(alt_les_2d5_limit) [expr ($val & (1 << 23)) != 0]
   set mcpData(hatch_cls) [expr ($val & (1 << 22)) != 0]
   set mcpData(rot_plc_perm_in) [expr ($val & (1 << 21)) != 0]
   set mcpData(bldg_perm_in) [expr ($val & (1 << 20)) != 0]
   set mcpData(spare_s5_c3) [expr ($val & (1 << 19)) != 0]
   set mcpData(rot_mtr_perm_in) [expr ($val & (1 << 18)) != 0]
   set mcpData(rot_mtr_ccw_perm_in) [expr ($val & (1 << 17)) != 0]
   set mcpData(rot_mtr_cw_perm_in) [expr ($val & (1 << 16)) != 0]
   set mcpData(spare_s8_c7) [expr ($val & (1 << 15)) != 0]
   set mcpData(spare_s8_c6) [expr ($val & (1 << 14)) != 0]
   set mcpData(az_pos_445b_ccw) [expr ($val & (1 << 13)) != 0]
   set mcpData(az_neg_201b_cw) [expr ($val & (1 << 12)) != 0]
   set mcpData(az_pos_445a_ccw) [expr ($val & (1 << 11)) != 0]
   set mcpData(az_neg_201a_cw) [expr ($val & (1 << 10)) != 0]
   set mcpData(az_dir_ccw) [expr ($val & (1 << 9)) != 0]
   set mcpData(az_dir_cw) [expr ($val & (1 << 8)) != 0]
   set mcpData(alt_velocity_limit) [expr ($val & (1 << 7)) != 0]
   set mcpData(alt_slip) [expr ($val & (1 << 6)) != 0]
   set mcpData(alt_grt_18d6_limit_2) [expr ($val & (1 << 5)) != 0]
   set mcpData(deg_15_stop_ext) [expr ($val & (1 << 4)) != 0]
   set mcpData(az_stow_2b) [expr ($val & (1 << 3)) != 0]
   set mcpData(az_stow_2a) [expr ($val & (1 << 2)) != 0]
   set mcpData(bldg_clear_alt) [expr ($val & (1 << 1)) != 0]
   set mcpData(alt_grt_83_limit_1) [expr ($val & (1 << 0)) != 0]
}


proc set_I8_L0 {val} {
   global mcpData

   set mcpData(rot_velocity_limit) [expr ($val & (1 << 31)) != 0]
   set mcpData(rot_slip) [expr ($val & (1 << 30)) != 0]
   set mcpData(rot_pos_380b_ccw) [expr ($val & (1 << 29)) != 0]
   set mcpData(rot_neg_200b_cw) [expr ($val & (1 << 28)) != 0]
   set mcpData(rot_pos_380a_ccw) [expr ($val & (1 << 27)) != 0]
   set mcpData(rot_neg_200a_cw) [expr ($val & (1 << 26)) != 0]
   set mcpData(rot_dir_ccw) [expr ($val & (1 << 25)) != 0]
   set mcpData(rot_dir_cw) [expr ($val & (1 << 24)) != 0]
   set mcpData(az_velocity_limit) [expr ($val & (1 << 23)) != 0]
   set mcpData(az_slip) [expr ($val & (1 << 22)) != 0]
   set mcpData(spare_s9_c5) [expr ($val & (1 << 21)) != 0]
   set mcpData(bldg_clear_az) [expr ($val & (1 << 20)) != 0]
   set mcpData(alt_grt_83_limit_2) [expr ($val & (1 << 19)) != 0]
   set mcpData(az_109_131_limit_2) [expr ($val & (1 << 18)) != 0]
   set mcpData(bldg_on_az) [expr ($val & (1 << 17)) != 0]
   set mcpData(alt_grt_18d6_limit_3) [expr ($val & (1 << 16)) != 0]
   set mcpData(t_bar_xport_stat) [expr ($val & (1 << 15)) != 0]
   set mcpData(in_8_bit_30_spare) [expr ($val & (1 << 14)) != 0]
   set mcpData(in_8_bit_29_spare) [expr ($val & (1 << 13)) != 0]
   set mcpData(in_8_bit_28_spare) [expr ($val & (1 << 12)) != 0]
   set mcpData(deg_15_stop_ret) [expr ($val & (1 << 11)) != 0]
   set mcpData(e_stop_byp_sw) [expr ($val & (1 << 10)) != 0]
   set mcpData(umbilical_strain_sw) [expr ($val & (1 << 9)) != 0]
   set mcpData(rot_mtr_rdy) [expr ($val & (1 << 8)) != 0]
   set mcpData(alt_mtr2_rdy) [expr ($val & (1 << 7)) != 0]
   set mcpData(alt_mtr1_rdy) [expr ($val & (1 << 6)) != 0]
   set mcpData(az_mtr2_rdy) [expr ($val & (1 << 5)) != 0]
   set mcpData(az_mtr1_rdy) [expr ($val & (1 << 4)) != 0]
   set mcpData(az_pos_440_ccw) [expr ($val & (1 << 3)) != 0]
   set mcpData(az_neg_196_cw) [expr ($val & (1 << 2)) != 0]
   set mcpData(az_110_130_limit) [expr ($val & (1 << 1)) != 0]
   set mcpData(az_stow_cntr_sw) [expr ($val & (1 << 0)) != 0]
}


proc set_I9_L0 {val} {
   global mcpData

   set mcpData(in_9_bit_15_spare) [expr ($val & (1 << 31)) != 0]
   set mcpData(in_9_bit_14_spare) [expr ($val & (1 << 30)) != 0]
   set mcpData(in_9_bit_13_spare) [expr ($val & (1 << 29)) != 0]
   set mcpData(in_9_bit_12_spare) [expr ($val & (1 << 28)) != 0]
   set mcpData(in_9_bit_11_spare) [expr ($val & (1 << 27)) != 0]
   set mcpData(in_9_bit_10_spare) [expr ($val & (1 << 26)) != 0]
   set mcpData(alt_locking_pin_in) [expr ($val & (1 << 25)) != 0]
   set mcpData(solenoid_engage_sw) [expr ($val & (1 << 24)) != 0]
   set mcpData(low_lvl_lighting_req) [expr ($val & (1 << 23)) != 0]
   set mcpData(alt_brake_dis_stat) [expr ($val & (1 << 22)) != 0]
   set mcpData(alt_brake_en_stat) [expr ($val & (1 << 21)) != 0]
   set mcpData(az_brake_dis_stat) [expr ($val & (1 << 20)) != 0]
   set mcpData(az_brake_en_stat) [expr ($val & (1 << 19)) != 0]
   set mcpData(clamp_dis_stat) [expr ($val & (1 << 18)) != 0]
   set mcpData(clamp_en_stat) [expr ($val & (1 << 17)) != 0]
   set mcpData(t_bar_tel_stat) [expr ($val & (1 << 16)) != 0]
   set mcpData(s2_c7_mcp_wtchdg_byp) [expr ($val & (1 << 15)) != 0]
   set mcpData(s2_c6_bypass_sw) [expr ($val & (1 << 14)) != 0]
   set mcpData(s2_c5_bypass_sw) [expr ($val & (1 << 13)) != 0]
   set mcpData(s2_c4_bypass_sw) [expr ($val & (1 << 12)) != 0]
   set mcpData(s2_c3_bypass_sw) [expr ($val & (1 << 11)) != 0]
   set mcpData(s2_c2_bypass_sw) [expr ($val & (1 << 10)) != 0]
   set mcpData(s2_c1_bypass_sw) [expr ($val & (1 << 9)) != 0]
   set mcpData(s2_c0_bypass_sw) [expr ($val & (1 << 8)) != 0]
   set mcpData(s1_c7_bypass_sw) [expr ($val & (1 << 7)) != 0]
   set mcpData(s1_c6_bypass_sw) [expr ($val & (1 << 6)) != 0]
   set mcpData(s1_c5_bypass_sw) [expr ($val & (1 << 5)) != 0]
   set mcpData(s1_c4_bypass_sw) [expr ($val & (1 << 4)) != 0]
   set mcpData(s1_c3_bypass_sw) [expr ($val & (1 << 3)) != 0]
   set mcpData(s1_c2_bypass_sw) [expr ($val & (1 << 2)) != 0]
   set mcpData(s1_c1_bypass_sw) [expr ($val & (1 << 1)) != 0]
   set mcpData(s1_c0_bypass_sw) [expr ($val & (1 << 0)) != 0]
}


proc set_I10_L0 {val} {
   global mcpData

   set mcpData(umbilical_dn) [expr ($val & (1 << 31)) != 0]
   set mcpData(alt_pos_gt_neg_2) [expr ($val & (1 << 30)) != 0]
   set mcpData(alt_pos_lt_0_2) [expr ($val & (1 << 29)) != 0]
   set mcpData(alt_position_gt_83_5) [expr ($val & (1 << 28)) != 0]
   set mcpData(alt_position_gt_15_5) [expr ($val & (1 << 27)) != 0]
   set mcpData(alt_position_gt_15_0) [expr ($val & (1 << 26)) != 0]
   set mcpData(alt_position_lt_18_5) [expr ($val & (1 << 25)) != 0]
   set mcpData(alt_position_gt_0_8) [expr ($val & (1 << 24)) != 0]
   set mcpData(alt_position_gt_19_5) [expr ($val & (1 << 23)) != 0]
   set mcpData(alt_position_gt_0_50) [expr ($val & (1 << 22)) != 0]
   set mcpData(alt_position_gt_89_8) [expr ($val & (1 << 21)) != 0]
   set mcpData(alt_position_lt_91_0) [expr ($val & (1 << 20)) != 0]
   set mcpData(alt_position_lt_90_29) [expr ($val & (1 << 19)) != 0]
   set mcpData(alt_position_lt_90_2) [expr ($val & (1 << 18)) != 0]
   set mcpData(alt_position_gt_89_75) [expr ($val & (1 << 17)) != 0]
   set mcpData(alt_position_lt_90_15) [expr ($val & (1 << 16)) != 0]
   set mcpData(in_10_bit_31_spare) [expr ($val & (1 << 15)) != 0]
   set mcpData(in_10_bit_30_spare) [expr ($val & (1 << 14)) != 0]
   set mcpData(in_10_bit_29_spare) [expr ($val & (1 << 13)) != 0]
   set mcpData(in_10_bit_28_spare) [expr ($val & (1 << 12)) != 0]
   set mcpData(in_10_bit_27_spare) [expr ($val & (1 << 11)) != 0]
   set mcpData(in_10_bit_26_spare) [expr ($val & (1 << 10)) != 0]
   set mcpData(in_10_bit_25_spare) [expr ($val & (1 << 9)) != 0]
   set mcpData(in_10_bit_24_spare) [expr ($val & (1 << 8)) != 0]
   set mcpData(in_10_bit_23_spare) [expr ($val & (1 << 7)) != 0]
   set mcpData(in_10_bit_22_spare) [expr ($val & (1 << 6)) != 0]
   set mcpData(in_10_bit_21_spare) [expr ($val & (1 << 5)) != 0]
   set mcpData(in_10_bit_20_spare) [expr ($val & (1 << 4)) != 0]
   set mcpData(in_10_bit_19_spare) [expr ($val & (1 << 3)) != 0]
   set mcpData(in_10_bit_18_spare) [expr ($val & (1 << 2)) != 0]
   set mcpData(lift_height_gt_h_cartridge_mount) [expr ($val & (1 << 1)) != 0]
   set mcpData(lift_force_gt_f_cartridge_mount) [expr ($val & (1 << 0)) != 0]
}


proc set_O1_L0 {val} {
   global mcpData

   set mcpData(spare_o1_l0) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L1 {val} {
   global mcpData

   set mcpData(low_lvl_light_2) [expr ($val & (1 << 31)) != 0]
   set mcpData(low_lvl_light_1) [expr ($val & (1 << 30)) != 0]
   set mcpData(az_stow_light) [expr ($val & (1 << 29)) != 0]
   set mcpData(stop_bypass_strobe) [expr ($val & (1 << 28)) != 0]
   set mcpData(az_stow_center_light) [expr ($val & (1 << 27)) != 0]
   set mcpData(rack_0_grp_2_bit_10) [expr ($val & (1 << 26)) != 0]
   set mcpData(lamp_on_enable) [expr ($val & (1 << 25)) != 0]
   set mcpData(inst_lift_dn_4) [expr ($val & (1 << 24)) != 0]
   set mcpData(inst_lift_dn_3) [expr ($val & (1 << 23)) != 0]
   set mcpData(inst_lift_dn_2) [expr ($val & (1 << 22)) != 0]
   set mcpData(inst_lift_dn_1) [expr ($val & (1 << 21)) != 0]
   set mcpData(inst_lift_up_1) [expr ($val & (1 << 20)) != 0]
   set mcpData(inst_lift_up_2) [expr ($val & (1 << 19)) != 0]
   set mcpData(inst_lift_up_3) [expr ($val & (1 << 18)) != 0]
   set mcpData(inst_lift_up_4) [expr ($val & (1 << 17)) != 0]
   set mcpData(inst_lift_high_psi) [expr ($val & (1 << 16)) != 0]
}


proc set_O1_L2 {val} {
   global mcpData

   set mcpData(spare_o1_l2) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L3 {val} {
   global mcpData

   set mcpData(spare_01_l3) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L4 {val} {
   global mcpData

   set mcpData(spare_o1_l4) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L5 {val} {
   global mcpData

   set mcpData(slit1_latched_led) [expr ($val & (1 << 31)) != 0]
   set mcpData(slit1_unlatched_led) [expr ($val & (1 << 30)) != 0]
   set mcpData(lift_down_led) [expr ($val & (1 << 29)) != 0]
   set mcpData(cart_in_place_led) [expr ($val & (1 << 28)) != 0]
   set mcpData(cam_crt_in_house_led) [expr ($val & (1 << 27)) != 0]
   set mcpData(dog_door_open_led) [expr ($val & (1 << 26)) != 0]
   set mcpData(jhook_in_place_led) [expr ($val & (1 << 25)) != 0]
   set mcpData(sad_in_place_led) [expr ($val & (1 << 24)) != 0]
   set mcpData(eng_in_place_led) [expr ($val & (1 << 23)) != 0]
   set mcpData(cartg_in_place_led) [expr ($val & (1 << 22)) != 0]
   set mcpData(cam_in_place_led) [expr ($val & (1 << 21)) != 0]
   set mcpData(cor_in_place_led) [expr ($val & (1 << 20)) != 0]
   set mcpData(eng_on_lift_led) [expr ($val & (1 << 19)) != 0]
   set mcpData(cartg_on_lift_led) [expr ($val & (1 << 18)) != 0]
   set mcpData(cam_on_lift_led) [expr ($val & (1 << 17)) != 0]
   set mcpData(cor_on_lift_led) [expr ($val & (1 << 16)) != 0]
   set mcpData(sec_latch2_cls_led) [expr ($val & (1 << 15)) != 0]
   set mcpData(sec_latch2_opn_led) [expr ($val & (1 << 14)) != 0]
   set mcpData(sec_latch1_cls_led) [expr ($val & (1 << 13)) != 0]
   set mcpData(sec_latch1_opn_led) [expr ($val & (1 << 12)) != 0]
   set mcpData(inst_latch_perm) [expr ($val & (1 << 11)) != 0]
   set mcpData(inst_unlatch_perm) [expr ($val & (1 << 10)) != 0]
   set mcpData(inst_latch3_cls_led) [expr ($val & (1 << 9)) != 0]
   set mcpData(inst_latch3_opn_led) [expr ($val & (1 << 8)) != 0]
   set mcpData(inst_latch2_cls_led) [expr ($val & (1 << 7)) != 0]
   set mcpData(inst_latch2_opn_led) [expr ($val & (1 << 6)) != 0]
   set mcpData(inst_latch1_cls_led) [expr ($val & (1 << 5)) != 0]
   set mcpData(inst_latch1_opn_led) [expr ($val & (1 << 4)) != 0]
   set mcpData(slit_latch_prm_led) [expr ($val & (1 << 3)) != 0]
   set mcpData(slit_unlatch_prm_led) [expr ($val & (1 << 2)) != 0]
   set mcpData(slit2_latched_led) [expr ($val & (1 << 1)) != 0]
   set mcpData(slit2_unlatched_led) [expr ($val & (1 << 0)) != 0]
}


proc set_O1_L6 {val} {
   global mcpData

   set mcpData(slit_dr_opn_perm_led) [expr ($val & (1 << 31)) != 0]
   set mcpData(slit_dr_cls_perm_led) [expr ($val & (1 << 30)) != 0]
   set mcpData(tbar_tel_perm_led) [expr ($val & (1 << 29)) != 0]
   set mcpData(tbar_xport_perm_led) [expr ($val & (1 << 28)) != 0]
   set mcpData(tbar_tel_led) [expr ($val & (1 << 27)) != 0]
   set mcpData(tbar_xport_led) [expr ($val & (1 << 26)) != 0]
   set mcpData(sad_latch_perm) [expr ($val & (1 << 25)) != 0]
   set mcpData(sad_unlatch_perm) [expr ($val & (1 << 24)) != 0]
   set mcpData(sad_latch2_cls_led) [expr ($val & (1 << 23)) != 0]
   set mcpData(sad_latch2_opn_led) [expr ($val & (1 << 22)) != 0]
   set mcpData(sad_latch1_cls_led) [expr ($val & (1 << 21)) != 0]
   set mcpData(sad_latch1_opn_led) [expr ($val & (1 << 20)) != 0]
   set mcpData(sec_latch_perm) [expr ($val & (1 << 19)) != 0]
   set mcpData(sec_unlatch_perm) [expr ($val & (1 << 18)) != 0]
   set mcpData(sec_latch3_cls_led) [expr ($val & (1 << 17)) != 0]
   set mcpData(sec_latch3_opn_led) [expr ($val & (1 << 16)) != 0]
   set mcpData(rack_1_grp_5_bit_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(rack_1_grp_5_bit_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(rack_1_grp_5_bit_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(saf_latch2_cls_led) [expr ($val & (1 << 12)) != 0]
   set mcpData(saf_latch2_opn_led) [expr ($val & (1 << 11)) != 0]
   set mcpData(saf_latch1_cls_led) [expr ($val & (1 << 10)) != 0]
   set mcpData(saf_latch1_opn_led) [expr ($val & (1 << 9)) != 0]
   set mcpData(manual_mode_led) [expr ($val & (1 << 8)) != 0]
   set mcpData(sad_latch_air_led) [expr ($val & (1 << 7)) != 0]
   set mcpData(sec_latch_air_led) [expr ($val & (1 << 6)) != 0]
   set mcpData(inst_latch_air_led) [expr ($val & (1 << 5)) != 0]
   set mcpData(ilcb_pres_led) [expr ($val & (1 << 4)) != 0]
   set mcpData(slit_dr2_opn_led) [expr ($val & (1 << 3)) != 0]
   set mcpData(slit_dr2_cls_led) [expr ($val & (1 << 2)) != 0]
   set mcpData(slit_dr1_opn_led) [expr ($val & (1 << 1)) != 0]
   set mcpData(slit_dr1_cls_led) [expr ($val & (1 << 0)) != 0]
}


proc set_O1_L7 {val} {
   global mcpData

   set mcpData(spare_o1_l7) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L8 {val} {
   global mcpData

   set mcpData(spare_o1_l8) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L9 {val} {
   global mcpData

   set mcpData(spare_o1_l9) [expr ($val & (1 << 31)) != 0]
   set mcpData(rack_2_grp_3_bit_15) [expr ($val & (1 << 15)) != 0]
   set mcpData(rack_2_grp_3_bit_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(rack_2_grp_3_bit_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(rack_2_grp_3_bit_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(rack_2_grp_3_bit_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(rack_2_grp_3_bit_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(rack_2_grp_3_bit_9) [expr ($val & (1 << 9)) != 0]
   set mcpData(rack_2_grp_3_bit_8) [expr ($val & (1 << 8)) != 0]
   set mcpData(rack_2_grp_3_bit_7) [expr ($val & (1 << 7)) != 0]
   set mcpData(rack_2_grp_3_bit_6) [expr ($val & (1 << 6)) != 0]
   set mcpData(slit_latch2_ext_perm) [expr ($val & (1 << 5)) != 0]
   set mcpData(slit_dr2_opn_perm) [expr ($val & (1 << 4)) != 0]
   set mcpData(slit_dr2_cls_perm) [expr ($val & (1 << 3)) != 0]
   set mcpData(slit_latch1_ext_perm) [expr ($val & (1 << 2)) != 0]
   set mcpData(slit_dr1_opn_perm) [expr ($val & (1 << 1)) != 0]
   set mcpData(slit_dr1_cls_perm) [expr ($val & (1 << 0)) != 0]
}


proc set_O1_L10 {val} {
   global mcpData

   set mcpData(spare_o1_l10) [expr ($val & (1 << 31)) != 0]
   set mcpData(audio_warning_2) [expr ($val & (1 << 15)) != 0]
   set mcpData(rack_2_grp_5_bit_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(rack_2_grp_5_bit_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(rack_2_grp_5_bit_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(rack_2_grp_5_bit_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(rack_2_grp_5_bit_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(rack_2_grp_5_bit_9) [expr ($val & (1 << 9)) != 0]
   set mcpData(rack_2_grp_5_bit_8) [expr ($val & (1 << 8)) != 0]
   set mcpData(rack_2_grp_5_bit_7) [expr ($val & (1 << 7)) != 0]
   set mcpData(rack_2_grp_5_bit_6) [expr ($val & (1 << 6)) != 0]
   set mcpData(rack_2_grp_5_bit_5) [expr ($val & (1 << 5)) != 0]
   set mcpData(rack_2_grp_5_bit_4) [expr ($val & (1 << 4)) != 0]
   set mcpData(rack_2_grp_5_bit_3) [expr ($val & (1 << 3)) != 0]
   set mcpData(rack_2_grp_5_bit_2) [expr ($val & (1 << 2)) != 0]
   set mcpData(rack_2_grp_5_bit_1) [expr ($val & (1 << 1)) != 0]
   set mcpData(purge_valve_permit) [expr ($val & (1 << 0)) != 0]
}


proc set_O1_L11 {val} {
   global mcpData

   set mcpData(spare_o1_l11) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L12 {val} {
   global mcpData

   set mcpData(spare_o1_l12) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L13 {val} {
   global mcpData

   set mcpData(spare_o1_l13) [expr ($val & (1 << 31)) != 0]
}


proc set_O1_L14 {val} {
   global mcpData

   set mcpData(spare_o1_l14) [expr ($val & (1 << 31)) != 0]
   set mcpData(audio_warning_1) [expr ($val & (1 << 15)) != 0]
   set mcpData(rack_4_grp_5_bit_14) [expr ($val & (1 << 14)) != 0]
   set mcpData(rack_4_grp_5_bit_13) [expr ($val & (1 << 13)) != 0]
   set mcpData(rack_4_grp_5_bit_12) [expr ($val & (1 << 12)) != 0]
   set mcpData(rack_4_grp_5_bit_11) [expr ($val & (1 << 11)) != 0]
   set mcpData(rack_4_grp_5_bit_10) [expr ($val & (1 << 10)) != 0]
   set mcpData(rack_4_grp_5_bit_9) [expr ($val & (1 << 9)) != 0]
   set mcpData(im_ff_uv_on_pmt) [expr ($val & (1 << 8)) != 0]
   set mcpData(im_ff_wht_on_pmt) [expr ($val & (1 << 7)) != 0]
   set mcpData(ff_screen2_enable_pm) [expr ($val & (1 << 6)) != 0]
   set mcpData(ff_screen2_open_pmt) [expr ($val & (1 << 5)) != 0]
   set mcpData(hgcd_lamps_on_pmt) [expr ($val & (1 << 4)) != 0]
   set mcpData(ne_lamps_on_pmt) [expr ($val & (1 << 3)) != 0]
   set mcpData(ff_lamps_on_pmt) [expr ($val & (1 << 2)) != 0]
   set mcpData(ff_screen_enable_pmt) [expr ($val & (1 << 1)) != 0]
   set mcpData(ff_screen_open_pmt) [expr ($val & (1 << 0)) != 0]
}


proc set_O1_L15 {val} {
   global mcpData

   set mcpData(spare_o1_l15) [expr ($val & (1 << 31)) != 0]
}


proc set_O2_L0 {val} {
   global mcpData

   set mcpData(out_2_bit_21_spare) [expr ($val & (1 << 5)) != 0]
   set mcpData(out_2_bit_20_spare) [expr ($val & (1 << 4)) != 0]
   set mcpData(wind_mtr_dn_perm) [expr ($val & (1 << 3)) != 0]
   set mcpData(wind_mtr_up_perm) [expr ($val & (1 << 2)) != 0]
   set mcpData(wind_mtr_ccw_perm) [expr ($val & (1 << 1)) != 0]
   set mcpData(wind_mtr_cw_perm) [expr ($val & (1 << 0)) != 0]
}


proc set_O3_L0 {val} {
   global mcpData

}


proc set_O3_L1 {val} {
   global mcpData

}


proc set_O3_L2 {val} {
   global mcpData

}


proc set_O3_L3 {val} {
   global mcpData

}


proc set_O4_L0 {val} {
   global mcpData

}


proc set_O4_L1 {val} {
   global mcpData

}


proc set_O4_L2 {val} {
   global mcpData

}


proc set_O4_L3 {val} {
   global mcpData

}


proc set_O5_L0 {val} {
   global mcpData

}


proc set_O5_L1 {val} {
   global mcpData

}


proc set_O5_L2 {val} {
   global mcpData

}


proc set_O5_L3 {val} {
   global mcpData

}


proc set_O11_L0 {val} {
   global mcpData

   set mcpData(s_ll_led) [expr ($val & (1 << 31)) != 0]
   set mcpData(n_ll_led) [expr ($val & (1 << 30)) != 0]
   set mcpData(w_rail_led) [expr ($val & (1 << 29)) != 0]
   set mcpData(s_rail_led) [expr ($val & (1 << 28)) != 0]
   set mcpData(n_rail_led) [expr ($val & (1 << 27)) != 0]
   set mcpData(rot_plc_perm) [expr ($val & (1 << 26)) != 0]
   set mcpData(rot_mtr_ccw_perm) [expr ($val & (1 << 25)) != 0]
   set mcpData(rot_mtr_cw_perm) [expr ($val & (1 << 24)) != 0]
   set mcpData(wind_az_plc_perm) [expr ($val & (1 << 23)) != 0]
   set mcpData(az_plc_perm) [expr ($val & (1 << 22)) != 0]
   set mcpData(az_mtr_ccw_perm) [expr ($val & (1 << 21)) != 0]
   set mcpData(az_mtr_cw_perm) [expr ($val & (1 << 20)) != 0]
   set mcpData(wind_alt_plc_perm) [expr ($val & (1 << 19)) != 0]
   set mcpData(alt_plc_perm) [expr ($val & (1 << 18)) != 0]
   set mcpData(alt_mtr_dn_perm) [expr ($val & (1 << 17)) != 0]
   set mcpData(alt_mtr_up_perm) [expr ($val & (1 << 16)) != 0]
   set mcpData(clamp_en) [expr ($val & (1 << 15)) != 0]
   set mcpData(clamp_dis) [expr ($val & (1 << 14)) != 0]
   set mcpData(t_bar_xport_perm) [expr ($val & (1 << 13)) != 0]
   set mcpData(t_bar_tel_perm) [expr ($val & (1 << 12)) != 0]
   set mcpData(out_11_bit_27_spare) [expr ($val & (1 << 11)) != 0]
   set mcpData(lift_pump_on) [expr ($val & (1 << 10)) != 0]
   set mcpData(out_11_bit_25_spare) [expr ($val & (1 << 9)) != 0]
   set mcpData(out_11_bit_24_spare) [expr ($val & (1 << 8)) != 0]
   set mcpData(deg_15_stop_ret_perm) [expr ($val & (1 << 7)) != 0]
   set mcpData(deg_15_stop_ext_perm) [expr ($val & (1 << 6)) != 0]
   set mcpData(lift_solenoid_en) [expr ($val & (1 << 5)) != 0]
   set mcpData(s_wind_led) [expr ($val & (1 << 4)) != 0]
   set mcpData(n_fork_led) [expr ($val & (1 << 3)) != 0]
   set mcpData(n_wind_led) [expr ($val & (1 << 2)) != 0]
   set mcpData(w_ll_led) [expr ($val & (1 << 1)) != 0]
   set mcpData(e_ll_led) [expr ($val & (1 << 0)) != 0]
}


proc set_O12_L0 {val} {
   global mcpData

   set mcpData(out_12_bit_15_spare) [expr ($val & (1 << 31)) != 0]
   set mcpData(out_12_bit_14_spare) [expr ($val & (1 << 30)) != 0]
   set mcpData(out_12_bit_13_spare) [expr ($val & (1 << 29)) != 0]
   set mcpData(umbilical_fast) [expr ($val & (1 << 28)) != 0]
   set mcpData(lift_enable) [expr ($val & (1 << 27)) != 0]
   set mcpData(velocity_trp_rst_out) [expr ($val & (1 << 26)) != 0]
   set mcpData(velocity_select_bit) [expr ($val & (1 << 25)) != 0]
   set mcpData(stow_pos_light) [expr ($val & (1 << 24)) != 0]
   set mcpData(inst_chg_pos_light) [expr ($val & (1 << 23)) != 0]
   set mcpData(nw_fork_led) [expr ($val & (1 << 22)) != 0]
   set mcpData(umbilical_up_dn) [expr ($val & (1 << 21)) != 0]
   set mcpData(umbilical_on_off) [expr ($val & (1 << 20)) != 0]
   set mcpData(alt_brake_en) [expr ($val & (1 << 19)) != 0]
   set mcpData(alt_brake_dis) [expr ($val & (1 << 18)) != 0]
   set mcpData(az_brake_en) [expr ($val & (1 << 17)) != 0]
   set mcpData(az_brake_dis) [expr ($val & (1 << 16)) != 0]
   set mcpData(out_12_bit_31_spare) [expr ($val & (1 << 15)) != 0]
   set mcpData(out_12_bit_30_spare) [expr ($val & (1 << 14)) != 0]
   set mcpData(out_12_bit_29_spare) [expr ($val & (1 << 13)) != 0]
   set mcpData(out_12_bit_28_spare) [expr ($val & (1 << 12)) != 0]
   set mcpData(out_12_bit_27_spare) [expr ($val & (1 << 11)) != 0]
   set mcpData(out_12_bit_26_spare) [expr ($val & (1 << 10)) != 0]
   set mcpData(out_12_bit_25_spare) [expr ($val & (1 << 9)) != 0]
   set mcpData(out_12_bit_24_spare) [expr ($val & (1 << 8)) != 0]
   set mcpData(out_12_bit_23_spare) [expr ($val & (1 << 7)) != 0]
   set mcpData(out_12_bit_22_spare) [expr ($val & (1 << 6)) != 0]
   set mcpData(out_12_bit_21_spare) [expr ($val & (1 << 5)) != 0]
   set mcpData(out_12_bit_20_spare) [expr ($val & (1 << 4)) != 0]
   set mcpData(out_12_bit_19_spare) [expr ($val & (1 << 3)) != 0]
   set mcpData(out_12_bit_18_spare) [expr ($val & (1 << 2)) != 0]
   set mcpData(out_12_bit_17_spare) [expr ($val & (1 << 1)) != 0]
   set mcpData(out_12_bit_16_spare) [expr ($val & (1 << 0)) != 0]
}


#
# Routines that are called by python keyword callbacks;  the ones for the ab_XXX
# words are generated automatically
#

proc set_aliveAt {val} {
     global mcpData

     set mcpData(ctime) $val
}

proc set_lavaLamp {val} {
   global mcpData
   set mcpData(cr_lava_lamp) $val
}

proc set_plcVersion {val} {
   global mcpData
   set mcpData(plcVersion) $val
}
#
# The automatic ones assume a single Int argument; status takes 4
#
proc set_status {v0 v1 v2 v3} {
   global mcpData

   set mcpData(status)   $v0
   set mcpData(azstate)  $v1
   set mcpData(altstate) $v2
   set mcpData(rotstate) $v3
}

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# Handle checking plcVersion strings
#
proc plcVersion {args} {
   global interlockDescriptions mcpData
   
   set version $mcpData(plcVersion)

   if {![regexp {Version ([^ ]+) +[$]Name:? *([^ $]*)} \
            $interlockDescriptions(version_id) {} plc_n plc_version] ||
       $plc_version == ""} {
      if {$version == $plc_n} {
	 return "NOCVS:$version"
      } else {
	 return "NOCVS:$version:$plc_n"
      }
   } elseif {$version == ""} {
      return "(unavailable)"
   } elseif {$version == $plc_n} {      # version from PLC matches version in
      return $plc_version;              # interlockDescriptions (i.e. sdss.csv)
   } else {
      return "MISMATCH:$version:$plc_n"
   }
}

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# Make a label l that doesn't appear but is the same size as one 
# labelled "text"
#
proc phantom_label {l text} {
   label $l -text $text -relief flat
   set bg [lindex [. configure -bg] 4]
   $l configure -foreground $bg

   return $l
}

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# Useful to show data via Tkinter.call()
#
proc showMcpData {key} {
   global mcpData
   
   puts "$key $mcpData($key)"
}

proc mcpGetFields {} {
   global mcpDataNames

   return [array get mcpDataNames]
}
