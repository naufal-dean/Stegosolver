from PIL import Image
from util.lsb_helper import LSBHelper
from controller.image_controller import StegoImage
from os.path import isfile,join

import cv2
import glob
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
        self.ffmpeg_extract_audio()

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
    def ffmpeg_extract_audio(self):
        subprocess.call(["ffmpeg", "-i", self.in_path, "-q:a", "0", "-map", "a", "temp/audio.mp3", "-y"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

    def ffmpeg_frames_to_video(self):
        subprocess.call(["ffmpeg", "-i", "temp/%d.png" , "-vcodec", "png", "temp/temp.avi", "-y"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

    def ffmpeg_merge_av(self, resvidname):
        subprocess.call(["ffmpeg", "-i", "temp/temp.avi", "-i", "temp/audio.mp3", "-codec", "copy", resvidname, "-y"],stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

    def ffmpeg_playvideo(self, vidpath):
        subprocess.call(["ffplay", vidpath], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

    ### Functions utils ###
    def is_enough(self):
        f = open(self.in_path, 'rb')
        filesize = len(f.read())
        f.close()

        return self.nframes * (self.framesize-1) >= filesize

    def get_rand_seed(self):
        temp = 0
        for i in range(len(self.key)):
            temp += ord(self.key[i])
        return temp
    
    def set_info(self, nframes, is_fr_seq):
        fr1 = open('{}/0.png'.format(self.TEMP_FOLDER), 'rb')
        dat = list(fr1.read())
        fr1.close()

        seed = self.get_rand_seed()

        n = list(int(nframes).to_bytes(8, byteorder='big'))
        if is_fr_seq:
            n.append(1)
        else:
            n.append(0)
        
        a = open('{}/tmpin.txt'.format(self.TEMP_FOLDER), 'wb+')
        a.write(bytes(n))
        a.close()

        ihandler = StegoImage('{}/0.png'.format(self.TEMP_FOLDER))
        ihandler.insert_data('{}/tmpin.txt'.format(self.TEMP_FOLDER), True, seed)
        ihandler.image.save('{}/0.png'.format(self.TEMP_FOLDER))
    
    def get_info(self):
        seed = self.get_rand_seed()
        ihandler = StegoImage('{}/0.png'.format(self.TEMP_FOLDER))
        fname = ihandler.extract_data('{}/tmpout.txt'.format(self.TEMP_FOLDER), seed)

        f = open('{}/tmpout.txt'.format(self.TEMP_FOLDER), 'rb+')
        content = f.read()
        f.close()

        nframes = int.from_bytes(bytes(content[:8]), byteorder='big')
        is_fr_seq = content[-1]
        return nframes, is_fr_seq

    def hide_lsb(self, data):
        size = math.ceil(len(data)/self.framesize)
        part_size = math.ceil(len(data)/size)
        data_arr = [data[i:i+part_size] for i in range(0, len(data), part_size)]
        seed = self.get_rand_seed()

        self.set_info(len(data_arr), self.frame_seq)
        print(self.get_info())

        if not self.frame_seq:
            np.random.seed(seed)
            rand_arr = np.random.choice(range(1, self.nframes), size=len(data_arr), replace=False)

            it = 0
            for fr in rand_arr:
                tempdat = '{}/tempdat.txt'.format(self.TEMP_FOLDER)
                a = open(tempdat, 'wb+')
                a.write(data_arr[i])
                a.close()

                frame_file = '{}/{}.png'.format(self.TEMP_FOLDER, fr)
                imhandler = StegoImage(frame_file)
                imhandler.insert_data(tempdat, self.pixel_seq, seed)
                imhandler.image.save(frame_file)

        else:
            for i in range(len(data_arr)):
                tempdat = '{}/tempdat.txt'.format(self.TEMP_FOLDER)
                a = open(tempdat, 'wb+')
                a.write(data_arr[i])
                a.close()

                frame_file = '{}/{}.png'.format(self.TEMP_FOLDER, i+1)
                imhandler = StegoImage(frame_file)
                imhandler.insert_data(tempdat, self.pixel_seq, seed)
                imhandler.image.save(frame_file)
        
    def extract_lsb(self):
        seed = self.get_rand_seed()
        full_content = b''
        nhideframes, is_fr_seq = self.get_info()
        print(self.get_info())
        self.frame_seq = is_fr_seq

        if not self.frame_seq:
            np.random.seed(seed)
            rand_arr = np.random.choice(range(1, self.nframes), size=nhideframes, replace=False)

            for fr in rand_arr:
                tempdat = '{}/tempdat.txt'.format(self.TEMP_FOLDER)

                frame_file = '{}/{}.png'.format(self.TEMP_FOLDER, fr)
                imhandler = StegoImage(frame_file)
                fname = imhandler.extract_data(tempdat, seed)

                a = open(tempdat, 'rb+')
                content = a.read()
                a.close()

                full_content += content

        else:
            for i in range(1, nhideframes):
                tempdat = '{}/tempdat.txt'.format(self.TEMP_FOLDER)

                frame_file = '{}/{}.png'.format(self.TEMP_FOLDER, i)
                imhandler = StegoImage(frame_file)
                fname = imhandler.extract_data(tempdat, seed)

                a = open(tempdat, 'rb+')
                content = a.read()
                a.close()

                full_content += content

        return full_content

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
        frame = Image.open('{}/0.png'.format(self.TEMP_FOLDER))
        width, height = frame.size
        self.framesize = width * height

    def hide(self):
        f = open(self.data_path, 'rb')
        data = f.read()
        f.close()

        self.hide_lsb(data)
        self.ffmpeg_frames_to_video()
        self.ffmpeg_merge_av(self.out_path)

    def extract(self):
        file = self.extract_lsb()

        f = open(self.out_path, 'wb+')
        f.write(file)
        f.close()

    def run(self):
        if not self.is_enough():
            print("NOT ENOUGH FILESIZE")
            return
        if self.mode == 'hide':
            self.hide()
        elif self.mode == 'extract':
            self.extract()
        
if __name__ == '__main__':
    mode = 'extract'
    key = 'test'
    in_path = './video.avi'
    out_path = './b.txt'
    data_path = './a.txt'
    frame_seq = True
    pixel_seq = True

    runner = StegoVideo(mode, key, in_path, out_path, data_path, frame_seq, pixel_seq)
    runner.run()