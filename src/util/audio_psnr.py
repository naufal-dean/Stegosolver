from scipy.io import wavfile
import numpy as np
from math import log10, sqrt 

def signaltonoise(a, axis=0, ddof=0):
    a = np.asanyarray(a)
    m = a.mean(axis)
    sd = a.std(axis=axis, ddof=ddof)
    return np.where(sd == 0, 0, m/sd)

def psnr(path1, path2):
    amp1 = wavfile.read(path1)[1]
    amp2 = wavfile.read(path2)[1]
    single1 = amp1
    single2 = amp2
    try:
        single1 = np.sum(amp1, axis=1)
        single2 = np.sum(amp2, axis=1)
    except:
        pass
    norm1 = single1 / (max(np.amax(single1), -1 * np.amin(single1)))
    norm2 = single2 / (max(np.amax(single2), -1 * np.amin(single2)))
    # psnr = 10 * 
    snr1 = signaltonoise(norm1)
    snr2 = signaltonoise(norm2)

    psnr = 10 * log10((snr2**2)/(snr2**2+snr1**2-2*snr1*snr2))
    print(psnr)
    return psnr