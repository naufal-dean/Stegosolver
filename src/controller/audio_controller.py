import wave
import os
import mmap
from util.lsb_helper import LSBHelper, i2b, b2i


class StegoAudio:
    def __init__(self, key, audio_path):
        self.key = key
        # read audio file
        self.audio = wave.open(audio_path, mode='rb')
        self.audio_filename = os.path.split(audio_path)[1]
        # get audio frames
        self.audio_frames = bytearray(list(self.audio.readframes(self.audio.getnframes())))

    def insert_data(self, file_path, is_sequential, key = "1337"):
        # get file name & convert to list of bit
        self.filename = os.path.split(file_path)[1]
        # get file & convert file to list of bit
        with open(file_path, 'r+b') as f:
            mem = mmap.mmap(f.fileno(), 0)
            self.data = bytearray(mem)
        self.audio_frames = LSBHelper.insert_data_as_lsb(self.audio_frames,
                            is_sequential, self.filename, self.data, key)

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


