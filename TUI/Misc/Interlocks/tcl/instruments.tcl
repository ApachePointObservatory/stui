###############################################################################
#
# Useful intermediate results
#
RESULT slitdoor1_opn \
    [AND \
	 slit_head_door1_opn \
	 [NOT slit_head_door1_cls]
     ]

RESULT slitdoor2_opn \
    [AND \
	 slit_head_door2_opn \
	 [NOT slit_head_door2_cls]
     ]

RESULT pri_latch_opn \
    [AND \
	 [AND \
	      pri_latch1_opn pri_latch2_opn pri_latch3_opn \
	     ] \
	 [NOT [OR \
		   pri_latch1_cls pri_latch2_cls pri_latch3_cls \
		  ]]
     ]

RESULT sec_latch_opn \
    [AND \
	 [AND \
	      sec_latch1_opn sec_latch2_opn sec_latch3_opn \
	     ] \
	 [NOT [OR \
		   sec_latch1_cls sec_latch2_cls sec_latch3_cls \
		  ]]
     ]

RESULT safety_latch_opn \
    [AND \
	 [NOT [OR \
		   safety_latch1_cls safety_latch2_cls \
		  ]] \
	 [OR bypass \
	      [AND \
		   safety_latch1_opn safety_latch2_opn \
		  ] \
	     ] \
	 ]
#
# Note that the protection latches are reversed
# (is this still true? RHL Jan 00 XXX)
#
RESULT sad_latch_opn \
    [AND \
	 [AND \
	      sad_latch1_opn sad_latch2_opn \
	     ] \
	 [NOT [OR \
		   sad_latch1_cls sad_latch2_cls \
		  ]]
     ]

RESULT doghouse_closed \
    [AND dog_house_door_cls [NOT dog_house_door_opn]]

MORE_THINGS umbilical_dn umbilical_dist {< 480} \
    0 "Umbilical is below 480"    

MORE_THINGS lift_force_gt_f_cartridge_mount inst_lift_force {> 1400} 0 \
    "Instrument lift force is > 1400lb"

MORE_THINGS lift_height_gt_h_cartridge_mount inst_lift_dist {>= 21.95} 0 \
    "Instrument lift distance is >= 21.95"

RESULT lift_holds_cartridge \
    [AND \
	 [NOT inst_lift_dn] \
	 [OR bypass \
	      [AND lift_force_gt_f_cartridge_mount \
		   lift_height_gt_h_cartridge_mount] \
	     ] \
	]
    
RESULT lift_holds_cartridge_and_corrector \
    [AND \
	 [NOT inst_lift_dn] \
	 [OR bypass \
	      [AND inst_lift_dist_ge_20 inst_lift_dist_le_22] \
	      [AND inst_lift_force_ge_400 inst_lift_force_le_420] \
	     ] \
	]
    
###############################################################################
#
# Logic diagrams for instrument changes
#
# Are all the ID bits consistent?
#
loop i 1 5 {
   RESULT consistent_inst_id_$i \
       [OR \
	    [AND inst_id1_$i [AND inst_id2_$i inst_id3_$i]] \
	    [NOT [OR inst_id1_$i inst_id2_$i inst_id3_$i]] \
	    ]
}

RESULT consistent_inst_id \
    [AND \
	 consistent_inst_id_1 \
	 consistent_inst_id_2 \
	 consistent_inst_id_3 \
	 consistent_inst_id_4 \
	]

#
# No instrument is installed: ID 0. We also check that the secondaries latches
# are open as a backup
#
RESULT no_instrument_is_installed \
    [AND \
	 [AND \
	      inst_id1_1 inst_id1_2 inst_id1_3 inst_id1_4 \
	     ] \
	 [AND \
	      sec_latch_opn \
	     ] \
     ]
#
# Imaging camera is installed: ID 14
#
RESULT camera_is_installed \
    [AND \
	 [NOT [AND \
	      inst_id1_1 \
	     ]] \
	 [OR \
	      inst_id1_2 inst_id1_3 inst_id1_4 \
	     ]
     ]
#
# A Cartridge is installed
#
RESULT cartridge_is_installed \
    [AND \
	 [NOT no_instrument_is_installed] \
	 [NOT [OR \
		   camera_is_installed \
		   engcamera_is_installed \
		  ]] \
	]

#
# Engineering camera is installed: ID ??
#
RESULT engcamera_is_installed \
    [AND \
	 [NOT [OR \
		   inst_id1_1 inst_id2_1 inst_id3_1 \
		   inst_id1_2 inst_id2_2 inst_id3_2 \
		   inst_id1_3 inst_id2_3 inst_id3_3 \
		   inst_id1_4 inst_id2_4 inst_id3_4 \
		  ]]
     ]

RESULT spec_corrector_is_installed \
    [AND \
	 spec_lens1 spec_lens2 \
	]

set statusDescriptions(spec_lens1) [list On Off]
set statusDescriptions(spec_lens2) [list Off On]
