'''
scans.py
Commonly used scans.
'''

'''
analyzer_scan(analyzer, 
            freq_min, freq_max, freq_step,
            ref_level=-63.0, span=30, bandwidth=0.01,
            init_pause = 5.0, pause=1.0,
            plot=False, save_trace=False)

generator_analyzer_scan(freq_min, freq_max, freq_step,
            generator_power=-50.0, rf=1,
            ref_level=-63.0, span=30, bandwidth=0.01,
            init_pause = 5.0, pause=1.0,
            plot=True, save_trace=False)

cw_odmr_scan(generator,
            power_dBm, freq_center, freq_span, freq_step,
            amplifier_dBm=30.0, lag=0.1, count_time=0.1,
            init_pause=0.0)

focus_scan(generator,
            power_dBm, freq_1, freq_2, scan_time,
            amplifier_dBm=30.0, lag=0.1, count_time=0.1,
            init_pause=0.0)

rabi_osc_scan(generator, power_dBm, freq,
            mw_pulse_min, mw_pulse_max, mw_pulse_step,
            amplifier_dBm=30.0, init_pause=0.0,
            loop_num=500000, repeat_each_pulse_width=1,
            green_time=2300, det_time=300, off_time=650,
            overlay=False)
'''

#Instruments:
#    HP E4401 spectrum analyzer.
#Scan HP E4401, and record trace for each frequency.
#Save (and plot) the scan. Save parameters (and traces).
def analyzer_scan(analyzer, 
                freq_min, freq_max, freq_step,
                ref_level=-63.0, span=30, bandwidth=0.01,
                init_pause=5.0, pause=1.0,
                plot=False, save_trace=False):
    '''
    Requires class hp_e4401 from instruments.py.
    Example: initialize as and use as...
    
    >>>#Initialization...
    >>>
    >>>import visa
    >>>import sjha_wang_lab.instruments as wli
    >>>
    >>>rm = visa.ResourceManager()
    >>>rm.list_resources()
    ('GPIB0::18::INSTR',)
    >>>
    >>>print(rm.open_resource('GPIB0::18::INSTR').query('*IDN?'))
    Hewlett-Packard, E4401B, MY41440151, A.14.03
    >>>
    >>>rsa = wli.hp_e4401(rm.open_resource('GPIB0::18::INSTR'))
    >>>
    >>>#Run a scan
    >>>
    >>>analyzer_scan(rsa, freq_min, freq_max, freq_step)
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    import os
    import time
    from general_tools import save_array, save_scan
    
    parameters = [['Analyzer reference level (dBm)', str(float(ref_level))],
                  ['Analyzer span (MHz)', str(float(span))],
                  ['Analyzer bandwidth (MHz)', str(float(bandwidth))],
                  ['Pause before scan (s)', str(float(init_pause))],
                  ['Pause between traces (s)', str(float(pause))],
                  ['Data points per trace', str(0)]
                 ]
    
    #scan_array_0 will be x-values, i.e., frequencies.
    #scan_array_1 will by y-values, i.e., power readings.
    scan_array_0 = np.arange(float(freq_min), freq_max + freq_step, freq_step)
    scan_array_1 = 0.0 * scan_array_0
    
    analyzer.set_span(span)
    analyzer.set_bandwidth(bandwidth)
    analyzer.set_reference_level(ref_level)
    
    time.sleep(init_pause)
    
    scan_ind = 0
    start_time = time.time() - init_pause
    
    #Directory for saved traces
    trace_dir = time.strftime('scans/%Y-%m-%d-%H-%M-%S_trace', time.localtime(start_time))
    if save_trace:
        try:
            os.mkdir('scans')
        except:
            #print('could not make one of the directories')
            pass
        try:
            os.mkdir(trace_dir)
        except:
            #print('could not make one of the directories')
            pass
    
    for freq in scan_array_0:
        #print(str(freq) + ' MHz')
        analyzer.set_frequency(freq)
        time.sleep(pause)
        
        readings = analyzer.trace()
        readings_ind = (np.where(readings[0] == freq))[0][0]
        #print(readings[0, readings_ind])
        #print(readings[1, readings_ind])
        value = readings[1, readings_ind]
        scan_array_1[scan_ind] = value
        
        #Save all traces
        if save_trace:
            save_array(trace_dir + '/' + str(freq) + '.txt', np.transpose(readings), delimiter=',')
        
        scan_ind = scan_ind + 1
        #Find total scan time based on time taken for first scan.
        if scan_ind == 1:
            scan_time = time.time() - (start_time + init_pause)
            end_time = start_time + init_pause + len(scan_array_0) * scan_time
            print('Scan start time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)))
            print('Estimated scan end time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
            
            #Data points per trace
            parameters[-1][1] = str(len(readings[0]))
        
    scan_array = np.array([scan_array_0, scan_array_1])
    save_scan(np.transpose(scan_array), scan_time=start_time, parameters=parameters)
    
    if plot:
        plt.plot(scan_array_0, scan_array_1)
    
    return scan_array

#Instruments:
#    HP 8647 frequency generator. Also works with other
#    generators in instruments.py.
#    HP E4401 spectrum analyzer.
#Scan HP 8647 through a range of frequencies. Match these
#with HP E4401, and record trace for each frequency.
#Save (and plot) the scan. Save parameters (and traces).
def generator_analyzer_scan(generator, analyzer, 
                freq_min, freq_max, freq_step,
                generator_power=-50.0, rf=1,
                ref_level=-63.0, span=30, bandwidth=0.01,
                init_pause = 5.0, pause=1.0,
                plot=False, save_trace=False):
    '''
    Requires classes hp_8647 and hp_e4401 from instruments.py.
    Example: initialize as and use as...
    
    >>>#Initialization...
    >>>
    >>>import visa
    >>>import sjha_wang_lab.instruments as wli
    >>>
    >>>rm = visa.ResourceManager()
    >>>rm.list_resources()
    ('GPIB0::12::INSTR', 'GPIB0::18::INSTR')
    >>>
    >>>print(rm.open_resource('GPIB0::12::INSTR').query('*IDN?'))
    Hewlett-Packard, 8648C, 3623A03349, B.04.03
    >>>
    >>>print(rm.open_resource('GPIB0::18::INSTR').query('*IDN?'))
    Hewlett-Packard, E4401B, MY41440151, A.14.03
    >>>
    >>>hp = wli.hp_8647(rm.open_resource('GPIB0::12::INSTR'))
    >>>rsa = wli.hp_e4401(rm.open_resource('GPIB0::18::INSTR'))
    >>>
    >>>#Run a scan
    >>>
    >>>generator_analyzer_scan(hp, rsa, freq_min, freq_max, freq_step)
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    import os
    import time
    from general_tools import save_array, save_scan
    
    parameters = [['Generator power (dBm)', str(float(generator_power))],
                  ['Generator RF on', str(bool(rf))],
                  ['Analyzer reference level (dBm)', str(float(ref_level))],
                  ['Analyzer span (MHz)', str(float(span))],
                  ['Analyzer bandwidth (MHz)', str(float(bandwidth))],
                  ['Pause before scan (s)', str(float(init_pause))],
                  ['Pause between traces (s)', str(float(pause))],
                  ['Data points per trace', str(0)]
                 ]
    
    #scan_array_0 will be x-values, i.e., frequencies.
    #scan_array_1 will by y-values, i.e., power readings.
    scan_array_0 = np.arange(float(freq_min), freq_max + freq_step, freq_step)
    scan_array_1 = 0.0 * scan_array_0
    
    generator.set_power(generator_power)
    analyzer.set_span(span)
    analyzer.set_bandwidth(bandwidth)
    analyzer.set_reference_level(ref_level)
    
    generator.rf_on = rf
    time.sleep(init_pause)
    
    scan_ind = 0
    start_time = time.time() - init_pause
    
    #Directory for saved traces
    trace_dir = time.strftime('scans/%Y-%m-%d-%H-%M-%S_trace', time.localtime(start_time))
    if save_trace:
        try:
            os.mkdir('scans')
        except:
            #print('could not make one of the directories')
            pass
        try:
            os.mkdir(trace_dir)
        except:
            #print('could not make one of the directories')
            pass
    
    for freq in scan_array_0:
        #print(str(freq) + ' MHz')
        generator.set_frequency(freq)
        analyzer.set_frequency(freq)
        time.sleep(pause)
        
        readings = analyzer.trace()
        readings_ind = (np.where(readings[0] == freq))[0][0]
        #print(readings[0, readings_ind])
        #print(readings[1, readings_ind])
        value = readings[1, readings_ind]
        scan_array_1[scan_ind] = value
        
        #Save all traces
        if save_trace:
            save_array(trace_dir + '/' + str(freq) + '.txt', np.transpose(readings), delimiter=',')
        
        scan_ind = scan_ind + 1
        #Find total scan time based on time taken for first scan.
        if scan_ind == 1:
            scan_time = time.time() - (start_time + init_pause)
            end_time = start_time + init_pause + len(scan_array_0) * scan_time
            print('Scan start time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)))
            print('Estimated scan end time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
            
            #Data points per trace
            parameters[-1][1] = str(len(readings[0]))
    
    generator.rf_on = 0
    
    scan_array = np.array([scan_array_0, scan_array_1])
    save_scan(np.transpose(scan_array), scan_time=start_time, parameters=parameters)
    
    if plot:
        plt.plot(scan_array_0, scan_array_1)
    
    return scan_array

def cw_odmr_scan(generator,
              power_dBm, freq_center, freq_span, freq_step,
              amplifier_dBm=30.0, lag=0.1,
              count_time=0.1, repeat_each_freq=1,
              init_pause=0.0, overlay=False):
    '''
    Requires class hp_8647 or similar from instruments.py.
    Example: initialize as and use as...
    
    Averaging parameter: effective averging parameter is count_time * repeat_each_freq.
    - count_time: how long, in s, to leave take in APD counts. APD samples at 10 Hz, so
    e.g., count_time=1 would have 1 s and 10 samples per data point.
    - repeat_each_freq: can measure at each mw pulse time more than once - this is
    mainly to get around the issue that count_time has an upper limit (>~ 5s)
    before memory issues occur.
    
    >>>#Initialization...
    >>>
    >>>import visa
    >>>import sjha_wang_lab.instruments as wli
    >>>
    >>>rm = visa.ResourceManager()
    >>>rm.list_resources()
    ('GPIB0::12::INSTR', 'GPIB0::18::INSTR')
    >>>
    >>>print(rm.open_resource('GPIB0::12::INSTR').query('*IDN?'))
    Hewlett-Packard, 8648C, 3623A03349, B.04.03
    >>>
    >>>hp = wli.hp_8647(rm.open_resource('GPIB0::12::INSTR'))
    >>>
    >>>#Set scan parameters, then run a scan
    >>>
    >>>power_dBm = 30.0
    >>>freq_center = 2871.0
    >>>freq_span = 100.0
    >>>freq_step = 2.0
    >>>count_time = 0.5
    >>>
    >>>cw_odmr_scan(hp, power_dBm, freq_center, freq_span, freq_step, count_time=count_time)
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    import time
    from itertools import count
    from wanglib.util import scanner, averager
    from wanglib.pylab_extensions.live_plot import plotgen
    from general_tools import save_scan
    from expt_supp import doct
    
    def doct2(t=count_time):
        return doct(t)
    
    parameters = [['Intended input power (dBm)', str(float(power_dBm))],
                  ['Generator power (dBm)', str(float(power_dBm - amplifier_dBm))],
                  ['Assumed amplifier gain (dBm)', str(float(amplifier_dBm))],
                  ['Generator frequency center (MHz)', str(float(freq_center))],
                  ['Generator frequency span (MHz)', str(float(freq_span))],
                  ['Generator frequency step (MHz)', str(float(freq_step))],
                  ['Lag time (s)', str(float(lag))],
                  ['Count time (s)', str(float(count_time))],
                  ['Repeat each frequency', str(int(repeat_each_freq))]
                  ]
    
    try:
        generator.set_pulsed(0)
    except:
        pass
    
    generator.set_rf(1)
    
    generator.set_power(power_dBm - amplifier_dBm)

    time.sleep(init_pause)
    
    generator.set_frequency(freq_center)
    repeat_each_freq = int(repeat_each_freq)
    freqs = np.arange(-1 * freq_span / 2.0, freq_span / 2.0, freq_step) + freq_center
    #freqs = np.repeat(freqs, repeat_each_freq)
    
    start_time = time.time() - init_pause
    end_time = start_time + init_pause + (count_time + lag) * len(freqs) * repeat_each_freq
    
    print('Scan start time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)))
    print('Estimated scan end time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
    #print(freqs)
    
    if repeat_each_freq < 2:
        odmr = scanner(freqs, set=generator.set_frequency, get=doct2, lag=lag)
    
    else:
        acq = averager(doct2, repeat_each_freq, lag=lag)
        odmr = scanner(freqs, set=generator.set_frequency, get=acq)
    
    #remove previous scans from plot that will be displayed
    if not overlay:
        plt.clf()
    
    data = plotgen(odmr)
    generator.set_rf(0)
    
    #Save scan data
    save_scan(np.transpose(data), base_name='cw_odmr', scan_time=start_time, parameters=parameters)

#Scan that jumps between two frequencies until told to
#stop. Purpose is to be able to actively focus so as to
#maximize the difference in signal between the two points.
def focus_scan(generator,
              power_dBm, freq_1, freq_2, scan_time,
              amplifier_dBm=30.0, lag=0.1, count_time=0.1,
              init_pause=0.0):
    import numpy as np
    import matplotlib.pyplot as plt
    import time
    from itertools import count
    from wanglib.util import scanner
    from wanglib.pylab_extensions.live_plot import plotgen
    from expt_supp import doct
    
    def doct2(t=count_time):
        return doct(t)
    
    len_freqs = int(scan_time / (count_time + lag))
    freqs = np.zeros(len_freqs)
    freqs[0::2] = freq_1
    freqs[1::2] = freq_2
    
    generator.set_power(power_dBm - amplifier_dBm)
    generator.set_frequency(freq_1)
    generator.rf_on = 1
    
    time.sleep(init_pause)
    
    focus_scanner = scanner(freqs, set=generator.set_frequency, get=doct2, lag=lag)
    
    data = plotgen(focus_scanner)
    generator.rf_on = 0

#Does a Rabi oscillation scan. Based on Ignas's iPython notebook from Fluorescence Microscopy Setup 1.
def rabi_osc_scan(generator, power_dBm, freq,
              mw_pulse_min, mw_pulse_max, mw_pulse_step,
              amplifier_dBm=30.0, init_pause=0.0,
              loop_num=500000, repeat_each_pulse_width=1,
              green_time=2300, det_time=300, off_time=650,
              overlay=False):
    '''
    Requires class hp_8647 or similar from instruments.py.
    
    Averaging parameter: effective averging parameter is loop_num * repeat_each_pulse_width.
    - loop_num: number of times that Rabi pulse sequence (basically, mw + detection)
    is performed. Each measurement includes the sum of all of what is detected
    from all of these pulse sequences, so loop_num is number of photon detections
    that are averaged for a given mw pulse time.
    - repeat_each_pulse_width: can measure at each mw pulse time more than once - this is
    mainly to get around the issue that loop_num has an upper limit (2**20 on one day
    that I tested it) before memory issues occur.
    - Note: for each iteration of loop_num, count_time = det_time * spin.ns * pulses in
    expt_supp.py, so hard to state exact count time. But, to control it, adjust det_time.
    
    Example: initialize as and use as...
    
    >>>#Initialization...
    >>>
    >>>import visa
    >>>import sjha_wang_lab.instruments as wli
    >>>
    >>>rm = visa.ResourceManager()
    >>>rm.list_resources()
    ('GPIB0::12::INSTR', 'GPIB0::18::INSTR')
    >>>
    >>>print(rm.open_resource('GPIB0::12::INSTR').query('*IDN?'))
    Hewlett-Packard, 8648C, 3623A03349, B.04.03
    >>>
    >>>hp = wli.hp_8647(rm.open_resource('GPIB0::12::INSTR'))
    >>>
    >>>#Set scan parameters, then run a scan
    >>>
    >>>power_dBm = 30.0
    >>>freq = 2871.0
    >>>mw_pulse_min = 15.0
    >>>mw_pulse_max = 600.0
    >>>mw_pulse_step = 60.0
    >>>
    >>>rabi_osc_scan(hp, power_dBm, freq, mw_pulse_min, mw_pulse_max, mw_pulse_step)
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    import time
    from wanglib.pylab_extensions.live_plot import plotgen
    from wanglib.util import scanner
    from general_tools import save_scan
    from expt_supp import gen_scan
    
    parameters = [['Intended input power (dBm)', str(float(power_dBm))],
                  ['Generator power (dBm)', str(float(power_dBm - amplifier_dBm))],
                  ['Assumed amplifier gain (dBm)', str(float(amplifier_dBm))],
                  ['Generator frequency (MHz)', str(float(freq))], 
                  ['Minimum microwave pulse time (ns)', str(float(mw_pulse_min))],
                  ['Maximum microwave pulse time (ns)', str(float(mw_pulse_max))],
                  ['Microwave pulse time step (ns)', str(float(mw_pulse_step))],
                  ['loop_num', str(int(loop_num))],
                  ['repeat_each_pulse_width', str(int(repeat_each_pulse_width))],
                  ['green_time', str(green_time)],
                  ['det_time', str(float(det_time))],
                  ['off_time', str(float(off_time))],
                  ]
    
    generator.set_power(power_dBm - amplifier_dBm)
    generator.set_frequency(freq)
    
    generator.set_rf(1)
    generator.set_pulsed(1) #Works on machines with hardware for pulsed mode only
    
    time.sleep(init_pause)
    
    repeat_each_pulse_width = int(repeat_each_pulse_width)
    widths = np.arange(1.0 * mw_pulse_min, 1.0 * mw_pulse_max + 1.0 * mw_pulse_step, 1.0 * mw_pulse_step)
    
    if widths[-1] > mw_pulse_max:
        widths = widths[: -1]
    
    if repeat_each_pulse_width >= 2:
        widths = np.repeat(widths, repeat_each_pulse_width)
    
    start_time = time.time() - init_pause
    print('Scan start time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)))
    #estimated end time calculated and printed by gen_scan function below
    
    gen = gen_scan(widths, loop_num=loop_num, repeat_each_pulse_width=repeat_each_pulse_width, det_time=det_time, off_time=off_time)
    data = plotgen(gen)
    if not overlay:
        plt.clf()
    
    generator.set_rf(0)
    generator.set_pulsed(0)
    
    #Save scan data
    save_scan(np.transpose(data), base_name='rabi_osc', scan_time=start_time, parameters=parameters)

#Does a Rabi oscillation scan. Based on Mayra's iPython notebook from Croystat Setup 2.
def rabi_scan(generator, power_dBm, freq, 
              mw_pulse_min, mw_pulse_max, mw_pulse_step,
              det_t=400, off_t=3000, green_t=5000,
              duty_t=5000, wait_t=0, loop_num=100000,
              amplifier_dBm=30.0, init_pause=0.0, 
              lag=0.1, count_time=1.0,
              overlay=True):
    '''
    Requires class hp_8647 or similar from instruments.py.
    
    Example: initialize as and use as...
    
    >>>#Initialization...
    >>>
    >>>import visa
    >>>import sjha_wang_lab.instruments as wli
    >>>
    >>>rm = visa.ResourceManager()
    >>>rm.list_resources()
    ('GPIB0::19::INSTR', 'GPIB0::19::INSTR')
    >>>
    >>>print(rm.open_resource('GPIB0::19::INSTR').query('*IDN?'))
    Hewlett-Packard, 8648C, 3847M01380, B.04.09
    >>>
    >>>gen = wli.hp_8647(rm.open_resource('GPIB0::19::INSTR'))
    >>>
    >>>#Set scan parameters, then run a scan
    >>>
    >>>power_dBm = 30.0
    >>>freq = 2871.0
    >>>mw_pulse_min = 15.0
    >>>mw_pulse_max = 600.0
    >>>mw_pulse_step = 60.0
    >>>
    >>>rabi_scan(gen, power_dBm, freq, mw_pulse_min, mw_pulse_max, mw_pulse_step)
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    import time
    from functools import partial
    from wanglib.pylab_extensions.live_plot import plotgen
    from wanglib.util import scanner
    from general_tools import save_scan
    from rabi_supp import rabi_start, do_count_v2, initialize, stop, close
    
    parameters = [['Intended input power (dBm)', str(float(power_dBm))],
                  ['Generator power (dBm)', str(float(power_dBm - amplifier_dBm))],
                  ['Assumed amplifier gain (dBm)', str(float(amplifier_dBm))],
                  ['Generator frequency (MHz)', str(float(freq))], 
                  ['Minimum microwave pulse time (ns)', str(float(mw_pulse_min))],
                  ['Maximum microwave pulse time (ns)', str(float(mw_pulse_max))],
                  ['Microwave pulse time step (ns)', str(float(mw_pulse_step))],
                  ['loop_num', str(int(loop_num))],
                  ['count_time', str(float(count_time))],
                  ['det_t', str(float(det_t))],
                  ['off_t', str(float(off_t))],
                  ['green_t', str(float(green_t))],
                  ['duty_t', str(float(duty_t))],
                  ]
    
    widths = np.arange(1.0 * mw_pulse_min, 1.0 * mw_pulse_max + 1.0 * mw_pulse_step, 1.0 * mw_pulse_step)
    
    def rabi_pulse(mw_t):
        rabi_start(mw_t, det_t=det_t, off_t=off_t, green_t=green_t, duty_t=duty_t, wait_t=wait_t, loop_num=loop_num)
    
    generator.set_power(power_dBm - amplifier_dBm)
    generator.set_frequency(freq)
    
    generator.set_rf(1)
    generator.set_pulsed(1) #Works on machines with hardware for pulsed mode only
    
    initialize()
    
    time.sleep(init_pause)
    start_time = time.time() - init_pause
    end_time = start_time + init_pause + (count_time + lag) * len(widths)
    
    print('Scan start time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)))
    print('Estimated scan end time: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
    
    #Note: count_time is time spent on each frequency, not total time that APD is counting.
    #Note: count_time only works up to whatever time loop_num allows.
    sgen = scanner(widths,
                   get=partial(do_count_v2, count_time),
                   set=rabi_pulse,
                   lag=lag)
    
    if not overlay:
        plt.clf()
    
    data = plotgen(sgen)
    
    save_scan(np.transpose(data), base_name='cw_odmr', scan_time=start_time, parameters=parameters)
    
    stop()
    close()
    
    generator.set_rf(0)
    generator.set_pulsed(0)