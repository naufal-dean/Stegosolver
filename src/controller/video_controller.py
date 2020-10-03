from PIL import Image
import cv2
import math
import numpy as np
import os
import subprocess

class StegoVideo:
    def __init__(self, mode, key, in_path, out_path, data_path, frame_seq, pixel_seq):
        self.mode = mode
        self.key = key
        self.in_path = in_path
        self.out_path = out_path
        self.data_path = data_path
        self.frame_seq = frame_seq
        self.pixel_seq = pixel_seq

        self.TEMP_FOLDER = './temp'
        self.nframes = 0
        self.framesize = 0
        self.extract_frames()

    ### Extended Vigenere cipher ###
    def encrypt_data(self):
        # Open file to get byte data
        in_file = open(self.data_path, 'rb')
        data = in_file.read()
        in_file.close()

        enc_bytes = bytearray()
        for i in range(len(data)):
            proc_byte = (data[i] + ord(self.key[i % len(self.key)])) % 256
            enc_bytes.append(proc_byte)
        
        return enc_bytes

    def decrypt_data(self, data):
        dec_bytes = bytearray()
        for i in range(len(data)):
            proc_byte = (data[i] - ord(self.key[i % len(self.key)])) % 256
            dec_bytes.append(proc_byte)

        return dec_bytes


    ### ffmpeg utils ##
    def ffmpeg_extract_audio(self, vidname):
        subprocess.call(["ffmpeg", "-i", vidname, "-q:a", "0", "-map", "a", "temp/audio.mp3", "-y"], stdout=open(os.devnull, "w"), stderr=STDOUT)

    def ffmpeg_frames_to_video(self):
        subprocess.call(["ffmpeg", "-i", "temp/%d.png" , "-vcodec", "png", "temp/temp.avi", "-y"], stdout=open(os.devnull, "w"), stderr=STDOUT)

    def ffmpeg_merge_av(self, resvidname):
        subprocess.call(["ffmpeg", "-i", "temp/temp.avi", "-i", "temp/audio.mp3", "-codec", "copy", "{}.avi".format(resvidname), "-y"],stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

    def ffmpeg_playvideo(self, vidpath):
        subprocess.call(["ffplay", vidpath], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

    ### Functions utils ###
    def is_enough(self):
        f = open(self.in_path, 'rb')
        filesize = len(f.read())
        f.close()

        return self.nframes * self.framesize >= filesize

    def get_rand_seed(self):
        temp = 0
        for i in range(len(self.key)):
            temp += ord(self.key[i])
        return temp

    def hide_lsb(self, data):
        size = math.ceil(len(data)/self.framesize)
        if not self.frame_seq:
            np.random.seed(self.get_rand_seed())
            rand_arr = np.random.randint(self.nframes, size=size)

            for fr in rand_arr:
                # hide lsb in there

        else:
            for i in range(size):
                # hide lsb in there

        
    # def extract_lsb(self):
    #     # Extract lsb

    def extract_frames(self):
        # Init temp folder for storing frames
        captures = cv2.VideoCapture(self.in_path)
        it = 0

        while True:
            success, image = captures.read()

            # If all frames are captured
            if not success:
                break

            # Save all frames to temporary folder
            cv2.imwrite(os.path.join(self.TEMP_FOLDER, "{:d}.png".format(it)), image)
            it += 1
            self.nframes += 1
        
        # Save the size, sample from first frame
        frame = Image.open('{}/1.png'.format(self.TEMP_FOLDER))
        width, height = frame.size
        self.framesize = width * height

    def run():
        if not self.is_enough():
            print("NOT ENOUGH FILESIZE")
            return
        


        

if __name__ == '__main__':
    # runner = StegoVideo()
    # runner.run()