'''
site_tools.py
A hodgepodge of tools handy for editing images, text files,
and strings for use with HTML.
'''

#Opens a file and replaces a list of strings in the file with a list of new strings, then saves the file.
def replace_strings(filename, old_string_list, new_string_list, temp_str='_t_e_m_p_', same_file=False):
    
    #Error catching
    
    if not len(old_string_list) == len(new_string_list):
        print('Error: lengths need to be the same.')
        return
    
    if not all(isinstance(item, str) for item in (old_string_list + new_string_list)):
        print('Error: all items in both lists must be strings.')
        return
    
    #Get the string from the file
    with open(filename) as f:
        s = f.read()
    
    if temp_str in s:
        print('Error: choose a different string for temp_str. The string must not be in the text file.')
        return
    
    #The function
    
    #save as different file from original if desired
    if not same_file:
        ext = '.' + filename.split('.')[-1]
        filename = filename[:-len(ext)]
        filename = filename + '_replaced' + ext
    
    #The actual replacement
    with open(filename, 'w') as f:
        for i in xrange(len(old_string_list)):
            s = s.replace(old_string_list[i], temp_str + str(i))
        for i in xrange(len(new_string_list)):
            s = s.replace(temp_str + str(i), new_string_list[i])
        f.write(s)

#Next three functions from http://stackoverflow.com/questions/8090229/resize-with-averaging-or-rebin-a-numpy-2d-array/29042041
def get_row_compressor(old_dimension, new_dimension):
    import numpy as np
    
    dim_compressor = np.zeros((new_dimension, old_dimension))
    bin_size = float(old_dimension) / new_dimension
    next_bin_break = bin_size
    which_row = 0
    which_column = 0
    while which_row < dim_compressor.shape[0] and which_column < dim_compressor.shape[1]:
        if round(next_bin_break - which_column, 10) >= 1:
            dim_compressor[which_row, which_column] = 1
            which_column += 1
        elif next_bin_break == which_column:

            which_row += 1
            next_bin_break += bin_size
        else:
            partial_credit = next_bin_break - which_column
            dim_compressor[which_row, which_column] = partial_credit
            which_row += 1
            dim_compressor[which_row, which_column] = 1 - partial_credit
            which_column += 1
            next_bin_break += bin_size
    dim_compressor /= bin_size
    return dim_compressor

#for compress_rgb_array
def get_column_compressor(old_dimension, new_dimension):
    import numpy as np
    
    return get_row_compressor(old_dimension, new_dimension).transpose()

#for compress_rgb_array
def compress_and_average(array, new_shape):
    import numpy as np
    
    # Note: new shape should be smaller in both dimensions than old shape
    return np.mat(get_row_compressor(array.shape[0], new_shape[0])) * \
           np.mat(array) * \
           np.mat(get_column_compressor(array.shape[1], new_shape[1]))

#Given an rgb array and the number of pixels the highest dimension
#should be reduced to, returns (and saves) the compressed array.
def compress_rgb_array(orig_image_name, max_dim, save=True):
    import numpy as np
    from scipy import misc
    
    if type(orig_image_name) == str:
        im1 = misc.imread(orig_image_name)
    else:
        im1 = orig_image_name
        orig_image_name = 'RGBIMAGE.png'
    shape1 = np.shape(im1)
    val1 = np.max(shape1) / float(max_dim)
    
    shape2 = np.around((np.array(shape1) / val1)).astype(int); shape2[2] = shape1[2]; shape2 = tuple(shape2)
    
    im1_0 = im1[:,:,0]
    im1_1 = im1[:,:,1]
    im1_2 = im1[:,:,2]
    
    im2_0 = compress_and_average(im1_0, shape2[:-1])
    im2_1 = compress_and_average(im1_1, shape2[:-1])
    im2_2 = compress_and_average(im1_2, shape2[:-1])
    
    im2 = np.zeros(shape2, 'uint8')
    im2[..., 0] = im2_0.astype(int)
    im2[..., 1] = im2_1.astype(int)
    im2[..., 2] = im2_2.astype(int)
    
    if save:
        misc.imsave(orig_image_name[:-4] + '_compressed_' + str(max_dim) + 'px' + orig_image_name[-4:], im2)
    return im2

#Convert rgb array to rgba array
def rgb_to_rgba(rgb_arr, alpha=1.0):
    import numpy as np
    
    #Assume either integer array with 0 to 255, or float array with 0.0 to 1.0.
    #Convert to the latter if the former.
    if rgb_arr.dtype.kind in ['i', 'u']:
        rgb_arr = rgb_arr.astype(float)
        rgb_arr = rgb_arr / 255.0
    
    shape1 = np.shape(rgb_arr)
    # http://stackoverflow.com/questions/14063530/computing-rgba-to-match-an-rgb-color
    rgba_arr = alpha * np.ones(tuple([shape1[0], shape1[1], 4]))
    rgba_arr[..., 0] = (rgb_arr[..., 0] -1 + alpha) / alpha
    rgba_arr[..., 1] = (rgb_arr[..., 1] -1 + alpha) / alpha
    rgba_arr[..., 2] = (rgb_arr[..., 2] -1 + alpha) / alpha
    
    return rgba_arr

#Convert rgba array to rgb array
def rgba_to_rgb(rgba_arr, bg=[1.0, 1.0, 1.0]):
    import numpy as np
    
    rgb_arr = rgba_arr[..., :-1]
    a_arr = rgba_arr[..., 3]
    #Assume either integer array with 0 to 255, or float array with 0.0 to 1.0.
    #Convert to the latter if the former.
    if rgb_arr.dtype.kind in ['i', 'u']:
        rgb_arr = rgb_arr.astype(float)
        rgb_arr = rgb_arr / 255.0
    if a_arr.dtype.kind in ['i', 'u']:
        a_arr = a_arr.astype(float)
        a_arr = a_arr / 255.0
    
    rgb_arr[..., 0] = (1.0 - a_arr) * bg[0] + (rgb_arr[..., 0] * a_arr)
    rgb_arr[..., 1] = (1.0 - a_arr) * bg[1] + (rgb_arr[..., 1] * a_arr)
    rgb_arr[..., 2] = (1.0 - a_arr) * bg[2] + (rgb_arr[..., 2] * a_arr)
    
    return rgb_arr

#Overlay one rgba array on another
def overlay(top_rgba, bottom_rgba):
    import numpy as np
    
    if top_rgba.dtype.kind in ['i', 'u']:
        top_rgba = top_rgba.astype(float)
        top_rgba = top_rgba / 255.0

    if bottom_rgba.dtype.kind in ['i', 'u']:
        bottom_rgba = bottom_rgba.astype(float)
        bottom_rgba = bottom_rgba / 255.0
    top_rgb = top_rgba[..., :-1]
    top_a = top_rgba[..., 3]
    
    overlay_arr = np.ones(np.shape(top_rgba))
    #http://stackoverflow.com/questions/2049230/convert-rgba-color-to-rgb
    overlay_arr[..., 0] = (1.0 - top_a) * bottom_rgba[..., 0] + (top_rgb[..., 0] * top_a)
    overlay_arr[..., 1] = (1.0 - top_a) * bottom_rgba[..., 1] + (top_rgb[..., 1] * top_a)
    overlay_arr[..., 2] = (1.0 - top_a) * bottom_rgba[..., 2] + (top_rgb[..., 2] * top_a)
    #print np.shape(overlay_arr)
    return rgba_to_rgb(overlay_arr)

#Generate string of random characters
def string_gen(str_len=5):
    import random
    import string
        
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(str_len))
