import os
import numpy as np
from PIL import Image

import util.vigenere
from util.lsb_helper import LSBHelper, i2b, b2i


class StegoImage:
    def __init__(self, image_path : str):
        self.image_path = image_path
        self.image = Image.open(image_path)
        _, _, self.channel_count = np.array(self.image).shape
        self.stego_image = None
        self.extracted_data = None
        self.extracted_filename = None
        # max capacity when RGB channel used
        self.max_capacity = self.image.size[0] * self.image.size[1] * 3

    def insert_data(self, in_file_path : str, is_encrypted : bool, is_sequential : bool, key : str = '1337'):
        # open file and check the size
        with open(in_file_path, 'rb') as f:
            in_file = f.read()
        in_filename = os.path.split(in_file_path)[1]
        # encrypt file (optional)
        if is_encrypted:
            in_file = vigenere.encrypt(key, in_file)
        # insert data in LSB
        data_container = []
        for t in self.image.getdata():
            data_container.extend(t)
        data_container = LSBHelper.insert_data_as_lsb(data_container,
                            is_sequential, in_filename, in_file, key)
        # group data as tuple of 3 and feed the list to putdata method
        self.stego_image = self.image.copy()
        self.stego_image.putdata(list(zip(*([iter(data_container)] * self.channel_count))))

    def extract_data(self, is_encrypted : bool, key : str = '1337'):
        # extract data from lsb
        data_container = []
        for t in self.image.getdata():
            data_container.extend(t)
        extract_result = LSBHelper.extract_data_from_lsb(data_container, key)
        self.extracted_filename, self.extracted_data = extract_result
        # decrypt file (optional)
        if is_encrypted:
            self.extracted_filename = vigenere.decrypt(key, self.extracted_filename)

    def save_stego_image(self, out_path):
        if self.stego_image is None:
            raise Exception('Stego image not exists!')
        self.stego_image.save(out_path)

    def save_extracted_data(self, out_path = None):
        if self.extracted_data is None:
            raise Exception('Extracted data not exists!')
        out_path = out_path or self.extracted_filename or 'default.txt'
        with open(out_path, 'wb') as f:
            f.write(self.extracted_data)


# if __name__ == '__main__':
#     ic = StegoImage('example/raw.png')
#     ic.insert_data('main.py', False, 'someseed')
#     ic.image.save('test.png')
#     oc = StegoImage('test.png')
#     f = oc.extract_data('test.txt', 'someseed')
#     print(f)
#     exit()
