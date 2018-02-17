#for counting
import sys
import time
import PyDAQmx as daq
from PyDAQmx import uInt32, int32, int16, byref
from contextlib import contextmanager

#for functions to support Rabi oscillation scans
import numpy as np
import spinapi as spin
#from wanglib.util import scanner
#from wanglib.pylab_extensions import plotgen
#from functools import partial
#from circa.util import get_next_filename

### -------------------------------------------------------
### COUNTING
### -------------------------------------------------------

def make_counter(countchan, trig=None):
    """
    Configure the given counter to count, maybe with a pause trigger.
    """
    ctr = daq.Task()
    ctr.CreateCICountEdgesChan(countchan, "",
                               daq.DAQmx_Val_Rising,
                               0,  # initial count
                               daq.DAQmx_Val_CountUp)

    if trig is not None:
        # configure pause trigger
        ctr.SetPauseTrigType(daq.DAQmx_Val_DigLvl)
        ctr.SetDigLvlPauseTrigSrc(trig)
        ctr.SetDigLvlPauseTrigWhen(daq.DAQmx_Val_Low)

    return ctr

def make_pulse(duration, pulsechan):
    """
    Configure the counter `pulsechan` to output
    a pulse of the given `duration` (in seconds).
    """
    pulse = daq.Task()
    pulse.CreateCOPulseChanTime(
        pulsechan, "",            # physical channel, name to assign
        daq.DAQmx_Val_Seconds,   # units:seconds
        daq.DAQmx_Val_Low,       # idle state: low
        0.00, .0001, duration,   # initial delay, low time, high time
    )
    return pulse

def configure_counter(duration=.1,
                      pulsechan="Dev1/ctr1",
                      countchan="Dev1/ctr0"):
    """
    Configure the card to count edges on `countchan`, for the specified
    `duration` of time (seconds). This is a hardware-timed thing,
    using the paired counter `pulsechan` to gate the detection
    """

    # configure pulse (for hardware timing)
    pulse = make_pulse(duration, pulsechan)

    # if these are paired counters, we can use the internal output
    # of the pulsing channel to trigger the counting channel
    trigchan = "/%sInternalOutput" % pulsechan.replace('ctr', 'Ctr')

    # configure counter
    ctr = make_counter(countchan, trig=trigchan)

    return pulse, ctr

def start_count(pulse, ctr):
    """ start counting events. """
    # start counter
    ctr.StartTask()
    # fire pulse
    pulse.StartTask()
    return

def finish_count(pulse, ctr):
    """ finish counting events and return the result. """
    # initialize memory for readout
    count = uInt32()
    # wait for pulse to be done
    pulse.WaitUntilTaskDone(10.)
    # timeout, ref to output value, reserved
    ctr.ReadCounterScalarU32(10., byref(count), None)
    pulse.StopTask()
    ctr.StopTask()
    return count.value

def do_count(pulse, ctr):
    """
    simple counting in a synchronous mode
    """
    start_count(pulse, ctr)
    return finish_count(pulse, ctr)

@contextmanager
def counting(pulse, ctr):
    try:
        yield
    except KeyboardInterrupt:
        # stop the counters
        try:
            ctr.StopTask()
            print("stopped counter")
        except daq.DAQError:
            print("no need to stop counter")
        try:
            pulse.StopTask()
            print("stopped timer")
        except daq.DAQError:
            print("no need to stop timer")
        raise

def scan(gen, t=0.1, **kwargs):
    """threaded version"""
    p,c = configure_counter(duration=t, **kwargs)
    with counting(p,c):
        next(gen)
        try:
            last = do_count(p,c)/t
        except daq.DAQError as e:
            print(str(e), sys.stderr)#formerly file=sys.stderr
            raise StopIteration
        for step in gen:
            start_count(p, c)
            yield last
            last = finish_count(p, c)/t
        yield last

def gen_count_rate(t=0.1, **kwargs):
    p,c = configure_counter(duration=t, **kwargs)
    start = time.time()
    while True:
        y = do_count(p,c)/t
        yield time.time() - start, y

def get_counts(ctr):
    """ this stops ``ctr`` and returns its result """
    count = daq.uInt32()
    ctr.ReadCounterScalarU32(10., daq.byref(count), None)
    ctr.StopTask()
    return count.value

def gen_gated_counts(t=0.1):
    """
    equivalent of gen_count_rate when something else (e.g. a spincore
    sequence) is gating the detection, not a pulse we generate
    ourselves.
    
    This counts both photons and gate edges, and returns the rate as
    photons collected per gated detection period. Divide by the width
    of the window to get counts per second.
    """
    # photon counter
    pc = make_counter("Dev1/ctr0", trig="PFI38")
    # and the gate counter:
    gc = make_counter("Dev1/ctr3")
    # the paths here are for Fusion setup, hardcoded for now (sorry)
    
    start = time.time()
    while True:
        gc.StartTask() # start both counters. this isn't
        pc.StartTask() # exactly synchronous (error source)
        time.sleep(t)
        photons = get_counts(pc)
        pulses  = get_counts(gc)
        if pulses:
            rate = photons 
        else:
            rate = 0.
        yield time.time() - start, rate

def do_count_v2(t):
    gen = gen_gated_counts(t=t)
    _,rate = next(gen)
    return rate

### -------------------------------------------------------
### Support for Rabi oscillation scans
### -------------------------------------------------------

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

# Pretty much always initialize and close at the beginning,
# so might as well just do that here.
initialize() 
close()

# Define the channels that will be used. 
onn = 0b111000000000000000001011
off = 0b111000000000000000000000
grn = 0b111000000000000000000001
mw1 = 0b111000000000000000001000
mw2 = 0b111000000000000000000100
det = 0b111000000000000000000011

mw1g = 0b111000000000000000001001
offg = 0b111000000000000000000001
'''
#Mayra's pulse sequence:
def rabi_seq(mw_t, det_t=400, off_t=3040, green_t=5000, duty_t=5000, loop_num=1000000):
    
    delay_1 = (duty_t - mw_t)
    delay_2 = (off_t - det_t)
    
    spin.pb_start_programming(spin.PULSE_PROGRAM)
    
    start = spin.pb_inst_pbonly(grn, spin.JSR, 2, green_t)
    spin.pb_inst_pbonly(off, spin.STOP, 0, 500)
    
    sub = spin.pb_inst_pbonly(off, spin.LOOP, loop_num, delay_1)
    spin.pb_inst_pbonly(mw1, spin.CONTINUE, 0, mw_t)
    spin.pb_inst_pbonly(det, spin.CONTINUE, 0, det_t)
    spin.pb_inst_pbonly(grn, spin.CONTINUE, 0, delay_2)
    spin.pb_inst_pbonly(grn, spin.END_LOOP, sub, green_t)
    
    spin.pb_inst_pbonly(off, spin.RTS, 0, 500)
    
    spin.pb_stop_programming()
'''

def rabi_seq(mw_t, det_t=400, off_t=3040, green_t=5000, duty_t=5000, wait_t=0, loop_num=1000000):
    
    #delay_1 keeps total duty cycle time constant as mw width varies
    #delay_1 = (duty_t - mw_t) 
    
    #since mw_t included in delay_2, delay_1 function is now just to give duty cycle
    delay_1 = (duty_t)
    
    #delay_2 times detection pulse to coincide at wait_t after mw_pulse,
    #and to be at beginning of green pulse, which has a delay of off_t due to AOM.
    delay_2 = (off_t - mw_t - wait_t) 
    
    spin.pb_start_programming(spin.PULSE_PROGRAM)
    
    start = spin.pb_inst_pbonly(grn, spin.JSR, 2, green_t)
    spin.pb_inst_pbonly(off, spin.STOP, 0, 500)
    
    sub = spin.pb_inst_pbonly(off, spin.LOOP, loop_num, delay_1) # then wait.
    spin.pb_inst_pbonly(grn, spin.CONTINUE, 0, delay_2) # then green pulse. Will hit just as detector turns on.
    spin.pb_inst_pbonly(mw1g, spin.CONTINUE, 0, mw_t) # think of this as beginning. MW pulse.
    #spin.pb_inst_pbonly(mw1, spin.CONTINUE, 0, mw_t) # think of this as beginning. MW pulse. Results in green gap that limits possible detection time.
    spin.pb_inst_pbonly(offg, spin.CONTINUE, 0, wait_t) # then wait
    #spin.pb_inst_pbonly(off, spin.CONTINUE, 0, wait_t) # then wait. Results in green gap that limits possible detection time.
    spin.pb_inst_pbonly(det, spin.CONTINUE, 0, det_t) # then detection pulse (green has just hit by now). Back to top.
    spin.pb_inst_pbonly(grn, spin.END_LOOP, sub, green_t)
    
    spin.pb_inst_pbonly(off, spin.RTS, 0, 500)
    
    spin.pb_stop_programming()

def rabi_start(mw_t, det_t=400, off_t=3000, green_t=5000, duty_t=5000, wait_t=0, loop_num=1000000):
    rabi_seq(mw_t, det_t=det_t, off_t=off_t, green_t=green_t, duty_t=duty_t, wait_t=wait_t, loop_num=loop_num)
    on()

