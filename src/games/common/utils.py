import numpy as np
import imageio  
import os

def merge_image_files(image_files, output_file):

    images = [imageio.imread(f) for f in image_files]
    
    output_image = np.concatenate(images, axis=1)
    
    imageio.imsave(output_file, output_image)

def generate_temp_dir(temp_base):
    """
    generate a new temp directory in the base temp directory folder for this game
    
    This function will try to make a temp directory at os.path.join(temp_base, 'temp_0'),
    if that temp directory already exists it will try os.path.join(temp_base, 'temp_1')
    and so on until it finds an unused temp directory name
    
    It will then return the temp directory name after it makes the temp directory
    """

    index = 0
    while os.path.isdir(os.path.join(temp_base, f"temp_{index}")):
        index+=1
        
    temp_dir = os.path.join(temp_base, f"temp_{index}")
    os.mkdir(temp_dir)
    
    return temp_dir   