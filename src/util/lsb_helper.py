import itertools
import random

from exception import NotEnoughCapacityException


i2b = lambda x, n: x.to_bytes(n, byteorder='big')
b2i = lambda x: int.from_bytes(x, byteorder='big')


class LSBHelper:
    @staticmethod
    def get_rand_idx(idx_list : list, seed : str) -> list:
        random.seed(seed)
        idx_list_out = random.sample(idx_list, len(idx_list))
        return idx_list_out

    @staticmethod
    def seq_lsb_generator(byte_list : list):
        for b in byte_list:
            yield '1' if b & 1 else '0'

    @staticmethod
    def rand_lsb_generator(byte_list : list, seed : str):
        idx_list = LSBHelper.get_rand_idx([i for i in range(len(byte_list))], seed)
        for i in idx_list:
            yield '1' if byte_list[i] & 1 else '0'

    @staticmethod
    def insert_data_as_lsb(byte_list : list, is_sequential : bool, filename : str,
                           contents : int, seed : str = None) -> list:
        # 1 byte sequential flag, 1 byte filename len, filename, 3 byte contents len, contents
        # byte sequential flag: 255 sequential, 0 random
        sequential_flag = i2b(255, 1) if is_sequential else i2b(0, 1)
        filename_len = i2b(len(filename), 1)
        filename = filename.encode('latin-1')
        contents_len = i2b(len(contents), 3)
        payload = sequential_flag + filename_len + filename + contents_len + contents
        # length check
        if len(payload) * 8 > len(byte_list):
            raise NotEnoughCapacityException(len(payload) * 8, len(byte_list))
        # insert payload
        bit_payload = list(map(int, ''.join([bin(i).lstrip('0b').rjust(8,'0') for i in payload])))
        *byte_list_out, = byte_list
        # branching, depends on is_sequential
        if is_sequential:
            for i, p in enumerate(bit_payload):
                byte_list_out[i] = (byte_list_out[i] & ~1) | (p)
        else:
            # write until contents_len
            front = sequential_flag + filename_len + filename + contents_len
            len_bit_front = len(front) * 8
            for i in range(len_bit_front):
                byte_list_out[i] = (byte_list_out[i] & ~1) | (bit_payload[i])
            # write contents randomly (with seed)
            bit_payload = bit_payload[len_bit_front:]
            idx_list = LSBHelper.get_rand_idx([i for i in range(len_bit_front, len(byte_list))], seed)
            for i, p in zip(idx_list, bit_payload):
                byte_list_out[i] = (byte_list_out[i] & ~1) | (p)
        # return
        return byte_list_out

    @staticmethod
    def extract_data_from_lsb(byte_list : list, seed : str = None) -> (str, bytes):
        # create sequential generator
        lsb_generator = LSBHelper.seq_lsb_generator(byte_list)
        next_n_byte_lsb = lambda n: ''.join(list(itertools.islice(lsb_generator, n * 8)))
        # parse sequential_flag
        sequential_flag = int(next_n_byte_lsb(1), 2)
        if sequential_flag == 255:
            is_sequential = True
        elif sequential_flag == 0:
            is_sequential = False
        else:
            raise Exception('Invalid sequential flag')
        # parse filename
        filename_len = int(next_n_byte_lsb(1), 2)
        filename = i2b(int(next_n_byte_lsb(filename_len), 2), filename_len).decode('latin-1')
        # parse contents_len
        contents_len = int(next_n_byte_lsb(3), 2)
        # if not sequential, switch to random generator
        if not is_sequential:
            len_bit_front = (1 + 1 + filename_len + 3) * 8
            lsb_generator = LSBHelper.rand_lsb_generator(byte_list[len_bit_front:], seed)
            next_n_byte_lsb = lambda n: ''.join(list(itertools.islice(lsb_generator, n * 8)))
        # parse contents
        contents = i2b(int(next_n_byte_lsb(contents_len), 2), contents_len)
        # return
        return filename, contents


if __name__ == '__main__':
    import random
    container = [random.randint(0, 255) for i in range(2000)]
    # print(container)

    is_sequential = False
    filename = 'filename.txt'
    contents = b'testcontentgan'

    # payload = LSBHelper.craft_payload(is_sequential, filename, contents)
    # print(payload)

    new_container = LSBHelper.insert_data_as_lsb(container, is_sequential, filename, contents, 'seed')

    filename, contents = LSBHelper.extract_data_from_lsb(new_container, 'seed')
    print(len(filename))
    print(len(contents))

    print(filename)
    print(contents)
