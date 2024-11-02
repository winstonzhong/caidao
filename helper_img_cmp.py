'''
Created on 2024 Nov 2

@author: Winston
'''


import cv2

from skimage.metrics import structural_similarity as ssim

def compare_images_ssim(image1, image2):
    if image1.shape == image2.shape:
        gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
    
        ssim_value = ssim(gray1, gray2, data_range=gray2.max() - gray2.min())
        return ssim_value
    return -1