array set AXIS_STAT [list \
   0x1          pvt_empty \
   0x2          pvt_time_late \
   0x4          min_pos \
   0x8          max_pos \
   0x10         max_vel \
   0x20         max_acc \
   0x40         min_limit \
   0x80         max_limit \
   0x100        closed_loop \
   0x200        amp_ok \
   0x400        stop_ok \
   0x800        out_closed_loop \
   0x1000       amp_bad \
   0x2000       stop_in \
   0x4000       semCmdPort_taken \
   0x10000      clock_loss_signal \
   0x20000      clock_slow_signal \
   0x40000      clock_not_set \
   0x1000000    ms_on_correction_too_large \
   0x20000000   bump_dn_cw_sticky \
   0x40000000   bump_up_ccw_sticky \
   0x80000000   always_zero \
]
