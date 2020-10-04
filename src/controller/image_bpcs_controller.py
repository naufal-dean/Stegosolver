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

    def complexity(self, plane : np.ndarray):
        color_change = 0
        for r in plane:
            color_change += sum([r[i] != r[i+1] for i in range(plane.shape[1] - 1)])
        for c in plane.transpose():
            color_change += sum([c[i] != c[i+1] for i in range(plane.shape[0] - 1)])
        return color_change / MAX_COLOR_CHANGE_ON_8_8_PLANE

    def pbc2cgc(self, plane : np.ndarray):
        if plane.shape[1] == 0:
            return np.array([[] for i in range(plane.shape[0])])
        # if column not empty
        pbc_plane_t = [plane[:,0]]
        for i in range(plane.shape[1] - 1):
            pbc_plane_t.append([b1 ^ b2 for b1, b2 in zip(plane[:,i], plane[:,i+1])])
        return np.array(pbc_plane_t).transpose()

    def cgc2pbc(self, plane : np.ndarray):
        if plane.shape[1] == 0:
            return np.array([[] for i in range(plane.shape[0])])
        # if column not empty
        pbc_plane_t = [plane[:,0]]
        for i in range(plane.shape[1] - 1):
            pbc_plane_t.append([b ^ g for b, g in zip(pbc_plane_t[-1], plane[:,i+1])])
        return np.array(pbc_plane_t).transpose()

    def conjugate(self, plane : np.ndarray):
        return plane ^ self.wc_plane

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
        bl_height, bl_width, im_height, im_width, channel_count = blocks.shape
        # craft empty flattened_blocks
        flattened_blocks_shape = (bl_height, bl_width, channel_count, im_height, im_width)
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
        bl_height, bl_width, channel_count, im_height, im_width = flattened_blocks.shape
        # craft empty unflattened_blocks
        unflattened_blocks_shape = (bl_height, bl_width, im_height, im_width, channel_count)
        unflattened_blocks = np.empty(unflattened_blocks_shape, dtype=np.uint8)
        # assign value
        for i in range(bl_height):
            for j in range(bl_width):
                for k in range(channel_count):
                    unflattened_blocks[i][j][:,:,k] = flattened_blocks[i][j][k]
        # return
        return unflattened_blocks

    def get_bit_plane_from_block(self, block : np.ndarray, plane_num : int):
        # plane 0: MSB, plane 8: LSB
        shift = 7 - plane_num
        print(((block >> shift) & 1))
        return ((block >> shift) & 1)

    def insert_data(self, data):
        image_data = np.array(self.image)[750:757,300:307]
        image_data = self.pad_image(image_data)
        im_height, im_width, channel_count = image_data.shape
        # get image blocks
        blocks = self.image_data_to_blocks(image_data)
        flattened_blocks = self.flatten_blocks(blocks)
        # get bit planes
        print(flattened_blocks[0][0][0])
        # print((flattened_blocks[0][0][0] >> 0) & 1)
        a = self.get_bit_plane_from_block(flattened_blocks[0][0][0], 0)
        print(self.complexity(a))
        a = self.get_bit_plane_from_block(flattened_blocks[0][0][0], 1)
        print(self.complexity(a))
        a = self.get_bit_plane_from_block(flattened_blocks[0][0][0], 2)
        print(self.complexity(a))
        a = self.get_bit_plane_from_block(flattened_blocks[0][0][0], 3)
        print(self.complexity(a))
        a = self.get_bit_plane_from_block(flattened_blocks[0][0][0], 4)
        print(self.complexity(a))
        a = self.get_bit_plane_from_block(flattened_blocks[0][0][0], 5)
        print(self.complexity(a))
        a = self.get_bit_plane_from_block(flattened_blocks[0][0][0], 6)
        print(self.complexity(a))
        a = self.get_bit_plane_from_block(flattened_blocks[0][0][0], 7)
        print(self.complexity(a))


        # print(self.complexity(flattened_blocks[0][0][0]))
        # print(self.complexity(flattened_blocks[0][0][1]))
        # print(self.complexity(flattened_blocks[0][0][2]))

        # self.test_reconstruct_img(flattened_blocks, image_data.shape, image_data)

    def test_reconstruct_img(self, flattened_blocks, image_data_shape, init_image_data):
        unflattened_blocks = self.unflatten_blocks(flattened_blocks)
        new_image_data = self.blocks_to_image_data(unflattened_blocks, image_data_shape)
        Image.fromarray(new_image_data).show()

    def extract_data(self):
        pass

    def save_stego_image(self, out_path = None):
        if self.stego_image is None:
            raise Exception('Stego image not exists!')
        out_path = out_path or 'defname.png'
        self.image.save(out_path)

    def save_extracted_data(self, out_path = None):
        self.extracted_data = b'hehe'
        if self.extracted_data is None:
            raise Exception('Extracted data not exists!')
        out_path = out_path or 'defname.txt'
        with open(out_path, 'wb') as f:
            f.write(self.extracted_data)


if __name__ == '__main__':
    s = StegoImageBPCS('../example/raw.png')

    s.insert_data(b'hehe')

    # a = np.array([
    #     [0,1,1,0,0,1,0,1],
    #     [0,0,1,1,0,0,1,1],
    #     [1,0,0,1,1,1,1,0],
    #     [0,0,0,0,1,1,0,0],
    #     [1,0,0,0,0,0,0,0],
    #     [1,0,1,0,0,0,0,0],
    #     [0,1,1,1,1,1,1,0],
    #     [0,1,1,0,0,1,1,0],
    # ])
    # b = a
    # b[0,0] = 99
    # print(id(a))
    # print(id(b))
    # print(a)
    # l = [99, 99]
    # a[:3,:2] = [
    #     l,
    #     [99, 99],
    #     [99, 99],
    # ]
    # print(a)
    # a[0,0] = 88
    # print(a)
    # print(l)

    #
    # print(a)
    # # print(s.complexity(a))
    # # cgc = (s.pbc2cgc(a))
    # # print(cgc)
    # # pbc = (s.cgc2pbc(cgc))
    # # print(pbc)
    # # print(a == pbc)
    # # print(s.get_wc_plane())
    # ac = (s.conjugate(a))
    # print(ac)
    # print(a ^ (ac))



    # img = Image.open('../example/raw.png').convert('RGB')
    # # img.show()
    # print(img.size)
    # imgdata = np.array(img)
    # print(imgdata.shape)
    #
    # Image.fromarray(imgdata).show()
