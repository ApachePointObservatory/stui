array set interlockDescriptions [list \
   flip_flop_0 {Used to debounce the low level lighting switch and latch the light on.} \
   flip_flop_1 {Used to debounce the low level lighting switch and latch the light on.} \
   flip_flop_2 {Used to debounce the low level lighting switch and latch the light on.} \
   flip_flop_3 {Used to create e-stop led flasher.} \
   flip_flop_4 {Used to create e-stop led flasher.} \
   flip_flop_5 {Used to create e-stop led flasher.} \
   led_flash {E-stop led flash bit.} \
   e_stop_flash_reset {OSR used to reset the e-stop LED flash timer.} \
   ff_screens_closed {This bit indicates that all flat field screens are closed.} \
   ilcb_led_on {Turns on the instrument latch control box lights when at the zenith.} \
   lift_speed_man_ovrid {Used to overide MCP lift speed from the lift controls.} \
   ne_lamp_on_request {} \
   hgcd_lamp_on_request {} \
   az_mtr_iv_good {} \
   alt_mtr_iv_good {} \
   rot_mtr_iv_good {} \
   up_inhibit_latch {Altitude Up inhibit latch bit} \
   dn_inhibit_latch_1 {Altitude Down inhibit latch bit 1} \
   dn_inhibit_latch_2 {Altitude Down inhibit latch bit 2} \
   dn_inhibit_latch_3 {Altitude Down inhibit latch bit 3} \
   dn_inhibit_latch_4 {Altitude Down inhibit latch bit 4} \
   e_stop_permit {} \
   mcp_cont_slit_dr {} \
   plc_cont_slit_dr {} \
   mcp_cont_slit_hd {} \
   plc_cont_slit_hd {} \
   mcp_cont_t_bar_latch {} \
   plc_cont_t_bar_latch {} \
   disc_cable {Instrument ID Cable Disconnected} \
   no_inst_in_place {No Instrument on the telescope} \
   cartridge_1 {Cartridge 1 on the telescope} \
   cartridge_2 {Cartridge 2 on the telescope} \
   cartridge_3 {Cartridge 3 on the telescope} \
   cartridge_4 {Cartridge 4 on the telescope} \
   cartridge_5 {Cartridge 5 on the telescope} \
   cartridge_6 {Cartridge 6 on the telescope} \
   cartridge_7 {Cartridge 7 on the telescope} \
   cartridge_8 {Cartridge 8 on the telescope} \
   cartridge_9 {Cartridge 9 on the telescope} \
   eng_cam_in_place {Engineering Camera on the telescope} \
   undefined_3 {Undefined instrument on the telescope} \
   undefined_1 {Undefined instrument on the telescope} \
   undefined_2 {Undefined instrument on the telescope} \
   img_cam_in_place {Imaging Camera on the telescope} \
   version_id {Version 23  $Name$} \
   plc_cont_slit_dr_osr {} \
   plc_cont_slit_hd_osr {} \
   mcp_cont_t_bar_osr {} \
   plc_cont_t_bar_osr {} \
   plc_t_bar_xport {} \
   plc_t_bar_tel {} \
   mcp_cont_slit_dr_os1 {} \
   mcp_cont_slit_dr_os2 {} \
   mcp_cont_slit_dr_os3 {} \
   mcp_cont_slit_dr_os4 {} \
   plc_cont_slit_dr_opn {} \
   plc_cont_slit_dr_cls {} \
   sad_in_place {Saddle in place on the telescope} \
   sad_not_in_place {Saddle not in place on the telescope} \
   mcp_cont_slit_hd_os1 {} \
   mcp_cont_slit_hd_os2 {} \
   mcp_cont_slit_hd_os3 {} \
   mcp_cont_slit_hd_os4 {} \
   plc_cont_slit_hd_unl {} \
   plc_cont_slit_hd_lth {} \
   cor_in_place {Corrector lens in place} \
   cor_not_in_place {Corrector lens not in place} \
   cartg_in_place {Cartridge in place on the telescope} \
   pri_latch_opn {Primary latches open} \
   pri_latch_cls {Primary latches closed} \
   sec_latch_opn {Secondary latches open} \
   sec_latch_cls {Secondary latches closed} \
   sad_latch_opn {Saddle latches open} \
   sad_latch_cls {Saddle latches closed} \
   lift_empty {Instrument lift empty} \
   auto_mode_enable {Instrument change auto mode enabled} \
   cor_on_lift {Corrector lens on lift} \
   cam_on_lift_wo_j_hok {Camera on lift without umbilical on j hook} \
   cam_on_lift_w_j_hok {Camera on lift with umbilical on j hook} \
   cartg_on_lift {Cartridge on lift} \
   cartg_on_lift_comp {Cartridge on lift and compressed to telescope} \
   eng_cam_on_lift {Engineering camera on lift} \
   eng_cam_on_lift_comp {Engineering camera on lift and compressed to telescope} \
   lift_force_up_enable {Instrument lift up force enable} \
   lift_force_dn_enable {Instrument lift down force enable} \
   lift_up_enable {Instrument lift up enable} \
   lift_down_enable {Instrument lift down enable} \
   speed_1 {Lift Speed bit} \
   speed_2 {Lift Speed bit} \
   speed_3 {Lift Speed bit} \
   speed_4 {Lift Speed bit} \
   img_cam_up_in_place {Imaging camera up in place on the telescope} \
   cartg_up_in_place {Cartridge up in place on the telescope} \
   cor_up_in_place {Corrector lens up in place on the telescope} \
   eng_cam_up_in_place {Engineering camera up in place on the telescope} \
   empty_plate_on_lift {Empty plate on lift} \
   flex_io_fault {Flex I/O read/write fault} \
   altitude_at_inst_chg {Altitude at instrument change position} \
   lh_les_18d5 {Lift height less than 18.5 inches} \
   lh_lim_18d0_21d89 {Lift height between 18.0 and 21.89 inches} \
   lh_lim_18d0_22d8 {Lift height between 18.0 and 22.8 inches} \
   lh_lim_18d0_23d0 {Lift height between 18.0 and 23.0 inches} \
   lh_lim_2d2_18d5 {Lift height between 2.2 and 18.5 inches} \
   lh_lim_18d0_21d74 {Lift height between 18.0 and 21.74 inches} \
   lh_lim_18d0_22d5 {Lift height between 18.0 and 22.5 inches} \
   lh_lim_18d0_22d75 {Lift height between 18.0 and 22.75 inches} \
   lh_lim_2d5_18d5 {Lift height between 2.5 and 18.5 inches} \
   lh_lim_18d0_20d99 {Lift height between 18.0 and 20.99 inches} \
   lh_lim_18d0_22d0 {Lift height between 18.0 and 22.0 inches} \
   lh_lim_18d0_22d2 {Lift height between 18.0 and 22.2 inches} \
   lh_les_2d0 {Lift height less than 2.0 inches} \
   lh_lim_1d95_18d0 {Lift height between 1.95 and 18.0 inches} \
   lh_grt_17d5 {Lift height greater than 17.5 inches} \
   lh_grt_23d1 {Lift height greater than 23.1 inches} \
   lh_lim_22d3_23d1 {Lift height between 22.3 and 23.1 inches} \
   lh_lim_18d0_22d3 {Lift height between 18.0 and 22.3 inches} \
   lh_les_18d5_2 {Lift height less than 18.5 inches} \
   lh_les_0d75 {Lift height less than 0.75 inches} \
   lf_les_500 {Lift force less than 500 lbs.} \
   lh_lim_0d75_2d0 {Lift height between 0.75 and 2.0 inches} \
   lh_lim_2d0_20d0 {Lift height between 2.0 and 20.0 inches} \
   lf_les_350 {Lift force less than 350 lbs} \
   lf_les_1400 {Lift force less than 1400 lbs} \
   lf_les_350_2 {Lift force less than 350 lbs} \
   lf_les_450 {Lift force less than 450 lbs} \
   lf_les_200 {Lift force less than 200 lbs} \
   lf_les_150 {Lift force less than 150 lbs} \
   lf_les_350_3 {Lift force less than 350 lbs} \
   lh_lim_20d0_21d89 {Lift height between 20.0 and 21.89 inches} \
   lf_les_1650 {Lift force less than 1650 lbs} \
   lf_les_350_4 {Lift force less than 350 lbs} \
   lf_les_500_2 {Lift force less than 500 lbs} \
   lf_les_200_2 {Lift force less than 200 lbs} \
   lf_les_150_2 {Lift force less than 150 lbs} \
   lf_les_350_5 {Lift force less than 350 lbs} \
   lh_lim_21d89_22d3 {Lift height between 21.89 and 22.3 inches} \
   lf_les_1700 {Lift force less than 1700 lbs} \
   lf_les_400 {Lift force less than 400 lbs} \
   lf_les_500_3 {Lift force less than 500 lbs} \
   lf_les_200_3 {Lift force less than 200 lbs} \
   lf_les_150_3 {Lift force less than 150 lbs} \
   lf_les_400_2 {Lift force less than 400 lbs} \
   lh_lim_22d3_23d1_2 {Lift height between 22.3 and 23.1 inches} \
   lf_les_1100 {Lift force less than 1100 lbs} \
   lh_lim_23d1_23d3 {Lift height between 23.1 and 23.3 inches} \
   lf_les_800 {Lift force less than 800 lbs} \
   lh_les_0d75_2 {Lift height less than 0.75 inches} \
   lf_grt_neg_125 {Lift force greater than negative 125 lbs} \
   lh_lim_0d75_3d0 {Lift height between 0.75 and 3.0 inches} \
   lh_lim_2d0_20d0_2 {Lift height between 2.0 and 20.0 inches} \
   lf_grt_150 {Lift force greater than 150 lbs} \
   lf_grt_1100 {Lift force greater than 1100 lbs} \
   lf_grt_220 {Lift force greater than 220 lbs} \
   lf_grt_310 {Lift force greater than 310 lbs} \
   lf_grt_0d0 {Lift force greater than 0.0 lbs} \
   lf_grt_0d0_2 {Lift force greater than 0.0 lbs} \
   lf_grt_125 {Lift force greater than 125 lbs} \
   lh_lim_20d0_21d89_2 {Lift height between 20.0 and 21.89 inches} \
   lf_grt_150_2 {Lift force greater than 150 lbs} \
   lf_grt_220_2 {Lift force greater than 220 lbs} \
   lf_grt_310_2 {Lift force greater than 310 lbs} \
   lf_grt_0d0_3 {Lift force greater than 0.0 lbs} \
   lf_grt_0d0_4 {Lift force greater than 0.0 lbs} \
   lf_grt_125_2 {Lift force greater than 125 lbs} \
   lh_lim_21d89_22d3_2 {Lift height between 21.89 and 22.3 inches} \
   lf_grt_150_3 {Lift force greater than 150 lbs} \
   lf_grt_220_3 {Lift force greater than 220 lbs} \
   lf_grt_310_3 {Lift force greater than 310 lbs} \
   lf_grt_0d0_5 {Lift force greater than 0.0 lbs} \
   lf_grt_0d0_6 {Lift force greater than 0.0 lbs} \
   lf_grt_125_3 {Lift force greater than 125 lbs} \
   lh_lim_22d3_24d0 {Lift height between 22.3 and 24.0 inches} \
   lh_lim_21d8_22d15 {Lift height between 21.8 and 22.15 inches} \
   lf_grt_1400 {Lift force greater than 1400 lbs} \
   lh_lim_22d85_23d05 {Lift height between 22.85 and 23.05 inches} \
   lf_grt_950 {Lift force greater than 950 lbs} \
   lh_lim_22d89_23d09 {Lift height between 22.89 and 23.09 inches} \
   lf_grt_950_1 {Lift force greater than 950 lbs} \
   lh_lim_23d04_23d24 {Lift height between 23.04 and 23.24 inches} \
   lf_grt_750 {Lift force greater then 750 lbs} \
   lh_les_6d0 {Lift height less than 6.0} \
   lh_les_6d0_1 {Lift height less than 6.0} \
   lh_les_6d0_2 {Lift height less than 6.0} \
   lh_les_6d0_3 {Lift height less than 6.0} \
   lh_les_6d0_4 {Lift height less than 6.0} \
   lh_les_6d0_5 {Lift height less than 6.0} \
   az_bump_cw_delay {Az CW Bump signal} \
   az_bump_ccw_delay {Az CCW Bump signal} \
   alt_bump_up_delay {Alt Up Bump signal} \
   alt_bump_dn_delay {Alt Down bump signal} \
   im_ff_wht_on_req {} \
   im_ff_uv_on_req {} \
   spare_b3_13_15 {} \
   spare_b3_14_0 {} \
   spare_b3_14_1 {} \
   spare_b3_14_2 {} \
   spare_b3_14_3 {} \
   spare_b3_14_4 {} \
   spare_b3_14_5 {} \
   spare_b3_14_6 {} \
   spare_b3_14_7 {} \
   spare_b3_14_8 {} \
   spare_b3_14_9 {} \
   spare_b3_14_10 {} \
   spare_b3_14_11 {} \
   spare_b3_14_12 {} \
   spare_b3_14_13 {} \
   spare_b3_14_14 {} \
   spare_b3_14_15 {} \
   spare_b3_15_0 {} \
   spare_b3_15_1 {} \
   spare_b3_15_2 {} \
   spare_b3_15_3 {} \
   spare_b3_15_4 {} \
   spare_b3_15_5 {} \
   spare_b3_15_6 {} \
   spare_b3_15_7 {} \
   spare_b3_15_8 {} \
   spare_b3_15_9 {} \
   spare_b3_15_10 {} \
   spare_b3_15_11 {} \
   spare_b3_15_12 {} \
   spare_b3_15_13 {} \
   spare_b3_15_14 {} \
   spare_b3_15_15 {} \
   spare_b3_16_0 {} \
   spare_b3_16_1 {} \
   spare_b3_16_2 {} \
   spare_b3_16_3 {} \
   spare_b3_16_4 {} \
   spare_b3_16_5 {} \
   spare_b3_16_6 {} \
   spare_b3_16_7 {} \
   spare_b3_16_8 {} \
   spare_b3_16_9 {} \
   spare_b3_16_10 {} \
   spare_b3_16_11 {} \
   spare_b3_16_12 {} \
   spare_b3_16_13 {} \
   spare_b3_16_14 {} \
   spare_b3_16_15 {} \
   spare_b3_17_0 {} \
   spare_b3_17_1 {} \
   spare_b3_17_2 {} \
   spare_b3_17_3 {} \
   spare_b3_17_4 {} \
   spare_b3_17_5 {} \
   spare_b3_17_6 {} \
   spare_b3_17_7 {} \
   spare_b3_17_8 {} \
   spare_b3_17_9 {} \
   spare_b3_17_10 {} \
   spare_b3_17_11 {} \
   spare_b3_17_12 {} \
   spare_b3_17_13 {} \
   spare_b3_17_14 {} \
   spare_b3_17_15 {} \
   spare_b3_18_0 {} \
   spare_b3_18_1 {} \
   spare_b3_18_2 {} \
   spare_b3_18_3 {} \
   spare_b3_18_4 {} \
   spare_b3_18_5 {} \
   spare_b3_18_6 {} \
   spare_b3_18_7 {} \
   spare_b3_18_8 {} \
   spare_b3_18_9 {} \
   spare_b3_18_10 {} \
   spare_b3_18_11 {} \
   spare_b3_18_12 {} \
   spare_b3_18_13 {} \
   spare_b3_18_14 {} \
   spare_b3_18_15 {} \
   spare_b3_19_0 {} \
   spare_b3_19_1 {} \
   spare_b3_19_2 {} \
   spare_b3_19_3 {} \
   spare_b3_19_4 {} \
   spare_b3_19_5 {} \
   spare_b3_19_6 {} \
   spare_b3_19_7 {} \
   spare_b3_19_8 {} \
   spare_b3_19_9 {} \
   spare_b3_19_10 {} \
   spare_b3_19_11 {} \
   spare_b3_19_12 {} \
   spare_b3_19_13 {} \
   spare_b3_19_14 {} \
   spare_b3_19_15 {} \
   mcp_lift_high_psi {MCP command to turn on the high lift pressure for camera exchange for the instrument lift.} \
   mcp_lift_up_4 {Part of the binary code for up lift speed.} \
   mcp_lift_up_3 {Part of the binary code for up lift speed.} \
   mcp_lift_up_2 {Part of the binary code for up lift speed.} \
   mcp_lift_up_1 {Part of the binary code for up lift speed.} \
   mcp_lift_dn_1 {Part of the binary code for down lift speed.} \
   mcp_lift_dn_2 {Part of the binary code for down lift speed.} \
   mcp_lift_dn_3 {Part of the binary code for down lift speed.} \
   mcp_lift_dn_4 {Part of the binary code for down lift speed.} \
   mcp_pump_on {MCP command to turn on the instrument lift pump.} \
   mcp_solenoid_engage {MCP command to turn on the instrument lift solenoid.  The solenoid must be on for the lift to work} \
   mcp_az_brk_dis_cmd {MCP Azimuth brake disengage command bit from VME} \
   mcp_az_brk_en_cmd {MCP Azimuth brake engage command bit from VME} \
   mcp_alt_brk_dis_cmd {MCP Altitude brake disengage command bit from VME} \
   mcp_alt_brk_en_cmd {MCP Altitude brake engage command bit from VME} \
   mcp_clamp_engage_cmd {MCP Clamp engage command} \
   mcp_clamp_disen_cmd {MCP Clamp disengage command} \
   mcp_15deg_stop_ext_c {MCP 15 degree stop insert command} \
   mcp_15deg_stop_ret_c {MCP 15 degree stop remove command} \
   mcp_umbilical_up_dn {MCP camera umbilical motor up / down command line. 0=up 1=down} \
   mcp_umbilical_on_off {MCP camera umbilical motor on / off command line. 1=on 0=off} \
   mcp_slit_dr1_opn_cmd {MCP slithead door 1 open command bit from VME} \
   mcp_slit_dr1_cls_cmd {MCP slithead door 1 close command bit from VME} \
   mcp_slit_latch1_cmd {MCP slithead latch 1 control bit from VME 1=engage 0=disengage} \
   mcp_slit_dr2_opn_cmd {MCP slithead door 2 open command bit from VME} \
   mcp_slit_dr2_cls_cmd {MCP slithead door 2 close command bit from VME} \
   mcp_slit_latch2_cmd {MCP slithead latch2 control 1=engage 0=disengage} \
   mcp_ff_scrn_opn_cmd {MCP command to open the ff screen.} \
   mcp_ff_lamp_on_cmd {MCP command to turn the ff lamps on} \
   mcp_ne_lamp_on_cmd {MCP command to turn the ne lamps on} \
   mcp_hgcd_lamp_on_cmd {MCP command to turn on the hgcd lamps} \
   mcp_ff_screen_enable {Enable motion of the flat field screens} \
   mcp_t_bar_xport {MCP command to unlatch the t-bar latches} \
   mcp_t_bar_tel {MCP command to latch the t-bar latches} \
   mcp_purge_cell_on {MCP command to start the purge cell.} \
   mcp_pri_latch_cls_cm {MCP command to close the primary latches.} \
   mcp_pri_latch_opn_cm {MCP command to open the primary latches.} \
   mcp_sec_latch_cls_cm {MCP command to close the secondary latches.} \
   mcp_sec_latch_opn_cm {MCP command to open the secondary latches.} \
   mcp_sad_latch_cls_cm {MCP command to close the saddle latches.} \
   mcp_sad_latch_opn_cm {MCP command to open the saddle latches.} \
   mcp_inst_chg_prompt {MCP command to alert the observers for an instrument change prompt.} \
   mcp_inst_chg_alert {MCP command to alert the observers for an instrument change malfunction.} \
   mcp_ff_scrn2_opn_cmd {MCP command to open flat field screen 2} \
   mcp_ff_screen2_enabl {MCP command to enable flat field screen 2} \
   mcp_umbilical_fast {MCP umbilical fast speed command} \
   mcp_im_ff_wht_req {} \
   mcp_im_ff_uv_req {} \
   velocity_trp_rst_in {MCP command to reset a velocity trip in the slip detection module.} \
   az_mtr_1_res {Azimuth motor 1 calculated resistance value. Used for motor overtemp interlock.} \
   az_mtr_2_res {Azimuth motor 2 calculated resistance value. Used for motor overtemp interlock.} \
   alt_mtr_1_res {Altitude motor 1 calculated resistance value. Used for motor overtemp interlock.} \
   alt_mtr_2_res {Altitude motor 2 calculated resistance value. Used for motor overtemp interlock.} \
   rot_mtr_res {Rotator motor calculated resistance value. Used for motor overtemp interlock.} \
   alt_angle {Floating point calculation representing the altitude angle in degrees.} \
   scaled_lift_force {Instrument lift strain gage force.} \
   scaled_lift_dist {Instrument lift string pot distance. Scaled to inches.} \
   alt_grt_19d5_az {} \
   alt_grt_83d5_az {} \
   alt_91d0_limit {} \
   alt_90d5_limit {} \
   alt_83d5_limit {} \
   alt_84d0_limit {} \
   alt_19d5_limit {} \
   alt_20d0_limit {} \
   alt_15d5_limit {} \
   alt_16d0_limit {} \
   alt_0d5_limit {} \
   alt_1d0_limit {} \
   alt_30d0_limit {} \
   alt_89d0_limit {} \
   alt_5d8_limit {} \
   inst_chg_low_lmt {The Lower altitude limit to allow instrument change operations} \
   inst_chg_high_lmt {The Upper altitude limit to allow instrument change operations} \
   inst_lift_low_lmt {} \
   inst_lift_high_lmt {} \
   inst_lift_height_max {The maximum hieght the instrument lift is allowed to travel to} \
   ff_screen_alt_limit {Flatfield screen altitude limit} \
   deg_15_stop_ext_lmt {The 15 Degree stop extends at this value} \
   deg_15_stop_ret_lmt {The 15 Degree stop retracts at this value} \
   clamp_low_limit {The azimuth clamp will work above this limit and below CLAMP_HIGH_LIMIT} \
   clamp_high_limit {The azimuth clamp will work below this limit and above CLAMP_LOW_LIMIT} \
   clamp_stow_limit {The azimuth clamp will work below this limit} \
   inst_lift_pump_on {Instrument lift pump on status bit.} \
   inst_lift_sw1 {Instrument lift plate switch 1 status bit.} \
   inst_lift_sw2 {Instrument lift plate switch 2 status bit.} \
   inst_lift_sw3 {Instrument lift plate switch 3 status bit.} \
   inst_lift_sw4 {Instrument lift plate switch 4 status bit.} \
   inst_lift_dn {Instrument lift plate in the down position status bit.} \
   inst_lift_man {Instrument lift in the manual mode status bit.} \
   inst_lift_high_force {Instrument lift in high force status bit.} \
   inst_lift_low_force {Instrument lift in low force status bit.} \
   fiber_cart_pos1 {Fiber cartridge cart in position 1 status bit.} \
   fiber_cart_pos2 {Fiber cartridge cart in position 2 status bit.} \
   ops_cart_in_pos {Imager cart in position status bit.} \
   rack_0_grp_0_bit_12 {Spare input bit} \
   az_bump_cw {Azimuth telescope to windscreen clockwise bump switch.} \
   az_bump_ccw {Azimuth telescope to windscreen counter-clockwise bump switch.} \
   rack_0_grp_0_bit_15 {Spare PLC input bit.} \
   dog_house_cw_pad {Dog house cw bump switch.  Stops telescope and windscreen motion if dog house hits obj.} \
   dog_house_ccw_pad {Dog house ccw bump switch.  Stops telescope and windscreen motion if dog house hits obj.} \
   dog_house_door_opn {Dog house door open status bit.} \
   dog_house_door_cls {Dog house door closed status bit.} \
   ops_cart_in_house {Imager operations cart in dog house status bit.} \
   optical_bench_opn {T Bar latches open or off t bars. CCD's safe to move camera.} \
   optical_bench_cls {T Bar latches closed or on t bars. CCD's unsafe to move camera.} \
   rack_0_grp_1_bit_7 {Spare PLC input bit.} \
   rack_0_grp_1_bit_8 {Spare PLC input bit.} \
   rack_0_grp_1_bit_9 {Spare PLC input bit.} \
   rack_0_grp_1_bit_10 {Spare PLC input bit.} \
   rack_0_grp_1_bit_11 {Spare PLC input bit.} \
   rack_0_grp_1_bit_12 {Spare PLC input bit.} \
   rack_0_grp_1_bit_13 {Spare PLC input bit.} \
   rack_0_grp_1_bit_14 {Spare PLC input bit.} \
   low_lvl_light_req {Low lever lighting request to change state of low level lighting from off to on or on to off.} \
   spare_i1_l1 {MCP Place Holder. Not used in logic code.} \
   spare_i1_l2 {MCP Place Holder. Not used in logic code.} \
   spare_i1_l3 {MCP Place Holder. Not used in logic code.} \
   rot_inst_chg_a {First of two switches used to determine the rotator is at the instrument change po} \
   rot_inst_chg_b {Second of two switches used to determine rotator is at the instrument change position.} \
   rot_neg_190_cw {First cw inhibit switch for the rotator.  Causes a directional inhibit.} \
   rot_pos_370_ccw {First ccw inhibit switch for the rotator.  Causes a directional inhibit.} \
   ilcb_pres_good {Instrument latch control box air pressure status switch.} \
   inst_man_valve_cls {Imager latch manual valve closed status switch.} \
   sec_man_valve_cls {Secondary latch manual valve closed status switch.} \
   sad_man_valve_cls {Saddle latch manual valve closed status switch.} \
   iclb_leds_on_cmd {Latch control box LEDs on switch} \
   off_mode_sw {Latch control box Off mode switch} \
   auto_mode_sw {Latch control box Auto mode switch} \
   man_mode_switch {Latch control box Manual mode switch} \
   inst_chg_install_sw {Latch control box Instrument change Install switch} \
   inst_chg_remove_sw {Latch control box Instrument change Remove switch} \
   close_slit_doors {Latch control box Slithead door Close switch} \
   open_slit_doors {Latch control box Slithead door Open switch} \
   slit_latch_unlth_cmd {Slit head unlatch command input} \
   slit_latch_lth_cmd {Slit head latch command input} \
   tbar_latch_xport_cmd {Tbar latch transport command input} \
   tbar_latch_tel_cmd {Tbar latch telescope command input} \
   rack_1_grp_1_bit_4 {Spare PLC input bit.} \
   rack_1_grp_1_bit_5 {Spare PLC input bit.} \
   rack_1_grp_1_bit_6 {Spare PLC input bit.} \
   rack_1_grp_1_bit_7 {Spare PLC input bit.} \
   rack_1_grp_1_bit_8 {Spare PLC input bit.} \
   rack_1_grp_1_bit_9 {Spare PLC input bit.} \
   rack_1_grp_1_bit_10 {Spare PLC input bit.} \
   rack_1_grp_1_bit_11 {Spare PLC input bit.} \
   rack_1_grp_1_bit_12 {Spare PLC input bit.} \
   rack_1_grp_1_bit_13 {Spare PLC input bit.} \
   rack_1_grp_1_bit_14 {Spare PLC input bit.} \
   rack_1_grp_1_bit_15 {Spare PLC input bit.} \
   spare_i1_l5 {MCP Place Holder. Not used in logic code.} \
   spare_i1_l6 {MCP Place Holder. Not used in logic code.} \
   spare_i1_l7 {MCP Place Holder. Not used in logic code.} \
   inst_id1_1 {Instrument ID block 1 switch 1 status.} \
   inst_id1_2 {Instrument ID block 1 switch 2 status.} \
   inst_id1_3 {Instrument ID block 1 switch 3 status.} \
   inst_id1_4 {Instrument ID block 1 switch 4 status.} \
   inst_id2_1 {Instrument ID block 2 switch 1 status.} \
   inst_id2_2 {Instrument ID block 2 switch 2 status.} \
   inst_id2_3 {Instrument ID block 2 switch 3 status.} \
   inst_id2_4 {Instrument ID block 2 switch 4 status.} \
   inst_id3_1 {Instrument ID block 3 switch 1 status.} \
   inst_id3_2 {Instrument ID block 3 switch 2 status.} \
   inst_id3_3 {Instrument ID block 3 switch 3 status.} \
   inst_id3_4 {Instrument ID block 3 switch 4 status.} \
   spec_lens1 {Spectrographic corrector lens mount position 1 switch.} \
   spec_lens2 {Spectrographic corrector lens mount position 2 switch.} \
   spec_autofill_on {Spectrograph autofill system connected.  Altitude and Rotator motion disabled.} \
   rack_2_grp_0_bit_15 {Spare PLC input bit.} \
   pri_latch1_opn {Primary latch 1 open status.} \
   pri_latch1_cls {Primary latch 1 closed status.} \
   pri_latch2_opn {Primary latch 2 open status.} \
   pri_latch2_cls {Primary latch 2 closed status.} \
   pri_latch3_opn {Primary latch 3 open status.} \
   pri_latch3_cls {Primary latch 3 closed status.} \
   sec_latch1_opn {Secondary latch 1 open status.} \
   sec_latch1_cls {Secondary latch 1 closed status.} \
   sec_latch2_opn {Secondary latch 2 open status.} \
   sec_latch2_cls {Secondary latch 2 closed status.} \
   sec_latch3_opn {Secondary latch 3 open status.} \
   sec_latch3_cls {Secondary latch 3 closed status.} \
   safety_latch1_opn {Protection bolt 1 open status.} \
   safety_latch1_cls {Protection bolt 1 closed status.} \
   safety_latch2_opn {Protection bolt 2 open status.} \
   safety_latch2_cls {Protection bolt 2 closed status.} \
   sad_latch1_opn {Saddle latch 1 open status.} \
   sad_latch1_cls {Saddle latch 1 closed status.} \
   sad_latch2_opn {Saddle latch 2 open status.} \
   sad_latch2_cls {Saddle latch 2 closed status.} \
   sad_mount1 {Saddle mount position 1 switch.} \
   sad_mount2 {Saddle mount position 2 switch.} \
   slit_head_door1_opn {Slit head door 1 open status.} \
   slit_head_door1_cls {Slit head door 1 closed status.} \
   slit_head_latch1_ext {Cartridge latch 1 extended status.} \
   slit_head_1_in_place {Cartridge 1 in place status.} \
   slit_head_door2_opn {Slit head door 2 open status.} \
   slit_head_door2_cls {Slit head door 2 closed status.} \
   slit_head_latch2_ext {Cartridge latch 2 extended status.} \
   slit_head_2_in_place {Cartridge 2 in place status.} \
   rack_2_grp_2_bit_14 {Spare PLC input bit.} \
   rack_2_grp_2_bit_15 {Spare PLC input bit.} \
   purge_air_pressur_sw {Purge air pressure switch} \
   alt_bump_up {Altitude telescope to windscreen up bump switch.} \
   alt_bump_dn {Altitude telescope to windscreen down bump switch.} \
   sec_mir_force_limits {Secondary Mirror Force Limit bit.} \
   rack_2_grp_4_bit_4 {Spare PLC input bit.} \
   rack_2_grp_4_bit_5 {Spare PLC input bit.} \
   rack_2_grp_4_bit_6 {Spare PLC input bit.} \
   rack_2_grp_4_bit_7 {Spare PLC input bit.} \
   rack_2_grp_4_bit_8 {Spare PLC input bit.} \
   rack_2_grp_4_bit_9 {Spare PLC input bit.} \
   rack_2_grp_4_bit_10 {Spare PLC input bit.} \
   rack_2_grp_4_bit_11 {Spare PLC input bit.} \
   rack_2_grp_4_bit_12 {Spare PLC input bit.} \
   rack_2_grp_4_bit_13 {Spare PLC input bit.} \
   rack_2_grp_4_bit_14 {Spare PLC input bit.} \
   rack_2_grp_4_bit_15 {Spare PLC input bit.} \
   spare_i1_l11 {MCP Place Holder. Not used in logic code.} \
   spare_i1_l12 {MCP Place Holder. Not used in logic code.} \
   rack_3_grp_1_bit_0 {Spare PLC input bit.} \
   inst_lift_auto {Instrument lift in automatic position.} \
   man_lift_up_1 {Manual control lift up 1 switch.} \
   man_lift_up_2 {Manual control lift up 2 switch.} \
   man_lift_up_3 {Manual control lift up 3 switch.} \
   man_lift_up_4 {Manual control lift up 4 switch.} \
   man_lift_dn_1 {Manual control lift down 1 switch.} \
   man_lift_dn_2 {Manual control lift down 2 switch.} \
   man_lift_dn_3 {Manual control lift down 3 switch.} \
   man_lift_dn_4 {Manual control lift down 4 switch.} \
   rack_3_grp_1_bit_10 {Spare PLC input bit.} \
   rack_3_grp_1_bit_11 {Spare PLC input bit.} \
   rack_3_grp_1_bit_12 {Spare PLC input bit.} \
   rack_3_grp_1_bit_13 {Spare PLC input bit.} \
   rack_3_grp_1_bit_14 {Spare PLC input bit.} \
   rack_3_grp_1_bit_15 {Spare PLC input bit.} \
   screen_status {FF Screen status word} \
   leaf_1_open_stat {Leaf Screen 1 open status bit} \
   leaf_1_closed_stat {Leaf Screen 1 closed status bit} \
   leaf_2_open_stat {Leaf Screen 2 open status bit} \
   leaf_2_closed_stat {Leaf Screen 2 closed status bit} \
   leaf_3_open_stat {Leaf Screen 3 open status bit} \
   leaf_3_closed_stat {Leaf Screen 3 closed status bit} \
   leaf_4_open_stat {Leaf Screen 4 open status bit} \
   leaf_4_closed_stat {Leaf Screen 4 closed status bit} \
   leaf_5_open_stat {Leaf Screen 5 open status bit} \
   leaf_5_closed_stat {Leaf Screen 5 closed status bit} \
   leaf_6_open_stat {Leaf Screen 6 open status bit} \
   leaf_6_closed_stat {Leaf Screen 6 closed status bit} \
   leaf_7_open_stat {Leaf Screen 7 open status bit} \
   leaf_7_closed_stat {Leaf Screen 7 closed status bit} \
   leaf_8_open_stat {Leaf Screen 8 open status bit} \
   leaf_8_closed_stat {Leaf Screen 8 closed status bit} \
   lamp_status {Flatfield Lamp Status Word} \
   ff_1_stat {Flatfield lamp 1 status bit} \
   ff_2_stat {Flatfield lamp 2 status bit} \
   ff_3_stat {Flatfield lamp 3 status bit} \
   ff_4_stat {Flatfield lamp 4 status bit} \
   ne_1_stat {Neon lamp 1 status bit} \
   ne_2_stat {Neon lamp 2 status bit} \
   ne_3_stat {Neon lamp 3 status bit} \
   ne_4_stat {Neon lamp 4 status bit} \
   hgcd_1_stat {Mercury-cadmium lamp 1 status bit} \
   hgcd_2_stat {Mercury-cadmium lamp 2 status bit} \
   hgcd_3_stat {Mercury-cadmium lamp 3 status bit} \
   hgcd_4_stat {Mercury-cadmium lamp 4 status bit} \
   rack_3_grp_3_bit_12 {Spare PLC input bit.} \
   rack_3_grp_3_bit_13 {Spare PLC input bit.} \
   rack_3_grp_3_bit_14 {Spare PLC input bit.} \
   rack_3_grp_3_bit_15 {Spare PLC input bit.} \
   man_ff_scrn_opn_cmd {Manual flatfield screen open command} \
   man_ff_scrn_en_cmd {Manual flatfield screen enable command} \
   man_ff_lamp_on_cmd {Manual flatfield lamps on command} \
   man_ne_lamp_on_cmd {Manual Neon lamps on command} \
   man_hgcd_lamp_on_cmd {Manual mercury cadmium lamps on command} \
   ff_man_cont_enable {Manual flatfield control module connected to telescope.  Alt and Az motion disabled.} \
   man_im_ff_wht_req {Manual input to turn on the imager ff white lamps} \
   man_im_ff_uv_req {Manual input to turn on the imager ff UV lamps} \
   rack_3_grp_4_bit_8 {Spare PLC input bit.} \
   rack_3_grp_4_bit_9 {Spare PLC input bit.} \
   rack_3_grp_4_bit_10 {Spare PLC input bit.} \
   rack_3_grp_4_bit_11 {Spare PLC input bit.} \
   rack_3_grp_4_bit_12 {Spare PLC input bit.} \
   rack_3_grp_4_bit_13 {Spare PLC input bit.} \
   rack_3_grp_4_bit_14 {Spare PLC input bit.} \
   rack_3_grp_4_bit_15 {Spare PLC input bit.} \
   spare_i1_l15 {MCP Place Holder. Not used in logic code.} \
   dcm_1_status_word {Direct communications module 1 status word.} \
   wind_dc_input_card {Windscreen digital input card values.} \
   wind_az1_fault {Windscreen azimuth amplifier 1 fault bit.} \
   wind_az2_fault {Windscreen azimuth amplifier 2 fault bit.} \
   wind_az3_fault {Windscreen azimuth amplifier 3 fault bit.} \
   wind_alt1_fault {Windscreen altitude amplifier fault bit.} \
   wind_az_perm {Windscreen azimuth motion permit bit.} \
   wind_alt_perm {Windscreen altitude motion permit bit.} \
   spare {Spare PLC input bit.} \
   az_pid_status {Azimuth PID Status Word} \
   az_lvdt_error {Azimuth LVDT error analog value.} \
   az_pri_drv {Azimuth primary drive value.} \
   az_feed_fwd_drv {Azimuth feed forward drive value.} \
   dcm_1_word6_spare {DCM 1 spare word} \
   dcm_1_word7_spare {DCM 1 spare word} \
   dcm_2_status_word {Direct communications module 2 status word.} \
   dcm_2_word1_spare {DCM 2 spare word} \
   alt_pid_status {Altitude PID Status Word} \
   alt_lvdt_error {Altitude LVDT error analog value.} \
   alt_pri_drv {Altitude primary drive value.} \
   dcm_2_word5_spare {DCM 2 spare word} \
   dcm_2_word6_spare {DCM 2 spare word} \
   dcm_2_word7_spare {DCM 2 spare word} \
   az_1_voltage {Azimuth motor 1 voltage.} \
   az_1_current {Azimuth motor 1 current.} \
   az_2_voltage {Azimuth motor 2 voltage.} \
   az_2_current {Azimuth motor 2 current.} \
   alt_1_voltage {Altitude motor 1 voltage.} \
   alt_1_current {Altitude motor 1 current.} \
   alt_2_voltage {Altitude motor 2 voltage.} \
   alt_2_current {Altitude motor 2 current.} \
   alt_position {Altitude clinometer raw position value.} \
   rot_1_voltage {Rotator motor voltage.} \
   rot_1_current {Rotator motor current.} \
   umbilical_dist {Camera umbilical distance value.} \
   inst_lift_force {Instrument lift strain gauge value.} \
   inst_lift_dist {Instrument lift string pot distance value. Scale = .001} \
   i_4_analog_6_spare {Spare analog channel.} \
   i_4_analog_7_spare {Spare analog channel.} \
   counterweight_1_pos {Counterweight #1 string pot position value} \
   counterweight_2_pos {Counterweight #2 string pot position value} \
   counterweight_3_pos {Counterweight #3 string pot position value} \
   counterweight_4_pos {Counterweight #4 string pot position value} \
   i_5_analog_4_spare {Spare analog channel.} \
   i_5_analog_5_spare {Spare analog channel.} \
   i_5_analog_6_spare {Spare analog channel.} \
   i_5_analog_7_spare {Spare analog channel.} \
   tcc_stop {TCC inhibit input hook.  Currently not implemented.} \
   cr_stop {Control Room e-stop switch.} \
   spare_s1_c2 {Spare splitter chassis channel.} \
   fiber_signal_loss {Control room e-stop fiber link signal loss indicator. Currently not implemented.} \
   n_wind_stop {North wind screen e-stop} \
   n_fork_stop {North fork e-stop} \
   n_rail_stop {North railing e-stop} \
   s_rail_stop {South railing e-stop} \
   w_rail_stop {West railing e-stop} \
   n_lower_stop {North lower level e-stop} \
   s_lower_stop {South lower level e-stop} \
   e_lower_stop {East lower level e-stop} \
   w_lower_stop {West lower level e-stop} \
   s_wind_stop {South wind screen e-stop} \
   nw_fork_stop {North West Fork E-Stop} \
   mcp_watchdog_timer {MCP Watchdog Timer. Removes drive amplifier reference if MCP Fault.} \
   alt_mtr_up_perm_in {Altitude motor up permit status} \
   alt_mtr_dn_perm_in {Altitude motor down permit status} \
   alt_mtr1_perm_in {Altitude motor 1 permit status} \
   alt_mtr2_perm_in {Altitude motor 2 permit status} \
   wind_alt_mtr_perm_in {Wind screen altitude motor permit in} \
   alt_plc_perm_in {Altitude PLC permit status} \
   wind_alt_plc_perm_in {Wind screen PLC permit status} \
   az_stow_3a {Azimuth stow position switch status} \
   az_mtr_cw_perm_in {Azimuth motor CW permit status} \
   az_mtr_ccw_perm_in {Azimuth motor CCW permit status} \
   az_mtr1_perm_in {Azimuth motor 1 permit status} \
   az_mtr2_perm_in {Azimuth motor 2 permit status} \
   wind_az_mtr_perm_in {Wind screen azimuth motor permit status} \
   az_plc_perm_in {Azimuth PLC permit status} \
   wind_az_plc_perm_in {Wind screen PLC permit status} \
   az_stow_3b {Azimuth stow position switch status} \
   rot_mtr_cw_perm_in {Rotator motor CW permit status} \
   rot_mtr_ccw_perm_in {Rotator motor CCW permit status} \
   rot_mtr_perm_in {Rotator motor permit status} \
   spare_s5_c3 {Spare splitter chassis channel} \
   bldg_perm_in {Building motion permit status} \
   rot_plc_perm_in {Rotator PLC permit status} \
   hatch_cls {Hatch closed status switch} \
   alt_les_2d5_limit {Altitude greater then 2.5 degree limit status} \
   alt_grt_0d3_limit {Altitude greater then 0.3 degree limit status} \
   alt_locking_pin_out {Altitude locking pin out status} \
   alt_les_90d5_limit {Altitude less than 90.5 degree limit status} \
   bldg_on_alt {Building on status for altitude logic} \
   az_109_131_limit_1 {Azimuth between 109 to 131 degrees status} \
   alt_grt_18d6_limit_1 {Altitude greater than 18.6 degree limit status} \
   az_stow_1a {Azimuth stow position status} \
   az_stow_1b {Azimuth stow position status} \
   alt_grt_83_limit_1 {Altitude greater than 83 degree limit status} \
   bldg_clear_alt {Building clear status for altitude logic} \
   az_stow_2a {Azimuth stow position status} \
   az_stow_2b {Azimuth stow position status} \
   deg_15_stop_ext {15 degree stop extended status} \
   alt_grt_18d6_limit_2 {Altitude greater than 18.6 degree limit status} \
   alt_slip {Altitude slip detection status} \
   alt_velocity_limit {Altitude velocity limit status} \
   az_dir_cw {Azimuth direction CW status} \
   az_dir_ccw {Azimuth direction CCW status} \
   az_neg_201a_cw {Azimuth greater then -201 degrees status} \
   az_pos_445a_ccw {Azimuth less than +445 degree limit status} \
   az_neg_201b_cw {Azimuth greater than -201 degrees status} \
   az_pos_445b_ccw {Azimuth less than +445 degree limit status} \
   spare_s8_c6 {Spare splitter chassis channel} \
   spare_s8_c7 {Spare splitter chassis channel} \
   alt_grt_18d6_limit_3 {Altitude greater than 18.6 degree limit status} \
   bldg_on_az {Building on status for Azimuth logic} \
   az_109_131_limit_2 {Azimuth between 109 and 131 degrees limit status} \
   alt_grt_83_limit_2 {Altitude greater then 83 degree limit status} \
   bldg_clear_az {Building clear status for Azimuth logic} \
   spare_s9_c5 {Spare splitter chassis channel} \
   az_slip {Azimuth slip detection status} \
   az_velocity_limit {Azimuth velocity limit status} \
   rot_dir_cw {Rotator direction CW status} \
   rot_dir_ccw {Rotator direction CCW status} \
   rot_neg_200a_cw {Rotator greater then -200 degrees status} \
   rot_pos_380a_ccw {Rotator less than +300 degree limit status} \
   rot_neg_200b_cw {Rotator greater then -200 degrees status} \
   rot_pos_380b_ccw {Rotator less than +300 degree limit status} \
   rot_slip {Rotator slip detection status} \
   rot_velocity_limit {Rotator velocity limit status} \
   az_stow_cntr_sw {Azimuth stow center switch status} \
   az_110_130_limit {Azimuth between 110 and 130 degree limit status} \
   az_neg_196_cw {Azimuth greater than -196 degree limit status} \
   az_pos_440_ccw {Azimuth less than +440 degree limit status} \
   az_mtr1_rdy {Azimuth motor 1 ready status} \
   az_mtr2_rdy {Azimuth motor 2 ready status} \
   alt_mtr1_rdy {Altitude motor 1 ready status} \
   alt_mtr2_rdy {Altitude motor 2 ready status} \
   rot_mtr_rdy {Rotator motor ready status} \
   umbilical_strain_sw {Camera umbilical strain switch status} \
   e_stop_byp_sw {E-stop bypass strobe enable key switch status} \
   deg_15_stop_ret {15 degree stop retracted (will not stop telescope altitude motion)} \
   in_8_bit_28_spare {Spare PLC Input Bit} \
   in_8_bit_29_spare {Spare PLC Input Bit} \
   in_8_bit_30_spare {Spare PLC Input Bit} \
   t_bar_xport_stat {Camera T-Bar latch latched status} \
   t_bar_tel_stat {Camera T-Bar latch unlatched status} \
   clamp_en_stat {Clamp engaged status} \
   clamp_dis_stat {Clamp disengaged status} \
   az_brake_en_stat {Azimuth brake enabled status} \
   az_brake_dis_stat {Azimuth brake disabled status} \
   alt_brake_en_stat {Altitude brake enabled status} \
   alt_brake_dis_stat {Altitude brake disabled status} \
   low_lvl_lighting_req {Low lever lighting state change request bit.} \
   solenoid_engage_sw {Solenoid engage (dead mans switch)} \
   alt_locking_pin_in {Altitude Locking Pin In place bit.} \
   in_9_bit_10_spare {Spare PLC Input Bit} \
   in_9_bit_11_spare {Spare PLC Input Bit} \
   in_9_bit_12_spare {Spare PLC Input Bit} \
   in_9_bit_13_spare {Spare PLC Input Bit} \
   in_9_bit_14_spare {Spare PLC Input Bit} \
   in_9_bit_15_spare {Spare PLC Input Bit} \
   s1_c0_bypass_sw {E-Stop bypass monitor status} \
   s1_c1_bypass_sw {E-Stop bypass monitor status} \
   s1_c2_bypass_sw {E-Stop bypass monitor status} \
   s1_c3_bypass_sw {E-Stop bypass monitor status} \
   s1_c4_bypass_sw {E-Stop bypass monitor status} \
   s1_c5_bypass_sw {E-Stop bypass monitor status} \
   s1_c6_bypass_sw {E-Stop bypass monitor status} \
   s1_c7_bypass_sw {E-Stop bypass monitor status} \
   s2_c0_bypass_sw {E-Stop bypass monitor status} \
   s2_c1_bypass_sw {E-Stop bypass monitor status} \
   s2_c2_bypass_sw {E-Stop bypass monitor status} \
   s2_c3_bypass_sw {E-Stop bypass monitor status} \
   s2_c4_bypass_sw {E-Stop bypass monitor status} \
   s2_c5_bypass_sw {E-Stop bypass monitor status} \
   s2_c6_bypass_sw {E-Stop bypass monitor status} \
   s2_c7_mcp_wtchdg_byp {MCP watchdog bypass monitor status} \
   in_10_bit_0_spare {Spare PLC Input Bit} \
   in_10_bit_1_spare {Spare PLC Input Bit} \
   in_10_bit_2_spare {Spare PLC Input Bit} \
   in_10_bit_3_spare {Spare PLC Input Bit} \
   in_10_bit_4_spare {Spare PLC Input Bit} \
   in_10_bit_5_spare {Spare PLC Input Bit} \
   in_10_bit_6_spare {Spare PLC Input Bit} \
   in_10_bit_7_spare {Spare PLC Input Bit} \
   in_10_bit_8_spare {Spare PLC Input Bit} \
   in_10_bit_9_spare {Spare PLC Input Bit} \
   in_10_bit_10_spare {Spare PLC Input Bit} \
   in_10_bit_11_spare {Spare PLC Input Bit} \
   in_10_bit_12_spare {Spare PLC Input Bit} \
   in_10_bit_13_spare {Spare PLC Input Bit} \
   in_10_bit_14_spare {Spare PLC Input Bit} \
   in_10_bit_15_spare {Spare PLC Input Bit} \
   in_10_bit_16_spare {Spare PLC Input Bit} \
   in_10_bit_17_spare {Spare PLC Input Bit} \
   in_10_bit_18_spare {Spare PLC Input Bit} \
   in_10_bit_19_spare {Spare PLC Input Bit} \
   in_10_bit_20_spare {Spare PLC Input Bit} \
   in_10_bit_21_spare {Spare PLC Input Bit} \
   in_10_bit_22_spare {Spare PLC Input Bit} \
   in_10_bit_23_spare {Spare PLC Input Bit} \
   in_10_bit_24_spare {Spare PLC Input Bit} \
   in_10_bit_25_spare {Spare PLC Input Bit} \
   in_10_bit_26_spare {Spare PLC Input Bit} \
   in_10_bit_27_spare {Spare PLC Input Bit} \
   in_10_bit_28_spare {Spare PLC Input Bit} \
   in_10_bit_29_spare {Spare PLC Input Bit} \
   in_10_bit_30_spare {Spare PLC Input Bit} \
   in_10_bit_31_spare {Spare PLC Input Bit} \
   az_mtr_1_abs_volts {Azimuth motor 1 absolute voltage} \
   az_mtr_1_abs_amps {Azimuth motor 1 absolute current} \
   az_mtr_2_abs_volts {Azimuth motor 2 absolute voltage} \
   az_mtr_2_abs_amps {Azimuth motor 2 absolute current} \
   alt_mtr_1_abs_volts {Altitude motor 1 absolute voltage} \
   alt_mtr_1_abs_amps {Altitude motor 1 absolute current} \
   alt_mtr_2_abs_volts {Altitude motor 2 absolute voltage} \
   alt_mtr_2_abs_amps {Altitude motor 2 absolute current} \
   rot_mtr_abs_volts {Rotator motor absolute voltage} \
   rot_mtr_abs_amps {Rotator motor absolute current} \
   lift_force_display {Instrument lift hand held force display scale factors.} \
   lift_dist_display {Instrument lift hand held distance display scale factors.} \
   spare_o1_l0 {MCP Place Holder. Not used in logic code.} \
   inst_lift_high_psi {Instrument lift high pressure enable bit} \
   inst_lift_up_4 {Instrument lift up speed bit 4} \
   inst_lift_up_3 {Instrument lift up speed bit 3} \
   inst_lift_up_2 {Instrument lift up speed bit 2} \
   inst_lift_up_1 {Instrument lift up speed bit 1} \
   inst_lift_dn_1 {Instrument lift down speed bit 1} \
   inst_lift_dn_2 {Instrument lift down speed bit 2} \
   inst_lift_dn_3 {Instrument lift down speed bit 3} \
   inst_lift_dn_4 {Instrument lift down speed bit 4} \
   lamp_on_enable {NE and HGCD lamp enable relay.} \
   rack_0_grp_2_bit_10 {Spare PLC Output Bit} \
   az_stow_center_light {Turns on the azimuth stow position center light.} \
   stop_bypass_strobe {E-Stop bypass warning strobe enable bit} \
   az_stow_light {Azimuth stow indicator light output bit} \
   low_lvl_light_1 {Low level lighting enable bit 1} \
   low_lvl_light_2 {Low level lighting enable bit 2} \
   spare_o1_l2 {MCP Place Holder. Not used in logic code.} \
   spare_01_l3 {MCP Place Holder. Not used in logic code.} \
   spare_o1_l4 {MCP Place Holder. Not used in logic code.} \
   cor_on_lift_led {Corrector on Lift LED} \
   cam_on_lift_led {Camera on Lift LED} \
   cartg_on_lift_led {Cartridge on Lift LED} \
   eng_on_lift_led {Eng Camera on Lift LED} \
   cor_in_place_led {Corrector in place LED} \
   cam_in_place_led {Camera in place LED} \
   cartg_in_place_led {Cartridge in place LED} \
   eng_in_place_led {Eng Camera in place LED} \
   sad_in_place_led {Saddle in place LED} \
   jhook_in_place_led {J Hook in place LED} \
   dog_door_open_led {Dog house door not closed LED} \
   cam_crt_in_house_led {Camera cart in dog house LED} \
   cart_in_place_led {Cart in  place LED} \
   lift_down_led {Lift plate down LED} \
   slit1_unlatched_led {Slit head 1  unltched LED} \
   slit1_latched_led {Slit head 1  latched LED} \
   slit2_unlatched_led {Slit head 2 unltched LED} \
   slit2_latched_led {Slit head 2 latched LED} \
   slit_unlatch_prm_led {Slit head unlatch permit LED} \
   slit_latch_prm_led {Slit head latch permit LED} \
   inst_latch1_opn_led {ILCB Instrument latch 1 open LED} \
   inst_latch1_cls_led {ILCB Instrument latch 1 closed LED} \
   inst_latch2_opn_led {ILCB Instrument latch 2 open LED} \
   inst_latch2_cls_led {ILCB Instrument latch 2 closed LED} \
   inst_latch3_opn_led {ILCB Instrument latch 3 open LED} \
   inst_latch3_cls_led {ILCB Instrument latch 3 closed LED} \
   inst_unlatch_perm {Instrument latch unlatch permit} \
   inst_latch_perm {Instrument latch latch permit} \
   sec_latch1_opn_led {ILCB Secondary latch 1 open LED} \
   sec_latch1_cls_led {ILCB Secondary latch 1 closed LED} \
   sec_latch2_opn_led {ILCB Secondary latch 2 open LED} \
   sec_latch2_cls_led {ILCB Secondary latch 2 closed LED} \
   sec_latch3_opn_led {ILCB Secondary latch 3 open LED} \
   sec_latch3_cls_led {ILCB Secondary latch 3 closed LED} \
   sec_unlatch_perm {Secondary latch unlatch permit} \
   sec_latch_perm {Secondary latch latch permit} \
   sad_latch1_opn_led {ILCB Saddle latch 1 open status LED} \
   sad_latch1_cls_led {ILCB Saddle latch 1 closed status LED} \
   sad_latch2_opn_led {ILCB Saddle latch 2 open status LED} \
   sad_latch2_cls_led {ILCB Saddle latch 2 closed status LED} \
   sad_unlatch_perm {Saddle latch unlatch permit} \
   sad_latch_perm {Saddle latch latch permit} \
   tbar_xport_led {T Bar latch transport status LED} \
   tbar_tel_led {T Bar latch telescope status LED} \
   tbar_xport_perm_led {T Bar latch transport permit LED} \
   tbar_tel_perm_led {T Bar latch telescope permit LED} \
   slit_dr_cls_perm_led {Slit head door close permit LED} \
   slit_dr_opn_perm_led {Slit head door open permit LED} \
   slit_dr1_cls_led {Slit head door 1 closed status LED} \
   slit_dr1_opn_led {Slit head door 1 open status LED} \
   slit_dr2_cls_led {Slit head door 2 closed status LED} \
   slit_dr2_opn_led {Slit head door 2 open status LED} \
   ilcb_pres_led {ILCB air pressure good LED} \
   inst_latch_air_led {Instrument latch air on status LED} \
   sec_latch_air_led {Secondary latch air on status LED} \
   sad_latch_air_led {Saddle latch air on status LED} \
   manual_mode_led {Manual mode status LED} \
   saf_latch1_opn_led {ILCB Protection bolt 1 open LED} \
   saf_latch1_cls_led {ILCB Protection bolt 1 closed LED} \
   saf_latch2_opn_led {ILCB Protection bolt 2 open LED} \
   saf_latch2_cls_led {ILCB Protection bolt 2 closed LED} \
   rack_1_grp_5_bit_13 {Spare PLC output bit.} \
   rack_1_grp_5_bit_14 {Spare PLC output bit.} \
   rack_1_grp_5_bit_15 {Spare PLC output bit.} \
   spare_o1_l7 {MCP Place Holder. Not used in logic code.} \
   spare_o1_l8 {MCP Place Holder. Not used in logic code.} \
   spare_o1_l9 {MCP Place Holder. Not used in logic code.} \
   slit_dr1_cls_perm {Slithead door 1 close permit} \
   slit_dr1_opn_perm {Slithead door 1 open permit} \
   slit_latch1_ext_perm {Slithead latch 1 extended permit} \
   slit_dr2_cls_perm {Slithead door 2 close permit} \
   slit_dr2_opn_perm {Slithead door 2 open permit} \
   slit_latch2_ext_perm {Slithead latch 2 extended permit} \
   rack_2_grp_3_bit_6 {Spare PLC output bit.} \
   rack_2_grp_3_bit_7 {Spare PLC output bit.} \
   rack_2_grp_3_bit_8 {Spare PLC output bit.} \
   rack_2_grp_3_bit_9 {Spare PLC output bit.} \
   rack_2_grp_3_bit_10 {Spare PLC output bit.} \
   rack_2_grp_3_bit_11 {Spare PLC output bit.} \
   rack_2_grp_3_bit_12 {Spare PLC output bit.} \
   rack_2_grp_3_bit_13 {Spare PLC output bit.} \
   rack_2_grp_3_bit_14 {Spare PLC output bit.} \
   rack_2_grp_3_bit_15 {Spare PLC output bit.} \
   spare_o1_l10 {MCP Place Holder. Not used in logic code.} \
   purge_valve_permit {Purge valve permit} \
   rack_2_grp_5_bit_1 {Spare PLC output bit.} \
   rack_2_grp_5_bit_2 {Spare PLC output bit.} \
   rack_2_grp_5_bit_3 {Spare PLC output bit.} \
   rack_2_grp_5_bit_4 {Spare PLC output bit.} \
   rack_2_grp_5_bit_5 {Spare PLC output bit.} \
   rack_2_grp_5_bit_6 {Spare PLC output bit.} \
   rack_2_grp_5_bit_7 {Spare PLC output bit.} \
   rack_2_grp_5_bit_8 {Spare PLC output bit.} \
   rack_2_grp_5_bit_9 {Spare PLC output bit.} \
   rack_2_grp_5_bit_10 {Spare PLC output bit.} \
   rack_2_grp_5_bit_11 {Spare PLC output bit.} \
   rack_2_grp_5_bit_12 {Spare PLC output bit.} \
   rack_2_grp_5_bit_13 {Spare PLC output bit.} \
   rack_2_grp_5_bit_14 {Spare PLC output bit.} \
   audio_warning_2 {Audio warning used for instrument change error} \
   spare_o1_l11 {MCP Place Holder. Not used in logic code.} \
   spare_o1_l12 {MCP Place Holder. Not used in logic code.} \
   spare_o1_l13 {MCP Place Holder. Not used in logic code.} \
   spare_o1_l14 {MCP Place Holder. Not used in logic code.} \
   flat_field_control {Flatfield screen control word} \
   ff_screen_open_pmt {Flatfield screen open permit} \
   ff_screen_enable_pmt {Flatfield screen enable permit} \
   ff_lamps_on_pmt {Flatfield lamps on permit} \
   ne_lamps_on_pmt {Neon lamps on permit} \
   hgcd_lamps_on_pmt {Mercury cadmium lamps on permit} \
   ff_screen2_open_pmt {Spare PLC output bit.} \
   ff_screen2_enable_pm {Spare PLC output bit.} \
   im_ff_wht_on_pmt {Imager flat field white lamp on permit} \
   im_ff_uv_on_pmt {Imager flat field uv lamp on permit} \
   rack_4_grp_5_bit_9 {Spare PLC output bit.} \
   rack_4_grp_5_bit_10 {Spare PLC output bit.} \
   rack_4_grp_5_bit_11 {Spare PLC output bit.} \
   rack_4_grp_5_bit_12 {Spare PLC output bit.} \
   rack_4_grp_5_bit_13 {Spare PLC output bit.} \
   rack_4_grp_5_bit_14 {Spare PLC output bit.} \
   audio_warning_1 {Audio warning used for instrument change error} \
   spare_o1_l15 {MCP Place Holder. Not used in logic code.} \
   wind_mtr_cw_perm {Windscreen motor CW permit} \
   wind_mtr_ccw_perm {Windscreen motor CCW permit} \
   wind_mtr_up_perm {Windscreen motor up permit} \
   wind_mtr_dn_perm {Windscreen motor down permit} \
   out_2_bit_20_spare {Spare PLC output bit.} \
   out_2_bit_21_spare {Spare PLC output bit} \
   az_1_voltage_config {Analog input module 3 configuration control word 0} \
   az_1_current_config {Analog input module 3 configuration control word 1} \
   az_2_voltage_config {Analog input module 3 configuration control word 2} \
   az_2_current_config {Analog input module 3 configuration control word 3} \
   alt_1_voltage_config {Analog input module 3 configuration control word 4} \
   alt_1_current_config {Analog input module 3 configuration control word 5} \
   alt_2_voltage_config {Analog input module 3 configuration control word 6} \
   alt_2_current_config {Analog input module 3 configuration control word 7} \
   alt_position_config {Analog input module 4 configuration control word 0} \
   rot_1_voltage_config {Analog input module 4 configuration control word 1} \
   rot_1_current_config {Analog input module 4 configuration control word 2} \
   umbilical_dist_confi {Analog input module 4 configuration control word 3} \
   inst_lift_force_conf {Analog input module 4 configuration control word 4} \
   inst_lift_dist_confi {Analog input module 4 configuration control word 5} \
   i_4_analog_6_config {Analog input module 4 configuration control word 6} \
   i_4_analog_7_config {Analog input module 4 configuration control word 7} \
   cntrwht_1_pos_config {Analog input module 5 configuration control word 0} \
   cntrwht_2_pos_config {Analog input module 5 configuration control word 1} \
   cntrwht_3_pos_config {Analog input module 5 configuration control word 2} \
   cntrwht_4_pos_config {Analog input module 5 configuration control word 3} \
   i_5_analog_4_config {Analog input module 5 configuration control word 4} \
   i_5_analog_5_config {Analog input module 5 configuration control word 5} \
   i_5_analog_6_config {Analog input module 5 configuration control word 6} \
   i_5_analog_7_config {Analog input module 5 configuration control word 7} \
   alt_mtr_up_perm {Altitude motor up permit} \
   alt_mtr_dn_perm {Altitude motor down permit} \
   alt_plc_perm {Altitude motion PLC permit} \
   wind_alt_plc_perm {Windscreen altitude motion PLC permit} \
   az_mtr_cw_perm {Azimuth motor CW permit} \
   az_mtr_ccw_perm {Azimuth motor CCW permit} \
   az_plc_perm {Azimuth motion PLC permit} \
   wind_az_plc_perm {Windscreen azimuth motion PLC permit} \
   rot_mtr_cw_perm {Rotator motor CW permit} \
   rot_mtr_ccw_perm {Rotator motor CCW permit} \
   rot_plc_perm {Rotator motion PLC permit} \
   n_rail_led {North Rail e-stop LED} \
   s_rail_led {South Rail e-stop LED} \
   w_rail_led {West Rail e-stop LED} \
   n_ll_led {North Lower Level e-stop LED} \
   s_ll_led {South Lower Level e-stop LED} \
   e_ll_led {East Lower Level e-stop LED} \
   w_ll_led {West Lower Level e-stop LED} \
   n_wind_led {North Windscreen e-stop LED} \
   n_fork_led {North Telescope fork e-stop LED} \
   s_wind_led {South Windscreen e-stop LED} \
   lift_solenoid_en {Instrument lift solenoid enable} \
   deg_15_stop_ext_perm {15 degree stop extended permit} \
   deg_15_stop_ret_perm {15 degree stop retracted permit} \
   out_11_bit_24_spare {Spare PLC output bit.} \
   out_11_bit_25_spare {Spare PLC output bit.} \
   lift_pump_on {Instrument lift pump on permit} \
   out_11_bit_27_spare {Spare PLC output bit.} \
   t_bar_tel_perm {Camera T-Bar latch latch permit} \
   t_bar_xport_perm {Camera T-Bar latch unlatch permit} \
   clamp_dis {Clamp disengage permit} \
   clamp_en {Clamp engage permit} \
   az_brake_dis {Azimuth brake disengage permit} \
   az_brake_en {Azimuth brake engage permit} \
   alt_brake_dis {Altitude brake disengage permit} \
   alt_brake_en {Altitude brake engage permit} \
   umbilical_on_off {Umbilical cord lift on / off command} \
   umbilical_up_dn {Umbilical cord lift up / down command} \
   nw_fork_led {North West Fork e-stop led} \
   inst_chg_pos_light {Instrument change position indicator light on permit} \
   stow_pos_light {Stow position indicator light on permit} \
   velocity_select_bit {This bit is used to select between the 1.0 degree per sec and 3.5 degree per sec velocity limits} \
   velocity_trp_rst_out {Output bit to reset a velocity trip in the slip detection module.} \
   lift_enable {Old MCP Lift Enable bit.} \
   umbilical_fast {If set the umbilical speed is set to fast} \
   out_12_bit_13_spare {Spare PLC Output Bit} \
   out_12_bit_14_spare {Spare PLC Output Bit} \
   out_12_bit_15_spare {Spare PLC Output Bit} \
   out_12_bit_16_spare {Spare PLC Output Bit} \
   out_12_bit_17_spare {Spare PLC Output Bit} \
   out_12_bit_18_spare {Spare PLC Output Bit} \
   out_12_bit_19_spare {Spare PLC Output Bit} \
   out_12_bit_20_spare {Spare PLC Output Bit} \
   out_12_bit_21_spare {Spare PLC Output Bit} \
   out_12_bit_22_spare {Spare PLC Output Bit} \
   out_12_bit_23_spare {Spare PLC Output Bit} \
   out_12_bit_24_spare {Spare PLC Output Bit} \
   out_12_bit_25_spare {Spare PLC Output Bit} \
   out_12_bit_26_spare {Spare PLC Output Bit} \
   out_12_bit_27_spare {Spare PLC Output Bit} \
   out_12_bit_28_spare {Spare PLC Output Bit} \
   out_12_bit_29_spare {Spare PLC Output Bit} \
   out_12_bit_30_spare {Spare PLC Output Bit} \
   out_12_bit_31_spare {Spare PLC Output Bit} \
   first_pass_bit {First Pass} \
   az_brake_delay {Azimuth brake delay timer.} \
   az_brake_delay_dn {Azimuth brake delay timer done bit.} \
   alt_brake_delay {Altitude brake delay timer.} \
   alt_brake_delay_dn {Altitude brake delay timer done bit.} \
   e_stop_led_flash_tmr {E-Stop switch LED flash timer.} \
   e_stop_led_f_tmr_dn {E-Stop switch LED flash timer done bit.} \
   alt_brake_off_delay {Altitude brake off delay timer} \
   az_brake_off_delay {Azimuth brake off delay timer} \
   purge_sell_timer {Purge cell air off delay timer} \
   az_mtr_res_trip_del {Azimuth motor over temperature trip delay.} \
   alt_mtr_res_trip_del {Altitude motor over temperature trip delay.} \
   rot_mtr_res_trip_del {Rotator motor over temperature trip delay.} \
   lamp_on_request {Lamp on request timer} \
   ne_lamp_on_delay {NE lamp on delay timer} \
   hg_lamp_on_delay {HG lamp on delay timer} \
   az_bump_cw_timer {Az CW bump timer} \
   az_bump_ccw_timer {Az CCW bump timer} \
   alt_bump_up_timer {Alt Up bump timer} \
   alt_bump_dn_timer {Alt Down bump timer} \
   im_ff_wht_on_delay {} \
   im_ff_uv_on_delay {} \
   alt_position_lt_90_15 {alt < 90.15} \
   alt_position_gt_89_75 {alt > 89.75} \
   alt_position_lt_90_2 {alt < 90.2} \
   alt_position_lt_90_29 {alt < 90.29} \
   alt_position_lt_91_0 {alt < 91.0} \
   alt_position_gt_89_8 {alt > 89.8} \
   alt_position_gt_0_50 {alt > 0.50} \
   alt_position_gt_19_5 {alt > 19.5} \
   alt_position_gt_0_8 {alt > 0.8} \
   alt_position_lt_18_5 {alt < 18.5} \
   alt_position_gt_15_0 {alt > 15.0} \
   alt_position_gt_15_5 {alt > 15.5} \
   alt_position_gt_83_5 {alt > 83.5} \
   alt_pos_lt_0_2 {alt < 0.2} \
   alt_pos_gt_neg_2 {alt > -0.2} \
   umbilical_dn {Umbilical is below 480} \
   lift_force_gt_f_cartridge_mount {Instrument lift force is > 1400lb} \
   lift_height_gt_h_cartridge_mount {Instrument lift distance is >= 21.95} \
]
