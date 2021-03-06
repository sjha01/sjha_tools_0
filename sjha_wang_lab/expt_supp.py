'''
expt_supp.py
Tools used by scans.py, and tools built on top of expt.py.
These are primarily tools made to use the APD, as well
as to use spincore to control the APD, AOM, lasers, etc.
'''
import expt

#DO a CounT
def doct(t=.1):
    pc = expt.configure_counter(duration=t)
    with expt.counting(*pc):
        val = expt.do_count(*pc) / t
        return val

###########################################################
#Spincore card
#initialization and basic counting
#Convert to class eventually
###########################################################

import spinapi as spin
import time
import PyDAQmx as daq
#from PyDAQmx import * #don't like this, figure out where it's used. I think in make_counter(), make_gate_counter()
import os
import itertools
import sys
from contextlib import contextmanager

if spin.pb_init() != 0:
    print("Error initializing board: %s" % spin.pb_get_error())
    input("Please press a key to continue.")
    exit(-1)

if spin.pb_count_boards()== 1: # check to see if we have one spincore card
    spin.pb_core_clock(500) # sets the spincore clock to 500 MHz
    #print("Ready to go!")
else:
    print("SpinCore board not found")

#Check that there is a single spincore board, and set clock
#to 500 MHz
def spincore_status_check(print_ready=False):
    if spin.pb_init() != 0:
        print('Error initializing board: %s' % spin.pb_get_error())
        input('Please press a key to continue.')
        exit(-1)
    
    if spin.pb_count_boards() == 1: # check to see if we have one spincore card
        spin.pb_core_clock(500) # sets the spincore clock to 500 MHz
        if print_ready:
            print('Ready to go!')
    else:
        print('SpinCore board not found')

#Checks if pulse sequence has finished
def is_stopped():   
    status = spin.pb_read_status()
    return status['stopped']    

#Start pulse sequence, check every .1 s to see if it has
#finished
def pulse_blast():
    spin.pb_start()
    i=0
    while not is_stopped():
        #print('Please wait... %r' % i)
        time.sleep(.1)
        i += 1
    #print('Finished')
    spin.pb_stop()

#this is from old file naming convention.
#Replace with new one.
def get_next_filename(dir='.', fmt="data%03d.npy", start=1):
    for i in itertools.count(start):
        if fmt % i not in os.listdir(dir):
            return fmt % i

#Makes a counter that counts when the gate is high and
#pause when the gate is low
def make_counter():
    ctr = daq.Task()
    ctr.CreateCICountEdgesChan("Dev1/ctr0", "",
                              daq.DAQmx_Val_Rising,
                              0, # initial count
                              daq.DAQmx_Val_CountUp)
    # configure pause trigger
    ctr.SetPauseTrigType(daq.DAQmx_Val_DigLvl)
    ctr.SetDigLvlPauseTrigWhen(daq.DAQmx_Val_Low)
    
    return ctr

#Counts the number of times the gate was activated
def make_gate_counter():
    ctr = daq.Task()
    ctr.CreateCICountEdgesChan("Dev1/ctr3", "",
                              daq.DAQmx_Val_Rising,
                              0, #initial count
                              daq.DAQmx_Val_CountUp)
    return ctr

#context manager for convenience
@contextmanager
#This stops the tasks if the python kernel is interrupted.
#provide arguments in the order you want them to shut down
def acquiring(*tasks):
    try: 
        yield
    except KeyboardInterrupt:
        # stop the counters
        for i, task in enumerate(tasks):
            try:
                task.StopTask()
                spin.pb_stop()
                print("stopped task %d" % i, sys.stderr)#formerly file=sys.stderr
            except daq.DAQError:
                print("no need to stop task %d" % i, sys.stderr)#formerly file=sys.stderr
            raise

#start sequence of tasks
def start_sequence(*tasks):
    for task in tasks:
        task.StartTask()

#finish sequence of tasks
def finish_sequence(*tasks):
    for task in tasks:
        task.WaitUntilTaskDone(10.)
        task.StopTask()

#get photon counts [from APD]
def get_counts(ctr): # must give it the channel to look into
    count = daq.uInt32()
    #ctr.WaitUntilTaskDone(10.) # not sure what for but could be useful?
    ctr.ReadCounterScalarU32(10.0, daq.byref(count), None)
    ctr.StopTask()
    return count.value

#Make a measurement.
def make_measurement():
    gc = make_gate_counter()
    pc = make_counter()
    
    with acquiring(pc, gc):
        start_sequence(gc, pc)
        pulse_blast()
        photons = get_counts(pc)
        pulses = get_counts(gc)
        finish_sequence(gc,pc)
    #print(photons, pulses)
    return photons, pulses

###########################################################
#Spincore card
#common pulses
###########################################################

#standard pulses
#make sure these channels match up with spincore card channels.
pulse_dict = dict(
                  off = 0b111000000000000000000000,
                  all_on = 0b111000000000000000000000,
                  green = 0b111000000000000000000001,
                  mw = 0b111000000000000000001000,
                  detection = 0b111000000000000000000011
                 )

#add a pulse to pulse_dict, or change an existing pulse.
def write_pulse(pulse_name, bits, num_channels=4):
    
    #Error catching
    
    bits = str(bits)    
    
    if not type(pulse_name) == str:
        print('pulse_name must be a string')
        return
    
    if not type(bits) == str:
        print('bits must be a string consisting of a sequence of ' + str(num_channels) + ' 0s and 1s')
        return
    
    if not len(bits) == num_channels:
        print('bits must be a string consisting of a sequence of ' + str(num_channels) + ' 0s and 1s')
        return
    
    if not all([item in ['0', '1'] for item in list(bits)]):
        print('bits must be a string consisting of a sequence of ' + str(num_channels) + ' 0s and 1s')
        return
    
    #The function
    
    default_off = '0b111000000000000000000000'
    
    bits = default_off[:-num_channels] + bits
    bits = int(bits[2:], 2)
    
    pulse_dict[pulse_name] = bits

#spin.pb_stop(), all_off(), and green_off() are all
#equivalent. Stop all pulses.
def all_off():
    spin.pb_stop()

#start custom pulse. It will be on for at least 1 s.
def custom_on(custom_pulse, pulse_name='custom', num_channels=4):
    
    write_pulse(pulse_name, custom_pulse, num_channels=num_channels)
    
    custom = pulse_dict[pulse_name]
    
    spin.pb_start_programming(spin.PULSE_PROGRAM)

    start = spin.pb_inst_pbonly(custom, spin.CONTINUE, 0, 500)
    spin.pb_inst_pbonly(custom, spin.BRANCH, start, 500)

    spin.pb_stop_programming()
    
    spin.pb_start()

#start green pulse. It will be on for at least 1 s.
def green_on(green_pulse='default', num_channels=4):

    if not green_pulse == 'default':
        write_pulse('green', green_pulse, num_channels=num_channels)
    
    green = pulse_dict['green']
    
    spin.pb_start_programming(spin.PULSE_PROGRAM)

    start = spin.pb_inst_pbonly(green, spin.CONTINUE, 0, 500)
    spin.pb_inst_pbonly(green, spin.BRANCH, start, 500)

    spin.pb_stop_programming()
    
    spin.pb_start()

#spin.pb_stop(), all_off(), and green_off() are all
#equivalent. Stop all pulses.
def green_off():
    spin.pb_stop()

###########################################################
#Spincore card
#common scans
###########################################################

#Programs into spincore card the sequence: initialization
#pulse, delay, MW pulse, delay, detection pulse. This is a
#single point in a Rabi oscillation scan.
def rabi_pulse(mw_duration, loop_num=500000,
               green_time=2300, det_time=300, off_time=650):
    
    green_time = green_time * spin.ns
    det_time = det_time * spin.ns
    off_time = off_time * spin.ns
    mw_time = mw_duration * spin.ns
    delay_time = (5500 * spin.ns - mw_time)
    #delay_time = 500
    
    off = pulse_dict['off']
    mw = pulse_dict['mw']
    green = pulse_dict['green']
    det = pulse_dict['detection']
    
    #note: rabi_program won't take loop_num > 2**20 = 1048576
    
    spin.pb_start_programming(spin.PULSE_PROGRAM)

    start = spin.pb_inst_pbonly(green, spin.JSR, 2, green_time) # JSR wants instruction line of the subroutine. Turn on green, go into subroutine (starting with sub = line) below
    spin.pb_inst_pbonly(off, spin.STOP, 0, off_time) #turn everything off. This occurs after the subroutine below.

    sub = spin.pb_inst_pbonly(off, spin.LOOP, loop_num, delay_time) #Begin subroutine loop. Delay is so that, for different mw times, loop as a whole (i.e., duty cycle) has the same amount of time.
    spin.pb_inst_pbonly(mw, spin.CONTINUE, 0, mw_time) #microwave pulse for state transfer.
    spin.pb_inst_pbonly(green, spin.CONTINUE, 0, off_time) #accounts for delay between telling green to turn on and green actually turning on.
    spin.pb_inst_pbonly(det, spin.CONTINUE, 0, det_time) #detection pulse
    spin.pb_inst_pbonly(green, spin.END_LOOP, sub, green_time) #End subroutine loop. Initialization pulse, it's at the end of the loop, intended for next loop.
    
    spin.pb_inst_pbonly(green, spin.RTS, 0, green_time) #After loops. Extra instruction needed after loop, chose green on arbitrarily.

    spin.pb_stop_programming()

#Measurements for Rabi oscillation pulse sequence
def gen_scan(widths, loop_num=500000, repeat_each_pulse_width=1,
             green_time=2300, det_time=300, off_time=650):
    
    repeat_each_pulse_width = int(repeat_each_pulse_width)
    cnt_arr = []
    start_time = time.time()
    
    w_ind = 0
    cnt_arr_ind = 0
    for w in widths:
        
        rabi_pulse(w, loop_num=loop_num, green_time=green_time, det_time=det_time, off_time=off_time)
        photons, pulses = make_measurement()
        #count_time = det_time * spin.ns * pulses
        count_time = det_time * (spin.ns * 10.0**-9.0) * pulses
        counts = photons / count_time
        
        if w_ind == 0: 
            cnt_arr.append(counts / float(repeat_each_pulse_width))
            
            end_time = start_time + ((time.time() - start_time) * len(widths))
            print('Estimated scan end time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
            
        elif  not widths[w_ind] == widths[w_ind - 1]:
            cnt_arr.append(counts / float(repeat_each_pulse_width))
            cnt_arr_ind += 1
        
        else:
            cnt_arr[cnt_arr_ind] +=  counts / float(repeat_each_pulse_width)
        
        w_ind += 1
        
        if w_ind % repeat_each_pulse_width == 0:
            yield (w - 1), cnt_arr[cnt_arr_ind]
    
    spin.pb_stop()
