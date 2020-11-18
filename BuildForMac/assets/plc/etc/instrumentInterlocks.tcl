RESULT no_inst_in_place \
    [AND \
	 inst_id1_1 inst_id1_2 inst_id1_3 inst_id1_4 \
	 inst_id2_1 inst_id2_2 inst_id2_3 inst_id2_4 \
	 inst_id3_1 inst_id3_2 inst_id3_3 inst_id3_4] \
    "No instrument is installed on the lift"

#-----------------------------------------------------------------------------
#
# New from John Anderson, 22nd August 2003
#
RESULT lift_pump_on \
    [AND altitude_at_inst_chg [NOT flex_io_fault]]

RESULT lift_solenoid_en \
    solenoid_engage_sw


RESULT lift_empty \
    [AND \
	 [NOT inst_lift_sw1] [NOT inst_lift_sw2] \
	 [NOT inst_lift_sw3] [NOT inst_lift_sw4]]

RESULT empty_plate_on_lift \
    [AND \
	 inst_lift_sw1 [NOT inst_lift_sw2] \
	 [NOT inst_lift_sw3] [NOT inst_lift_sw4]]

RESULT cor_on_lift \
    [AND \
	 [NOT inst_lift_sw1] [NOT inst_lift_sw2] \
	 inst_lift_sw3 [NOT inst_lift_sw4]]

RESULT cam_on_lift_wo_j_hok \
    [AND \
	 [NOT inst_lift_sw1] [NOT inst_lift_sw2] \
	 [NOT inst_lift_sw3] inst_lift_sw4]

RESULT cam_on_lift_w_j_hok \
    [AND \
	 inst_lift_sw1 [NOT inst_lift_sw2] \
	 [NOT inst_lift_sw3] inst_lift_sw4]

RESULT cartg_on_lift \
    [AND \
	 inst_lift_sw1 [NOT inst_lift_sw2] \
	 inst_lift_sw3 inst_lift_sw4]

RESULT cartg_on_lift_comp \
    [AND \
	 inst_lift_sw1 inst_lift_sw2 \
	 inst_lift_sw3 inst_lift_sw4]

RESULT eng_cam_on_lift \
    [AND \
	 inst_lift_sw1 [NOT inst_lift_sw2] \
	 inst_lift_sw3 [NOT inst_lift_sw4]]

RESULT eng_cam_on_lift_comp \
    [AND \
	 inst_lift_sw1 inst_lift_sw2 \
	 inst_lift_sw3 [NOT inst_lift_sw4]]

RESULT lift_up_enable \
    [AND \
	 [NOT alt_locking_pin_out] alt_locking_pin_in \
	 rot_inst_chg_a rot_inst_chg_b az_stow_1a az_stow_1b \
	 inst_lift_auto \
	 [OR \
	      [AND \
		   lh_les_2d0\
		   [OR \
			ops_cart_in_pos ops_cart_in_house \
			cam_on_lift_w_j_hok cam_on_lift_wo_j_hok]] \
	      [AND \
		   lh_lim_1d95_18d0 \
		   [OR \
			empty_plate_on_lift \
			[AND \
			     cor_on_lift pri_latch_opn \
			     [OR \
				  cor_in_place \
				  [AND cor_not_in_place sec_latch_opn]]] \
			[AND \
			     cam_on_lift_w_j_hok \
			     img_cam_in_place cor_not_in_place] \
			[AND \
			     cam_on_lift_w_j_hok no_inst_in_place \
			     pri_latch_opn sec_latch_opn sad_latch_opn \
			     cor_not_in_place] \
			[AND \
			     [OR \
				  cartg_on_lift cartg_on_lift_comp \
				  empty_plate_on_lift] \
			     [OR \
				  cartg_in_place \
				  [AND \
				       no_inst_in_place pri_latch_opn \
				       slit_head_door1_opn \
				       slit_head_door2_opn \
				       [NOT slit_head_latch1_ext] \
				       [NOT slit_head_latch2_ext]]]] \
			[AND \
			     [OR \
				  eng_cam_on_lift eng_cam_on_lift_comp \
				  empty_plate_on_lift] \
			     [OR \
				  [AND eng_cam_in_place cor_not_in_place] \
				  [AND \
				       no_inst_in_place \
				       pri_latch_opn sec_latch_opn \
				       cor_not_in_place]]] \
		       ] \
		  ] \
	      lh_grt_17d5] \
	 ] \
    "The instrument lift is permitted to be raised"

RESULT lift_down_enable \
    [AND \
	 inst_lift_auto \
	 [OR \
	      [AND \
		   lh_grt_23d1 \
		   cor_on_lift pri_latch_opn \
		   [OR sec_latch_opn sec_latch_cls]] \
	      [AND \
		   lh_lim_22d3_23d1 \
		   [OR \
			[AND cor_on_lift pri_latch_opn \
			     [OR sec_latch_opn sec_latch_cls]] \
			[AND \
			     [OR cartg_on_lift cartg_on_lift_comp] \
			     [OR \
				  [AND \
				       pri_latch_opn \
				       slit_head_door1_opn \
				       slit_head_door2_opn \
				       [NOT slit_head_latch1_ext] \
				       [NOT slit_head_latch2_ext]] \
				  [AND \
				       pri_latch_cls \
				       slit_head_latch1_ext \
				       slit_head_latch2_ext]]] \
			[AND \
			     cartg_in_place pri_latch_cls \
			     slit_head_latch1_ext \
			     slit_head_latch2_ext] \
			[AND \
			     [OR eng_cam_on_lift eng_cam_on_lift_comp] \
			     [OR pri_latch_opn pri_latch_cls]] \
			[AND eng_cam_in_place pri_latch_cls] \
		       ] \
		  ] \
	      [AND \
		   lh_lim_18d0_22d3 \
		   [OR \
			[AND cor_on_lift pri_latch_opn \
			     [OR sec_latch_opn sec_latch_cls]] \
			[AND \
			     cam_on_lift_w_j_hok \
			     [OR \
				  [AND \
				       pri_latch_opn \
				       sec_latch_opn \
				       sad_latch_opn] \
				  [AND \
				       pri_latch_cls \
				       sec_latch_cls \
				       sad_latch_cls]]] \
			[AND \
			     [OR cartg_on_lift cartg_on_lift_comp] \
			     [OR \
				  [AND \
				       pri_latch_opn \
				       slit_head_door1_opn \
				       slit_head_door2_opn \
				       [NOT slit_head_latch1_ext] \
				       [NOT slit_head_latch2_ext]] \
				  [AND \
				       pri_latch_cls \
				       [NOT slit_head_latch1_ext] \
				       [NOT slit_head_latch2_ext]]]] \
			[AND \
			     [OR eng_cam_on_lift eng_cam_on_lift_comp] \
			     [OR pri_latch_opn pri_latch_cls]] \
			[AND \
			     empty_plate_on_lift \
			     [OR pri_latch_opn pri_latch_cls]] \
		       ] \
		  ] \
	      lh_les_18d5_2 \
	     ] \
    ] \
    "The instrument lift is permitted to be lowered"

#-----------------------------------------------------------------------------

RESULT latch_perm \
    [OR \
	 inst_latch_perm \
	 sec_latch_perm \
	 sad_latch_perm] \
    "At least one latch permit is granted"

RESULT unlatch_perm \
    [OR \
	 inst_unlatch_perm \
	 sec_unlatch_perm \
	 sad_unlatch_perm] \
    "At least one unlatch permit is granted"

RESULT auto_mode_enable \
    [AND \
	 auto_mode_sw [NOT flex_io_fault] [NOT alt_locking_pin_out] \
	 alt_locking_pin_in inst_lift_auto rot_inst_chg_a \
	 rot_inst_chg_b az_stow_1a az_stow_1b altitude_at_inst_chg]

RESULT inst_latch_perm \
    [AND \
	 ilcb_led_on [NOT iclb_leds_on_cmd] \
	 auto_mode_enable \
	 inst_chg_install_sw \
	 [OR \
	      img_cam_up_in_place \
	      cartg_up_in_place \
	      eng_cam_up_in_place \
	      [AND \
		   lh_les_6d0 no_inst_in_place sad_not_in_place \
		   [OR \
			cam_on_lift_w_j_hok cam_on_lift_wo_j_hok \
			cartg_on_lift \
			cor_on_lift eng_cam_on_lift]] \
	     ] \
	]

RESULT inst_unlatch_perm \
    [AND \
	 ilcb_led_on [NOT iclb_leds_on_cmd] \
	 auto_mode_enable \
	 inst_chg_remove_sw \
	 [OR \
	      img_cam_up_in_place \
	      cartg_up_in_place \
	      eng_cam_up_in_place \
	      [AND \
		   lh_les_6d0_1 \
		   no_inst_in_place \
		   sad_not_in_place \
		   [OR \
			cam_on_lift_w_j_hok cam_on_lift_wo_j_hok \
			cartg_on_lift cor_on_lift eng_cam_on_lift]] \
	     ] \
	]

RESULT pri_latch_opn \
    [AND pri_latch1_opn pri_latch2_opn pri_latch3_opn]

RESULT pri_latch_cls \
    [AND pri_latch1_cls pri_latch2_cls pri_latch3_cls]

RESULT sec_latch_perm \
    [AND \
	 ilcb_led_on [NOT iclb_leds_on_cmd] \
	 auto_mode_enable \
	 inst_chg_install_sw \
	 [OR \
	      img_cam_up_in_place \
	      cor_up_in_place \
	      [AND \
		   lh_les_6d0_2 \
		   no_inst_in_place \
		   sad_not_in_place \
		   cor_not_in_place \
		   [OR \
			cam_on_lift_w_j_hok cam_on_lift_wo_j_hok \
			cor_on_lift eng_cam_on_lift]] \
	     ] \
	 ]
     
RESULT sec_unlatch_perm \
    [AND \
	 ilcb_led_on [NOT iclb_leds_on_cmd] \
	 auto_mode_enable \
	 inst_chg_remove_sw \
	 [OR \
	      img_cam_up_in_place \
	      cor_up_in_place \
	      [AND \
		   lh_les_6d0_3 \
		   no_inst_in_place sad_not_in_place cor_not_in_place \
		   [OR \
			cam_on_lift_w_j_hok cam_on_lift_wo_j_hok \
			cor_on_lift eng_cam_on_lift]] \
	     ] \
	 ]

RESULT sec_latch_opn \
    [AND sec_latch1_opn sec_latch2_opn sec_latch3_opn]

RESULT sec_latch_cls \
    [AND sec_latch1_cls sec_latch2_cls sec_latch3_cls]

RESULT sad_latch_perm \
    [AND \
	 ilcb_led_on [NOT iclb_leds_on_cmd] \
	 auto_mode_enable \
	 inst_chg_install_sw \
	 [OR \
	      img_cam_up_in_place \
	      [AND \
		   lh_les_6d0_4 \
		   no_inst_in_place sad_not_in_place \
		   [OR cam_on_lift_w_j_hok cam_on_lift_wo_j_hok]] \
	     ] \
	]

RESULT sad_unlatch_perm \
    [AND \
	 ilcb_led_on [NOT iclb_leds_on_cmd] \
	 auto_mode_enable \
	 inst_chg_remove_sw \
	 [OR \
	      img_cam_up_in_place \
	      [AND \
		   lh_les_6d0_5 \
		   no_inst_in_place sad_not_in_place \
		   [OR cam_on_lift_w_j_hok cam_on_lift_wo_j_hok]] \
	     ] \
	]

RESULT sad_latch_opn \
    [AND sad_latch1_opn sad_latch2_opn]

RESULT sad_latch_cls \
    [AND sad_latch1_cls sad_latch2_cls]

RESULT img_cam_up_in_place \
    [AND cam_on_lift_w_j_hok lh_lim_21d8_22d15 lf_grt_1400]

RESULT cartg_up_in_place \
    [AND cartg_on_lift_comp cartg_in_place lh_lim_22d85_23d05 lf_grt_950]

RESULT eng_cam_up_in_place \
    [AND \
	 eng_cam_on_lift_comp eng_cam_in_place \
	 lh_lim_22d89_23d09 lf_grt_950_1]

RESULT cor_up_in_place \
    [AND cor_on_lift cor_in_place lh_lim_23d04_23d24 lf_grt_750]

RESULT cor_in_place \
    [AND [NOT spec_lens1] spec_lens2]

RESULT cor_not_in_place \
    [AND spec_lens1 [NOT spec_lens2]]

RESULT disc_cable \
    [AND [NOT inst_id1_1] [NOT inst_id1_2] [NOT inst_id1_3] [NOT inst_id1_4]\
	 [NOT inst_id2_1] [NOT inst_id2_2] [NOT inst_id2_3] [NOT inst_id2_4]\
	 [NOT inst_id3_1] [NOT inst_id3_2] [NOT inst_id3_3] [NOT inst_id3_4]]

RESULT no_inst_in_place \
    [AND inst_id1_1 inst_id1_2 inst_id1_3 inst_id1_4 \
	 inst_id2_1 inst_id2_2 inst_id2_3 inst_id2_4 \
	 inst_id3_1 inst_id3_2 inst_id3_3 inst_id3_4]

RESULT cartridge_1 \
    [AND inst_id1_1 inst_id1_2 inst_id1_3 [NOT inst_id1_4] \
	 inst_id2_1 inst_id2_2 inst_id2_3 [NOT inst_id2_4] \
	 inst_id3_1 inst_id3_2 inst_id3_3 [NOT inst_id3_4]]

RESULT cartridge_2 \
    [AND inst_id1_1 inst_id1_2 [NOT inst_id1_3] inst_id1_4 \
	 inst_id2_1 inst_id2_2 [NOT inst_id2_3] inst_id2_4 \
	 inst_id3_1 inst_id3_2 [NOT inst_id3_3] inst_id3_4]

RESULT cartridge_3 \
    [AND inst_id1_1 inst_id1_2 [NOT inst_id1_3] [NOT inst_id1_4] \
	 inst_id2_1 inst_id2_2 [NOT inst_id2_3] [NOT inst_id2_4] \
	 inst_id3_1 inst_id3_2 [NOT inst_id3_3] [NOT inst_id3_4]]

RESULT cartridge_4 \
    [AND inst_id1_1 [NOT inst_id1_2] inst_id1_3 inst_id1_4 \
	 inst_id2_1 [NOT inst_id2_2] inst_id2_3 inst_id2_4 \
	 inst_id3_1 [NOT inst_id3_2] inst_id3_3 inst_id3_4]

RESULT cartridge_5 \
    [AND inst_id1_1 [NOT inst_id1_2] inst_id1_3 [NOT inst_id1_4] \
	 inst_id2_1 [NOT inst_id2_2] inst_id2_3 [NOT inst_id2_4] \
	 inst_id3_1 [NOT inst_id3_2] inst_id3_3 [NOT inst_id3_4]]

RESULT cartridge_6 \
    [AND inst_id1_1 [NOT inst_id1_2] [NOT inst_id1_3] inst_id1_4 \
	 inst_id2_1 [NOT inst_id2_2] [NOT inst_id2_3] inst_id2_4 \
	 inst_id3_1 [NOT inst_id3_2] [NOT inst_id3_3] inst_id3_4]

RESULT cartridge_7 \
    [AND inst_id1_1 [NOT inst_id1_2] [NOT inst_id1_3] [NOT inst_id1_4] \
	 inst_id2_1 [NOT inst_id2_2] [NOT inst_id2_3] [NOT inst_id2_4] \
	 inst_id3_1 [NOT inst_id3_2] [NOT inst_id3_3] [NOT inst_id3_4]]

RESULT cartridge_8 \
    [AND [NOT inst_id1_1] inst_id1_2 inst_id1_3 inst_id1_4 \
	 [NOT inst_id2_1] inst_id2_2 inst_id2_3 inst_id2_4 \
	 [NOT inst_id3_1] inst_id3_2 inst_id3_3 inst_id3_4]

RESULT cartridge_9 \
    [AND [NOT inst_id1_1] inst_id1_2 inst_id1_3 [NOT inst_id1_4] \
	 [NOT inst_id2_1] inst_id2_2 inst_id2_3 [NOT inst_id2_4] \
	 [NOT inst_id3_1] inst_id3_2 inst_id3_3 [NOT inst_id3_4]]

RESULT eng_cam_in_place \
    [AND [NOT inst_id1_1] inst_id1_2 [NOT inst_id1_3] inst_id1_4 \
	 [NOT inst_id2_1] inst_id2_2 [NOT inst_id2_3] inst_id2_4 \
	 [NOT inst_id3_1] inst_id3_2 [NOT inst_id3_3] inst_id3_4]

RESULT undefined_1 \
    [AND [NOT inst_id1_1] [NOT inst_id1_2] inst_id1_3 inst_id1_4 \
	 [NOT inst_id2_1] [NOT inst_id2_2] inst_id2_3 inst_id2_4 \
	 [NOT inst_id3_1] [NOT inst_id3_2] inst_id3_3 inst_id3_4]

RESULT undefined_2 \
    [AND [NOT inst_id1_1] [NOT inst_id1_2] inst_id1_3 [NOT inst_id1_4] \
	 [NOT inst_id2_1] [NOT inst_id2_2] inst_id2_3 [NOT inst_id2_4] \
	 [NOT inst_id3_1] [NOT inst_id3_2] inst_id3_3 [NOT inst_id3_4]]

RESULT undefined_3 \
    [AND [NOT inst_id1_1] inst_id1_2 [NOT inst_id1_3] [NOT inst_id1_4] \
	 [NOT inst_id2_1] inst_id2_2 [NOT inst_id2_3] [NOT inst_id2_4] \
    [NOT inst_id3_1] inst_id3_2 [NOT inst_id3_3] [NOT inst_id3_4]]

RESULT img_cam_in_place \
    [AND [NOT inst_id1_1] [NOT inst_id1_2] [NOT inst_id1_3] inst_id1_4 \
	 [NOT inst_id2_1] [NOT inst_id2_2] [NOT inst_id2_3] inst_id2_4 \
	 [NOT inst_id3_1] [NOT inst_id3_2] [NOT inst_id3_3] inst_id3_4]

RESULT cartg_in_place \
    [OR \
	 cartridge_1 cartridge_2 cartridge_3 cartridge_4 \
	 cartridge_5 cartridge_6 cartridge_7 cartridge_8 cartridge_9]

RESULT sad_in_place \
    [AND [NOT sad_mount1] sad_mount2]

RESULT sad_not_in_place \
    [AND sad_mount1 [NOT sad_mount2]]
