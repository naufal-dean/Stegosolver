import cv2
import numpy as np
import os
import subprocess

### ffmpeg utils ##

def ffmpeg_extract_audio(vidname):
    subprocess.call(["ffmpeg", "-i", vidname, "-q:a", "0", "-map", "a", "temp/audio.mp3", "-y"], stdout=open(os.devnull, "w"), stderr=STDOUT)

def ffmpeg_frames_to_video():
    subprocess.call(["ffmpeg", "-i", "temp/%d.png" , "-vcodec", "png", "temp/temp.avi", "-y"], stdout=open(os.devnull, "w"), stderr=STDOUT)

def ffmpeg_merge_av(resvidname):
    subprocess.call(["ffmpeg", "-i", "temp/temp.avi", "-i", "temp/audio.mp3", "-codec", "copy", "{}.mov".format(resvidname), "-y"],stdout=open(os.devnull, "w"), stderr=STDOUT)


### Functions utils ###

def hide_lsb():
    # Hiding lsb

def extract_lsb():
    # Extract lsb

def extract_frames(vidname):
    # Init temp folder for storing frames
    temp_folder = "./temp"

    captures = cv2.VideoCapture(vidname)
    it = 0

    while True:
        success, image = captures.read()

        # If all frames are captured
        if not success:
            break

        # Save all frames to temporary folder
        cv2.imwrite(os.path.join(temp_folder, "{:d}.png".format(it)), image)
        it += 1

def run():
    # Main func

if __name__ == '__main__':
    run()