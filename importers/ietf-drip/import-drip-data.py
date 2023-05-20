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

class DRIP_Message_encoded(ctypes.Structure):
    _fields_ = [
        ("rawData", ctypes.c_uint8 * DRIP_MESSAGE_SIZE),
    ]

class DRIP_MessagePack_encoded(ctypes.Structure):
    _fields_ = [
        ('ProtoVersion', ctypes.c_uint8, 4),
        ('MessageType', ctypes.c_uint8, 4),
        ("SingleMessageSize", ctypes.c_uint8),
        ("MsgPackSize", ctypes.c_uint8),
        ("Messages", DRIP_Message_encoded * DRIP_PACK_MAX_MESSAGES),
    ]

def decode_basic_id(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) != DRIP_MESSAGE_SIZE_BASIC_ID:
        return DRIP_FAIL

    uas_data.IDType = (raw_data[1] & 0x80) >> 7
    uas_data.UAType = raw_data[1] & 0x7F
    uas_data.OperatorLatitude = (raw_data[2] << 25) | (raw_data[3] << 17) | (raw_data[4] << 9) | (raw_data[5] << 1) | (raw_data[6] >> 7)
    uas_data.OperatorLongitude = ((raw_data[6] & 0x7F) << 26) | (raw_data[7] << 18) | (raw_data[8] << 10) | (raw_data[9] << 2) | (raw_data[10] >> 6)

    return DRIP_SUCCESS

def decode_location(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) != DRIP_MESSAGE_SIZE_LOCATION:
        return DRIP_FAIL

    uas_data.Status = (raw_data[1] & 0x80) >> 7
    uas_data.Direction = (raw_data[1] & 0x7F) * 3.14159 / 180
    uas_data.SpeedHorizontal = raw_data[2]
    uas_data.SpeedVertical = raw_data[3] - 64
    uas_data.Latitude = ((raw_data[4] & 0x7F) << 24) | (raw_data[5] << 16) | (raw_data[6] << 8) | raw_data[7]
    uas_data.Longitude = (raw_data[8] << 25) | (raw_data[9] << 17) | (raw_data[10] << 9) | (raw_data[11] << 1) | (raw_data[12] >> 7)
    uas_data.AltitudeBaro = ((raw_data[12] & 0x7F) << 8) | raw_data[13]
    uas_data.AltitudeGeo = (raw_data[14] << 8) | raw_data[15]

    return DRIP_SUCCESS

def decode_authentication(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) != DRIP_MESSAGE_SIZE_AUTH:
        return DRIP_FAIL

    uas_data.OperatorAltitudeGeo = (raw_data[1] << 8) | raw_data[2]
    uas_data.OperatorAltitudeBaro = (raw_data[3] << 8) | raw_data[4]

    return DRIP_SUCCESS


def decode_self_id(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) != DRIP_MESSAGE_SIZE_SELF_ID:
        return DRIP_FAIL

    # TODO: Decode self ID message

    return DRIP_SUCCESS


def decode_system(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) != DRIP_MESSAGE_SIZE_SYSTEM:
        return DRIP_FAIL

    uas_data.OperatorLocationType = (raw_data[1] & 0x80) >> 7
    uas_data.AreaCount = raw_data[1] & 0x7F
    uas_data.AreaRadius = raw_data[2]
    uas_data.AreaCeiling = raw_data[3]
    uas_data.AreaFloor = raw_data[4]

    return DRIP_SUCCESS

def decode_drone_id(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    message_size = len(raw_data)

    if DRIP_MESSAGE_SIZE <= message_size:
        msg_type = raw_data[0] & 0x0F
        message_type_bytes = struct.pack('B', raw_data[0])
        print(message_type_bytes.hex() + ':' +  str(msg_type))

        if msg_type == DRIP_MESSAGE_BASIC_ID:
            print("DRIP_MESSAGE_BASIC_ID")
            # Decode basic ID message
            decode_basic_id(uas_data, raw_data[:DRIP_MESSAGE_SIZE])

        elif msg_type == DRIP_MESSAGE_LOCATION:
            print("DRIP_MESSAGE_LOCATION")
            # Decode location message
            decode_location(uas_data, raw_data[:DRIP_MESSAGE_SIZE])

        elif msg_type == DRIP_MESSAGE_AUTH:
            print("DRIP_MESSAGE_AUTH")
            # Decode authentication message
            decode_authentication(uas_data, raw_data[:DRIP_MESSAGE_SIZE])

        elif msg_type == DRIP_MESSAGE_SELF_ID:
            print("DRIP_MESSAGE_SELF_ID")
            # Decode self ID message
            decode_self_id(uas_data, raw_data[:DRIP_MESSAGE_SIZE])

        elif msg_type == DRIP_MESSAGE_SYSTEM:
            print("DRIP_MESSAGE_SYSTEM")
            # Decode system message
            decode_system(uas_data, raw_data[:DRIP_MESSAGE_SIZE])

        else:
            return DRIP_FAIL

    return DRIP_SUCCESS

def decode_message_pack(uas_data, pack):
    if not uas_data or not pack or pack.MessageType != DRIP_MESSAGETYPE_PACKED:
        message_type_bytes = struct.pack('B', pack.MessageType)
        print(message_type_bytes)
        return DRIP_FAIL

    if pack.SingleMessageSize != DRIP_MESSAGE_SIZE:
        return DRIP_FAIL


    for i in range(pack.MsgPackSize):
        print("Raw Data:", ' '.join([hex(byte) for byte in pack.Messages[i].rawData[:DRIP_MESSAGE_SIZE]]))
        decode_drone_id(uas_data, pack.Messages[i].rawData)

    return DRIP_SUCCESS

def decodeMessagePack(data):
    uasData = DRIP_UAS_Data()
    pack = DRIP_MessagePack_encoded()
    ctypes.memmove(ctypes.addressof(pack), data, ctypes.sizeof(pack))
    ret = decode_message_pack(uasData, pack)
    print('status:' + str(ret))

    return uasData

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
