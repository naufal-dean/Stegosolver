import os
from PIL import Image

from util.lsb_helper import LSBHelper, i2b, b2i


class StegoImage:
    def __init__(self, image_path : str):
        self.image_path = image_path
        self.image = Image.open(image_path)
        if self.image.mode != 'RGB':
            print('Warning, image converted to RGB mode!')
            self.image = self.image.convert('RGB')
        # max capacity when RGB channel used
        self.max_capacity = self.image.size[0] * self.image.size[1] * 3

    def insert_data(self, in_file_path : str, is_sequential : bool, seed : str = '1337'):
        # open file and check the size
        with open(in_file_path, 'rb') as f:
            in_file = f.read()
        in_filename = os.path.split(in_file_path)[1]
        # insert data in LSB
        data_container = []
        for t in self.image.getdata():
            data_container.extend(t)
        data_container = LSBHelper.insert_data_as_lsb(data_container,
                            is_sequential, in_filename, in_file, seed)
        # group data as tuple of 3 and feed the list to putdata method
        self.image.putdata(list(zip(*([iter(data_container)] * 3))))

    def extract_data(self, out_file_path : str, seed : str = '1337'):
        # extract data from lsb
        data_container = []
        for t in self.image.getdata():
            data_container.extend(t)
        filename, contents = LSBHelper.extract_data_from_lsb(data_container, seed)
        # write to file
        with open(out_file_path, 'wb') as f:
            f.write(contents)
        # return
        return filename


# if __name__ == '__main__':
#     ic = StegoImage('example/raw.png')
#     ic.insert_data('main.py', False, 'someseed')
#     ic.image.save('test.png')
#     oc = StegoImage('test.png')
#     f = oc.extract_data('test.txt', 'someseed')
#     print(f)
#     exit()
