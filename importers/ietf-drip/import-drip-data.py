# import codecs
import binascii
import struct

DRIP_MESSAGE_SIZE = 25
DRIP_MESSAGE_SIZE_BASIC_ID = 25
DRIP_MESSAGE_SIZE_LOCATION = 16
DRIP_MESSAGE_SIZE_AUTH = 22
DRIP_MESSAGE_SIZE_SELF_ID = 23
DRIP_MESSAGE_SIZE_SYSTEM = 14
DRIP_MESSAGE_BASIC_ID = 0x0
DRIP_MESSAGE_LOCATION = 0x1
DRIP_MESSAGE_AUTH = 0x2
DRIP_MESSAGE_SELF_ID = 0x3
DRIP_MESSAGE_SYSTEM = 0x4
DRIP_MESSAGETYPE_OPERATOR_ID = 0x5
DRIP_MESSAGETYPE_PACKED = 0xF
DRIP_MAX_AREA_COUNT = 4
DRIP_PACK_MAX_MESSAGES = 9
DRIP_SUCCESS = 0
DRIP_FAIL = -1

class DRIP_UAS_Data(ctypes.Structure):
    _fields_ = [
        ("Version", ctypes.c_uint8),
        ("IDType", ctypes.c_uint8),
        ("UAType", ctypes.c_uint8),
        ("OperatorLocationType", ctypes.c_uint8),
        ("OperatorLatitude", ctypes.c_double),
        ("OperatorLongitude", ctypes.c_double),
        ("AreaCount", ctypes.c_uint8),
        ("AreaRadius", ctypes.c_double * DRIP_MAX_AREA_COUNT),
        ("AreaCeiling", ctypes.c_double * DRIP_MAX_AREA_COUNT),
        ("AreaFloor", ctypes.c_double * DRIP_MAX_AREA_COUNT),
        ("CategoryEU", ctypes.c_uint8),
        ("ClassEU", ctypes.c_uint8),
        ("OperatorAltitudeGeo", ctypes.c_double),
        ("OperatorAltitudeBaro", ctypes.c_double),
    ]

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
