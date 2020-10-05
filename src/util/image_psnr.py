import math
import numpy as np


def rms(arr1 : np.ndarray, arr2 : np.ndarray):
    assert arr1.shape == arr2.shape
    diff = (arr1 - arr2) ** 2
    ret = math.sqrt((1 / arr1.shape[0]) * sum(diff))
    return ret


def psnr(imgdata1 : np.ndarray, imgdata2 : np.ndarray):
    assert imgdata1.shape == imgdata2.shape
    arr1 = np.append(imgdata1, np.array([], dtype=np.uint8))
    arr2 = np.append(imgdata2, np.array([], dtype=np.uint8))
    rms_val = max(rms(arr1, arr2), 0.00255)  # assert no division by zero, max psnr = 100
    return 20 * math.log10(255 / rms_val)
