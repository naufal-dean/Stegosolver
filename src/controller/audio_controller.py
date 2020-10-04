import wave
import os
import mmap
from util.lsb_helper import LSBHelper, i2b, b2i
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

class StegoAudio:
    def __init__(self, key, audio_path):
        self.key = key
        # read audio file
        self.audio = wave.open(audio_path, mode='rb')
        self.audio_filename = os.path.split(audio_path)[1]
        # get audio frames
        self.audio_frames = bytearray(list(self.audio.readframes(self.audio.getnframes())))

    def insert_data(self, file_path, is_sequential):
        # get file name & convert to list of bit
        self.filename = os.path.split(file_path)[1]
        # get file & convert file to list of bit
        with open(file_path, 'r+b') as f:
            mem = mmap.mmap(f.fileno(), 0)
            self.data = bytearray(mem)
        self.audio_frames = LSBHelper.insert_data_as_lsb(self.audio_frames,
                            is_sequential, self.filename, self.data)

    def extract_data(self):
        
        self.filename, self.data = LSBHelper.extract_data_from_lsb(self.audio_frames)

    def save_stego_audio(self, dest_filename = None):
        # write audio
        if dest_filename is None:
            fin_audio = wave.open(self.audio_filename, mode='wb')
        else:
            fin_audio = wave.open(dest_filename, mode='wb')
        
        # simpan audio
        fin_audio.setparams(self.audio.getparams())
        fin_audio.writeframes(bytes(self.audio_frames))
        fin_audio.close()
        self.audio.close()
    
    def save_extracted_file(self, dest_filename = None):
        # write file
        if dest_filename is None:
            extracted_file = open(self.filename, 'wb')
        else:
            extracted_file = open(dest_filename, 'wb')
        
        # simpan file
        extracted_file.write(self.data)
        extracted_file.close()
        self.audio.close()


