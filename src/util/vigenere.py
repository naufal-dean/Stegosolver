def encrypt_data(self, key : str, data : bytes) -> bytes:
    enc_bytes = bytearray()
    for i in range(len(data)):
        proc_byte = (data[i] + ord(key[i % len(key)])) % 256
        enc_bytes.append(proc_byte)
    return bytes(enc_bytes)

def decrypt_data(self, key : str, data : bytes) -> bytes:
    dec_bytes = bytearray()
    for i in range(len(data)):
        proc_byte = (data[i] - ord(key[i % len(key)])) % 256
        dec_bytes.append(proc_byte)
    return bytes(dec_bytes)
