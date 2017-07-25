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
    if save_trace:
        try:
            os.mkdir('scans')
            trace_dir = time.strftime('scans/%Y-%m-%d-%H-%M-%S_trace', time.localtime(start_time))
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
    if save_trace:
        try:
            os.mkdir('scans')
            trace_dir = time.strftime('scans/%Y-%m-%d-%H-%M-%S_trace', time.localtime(start_time))
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
              amplifier_dBm=30.0, lag=0.1, count_time=0.1,
              init_pause=0.0):
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
    from wanglib.util import scanner
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
                  ['Count time (s)', str(float(count_time))]
                  ]
    
    generator.rf_on = 1
    generator.set_power(power_dBm - amplifier_dBm)

    time.sleep(init_pause)
    
    generator.set_frequency(freq_center)
    freqs = np.arange(-1 * freq_span / 2.0, freq_span / 2.0, freq_step) + freq_center
    
    start_time = time.time() - init_pause
    
    #print(freqs)
    
    odmr = scanner(freqs, set=generator.set_frequency, get=doct2, lag=lag)
    
    generator.rf_on = 1
    data = plotgen(odmr)
    generator.rf_on = 0
    
    #Save scan data
    save_scan(np.transpose(data), base_name='cw_odmr', scan_time=start_time, parameters=parameters)