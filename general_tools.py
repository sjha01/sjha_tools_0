'''
general_tools.py
A hodgepodge of tools useful for controlling scans, saving
data from scans, and analyzing data from scans.
'''

'''
List of defined functions with arguments:

save_array(file_name, data_array,
           delimiter=' ', newline='\n')

save_scan(scan_data, base_name='scan',
          scan_time=0.0,
          parameters=[['param_1 (units)', str(1.0)]],
          param_save=True, ext='txt', data_2d=True)

str_local_time(time_float)

time_difference(delta_t)

str_time_difference(delta_t)

timed_for(lst, funct, args,
          kwargs=dict(), loop_num=1, add_time=0.0,
          print_start=True, print_est=True,
          print_est_end=True, print_end=True)

smooth(x,
       window_len=11, window='hanning',
       original_length=True)
'''

#Saves an array-like data structure to a text file
def save_array(file_name, data_array, delimiter=' ', newline='\n'):
    import numpy as np
    
    #Error catching
    
    try:
        temp_var = len(data_array)
    except:
        print('data_array must be array or list with array-like shape')
        return

    if type(data_array) == str:
        print('data_array must be array or list with array-like shape')
        return
    
    try:
        temp_var = np.shape(data_array)
    except:
        print('data_array must be array or list with array-like shape')
        return
    
    if not len(np.shape(data_array)) < 3:
        print('data_array cannot have depth greater than 2')
        return
    
    #Error catching, and begin function
    
    if not type(data_array) == list:
        try:
            data_array = data_array.astype(str)
        except:
            print('data_array must be array or list with array-like shape')
            return
    else:
        if len(np.shape(data_array)) == 1:
            data_array = [str(item) for item in data_array]
        else:
            data_array = [[str(sub_item) for sub_item in item] for item in data_array]
    
    file_string = '';
    
    if len(np.shape(data_array)) == 1:
        for item in data_array:
            file_string = file_string + item + newline
    elif len(np.shape(data_array)) == 2:
        for item in data_array:
            file_string = file_string + delimiter.join(item) + newline
    
    f = open(file_name, 'w')
    f.write(file_string)
    f.close()

#Saves scan data and optionally parameters.
def save_scan(scan_data, base_name='scan', scan_time=0.0,
              parameters=[['param_1 (units)', str(1.0)]],
              param_save=True, ext='txt', data_2d=True):
    import numpy as np
    import time
    import os
    
    #Get the time as early as possible
    if scan_time == 0.0:
        scan_time = time.time()
    
    #Error catching
    
    if type(scan_data) == int or type(scan_data) == float:
        print('scan_data must be convertible to numpy.ndarray')
        return
    
    elif type(scan_data) == list:
        try:
            scan_data = np.array(scan_data).astype(float)
        except:
            print('scan_data must be convertible to numpy.ndarray')
            return
    
    elif not type(scan_data) == np.ndarray:
        try:
            scan_data = scan_data.astype(float)
        except:
            print('scan_data must be convertible to numpy.ndarray')
            return
    
    if data_2d:
        if not len(np.shape(scan_data)) == 2:
            print('scan_data must be of shape [n, 2]')
            return
        
        if not np.shape(scan_data)[1] == 2:
            print('scan_data must be a list of shape [n, 2]')
            return 
    
    if not type(scan_time) == float:
        print('scan_time must be a non-negative float')
        return
    
    if not scan_time >= 0.0:
        print('scan_time must be a non-negative float')
        return
    
    if not type(parameters) == list:
        print('parameters must be a list of lists of strings')
        return
    
    if not type(parameters[0]) == list:
        print('parameters must be a list of lists of strings')
        return
    
    if not all([type(item) == str for item in parameters[0]]):
        print('parameters must be a list of lists of strings')
        return
    
    if not len(np.shape(parameters)) == 2:
        print('parameters must be a list of shape [n, 2]')
        return
    
    if not np.shape(parameters)[1] == 2:
        print('parameters must be a list of shape [n, 2]')
        return
    
    if not type(ext) == str:
        print('ext must be a non-empty string.')
        return
    
    if not len(ext) > 0:
        print('ext must be a non-empty string.')
        return
    
    #The function
    
    time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(scan_time))
    
    try:
        os.mkdir('scans')
    except:
        #print('could not make directory scans')
        pass
    
    file_name_scan = 'scans/' + base_name + '_%s.%s' % (time_str, ext)
    
    #Save scan data
    np.savetxt(file_name_scan, scan_data, newline='\r\n')
    
    print('Scan file name: ' + file_name_scan)
    
    #Save scan parameters
    if param_save:
        file_name_parameters = 'scans/' + base_name + '_%s_parameters.%s' % (time_str, ext)
        save_array(file_name_parameters, parameters)

#Format time as float to time as a string Y-m-d H:M:S
def str_local_time(time_float):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_float))

#Time difference in S to time difference in [d, H, M, S]
def time_difference(delta_t):
    d = int(int(delta_t) / 86400)
    H = int((int(delta_t) - (d * 86400)) / 3600)
    M = int((int(delta_t) - (d * 86400) - (H * 3600)) / 60)
    S = int((delta_t) - (d * 86400) - (H * 3600) - (M * 60))
    return [d, H, M, S]

#Time differece in S to formatted string of time difference as d H:M:S.
def str_time_difference(delta_t):
    difference_list = [str(item) for item in time_difference(delta_t)]
    return '%s %s:%s:%s' % tuple(difference_list)

#Iterate function over a list. Time one iteration of the
#function, use it to estimate amount of time it will take
#to iterate over the whole list.
#Function prints any of start time, time list takes,
#estimated end time, and actual end time.
def timed_for(lst, funct, args, kwargs=dict(), loop_num=1, delay_time=0.0, add_time=0.0,
              print_start=True, print_est=True, print_est_end=True, print_end=True):
    import time
    
    #Error catching
    
    try:
        len(lst)
    except:
        print('lst must be an iterable object')
        return
            
    if not callable(funct):
        print('funct must be the name of a function (without the parentheses)')
        return
    
    try:
        len(args)
    except:
        print('args must be list-like structure containing non-keyword arguments of funct')
        return
    
    if not type(kwargs) == dict:
        print('kwargs must a dictionary containing keyword arguments of funct. Format: dict(param_1=val_1, param_2=val_2, ...)')
        return
    
    if loop_num > len(lst):
        print('loop_num cannot be greater than number of loops')
        return
    
    if not type(delay_time) in [int, float]:
        print('delay_time must be of type int or float')
        return
    
    if not type(add_time) in [int, float]:
        print('add_time must be of type int or float')
        return
    
    if not all([type(item) == bool for item in [print_start, print_est, print_est_end, print_end]]):
        print('print_start, print_est, print_est_end, and print_end must all be of type bool')
        return
    
    #The function
    
    start_time = time.time()
    
    if print_start:
        print('Start time: %s.' % str_local_time(start_time - delay_time))
    
    iter_num = 1
    
    for iterator in lst:
        if iter_num == loop_num:
            iter_start_time = time.time()
            funct(*args, **kwargs)
            iter_end_time = time.time()
            
            iter_time = iter_end_time - iter_start_time
            
            loop_time_estimate = iter_time * len(lst) + add_time
            end_time_estimate = start_time + loop_time_estimate
            
            if print_est:
                print('Total time: %s.' % str_time_difference(loop_time_estimate))
            if print_est_end:
                print('Estimated end time: %s.' % str_local_time(end_time_estimate))
        
        else:
            funct(*args, **kwargs)
        
        iter_num = iter_num + 1
    
    if print_end:
        end_time = time.time()
        print('Actual end time: %s.' % str_local_time(end_time))

#Smooth a 1D array
def smooth(x, window_len=11, window='hanning', original_length=True):
    import numpy as np
    
    #Error catching
    
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")
    
    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")
        
    if window_len<3:
        return x
    
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")
    
    #The function
    
    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')
    
    y=np.convolve(w/w.sum(),s,mode='valid')
    
    if original_length:
        y = y[int((window_len - 1) / 2): int(-(window_len - 1) / 2)]
    
    return y