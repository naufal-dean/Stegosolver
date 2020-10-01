import wave
import os
import mmap

# todo
# 1. Implemen panjang data int = 24 bytes = 24*8 bit
#    alasan : file ttp nulis \x00 gt jd gbs dibuka
# 2. Random hide & extract

class StegoAudio:
    def __init__(self, key, audio_path):
        self.key = key
        # read audio file
        self.audio = wave.open(audio_path, mode='rb')
        self.audio_filename = os.path.split(audio_path)[1]
        # get audio frames
        self.audio_frames = bytearray(list(self.audio.readframes(self.audio.getnframes())))

    def is_enough_frames(self):
        # yang disisipkan pada frame:
        # 1. file dlm bit
        # 2. nama file dlm bit + 8 bit (menandakan panjang nama file dlm string)
        # 3. 1 bit untuk menandakan dia acak atau sekuensial
        return len(self.audio_frames) >= (len(self.data) + len(self.filename)) * 8 + 9

    def sequential_hide(self):
        # hide filename length indeks 1 - 8
        filename_len = len(self.filename)
        for i, bit in enumerate(bin(filename_len).lstrip('0b').rjust(8,'0')):
            self.audio_frames[i+1] = self.audio_frames[i+1] & 254 | int(bit)

        # hide filename indeks 9 dst
        filename_bit = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8,'0') for i in self.filename])))
        for i, bit in enumerate(filename_bit):
            self.audio_frames[i+9] = self.audio_frames[i+9] & 254 | int(bit)

        # hide file
        s = len(filename_bit) + 9
        bit_data = list(map(int, ''.join([bin(i).lstrip('0b').rjust(8,'0') for i in self.data])))
        for i, bit in enumerate(bit_data):
            self.audio_frames[i+s] = self.audio_frames[i+s] & 254 | int(bit)
        
        # tambal sama 0
        frames_cnt = len(self.audio_frames)
        data_cnt = len(bit_data)
        if frames_cnt > data_cnt:
            print("yey")
            for i in range(data_cnt+len(filename_bit)+9, frames_cnt):
                self.audio_frames[i] = self.audio_frames[i] & 254
        
    # def random_hide():
    #     # generate random 

    def hide_lsb(self, file_path, is_sequential):
        # get file name & convert to list of bit
        self.filename = os.path.split(file_path)[1]
        # get file & convert file to list of bit
        with open(file_path, 'r+b') as f:
            mem = mmap.mmap(f.fileno(), 0)
            self.data = bytearray(mem)
        sequential = is_sequential

        # cek muat atau ndak
        if self.is_enough_frames():
            # hide sequential
            self.audio_frames[0] = self.audio_frames[0] & 254 | sequential
            if sequential:
                self.sequential_hide()
        else:
            print("gak muat")
    
    def sequential_extract(self):
        # get filename length
        filename_len = 0
        for i in range(1, 9):
            filename_len |= self.bit_extracted[i] << (8-i)

        # get filename
        # panjang bitnya = panjang filename * 8 (duh)
        self.filename = ''.join(chr(int(''.join(map(str,self.bit_extracted[i:i+8])),2)) for i in range(9,9+filename_len*8,8))
        
        # get data
        frames_cnt = len(self.audio_frames)
        self.data = bytearray(0)
        str_data = ''.join(chr(int(''.join(map(str,self.bit_extracted[i:i+8])),2)) for i in range(9+filename_len*8,frames_cnt,8))
        print(str_data)
        self.data[0:] = bytes(str_data, encoding='utf-8')
    
    def extract_lsb(self):
        self.bit_extracted = [self.audio_frames[i] & 1 for i in range(len(self.audio_frames))]
        
        # cek sekuensial
        if self.bit_extracted[0]:
            self.sequential_extract()

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

if __name__ == '__main__':
    key = "STEGANO"
    path = "test.wav"
    hide = StegoAudio(key, path)
    hide.hide_lsb("../plan.txt", 1)
    hide.save_stego_audio("save.wav")

    extractor = StegoAudio(key, "save.wav")
    extractor.extract_lsb()
    extractor.save_extracted_file("lala.txt")
