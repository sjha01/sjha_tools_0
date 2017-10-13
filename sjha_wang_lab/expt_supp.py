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
from PyDAQmx import * #don't like this, figure out where it's used. I think in make_counter(), make_gate_counter()
import os
import itertools
import sys
from contextlib import contextmanager

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
    ctr = Task()
    ctr.CreateCICountEdgesChan("Dev1/ctr0", "",
                              DAQmx_Val_Rising,
                              0, # initial count
                              DAQmx_Val_CountUp)
    # configure pause trigger
    ctr.SetPauseTrigType(DAQmx_Val_DigLvl)
    ctr.SetDigLvlPauseTrigWhen(DAQmx_Val_Low)
    
    return ctr

#Counts the number of times the gate was activated
def make_gate_counter():
    ctr = Task()
    ctr.CreateCICountEdgesChan("Dev1/ctr3", "",
                              DAQmx_Val_Rising,
                              0, #initial count
                              DAQmx_Val_CountUp)
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
                print("stopped task %d" % i, file=sys.stderr)
            except DAQError:
                print("no need to stop task %d" % i, file=sys.stderr)
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
    count = uInt32()
    #ctr.WaitUntilTaskDone(10.) # not sure what for but could be useful?
    ctr.ReadCounterScalarU32(10.0, byref(count), None)
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
pulse_dict = dict(
                  off = 0b111000000000000000000000,
                  all_on = 0b111000000000000000000000,
                  green = 0b111000000000000000000001,
                  mw = 0b111000000000000000000010,
                  detection = 0b111000000000000000000101
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

#Does sequence: initialization pulse, delay, MW pulse,
#delay, detection pulse. This is a single point in a Rabi
#oscillation scan.
def rabi_pulse(mw_duration, loop_num=500000,
               green_time=2300, det_time=300, off_time=650):
    
    green_time = green_time * spin.ns
    det_time = det_time * spin.ns
    off_time = off_time * spin.ns #650 original
    mw_time = mw_time * spin.ns
    delay = (5500 * spin.ns - mw_time)
    
    off = pulse_dict['off']
    mw = pulse_dict['mw']
    green = pulse_dict['green']
    det = pulse_dict['detection']
    
    #loop_num = 500000 #original 100,000 #20161031 put this as optional parameter in function
    #20161031 due to how code is written, rabi_program won't take loop_num > 2**20 = 1048576
    
    spin.pb_start_programming(spin.PULSE_PROGRAM)

    start = spin.pb_inst_pbonly(green, spin.JSR, 2, green_time) # JSR wants instruction line of the subroutine
    spin.pb_inst_pbonly(off, spin.STOP, 0, off_time) #turn everything off

    sub = spin.pb_inst_pbonly(off, spin.LOOP, loop_num, delay) #delay to isolate from other pulse programs?
    spin.pb_inst_pbonly(mw, spin.CONTINUE, 0, mw_time) #microwave pulse for state transfer
    spin.pb_inst_pbonly(green, spin.CONTINUE, 0, off_time) #what does this do?
    spin.pb_inst_pbonly(det, spin.CONTINUE, 0, det_time) #detection pulse
    spin.pb_inst_pbonly(green, spin.END_LOOP, sub, green_time) #what does this do?
    spin.pb_inst_pbonly(green, spin.RTS, 0, green_time) #what this does

    spin.pb_stop_programming()

#Measurements for Rabi oscillation pulse sequence
def gen_scan(widths, loops=1, loop_num=500000,
             green_time=2300, det_time=300, off_time=650):
    
    cntArr = []
    start_time = time.time()
    
    for i in range(loops):
        print('beginning loop ' + str(i + 1) + ' of ' + str(loops))
        
        for w in range(len(widths)):
            rabi_pulse(widths[w], loop_num=loop_num, green_time=green_time, det_time=det_time, off_time=off_time)
            photons, pulses = make_measurement()
            count_time = det_time * pulses
            counts = photons / count_time
            if w==0:
                cntArr.append(counts / float(loops))
                
                end_time = start_time + ((time.time() - start_time) * loops * len(widths))
                print('Estimated scan end time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
                
            else:
                cntArr[w] +=  counts / float(loops) 
                   
    for w in range(len(widths)):
        counts = cntArr[temp]
        yield widths[w], counts

    spin.pb_stop()

