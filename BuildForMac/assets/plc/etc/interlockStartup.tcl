if {![info exists env(PLC_DIR)]} {
    #puts "[utclock [getclock]]: You need to setup the plc";
    return -code error -errorinfo "You need to setup the plc"
}

if [info exists env(MCPOP_DIR)] {
   source $env(MCPOP_DIR)/etc/utils.tcl
}

source $env(PLC_DIR)/etc/dervish.tcl

foreach file [list \
		  $env(PLC_DIR)/etc/help.tcl \
		  $env(PLC_DIR)/etc/sockmon.tcl \
		  $env(PLC_DIR)/etc/logic.tcl \
		  $env(PLC_DIR)/etc/instrumentChanges.tcl \
		  $env(PLC_DIR)/etc/documentation.tcl \
		  $env(PLC_DIR)/etc/constants.tcl \
		 ] {
   source $file
}

array set mcpData [mcpGetFields]
array set mcp_interlock_fields [mcpGetFields]
#
# Values that the user might want to ignore; they can add others using
# set, toggle_mcpIgnoreValue, or a middle mouse button click
#
foreach el [list \
		alt_motor1_VI_R_check \
		alt_motor2_VI_R_check \
		alt_mtr1_rdy \
		alt_mtr2_rdy \
		az_motor1_VI_R_check \
		az_motor2_VI_R_check \
		az_mtr1_rdy \
		az_mtr2_rdy \
		permit_timed_out \
		rot_motor_VI_R_check \
		rot_mtr_rdy \
	       ] {
   toggle_mcpIgnoreValue $el 0
}

if [info exists env(INTERLOCKS_LOGIC_FILE)] {
   set interlock_logic_file $env(INTERLOCKS_LOGIC_FILE)
} else {
   set interlock_logic_file $env(PLC_DIR)/etc/interlocks.tcl
}
read_interlock_logic $interlock_logic_file

if ![info exists env(MCPOP_DIR)] {
   # override the "real" one;  we get the keywords via reactor callbacks
   proc readMCPValues {} {
      global mcpDerivedData;		# array of cached derived values
      
      if [info exists mcpDerivedData] {
	 unset mcpDerivedData
      }
   }
}
