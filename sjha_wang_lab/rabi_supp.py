import numpy as np
import spinapi as spin

def initialize():
    if spin.pb_init() != 0:
        print ("Error initializing board: %s" % spin.pb_get_error())
        input("Please press any key to continue.")
        exit(-1)
    else:
        spin.pb_core_clock(500)

def on():
    spin.pb_start()
        
def stop():
    spin.pb_stop()
    
def close():
    spin.pb_close()

# Define the channels that will be used. 
onn = 0b111000000000000000001011
off = 0b111000000000000000000000
grn = 0b111000000000000000000001
mw1 = 0b111000000000000000001000
mw2 = 0b111000000000000000000100
det = 0b111000000000000000000011

def rabi_seq(mw_t, det_t=400, off_t=3000, green_t=5000, duty=5000, loop_num=500000):

    delay1 = (duty - mw_t)
    delay2 = (off_t - det_t)

    spin.pb_start_programming(spin.PULSE_PROGRAM)

    start = spin.pb_inst_pbonly(grn, spin.JSR, 2, green_t)
    spin.pb_inst_pbonly(off, spin.STOP, 0, 500)

    sub = spin.pb_inst_pbonly(off, spin.LOOP, loop_num, delay1)
    spin.pb_inst_pbonly(mw1, spin.CONTINUE, 0, mw_t)
    spin.pb_inst_pbonly(det, spin.CONTINUE, 0, det_t)
    spin.pb_inst_pbonly(grn, spin.CONTINUE, 0, delay2)
    spin.pb_inst_pbonly(grn, spin.END_LOOP, sub, green_t)
    spin.pb_inst_pbonly(off, spin.RTS, 0, 500)

    spin.pb_stop_programming()

def rabi_start(w, det_t=400):
    rabi_seq(w,det_t=det_t)
    on()