##########################################################
#  Tcl/Tk program for SDSS Telescope Interlocks monitor
#  Dennis Nicklaus nicklaus@fnal.gov    Feb. 1998

# Interconnection Logic for the SDSS Interlocks.
# The information here drives Tcl functions to create the structures
# which are used to display the interconnection statuses and logic diagrams.
#
# The trickiest part of the logic language is knowing when you have to 
# quote in RESULTs to make the Tcl interpretation happy. Your best bet
# is to just follow the examples here.

# It is important to have the MORE_THINGS bit
# descriptions in this file before those bits are used in any
# RESULTs  statements.

#
# Here are the axis_state values; see PR#417
#
array set msg_axis_state [list \
			      0 "NO_EVENT" \
			      1 "??_EVENT" \
			      2 "NEW_FRAME" \
			      8 "STOP_EVENT" \
			      10 "E_STOP_EVENT" \
			      14 "ABORT_EVENT" \
			      ]
#
# Is the specified axis in a Bad State?
#
proc bad_axis_state {axis} {
   global mcpData
   switch -regexp $axis {
      {^[Aa]lt(itude)?$} {
	 set axis "alt"
      }
      {^[Aa]z(imuth)?$} {
	 set axis "az"
      }
      {^[Rr]ot(ator)?$} {
	 set axis "rot"
      }
   }
      
   return [expr ($mcpData(${axis}state) <= 2) ? 0 : 1]
}

#
# Some simple logicals
#

RESULT true \
    [OR \
	 spare_s1_c2 \
	 [NOT spare_s1_c2] \
	] \
    "always true"


RESULT false \
    [AND \
	 spare_s1_c2 \
	 [NOT spare_s1_c2] \
	] \
    "always false"

RESULT bypass true
set interlockDescriptions(bypass) "A true value; used to bypass an interlock"

RESULT permit_timed_out true
set interlockDescriptions(permit_timed_out) \
    "A permit was granted (or allowed to linger) and has now timed out.
 Always true"

RESULT glentek_is_on true
set interlockDescriptions(glentek_is_on) "The Glenteks are powered up"

RESULT glenteks \
    [AND \
	 glentek_is_on \
	 [OR \
	      mcp_watchdog_timer \
	      s2_c7_mcp_wtchdg_byp \
	     ] \
	 ] \
    "The Glenteks are permitted to drive the telescope"

RESULT zenith \
    [AND alt_position_lt_90_15 alt_position_gt_89_75] \
    "Telescope is at zenith"

##########################################################
# RESULTs are the basic inter-connection logic descriptions.
# A very important distinction between RESULTs and MORE_THINGS:
# RESULTs is just a description of logic paths that the
# interlock system is supposed to follow. No processing
# by this software display program is implied.
# Nothing in this program
# checks that the value of the various bits actually follows
# this prescribed logic or calculates results based on this logic.
#
# You can call RESULT lots of times.
# Remember to put a backslash at the end of each newline 
# in a RESULT statement.

###############################################################################
#
# Windscreen
#

###############################################################################
#
# Azimuth Motion Logic Diagram
#
#
# Is the building clear enough to move the telescope?
#
RESULT bldg_ok_az \
    [AND \
	 [OR \
	      [AND az_dir_cw  az_neg_201a_cw] \
	      [AND az_dir_ccw az_pos_445a_ccw] \
	      [AND az_neg_201b_cw az_pos_445b_ccw] \
	     ] \
	 [OR \
	      [AND bldg_on_az \
		   [OR az_109_131_limit_2 alt_grt_83_limit_2] \
		  ] \
	      bldg_clear_az \
	     ] \
	 az_velocity_limit \
	 ]

RESULT az_plc_tmp1 \
    [AND \
	 [AND \
	      [OR \
		   [AND [NOT permit_timed_out] mcp_az_brk_en_cmd] \
		   az_brake_dis_stat \
		  ] \
	      az_mtr1_rdy \
	      az_mtr2_rdy \
	      clamp_dis_stat \
	      alt_position_gt_19_5 \
	      ] \
	 [OR flat_field_scr_clsd bldg_clear_az] \
	] \
    "Temp value in PLC Azimuth Logic Code"	 

RESULT az_mtr_cw_perm  \
    [AND \
	 az_plc_tmp1 \
	 [OR \
	      az_dir_ccw \
	      [OR \
		   bldg_clear_az \
		   az_110_130_limit \
		   alt_position_gt_83_5 \
		  ] \
	      ] \
	 [AND \
	      dog_house_cw_pad \
	      [OR \
		   az_dir_ccw \
		   [AND az_dir_cw az_neg_196_cw] \
		   [AND az_neg_196_cw az_pos_440_ccw] \
		   ] \
	      ] \
	 ] 

EQUIV wind_mtr_cw_perm az_mtr_cw_perm

RESULT az_mtr_ccw_perm  \
    [AND \
	 az_plc_tmp1 \
	 [OR \
	      [OR \
		   bldg_clear_az \
		   az_110_130_limit \
		   alt_position_gt_83_5 \
		  ] \
	      az_dir_cw \
	      ]\
	 [AND \
	      [OR \
		   [AND az_neg_196_cw az_pos_440_ccw] \
		   az_dir_cw \
		   [AND az_dir_ccw az_pos_440_ccw] \
		   ] \
	      ] \
	      dog_house_ccw_pad \
	 ]

EQUIV wind_mtr_ccw_perm az_mtr_ccw_perm

RESULT wind_az_ready \
    [AND \
	 wind_az_perm \
	 [NOT wind_az_fault] \
	 ]

RESULT wind_az_fault \
    [OR \
	 wind_az1_fault \
	 wind_az2_fault \
	 wind_az3_fault \
	] "Low when the windscreen azimuth amplifiers are on and ready AND the motor klixons are good"

RESULT az_plc_perm  \
    [AND \
	 [NOT ff_man_cont_enable] \
	 az_mtr_iv_good \
	 ]

RESULT az_mtr1_perm  \
    [AND az_plc_perm az_slip bldg_ok_az]

RESULT az_mtr2_perm  \
    [AND az_plc_perm az_slip bldg_ok_az]

RESULT wind_az_mtr_perm \
    [AND wind_az_plc_perm alt_grt_18d6_limit_3 bldg_ok_az]

###############################################################################
#
# Altitude Motion Logic Diagram
#
RESULT bldg_ok_alt \
    [AND \
	 [OR \
	      [AND \
		   [OR \
			[AND az_109_131_limit_1 alt_grt_18d6_limit_1] \
			[AND az_stow_1a az_stow_1b] \
			alt_grt_83_limit_1 \
		       ] \
		   bldg_on_alt \
		  ] \
	      [AND \
		   [OR \
			[AND deg_15_stop_ext alt_grt_18d6_limit_2] \
			[AND az_stow_2a az_stow_2b] \
		       ] \
		   bldg_clear_alt \
		  ] \
	      ] \
	 [AND \
	      alt_grt_0d3_limit \
	      alt_locking_pin_out \
	      alt_les_90d5_limit \
	      alt_velocity_limit \
	     ] \
	]

RESULT alt_mtr_up_perm \
    [AND \
	 [AND \
	      [OR \
		   [AND [NOT permit_timed_out] mcp_alt_brk_en_cmd] \
		   alt_brake_dis_stat \
		  ] \
	      alt_mtr1_rdy \
	      alt_mtr2_rdy \
	     ] \
	 [OR \
	      flat_field_scr_clsd \
	      [AND bldg_clear_alt [NOT bldg_on_alt]] \
	     ] \
	 alt_position_lt_91_0 \
	]

EQUIV wind_mtr_up_perm alt_mtr_up_perm

RESULT alt_mtr_dn_perm \
    [AND \
	 [AND \
	      [OR \
		   [AND [NOT permit_timed_out] mcp_alt_brk_en_cmd] \
		   alt_brake_dis_stat \
		  ] \
	      alt_mtr1_rdy \
	      alt_mtr2_rdy \
	     ] \
	 [OR \
	      [AND bldg_clear_alt [NOT bldg_on_alt]] \
	      flat_field_scr_clsd \
	     ] \
	 [OR \
	      [AND bldg_clear_alt [NOT bldg_on_alt]] \
	      [OR \
		   alt_position_gt_83_5 \
		   az_110_130_limit \
		  ] \
	     ] \
	 [AND \
	      alt_position_gt_0_50 \
	      [OR \
		   alt_position_gt_19_5 \
		   [AND az_stow_1a az_stow_1b] \
		  ] \
	      [OR \
		   alt_position_gt_15_5 \
		   [AND \
			flat_field_scr_clsd \
			[NOT deg_15_stop_ext] \
			deg_15_stop_ret \
		       ] \
		  ] \
	     ] \
	]

EQUIV wind_mtr_dn_perm alt_mtr_dn_perm

RESULT wind_alt_ready \
    [AND \
	 wind_alt_perm \
	 [NOT wind_alt_fault] \
	 ]

RESULT wind_alt_fault \
    [OR \
	 wind_alt1_fault \
	] "Low when the windscreen altitude amplifier is on and ready AND the motor klixon is good"

RESULT alt_mtr1_perm  \
    [AND alt_slip alt_plc_perm bldg_ok_alt]

RESULT alt_mtr2_perm  \
    [AND alt_slip alt_plc_perm bldg_ok_alt]

RESULT alt_plc_perm  \
    [AND \
	 alt_mtr_iv_good \
	 [AND \
	      umbilical_strain_sw \
	      ops_cart_in_house \
	      inst_lift_dn \
	      dog_house_door_cls \
	      ] \
	 [NOT ff_man_cont_enable] \
	 [NOT spec_autofill_on] \
	 [OR \
	      [AND \
		   [NOT sad_mount1] \
		   sad_mount2 \
		   t_bar_tel_stat \
		   ] \
	      [AND \
		   sad_mount1 \
		   [NOT sad_mount2] \
		   ] \
	      ] \
	 [AND \
	      safety_latch1_cls \
	      safety_latch2_cls \
	      ] \
	] "" "Altitude Motion Logic Drawing: rev Q"

RESULT wind_alt_mtr_perm \
    [AND wind_alt_plc_perm bldg_ok_alt]

###############################################################################
#
# Rotator Motion Logic
#
RESULT rot_mtr_perm \
    [AND \
	 rot_plc_perm \
	 [OR \
	      [AND rot_dir_cw rot_neg_200a_cw] \
	      [AND rot_dir_ccw rot_pos_380a_ccw] \
	      [AND rot_neg_200b_cw rot_pos_380b_ccw] \
	      ] \
	 rot_slip \
	 rot_velocity_limit
     ]

RESULT rot_mtr_cw_perm \
    [AND \
	 rot_mtr_rdy \
	 [OR \
	      rot_dir_ccw \
	      [AND \
		   rot_dir_cw \
		   rot_neg_190_cw \
		   ] \
	      [AND \
		   rot_neg_190_cw \
		   rot_pos_370_ccw \
		   ] \
	      ] \
	 ]

RESULT rot_mtr_ccw_perm \
    [AND \
	 rot_mtr_rdy \
	 [OR \
	      [AND \
		   rot_neg_190_cw \
		   rot_pos_370_ccw \
		   ] \
	      rot_dir_cw \
	      [AND \
		   rot_dir_ccw \
		   rot_pos_370_ccw \
		  ] \
	      ] \
	 ]

###############################################################################
#
# Misc systems
#
# Parts of the UDP packets that we can safely ignore when seeing if there
# is unused information in the packets
#
foreach el [list \
		ascii_len binary_len ctime sdsstime state_ascii errcnt
	   ] {
   VALUE_IS_USED $el
}

RESULT flat_field_scr_clsd \
    [AND \
	 flat_field_scr_1_clsd \
	 flat_field_scr_2_clsd \
	 flat_field_scr_3_clsd \
	 flat_field_scr_4_clsd \
	 flat_field_scr_5_clsd \
	 flat_field_scr_6_clsd \
	 flat_field_scr_7_clsd \
	 flat_field_scr_8_clsd \
	 ] \
    "Flat field petals are all closed"

loop i 1 9 {
   RESULT flat_field_scr_${i}_clsd \
       [AND leaf_${i}_closed_stat [NOT leaf_${i}_open_stat]] \
   "Flat field leaf $i is closed"
}

RESULT stop_buttons_out \
    [AND \
	 [OR tcc_stop     [AND s1_c0_bypass_sw e_stop_byp_sw]] \
	 [OR cr_stop      [AND s1_c1_bypass_sw e_stop_byp_sw]] \
	 [OR n_wind_stop  [AND s1_c4_bypass_sw e_stop_byp_sw]] \
	 [OR n_fork_stop  [AND s1_c5_bypass_sw e_stop_byp_sw]] \
	 [OR nw_fork_stop [AND s2_c6_bypass_sw e_stop_byp_sw]] \
	 [OR n_rail_stop  [AND s1_c6_bypass_sw e_stop_byp_sw]] \
	 [OR s_rail_stop  [AND s1_c7_bypass_sw e_stop_byp_sw]] \
	 [OR w_rail_stop  [AND s2_c0_bypass_sw e_stop_byp_sw]] \
	 [OR n_lower_stop [AND s2_c1_bypass_sw e_stop_byp_sw]] \
	 [OR s_lower_stop [AND s2_c2_bypass_sw e_stop_byp_sw]] \
	 [OR e_lower_stop [AND s2_c3_bypass_sw e_stop_byp_sw]] \
	 [OR w_lower_stop [AND s2_c4_bypass_sw e_stop_byp_sw]] \
	 [OR s_wind_stop  [AND s2_c5_bypass_sw e_stop_byp_sw]] \
	] \
    "All of the stop buttons are out or bypassed"   
#
# unused bypass bits
#
foreach el [list \
		s1_c2_bypass_sw s1_c3_bypass_sw s2_c7_bypass_sw \
	   ] {
   VALUE_IS_USED $el
}

RESULT stop_button_in \
    [NOT \
	 stop_buttons_out \
	] \
    "At least one of the stop buttons is in"
#
# We don't care about the e-stop LEDs
#
foreach el [list \
		n_rail_led s_rail_led w_rail_led \
		n_ll_led s_ll_led e_ll_led w_ll_led \
		n_wind_led n_fork_led nw_fork_led s_wind_led \
		e_stop_led_flash_tmr e_stop_led_f_tmr_dn
	   ] {
   VALUE_IS_USED $el
}

RESULT t_bar_maintainance_pos \
    [OR bypass \
	 [AND \
	      optical_bench_opn \
	      [NOT optical_bench_cls] \
	      t_bar_xport_stat \
	      [NOT t_bar_tel_stat] \
	     ] \
	] \
    "T-Bars are in maintainance position"
###############################################################################
#
# Flat field screens
#
RESULT ff_screen_open_pmt \
    [OR \
	 man_ff_scrn_opn_cmd \
	 [AND \
	      alt_position_gt_15_0 \
	      [NOT bldg_on_alt] \
	      bldg_clear_alt \
	      [OR bypass mcp_ff_scrn_opn_cmd] \
	     ] \
	 ]

###############################################################################
#
# Instrument Changes
#
if 0 {					# XXX
if 0 {
   EQUIV inst_chg_pos inst_chg_pos_light
} else {
   RESULT inst_chg_pos [OR bypass inst_chg_pos_light]
}

RESULT az_stow_light \
    [AND az_stow_1a  az_stow_1b]
	 
RESULT stow_pos_light \
    [AND \
	 [AND az_stow_1a  az_stow_1b] \
	 alt_les_2d5_limit \
	 ]

RESULT az_stow_center_light \
    az_stow_cntr_sw

RESULT low_lvl_light_1 \
    low_lvl_light_req

RESULT low_lvl_light_2 \
    low_lvl_light_req

RESULT stow_pos_light  \
    [AND [AND alt_pos_lt_0_2 alt_pos_gt_neg_2] \
	 [AND az_stow_b  az_stow_a]  \
	]

RESULT low_lvl_light_1  \
    [AND low_lvl_light_req]

RESULT  low_lvl_light_2  \
    [AND low_lvl_light_req]

RESULT  inst_lift_up_1  \
    [AND [AND solenoid_enable  lift_up_sw]  ]

RESULT inst_lift_up_2  \
    [AND [AND solenoid_enable  lift_up_sw]  ]

RESULT inst_lift_up_3  \
    [AND [AND solenoid_enable  lift_up_sw]  ]

RESULT inst_lift_up_4  \
    [AND [AND solenoid_enable  lift_up_sw]  ]

RESULT inst_lift_high_psi  \
    [AND inst_lift_high  solenoid_enable  ]

RESULT solenoid_enable  \
    [OR lift_dn_sw  lift_up_sw  ]

RESULT lift_estop_light  \
    [NOT lift_estop_sw]

RESULT  lift_dn_light  \
    [NOT inst_lift_dn]

RESULT  lift_up_light  \
    [AND inst_lift_dist_ge_0 inst_lift_dist_le_22]

RESULT pump_on_cmd  \
    [AND zenith \
	 lift_estop_sw  \
	 inst_lift_pump_on  ]

RESULT ilcb_pres_led  \
    [AND  zenith ilcb_pres_good]

RESULT  inst_latch_perm\
    [AND   zenith pri_latch_cls_cmd]

RESULT  inst_unlatch_perm\
    [AND   zenith pri_latch_opn_cmd]

RESULT  inst_man_req  \
    [OR [AND \
      zenith \
      inst_unlatch_perm  \
      [ OR [NOT pri_latch1_opn]  \
	   [NOT pri_latch2_opn]  \
	   [NOT pri_latch3_opn]  \
      ] ] \
    [AND \
      zenith \
      inst_latch_perm  \
      [ OR [NOT pri_latch1_cls]  \
	   [NOT pri_latch2_cls]  \
	   [NOT pri_latch3_cls]  \
      ] ] \
]

RESULT inst_latch1_opn_led  \
    [AND  zenith pri_latch1_opn]

RESULT  inst_latch1_cls_led  \
    [AND  zenith pri_latch1_cls]

RESULT  inst_latch2_opn_led  \
    [AND  zenith pri_latch2_opn]

RESULT  inst_latch2_cls_led  \
    [AND  zenith pri_latch2_cls]

RESULT  inst_latch3_opn_led  \
    [AND  zenith pri_latch3_opn]

RESULT  inst_latch3_cls_led  \
    [AND  zenith pri_latch3_cls]

RESULT  sec_latch_perm  \
    [AND  zenith  sec_latch_cls_cmd]

RESULT  sec_unlatch_perm  \
    [AND  zenith  sec_latch_opn_cmd]

RESULT  sec_man_req  \
    [OR [AND \
	     zenith \
	     sec_unlatch_perm  \
	     [OR [NOT sec_latch1_opn]  \
		  [NOT sec_latch2_opn]  \
		  [NOT sec_latch3_opn]  \
		 ] \
	    ] \
	 [AND \
	      zenith \
	      sec_latch_perm  \
	      [OR [NOT sec_latch1_cls]  \
		   [NOT sec_latch2_cls]  \
		   [NOT sec_latch3_cls]  \
		  ] \
	     ] \
	]

RESULT sec_latch1_opn_led  \
    [AND  zenith sec_latch1_opn]

RESULT  sec_latch1_cls_led  \
    [AND  zenith sec_latch1_cls]

RESULT  sec_latch2_opn_led  \
    [AND  zenith sec_latch2_opn]

RESULT  sec_latch2_cls_led  \
    [AND  zenith sec_latch2_cls]

RESULT  sec_latch3_opn_led  \
    [AND  zenith sec_latch3_opn]

RESULT  sec_latch3_cls_led  \
    [AND  zenith sec_latch3_cls]

RESULT  sad_latch_perm  \
    [AND  zenith  sad_latch_cls_cmd]

RESULT  sad_unlatch_perm  \
    [AND  zenith  sad_latch_opn_cmd]

RESULT  sad_man_req  \
[OR [AND \
      zenith \
      sad_unlatch_perm  \
      [OR [NOT sad_latch1_opn]  \
	   [NOT sad_latch2_opn]  \
      ] ] \
    [AND \
      zenith \
      sad_latch_perm  \
      [OR [NOT sad_latch1_cls]  \
	   [NOT sad_latch2_cls]  \
      ] ] \
]

RESULT sad_latch1_opn_led  \
    [AND  zenith sad_latch1_opn]

RESULT  sad_latch1_cls_led  \
    [AND  zenith sad_latch1_cls]

RESULT  sad_latch2_opn_led  \
    [AND  zenith sad_latch2_opn]

RESULT  sad_latch2_cls_led  \
    [AND  zenith sad_latch2_cls]

RESULT  safety_latch1_opn_led  \
    [AND  zenith safety_latch1_opn]

RESULT  safety_latch1_cls_led  \
    [AND  zenith safety_latch1_cls]

RESULT  safety_latch2_opn_led  \
    [AND  zenith safety_latch2_opn]

RESULT  safety_latch2_cls_led  \
    [AND  zenith safety_latch2_cls]
}

RESULT rot_plc_perm \
    [AND \
	 rot_mtr_iv_good \
 	 [NOT spec_autofill_on] \
	 umbilical_strain_sw \
	] "" "Rotator Motion Logic Drawing: rev L"

###############################################################
# For the first argument of all BIGANDs and the "names"  in HARDWARE_STATUS
# the words cannot begin with an uppercase letter because of Tcl restrictions.
#  You can call BIGAND lots of times.
#  BIGANDs are the major groupings of bits which are and-ed together and shown
#  as either a red or green button to reflect that and-ed result.

BIGAND keydisplays \
    rotator \
    stop_buttons_out \
    glenteks \
    rot_mtr_cw_perm \
    rot_mtr_ccw_perm \
    rot_mtr_perm

BIGAND keydisplays altitude \
    stop_buttons_out \
    glenteks \
    alt_mtr_up_perm \
    alt_mtr_dn_perm \
    alt_mtr1_perm \
    alt_mtr2_perm \
    wind_mtr_up_perm \
    wind_mtr_dn_perm \
    wind_alt_mtr_perm \
    wind_alt_ready

BIGAND  keydisplays azimuth \
    stop_buttons_out \
    glenteks \
    az_mtr_cw_perm \
    az_mtr_ccw_perm \
    az_mtr1_perm \
    az_mtr2_perm \
    wind_mtr_cw_perm \
    wind_mtr_ccw_perm \
    wind_az_mtr_perm \
    wind_az_ready

if 0 {
   BIGOR instrument_changes "instrumentChange" \
       lift_up_enable \
       lift_down_enable \
       latch_perm \
       unlatch_perm
}

###############################################################
#   You can only have ONE call to SPECIAL_BICOLOR for each variable name
# These are like HARDWARE_STATUS, but have _two_ sensors (e.g. open and closed)
# rather than just one (e.g. open)
# Note by placing this in the file before HARDWARE_STATUS, these bipolar
# buttons will be positioned above the other HW_STATUS bits on the display window.

SPECIAL_BICOLOR bicolor_status_list \
  {"azimuth_brake" \
	{on off} \
	{az_brake_en_stat  az_brake_dis_stat}\
	}\
   {"altitude_brake" \
	{on off} \
	{alt_brake_en_stat  alt_brake_dis_stat}\
	}\
   {"alignment_clamp" \
	{on off} \
	{clamp_en_stat  clamp_dis_stat}\
	}\
   {"15degree_stop" \
	{rtrctd extnd} \
	{deg_15_stop_ret deg_15_stop_ext}\
        }

###############################################################################
#
# This needs to come before HARDWARE_STATUS
#
RESULT audioAlarms [NOT \
			[OR \
			     audio_warning_1 \
			    ]] "_No_ audible warning is going off"

RESULT audio_warning_1 \
    [AND \
	 t_bar_tel_stat \
	 [OR safety_latch1_opn safety_latch2_opn] \
	] "Flat Field Screen Control Logic Diagram: rev G"

###############################################################
#  You can only have ONE call to HARDWARE_STATUS for each variable name
#  Hardware status is the various named status bits that we always display
#  as colored buttons.

if ![info exists mcpData(cr_lava_lamp)] {
   set mcpData(cr_lava_lamp) 0
}

HARDWARE_STATUS big_button_status_args \
    {"building Alt/Az" \
	 {"clear :closed" "clear: closed"} \
	 {bldg_clear_alt bldg_clear_az} } \
    {"instrument_lift" \
	 {down:up} \
	 {inst_lift_dn}  } \
    {"lower_stop_buttons" \
	 {n s e w} \
	 {n_lower_stop  s_lower_stop  e_lower_stop  w_lower_stop}  } \
    {"rail_stop_buttons" \
	 {n s w} \
	 {n_rail_stop  s_rail_stop  w_rail_stop}  } \
    {"wind_stop_buttons" \
	 {n nfork nwfork s} \
	 {n_wind_stop  n_fork_stop nw_fork_stop s_wind_stop}   }\
    {"misc_stop_buttons" \
	 {ctrlRoom tcc} \
	 {cr_stop  tcc_stop}} \
    {"critical_systems" \
	 {mcp lavaLamp audioAlarms} {mcp_watchdog_timer cr_lava_lamp audioAlarms}}

###############################################################
# Watchslopes lets us define a slope and offset (as in mX+b) for 
# converting various analog readings to engineering units.
# "Analog" here means more than just 1 bit.
# This also defines the list of these analog variables that we want to view.
#  You can only have ONE call to WATCHSLOPES
# Or instead of giving two scaling constants, m and b, you can give
# a Tcl function that is used to convert the values.
# When a function is given, it must take exactly one input, which is the
# raw value, and return the converted value.

WATCHSLOPES  \
    {rot_1_voltage 0.000305 0 } \
    {rot_1_current 0.0001606 0}\
    {az_1_voltage 1.0 0 } \
    {az_1_current 1.0 0 } \
    {az_2_voltage 1.0 0 } \
    {az_2_current 1.0 0 } \
    {alt_1_voltage 1.0 0 } \
    {alt_1_current 1.0 0 } \
    {alt_2_voltage 1.0 0 } \
    {alt_2_current 1.0 0 } \
    {alt_position clino_convert } \
    {az_lvdt_error 1.0 0 } \
    {az_primary_drv 1.0 0 } \
    {az_feed_forward_drv 1.0 0 } \
    {alt_primary_drv 1.0 0 } \
    {inst_lift_force 1.0 0 } \
    {inst_lift_dist 1.0 0 } \
    {alt_lvdt_error 1.0 0 } \
    [list azvel:val  [expr 10.0/4096.0] 0] \
    [list altvel:val [expr 10.0/4096.0] 0] \
    [list rotvel:val [expr 10.0/4096.0] 0]

###############################################################
# sample function to do conversion, this one is for clinometer conversion.

proc clino_convert { inValue } {
   #
   # from the MCP axis_cmds.c:
   #
   # 8857 is pinned at 0 degrees; -9504 is zenith 90 degrees 22-Aug-98
   #
   set altclino_sf 0.0048683116163;	# scale factor
   set altclino_off 8937;		# offset

   return [expr ($altclino_off - $inValue)*$altclino_sf]
}

source $env(INTERLOCKS_DIR)/etc/instruments.tcl
source $env(INTERLOCKS_DIR)/etc/instrumentInterlocks.tcl

return ""
