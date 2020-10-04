import numpy as np
from PIL import Image


PLANE_HEIGHT = 8
PLANE_WIDTH = 8
MAX_COLOR_CHANGE_ON_8_8_PLANE = 112


class StegoImageBPCS:
    def __init__(self, image_path, threshold = 0.3):
        self.image_path = image_path
        self.image = Image.open(image_path).convert('RGB')
        self.threshold = threshold
        self.__gen_wc_plane()
        self.stego_image = None
        self.extracted_data = None

    def __gen_wc_plane(self):
        temp = []
        for i in range(PLANE_HEIGHT):
            temp.append([j % 2 for j in range(i % 2, PLANE_WIDTH + (i % 2))])
        self.wc_plane = np.array(temp)

    def complexity(self, bit_plane : np.ndarray):
        color_change = 0
        for r in bit_plane:
            color_change += sum([r[i] != r[i+1] for i in range(bit_plane.shape[1] - 1)])
        for c in bit_plane.transpose():
            color_change += sum([c[i] != c[i+1] for i in range(bit_plane.shape[0] - 1)])
        return color_change / MAX_COLOR_CHANGE_ON_8_8_PLANE

    def is_noise_like(self, bit_plane : np.ndarray):
        return self.complexity(bit_plane) >= self.threshold

    def identify_noise_like_region(self, f_blocks_bit_planes_cgc : np.ndarray):
        # True if it is noise-like region
        bl_height, bl_width, channel_count, bp_count, _, _ = f_blocks_bit_planes_cgc.shape
        complexity_map_shape = (bl_height, bl_width, channel_count, bp_count)
        complexity_map = np.empty(complexity_map_shape, dtype=bool)
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    for l in range(bp_count):
                        is_noise_like = self.complexity(f_blocks_bit_planes_cgc[i][j][k][l]) >= self.threshold
                        complexity_map[i][j][k][l] = is_noise_like
        return complexity_map

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

    def f_blocks_bit_planes_to_cgc(self, f_blocks_bit_planes_pbc : np.ndarray):
        bl_height, bl_width, channel_count, bp_count, pl_height, pl_width = f_blocks_bit_planes_pbc.shape
        f_blocks_bit_planes_cgc = np.empty(f_blocks_bit_planes_pbc.shape, dtype=np.uint8)
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    for l in range(bp_count):
                        f_blocks_bit_planes_cgc[i][j][k][l] = self.pbc2cgc(f_blocks_bit_planes_pbc[i][j][k][l])
        return f_blocks_bit_planes_cgc

    def f_blocks_bit_planes_to_pbc(self, f_blocks_bit_planes_cgc : np.ndarray):
        bl_height, bl_width, channel_count, bp_count, pl_height, pl_width = f_blocks_bit_planes_cgc.shape
        f_blocks_bit_planes_pbc = np.empty(f_blocks_bit_planes_cgc.shape, dtype=np.uint8)
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    for l in range(bp_count):
                        f_blocks_bit_planes_pbc[i][j][k][l] = self.cgc2pbc(f_blocks_bit_planes_cgc[i][j][k][l])
        return f_blocks_bit_planes_pbc

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

    def get_all_bit_plane_from_f_blocks(self, f_blocks : np.ndarray):
        bl_height, bl_width, channel_count, pl_height, pl_width = f_blocks.shape
        f_blocks_bit_planes_shape = (bl_height, bl_width, channel_count, 8, pl_height, pl_width)
        f_blocks_bit_planes = np.empty(f_blocks_bit_planes_shape, dtype=np.uint8)
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    f_blocks_bit_planes[i][j][k] = self.get_all_bit_plane_from_block(f_blocks[i][j][k])
        return f_blocks_bit_planes

    def all_bit_plane_to_block(self, bit_planes : np.ndarray):
        assert len(bit_planes) == 8
        _, pl_height, pl_width = bit_planes.shape
        block_shape = (pl_height, pl_width)
        block = np.zeros(block_shape, dtype=np.uint8)
        for i in range(len(bit_planes)):
            block <<= 1
            block += bit_planes[i]
        return block

    def f_blocks_bit_planes_to_f_blocks(self, f_blocks_bit_planes_pbc : np.ndarray):
        bl_height, bl_width, channel_count, _, pl_height, pl_width = f_blocks_bit_planes_pbc.shape
        f_blocks_shape = (bl_height, bl_width, channel_count, pl_height, pl_width)
        f_blocks = np.empty(f_blocks_shape, dtype=np.uint8)
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    f_blocks[i][j][k] = self.all_bit_plane_to_block(f_blocks_bit_planes_pbc[i][j][k])
        return f_blocks

    def insert_data_to_bit_plane(self, f_blocks_bit_planes_pbc : np.ndarray, is_sequential : bool, data : bytes):
        bl_height, bl_width, channel_count, bp_count, pl_height, pl_width = f_blocks_bit_planes_pbc.shape
        message = MessagePacker.pack_message(data)
        print(message)
        # copy to new array
        new_f_blocks_bit_planes_pbc = np.copy(f_blocks_bit_planes_pbc)
        # insert message to noise-like region
        conjugate_pos_map = []
        inserted_message_count = 0
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    for l in range(bp_count):
                        temp_cgc_bp = self.pbc2cgc(f_blocks_bit_planes_pbc[i][j][k][l])
                        if not self.is_noise_like(temp_cgc_bp):
                            continue
                        message_bit_plane = message[inserted_message_count]
                        if not self.is_noise_like(message_bit_plane):
                            print('conjugate')
                            message_bit_plane = self.conjugate(message_bit_plane)
                            conjugate_pos_map.append((i, j, k, l))
                        print(f'inserted in {(i, j, k, l)}')
                        inserted_message_count += 1
                        # convert message to pbc system
                        message_bit_plane = self.cgc2pbc(message_bit_plane)
                        # insert to bit plane
                        new_f_blocks_bit_planes_pbc[i][j][k][l] = message_bit_plane
                        # if all message inserted return
                        if inserted_message_count == message.shape[0]:
                            return new_f_blocks_bit_planes_pbc, conjugate_pos_map
        # failed to insert all message
        raise Exception('Not enough noise-like region to store data')

    def insert_data(self, data):
        image_data = np.array(self.image)
        image_data = self.pad_image(image_data)
        im_height, im_width, channel_count = image_data.shape
        # get image blocks
        blocks = self.image_data_to_blocks(image_data)
        f_blocks = self.flatten_blocks(blocks)
        # get bit planes
        f_blocks_bit_planes_pbc = self.get_all_bit_plane_from_f_blocks(f_blocks)
        # insert data to bit plane
        print('inserting data')
        new_f_blocks_bit_planes_pbc, conjugate_pos_map = self.insert_data_to_bit_plane(f_blocks_bit_planes_pbc, True, data)
        print('inserting data end')
        print(conjugate_pos_map)
        # construct stego_image
        new_f_blocks = self.f_blocks_bit_planes_to_f_blocks(new_f_blocks_bit_planes_pbc)
        new_uf_blocks = self.unflatten_blocks(new_f_blocks)
        new_image_data = self.blocks_to_image_data(new_uf_blocks, image_data.shape)
        self.stego_image = Image.fromarray(new_image_data)
        # self.stego_image.show()
        # self.test_reconstruct_img(f_blocks, image_data.shape, image_data)

    def test_reconstruct_img(self, flattened_blocks, image_data_shape, init_image_data):
        unflattened_blocks = self.unflatten_blocks(flattened_blocks)
        new_image_data = self.blocks_to_image_data(unflattened_blocks, image_data_shape)
        Image.fromarray(new_image_data).show()

    def extract_data_from_bit_plane(self, f_blocks_bit_planes_pbc : np.ndarray):
        bl_height, bl_width, channel_count, bp_count, pl_height, pl_width = f_blocks_bit_planes_pbc.shape
        # read metadata
        conjugate_pos_map = [(5, 46, 0, 4)]
        # insert message to noise-like region
        message = []
        extracted_message_count = 0
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    for l in range(bp_count):
                        # read candidate
                        cand_message_bit_plane = self.pbc2cgc(f_blocks_bit_planes_pbc[i][j][k][l])
                        # check if noise like
                        if not self.is_noise_like(cand_message_bit_plane):
                            continue
                        # check if conjugate
                        if (i, j, k, l) in conjugate_pos_map:
                            print('conjugating')
                            cand_message_bit_plane = self.conjugate(cand_message_bit_plane)
                        # store message bit plane
                        message.append(cand_message_bit_plane)
                        print(f'extracted from {(i, j, k, l)}')
                        extracted_message_count += 1
                        # if all message inserted return
                        if extracted_message_count == 2:
                            print(np.array(message))
                            return MessagePacker.unpack_message(np.array(message))
        # failed to retrieve all message
        raise Exception('Image ended when searching hidden message')

    def extract_data(self):
        image_data = np.array(self.image)
        image_data = self.pad_image(image_data)
        im_height, im_width, channel_count = image_data.shape
        # get image blocks
        blocks = self.image_data_to_blocks(image_data)
        f_blocks = self.flatten_blocks(blocks)
        # get bit planes
        f_blocks_bit_planes_pbc = self.get_all_bit_plane_from_f_blocks(f_blocks)
        # extract data from bit plane
        print('extracting data')
        self.extracted_data = self.extract_data_from_bit_plane(f_blocks_bit_planes_pbc)
        print('extracting data end')
        print(self.extracted_data)


    def save_stego_image(self, out_path = None):
        if self.stego_image is None:
            raise Exception('Stego image not exists!')
        out_path = out_path or 'defname.png'
        self.stego_image.save(out_path)

    def save_extracted_data(self, out_path = None):
        self.extracted_data = b'hehe'
        if self.extracted_data is None:
            raise Exception('Extracted data not exists!')
        out_path = out_path or 'defname.txt'
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
    def pack_message(payload : bytes):
        block_size = PLANE_HEIGHT * PLANE_WIDTH
        payload = MessagePacker.pad(payload)
        bit_payload = list(map(int, ''.join([bin(i).lstrip('0b').rjust(8,'0') for i in payload])))
        message = []
        for i in range(0, len(bit_payload), block_size):
            temp = bit_payload[i:i+block_size]
            message.append([temp[j:j+PLANE_HEIGHT] for j in range(0, len(temp), PLANE_HEIGHT)])
        return np.array(message)

    @staticmethod
    def unpack_message(message : np.ndarray):
        bit_string = ''.join(list(map(str, np.append(message, np.array([], dtype=np.ndarray)))))
        payload = int(bit_string, 2).to_bytes(len(message) * 8, byteorder='big')
        payload = MessagePacker.unpad(payload)
        return payload




if __name__ == '__main__':
    s = StegoImageBPCS('../example/raw.png')
    s.insert_data(b'hehehehe')
    s.save_stego_image('out.png')
    del s

    s2 = StegoImageBPCS('out.png')
    s2.extract_data()
