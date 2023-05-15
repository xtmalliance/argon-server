# import codecs
import binascii


if __name__ == '__main__':

    with open('data/rid-test-vectors', 'rb') as f:
        hexdata = f.read(1)
    
    print('{0:08b}'.format(ord(hexdata)))
    # with open('data/rid-test-vectors', 'rb') as f:
    #     hexdata = f.read().hex()

    # decode_hex = codecs.getdecoder("hex_codec")

    # print(decode_hex(hexdata))


    # with open('data/rid-test-vectors', 'rb') as f:
    #     hexdata = f.read().hex()
    
    # print(bytes.fromhex(hexdata).decode('utf-8'))