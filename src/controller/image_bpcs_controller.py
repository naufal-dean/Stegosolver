import itertools
import math
import numpy as np
import os
from PIL import Image


PLANE_HEIGHT = 8
PLANE_WIDTH = 8
MAX_COLOR_CHANGE_ON_8_8_PLANE = 112


class StegoImageBPCS:
    def __init__(self, image_path, threshold = 0.3):
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.threshold = threshold
        self.__gen_wc_plane()
        self.stego_image = None
        self.extracted_data = None
        self.extracted_filename = None

    def __gen_wc_plane(self):
        temp = []
        for i in range(PLANE_HEIGHT):
            temp.append([j % 2 for j in range(i % 2, PLANE_WIDTH + (i % 2))])
        self.wc_plane = np.array(temp)

    def complexity(self, bit_plane : np.ndarray):
        color_change = 0
        for r in bit_plane:
            color_change += sum([r[i] ^ r[i+1] for i in range(bit_plane.shape[1] - 1)])
        for c in bit_plane.transpose():
            color_change += sum([c[i] ^ c[i+1] for i in range(bit_plane.shape[0] - 1)])
        return color_change / MAX_COLOR_CHANGE_ON_8_8_PLANE

    def is_noise_like(self, bit_plane : np.ndarray):
        return self.complexity(bit_plane) >= self.threshold

    def pbc2cgc(self, bit_plane : np.ndarray):
        if bit_plane.shape[1] == 0:
            return np.array([[] for i in range(bit_plane.shape[0])])
        # if column not empty
        pbc_plane_t = [bit_plane[:,0]]
        for i in range(bit_plane.shape[1] - 1):
            pbc_plane_t.append([b1 ^ b2 for b1, b2 in zip(bit_plane[:,i], bit_plane[:,i+1])])
        return np.array(pbc_plane_t).transpose()

    def cgc2pbc(self, bit_plane : np.ndarray):
        if bit_plane.shape[1] == 0:
            return np.array([[] for i in range(bit_plane.shape[0])])
        # if column not empty
        pbc_plane_t = [bit_plane[:,0]]
        for i in range(bit_plane.shape[1] - 1):
            pbc_plane_t.append([b ^ g for b, g in zip(pbc_plane_t[-1], bit_plane[:,i+1])])
        return np.array(pbc_plane_t).transpose()

    def conjugate(self, bit_plane : np.ndarray):
        return bit_plane ^ self.wc_plane

    def pad_image(self, image_data : np.ndarray):
        pad_height = PLANE_HEIGHT - (image_data.shape[0] % PLANE_HEIGHT)
        pad_width = PLANE_HEIGHT - (image_data.shape[1] % PLANE_WIDTH)
        im_height, im_width, channel_count = image_data.shape
        # row
        row_pad = []
        for i in range(pad_height):
            row_pad.append([([0] * channel_count) for j in range(im_width)])
        row_pad = np.array(row_pad)
        # column
        col_pad = []
        for j in range(im_height + pad_height):
            col_pad.append([([0] * channel_count) for j in range(pad_width)])
        col_pad = np.array(col_pad)
        # pad image data
        padded_image_data = np.empty((im_height + pad_height, im_width + pad_width, channel_count),
                                     dtype=np.uint8)
        padded_image_data[:im_height, :im_width] = image_data
        padded_image_data[im_height:, :im_width] = row_pad
        padded_image_data[:, im_width:] = col_pad
        # return
        return padded_image_data

    def image_data_to_blocks(self, image_data : np.ndarray):
        # image_data is the data after padded
        im_height, im_width, channel_count = image_data.shape
        assert im_height % PLANE_HEIGHT == 0
        assert im_width % PLANE_WIDTH == 0
        # separate image_data to phxpw blocks
        image_blocks = []
        for ri in range(0, im_height, PLANE_HEIGHT):
            temp = []
            for ci in range(0, im_width, PLANE_WIDTH):
                temp.append(image_data[ri:ri+PLANE_HEIGHT, ci:ci+PLANE_WIDTH])
            image_blocks.append(temp)
        # return
        return np.array(image_blocks)

    def blocks_to_image_data(self, blocks : np.ndarray, image_shape):
        # image_shape is the shape after padded
        im_height, im_width, channel_count = image_shape
        assert im_height % PLANE_HEIGHT == 0
        assert im_width % PLANE_WIDTH == 0
        # join blocks
        image_data = np.empty((im_height, im_width, channel_count), dtype=np.uint8)
        for i in range(blocks.shape[0]):
            for j in range(blocks.shape[1]):
                ri, ci = i * 8, j * 8
                image_data[ri:ri+PLANE_HEIGHT, ci:ci+PLANE_WIDTH] = blocks[i][j]
        # return
        return image_data

    def flatten_blocks(self, blocks : np.ndarray):
        # unpack shape
        bl_height, bl_width, pl_height, pl_width, channel_count = blocks.shape
        # craft empty flattened_blocks
        flattened_blocks_shape = (bl_height, bl_width, channel_count, pl_height, pl_width)
        flattened_blocks = np.empty(flattened_blocks_shape, dtype=np.uint8)
        # assign value
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    flattened_blocks[i][j][k][:,:] = blocks[i][j][:,:,k]
        # return
        return flattened_blocks

    def unflatten_blocks(self, flattened_blocks : np.ndarray):
        # unpack shape
        bl_height, bl_width, channel_count, pl_height, pl_width = flattened_blocks.shape
        # craft empty unflattened_blocks
        unflattened_blocks_shape = (bl_height, bl_width, pl_height, pl_width, channel_count)
        unflattened_blocks = np.empty(unflattened_blocks_shape, dtype=np.uint8)
        # assign value
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    unflattened_blocks[i][j][:,:,k] = flattened_blocks[i][j][k]
        # return
        return unflattened_blocks

    def get_nth_bit_plane_from_block(self, block : np.ndarray, n : int):
        # plane 0: MSB, plane 8: LSB
        shift = 7 - n
        return ((block >> shift) & 1)

    def get_all_bit_plane_from_block(self, block : np.ndarray):
        # return numpy array containing bit plane from 0th to 7th
        return np.array([self.get_nth_bit_plane_from_block(block, n) for n in range(8)])

    def all_bit_plane_to_block(self, bit_planes : np.ndarray):
        assert len(bit_planes) == 8
        _, pl_height, pl_width = bit_planes.shape
        block_shape = (pl_height, pl_width)
        block = np.zeros(block_shape, dtype=np.uint8)
        for i in range(len(bit_planes)):
            block <<= 1
            block += bit_planes[i]
        return block

    def insert_data_to_bit_plane(self, f_blocks : np.ndarray, is_sequential : bool,
                                 message : np.ndarray, conjugate_map_len : int):
        bl_height, bl_width, channel_count, pl_height, pl_width = f_blocks.shape
        # copy to new array
        new_f_blocks = np.copy(f_blocks)
        # skip reserved header and conjugate map blocks
        skip_counter = math.ceil((conjugate_map_len + 1) / 8)
        for si in range(bl_height):
            for sj in range(bl_width):
                for sk in range(channel_count):
                    if skip_counter == 0: break
                    skip_counter -= 1
                if skip_counter == 0: break
            if skip_counter == 0: break
        sj += 1
        sk = 0
        print(f'started at = {si, sj, sk}')
        if skip_counter != 0:
            raise Exception('Not enough noise-like region to store data')
        # insert message to noise-like region
        conjugate_flag = []
        inserted_message_count = 0
        for i in range(si, bl_height):
            for j in range(sj, bl_width):
                for k in range(sk, channel_count):
                    # load bit planes from block
                    bps = self.get_all_bit_plane_from_block(f_blocks[i][j][k])
                    new_bps = np.copy(bps)
                    changed = False
                    # check bit planes
                    for l, bp in enumerate(bps):
                        temp_cgc_bp = self.pbc2cgc(bp)
                        if not self.is_noise_like(temp_cgc_bp):
                            continue
                        message_bit_plane = message[inserted_message_count]
                        if not self.is_noise_like(message_bit_plane):
                            # print('conjugate')
                            message_bit_plane = self.conjugate(message_bit_plane)
                            conjugate_flag.append(1)
                        else:
                            conjugate_flag.append(0)
                        # print(f'inserted in {(i, j, k, l)}')
                        inserted_message_count += 1
                        # convert message to pbc system
                        message_bit_plane = self.cgc2pbc(message_bit_plane)
                        # insert message to bit plane
                        new_bps[l] = message_bit_plane
                        changed = True
                        # if all message inserted, break and check if any changes happened
                        if inserted_message_count == message.shape[0]:
                            break
                    # check if any changes happened
                    if changed:
                        # insert bit planes to block
                        new_f_blocks[i][j][k] = self.all_bit_plane_to_block(new_bps)
                        # if all message inserted return
                        if inserted_message_count == message.shape[0]:
                            return new_f_blocks, conjugate_flag
        # failed to insert all message
        raise Exception('Not enough noise-like region to store data')

    def insert_header_conj_map_to_bit_plane(self, f_blocks : np.ndarray,
                                            header : np.ndarray, conj_map : np.ndarray):
        bl_height, bl_width, channel_count, pl_height, pl_width = f_blocks.shape
        new_f_blocks = np.copy(f_blocks)
        joined = np.array(list(itertools.chain(iter(header), iter(conj_map))))
        counter = 0
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    # load bit planes from block
                    bps = self.get_all_bit_plane_from_block(new_f_blocks[i][j][k])
                    # check bit planes
                    for l, bp in enumerate(bps):
                        # insert message to bit plane
                        bps[l] = self.cgc2pbc(joined[counter])
                        counter += 1
                        # if all message inserted, break
                        if counter == joined.shape[0]:
                            break
                    # insert bit planes to block
                    new_f_blocks[i][j][k] = self.all_bit_plane_to_block(bps)
                    # if all message inserted return
                    if counter == joined.shape[0]:
                        return new_f_blocks
        raise Exception('Error happened when inserting header and conj map')

    def insert_data(self, in_file_path : str, is_sequential : bool):
        # open file
        with open(in_file_path, 'rb') as f:
            contents = f.read()
        in_filename = os.path.split(in_file_path)[1]
        # init
        image_data = np.array(self.image)
        image_data = self.pad_image(image_data)
        im_height, im_width, channel_count = image_data.shape
        # get image blocks
        blocks = self.image_data_to_blocks(image_data)
        f_blocks = self.flatten_blocks(blocks)
        # pack message
        message = MessagePacker.pack_message(in_filename, contents)
        conjugate_map_len = math.ceil(len(message) / (PLANE_HEIGHT * PLANE_WIDTH))
        message_len = len(message)
        # insert data to bit plane
        new_f_blocks, conjugate_flag = self.insert_data_to_bit_plane(f_blocks, is_sequential, message, conjugate_map_len)
        # print(f'conjugate_flag = {conjugate_flag}')
        # insert header and conjugate map to bit plane
        header = MessagePacker.pack_header(conjugate_map_len, message_len)
        conj_map = MessagePacker.pack_conj_map(conjugate_flag)
        new_f_blocks = self.insert_header_conj_map_to_bit_plane(new_f_blocks, header, conj_map)
        # construct stego_image
        new_uf_blocks = self.unflatten_blocks(new_f_blocks)
        new_image_data = self.blocks_to_image_data(new_uf_blocks, image_data.shape)
        self.stego_image = Image.fromarray(new_image_data)

    def extract_data_from_bit_plane(self, f_blocks : np.ndarray, conjugate_map_len : int,
                                    message_len : int, conjugate_flag : list):
        bl_height, bl_width, channel_count, pl_height, pl_width = f_blocks.shape
        # skip reserved header and conjugate map blocks
        skip_counter = math.ceil((conjugate_map_len + 1) / 8)
        for si in range(bl_height):
            for sj in range(bl_width):
                for sk in range(channel_count):
                    if skip_counter == 0: break
                    skip_counter -= 1
                if skip_counter == 0: break
            if skip_counter == 0: break
        sj += 1
        sk = 0
        print(f'started at = {si, sj, sk}')
        if skip_counter != 0:
            raise Exception('Image ended when searching hidden message')
        # extract message
        message = []
        extracted_message_count = 0
        conjugate_iter = iter(conjugate_flag)
        for i in range(si, bl_height):
            for j in range(sj, bl_width):
                for k in range(sk, channel_count):
                    bps = self.get_all_bit_plane_from_block(f_blocks[i][j][k])
                    for l, bp in enumerate(bps):
                        # read candidate
                        cand_message_bit_plane = self.pbc2cgc(bp)
                        # check if noise like
                        if not self.is_noise_like(cand_message_bit_plane):
                            continue
                        # check if conjugate
                        if next(conjugate_iter):
                            # print('conjugate')
                            cand_message_bit_plane = self.conjugate(cand_message_bit_plane)
                        # store message bit plane
                        message.append(cand_message_bit_plane)
                        # print(f'extracted from {(i, j, k, l)}')
                        extracted_message_count += 1
                        # if all message inserted return
                        if extracted_message_count == message_len:
                            return MessagePacker.unpack_message(np.array(message))
        # failed to retrieve all message
        raise Exception('Image ended when searching hidden message')

    def extract_header_conj_map_from_bit_plane(self, f_blocks : np.ndarray):
        bl_height, bl_width, channel_count, pl_height, pl_width = f_blocks.shape
        bps = self.get_all_bit_plane_from_block(f_blocks[0][0][0])
        conjugate_map_len, message_len = MessagePacker.unpack_header(self.pbc2cgc(bps[0]))
        # extract conj_map
        conj_map = []
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    bps = self.get_all_bit_plane_from_block(f_blocks[i][j][k])
                    bps_cgc = [self.pbc2cgc(bp) for bp in bps]
                    conj_map.extend(bps_cgc)
                    if len(conj_map) > conjugate_map_len + 1:
                        conjugate_flag = MessagePacker.unpack_conj_map(np.array(conj_map[1:1+conjugate_map_len]))
                        return conjugate_map_len, message_len, conjugate_flag
        raise Exception('Error happened when extracting header and conj map')

    def extract_data(self):
        image_data = np.array(self.image)
        image_data = self.pad_image(image_data)
        im_height, im_width, channel_count = image_data.shape
        # get image blocks
        blocks = self.image_data_to_blocks(image_data)
        f_blocks = self.flatten_blocks(blocks)
        # extract header and conj_map
        temp = self.extract_header_conj_map_from_bit_plane(f_blocks)
        conjugate_map_len, message_len, conjugate_flag = temp
        # print(f'conjugate_flag = {conjugate_flag}')
        # extract data from bit plane
        extract_result = self.extract_data_from_bit_plane(f_blocks, conjugate_map_len, message_len, conjugate_flag)
        self.extracted_filename, self.extracted_data = extract_result
        print(self.extracted_filename)
        # print(self.extracted_data)

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


class MessagePacker:
    @staticmethod
    def pad(payload : bytes):
        pad_len = 8 - (len(payload) % 8)
        pad = chr(pad_len).encode('latin-1') * pad_len
        return payload + pad

    @staticmethod
    def unpad(padded_payload : bytes):
        pad_len = padded_payload[-1]
        return padded_payload[:-pad_len]

    @staticmethod
    def pack_header(conjugate_map_len : int, message_len : int):
        assert conjugate_map_len < 2 ** 32
        assert message_len < 2 ** 32
        block_size = PLANE_HEIGHT * PLANE_WIDTH
        bit_conjugate_map_len = bin(conjugate_map_len).lstrip('0b').rjust(32, '0')
        bit_message_len = bin(message_len).lstrip('0b').rjust(32, '0')
        bit_header = list(map(int, bit_conjugate_map_len + bit_message_len))
        header = []
        for i in range(0, len(bit_header), block_size):
            temp = bit_header[i:i+block_size]
            header.append([temp[j:j+PLANE_HEIGHT] for j in range(0, len(temp), PLANE_HEIGHT)])
        return np.array(header)

    @staticmethod
    def unpack_header(header : np.ndarray):
        bit_string = ''.join(list(map(str, np.append(header, np.array([], dtype=np.uint8)))))
        conjugate_map_len = int(bit_string[:32], 2)
        message_len = int(bit_string[32:], 2)
        return conjugate_map_len, message_len

    @staticmethod
    def pack_conj_map(conjugate_flag : list):
        block_size = PLANE_HEIGHT * PLANE_WIDTH
        *lcf, = conjugate_flag
        if len(lcf) % block_size != 0:
            lcf.extend([0 for i in range(block_size - len(lcf) % block_size)])
        conj_map = []
        for i in range(0, len(lcf), block_size):
            temp = lcf[i:i+block_size]
            conj_map.append([temp[j:j+PLANE_HEIGHT] for j in range(0, len(temp), PLANE_HEIGHT)])
        return np.array(conj_map)

    @staticmethod
    def unpack_conj_map(conj_map : np.ndarray):
        return np.append(conj_map, np.array([], dtype=np.uint8)).tolist()

    @staticmethod
    def pack_message(filename : str, contents : bytes):
        assert len(filename) < 256
        block_size = PLANE_HEIGHT * PLANE_WIDTH
        filename_len = len(filename).to_bytes(1, byteorder='big')
        filename = filename.encode('latin-1')
        payload = MessagePacker.pad(filename_len + filename + contents)
        bit_payload = list(map(int, ''.join([bin(i).lstrip('0b').rjust(8,'0') for i in payload])))
        # pack message
        message = []
        for i in range(0, len(bit_payload), block_size):
            temp = bit_payload[i:i+block_size]
            message.append([temp[j:j+PLANE_HEIGHT] for j in range(0, len(temp), PLANE_HEIGHT)])
        return np.array(message)

        i2b = lambda x, n: x.to_bytes(n, byteorder='big')
        b2i = lambda x: int.from_bytes(x, byteorder='big')

    @staticmethod
    def unpack_message(message : np.ndarray):
        bit_string = ''.join(list(map(str, np.append(message, np.array([], dtype=np.uint8)))))
        payload = int(bit_string, 2).to_bytes(len(message) * 8, byteorder='big')
        payload = MessagePacker.unpad(payload)
        # parse filename and contents
        filename_len = int.from_bytes(payload[0:1], byteorder='big')
        filename = payload[1:1+filename_len].decode('latin-1')
        contents = payload[1+filename_len:]
        return filename, contents


if __name__ == '__main__':
    import time

    st = time.time()
    s = StegoImageBPCS('../example/raw.png')
    s.insert_data('test.jpg', True)
    s.save_stego_image('out.png')
    del s
    ed = time.time()
    print(f'time = {ed - st}')
    print()

    st = time.time()
    s2 = StegoImageBPCS('out.png')
    s2.extract_data()
    s2.save_extracted_data('test_out.jpg')
    ed = time.time()
    print(f'time = {ed - st}')
