# import codecs
import binascii
import struct
import ctypes
from ctypes import Structure, c_uint8, c_uint16, c_uint32, c_char, c_float, c_double, c_void_p, sizeof, POINTER

# Define constants
DRIP_BASIC_ID_MAX_MESSAGES = 2
DRIP_AUTH_MAX_PAGES = 16
DRIP_ID_SIZE = 20
DRIP_AUTH_MAX_PAGES = 16
DRIP_AUTH_PAGE_ZERO_DATA_SIZE = 17
DRIP_AUTH_PAGE_NONZERO_DATA_SIZE = 23
DRIP_STR_SIZE = 23
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
DRIP_ALT_DIV = 0.5
DRIP_ALT_ADDER = 1000
DRIP_INV_TIMESTAMP = 0xFFFF
DRIP_DEBUG = False
DRIP_CUSTOM = True

# Define the DRIP_MessageType enum
class DRIP_MessageType(ctypes.c_int):
    BASIC_ID = 0
    LOCATION = 1
    AUTH = 2
    SELF_ID = 3
    SYSTEM = 4
    OPERATOR_ID = 5
    MESSAGETYPE_PACKED = 0xF
    MESSAGETYPE_INVALID = 0xFF

# Define the DRIP_uatype_t enum
class DRIP_uatype_t(ctypes.c_int):
    DRIP_UATYPE_NONE = 0,
    DRIP_UATYPE_AEROPLANE = 1, # Fixed wing
    DRIP_UATYPE_HELICOPTER_OR_MULTIROTOR = 2,
    DRIP_UATYPE_GYROPLANE = 3,
    DRIP_UATYPE_HYBRID_LIFT = 4, # Fixed wing aircraft that can take off vertically
    DRIP_UATYPE_ORNITHOPTER = 5,
    DRIP_UATYPE_GLIDER = 6,
    DRIP_UATYPE_KITE = 7,
    DRIP_UATYPE_FREE_BALLOON = 8,
    DRIP_UATYPE_CAPTIVE_BALLOON = 9,
    DRIP_UATYPE_AIRSHIP = 10, # Such as a blimp
    DRIP_UATYPE_FREE_FALL_PARACHUTE = 11, #/# Unpowered
    DRIP_UATYPE_ROCKET = 12,
    DRIP_UATYPE_TETHERED_POWERED_AIRCRAFT = 13,
    DRIP_UATYPE_GROUND_OBSTACLE = 14,
    DRIP_UATYPE_OTHER = 15,

class DRIP_idtype_t(ctypes.c_int):
# Define the DRIP_BasicID_data struct
    DRIP_IDTYPE_NONE = 0,
    DRIP_IDTYPE_SERIAL_NUMBER = 1,
    DRIP_IDTYPE_CAA_REGISTRATION_ID = 2, # Civil Aviation Authority
    DRIP_IDTYPE_UTM_ASSIGNED_UUID = 3,   # UAS (Unmanned Aircraft System) Traffic Management
    DRIP_IDTYPE_SPECIFIC_SESSION_ID = 4, # The exact id type is specified by the first byte of UASID and these type
                                         # values are managed by ICAO. 0 is reserved. 1 - 224 are managed by ICAO.
                                         # 225 - 255 are available for private experimental usage only
    # 5 to 15 reserved

class DRIP_BasicID_data(Structure):
    _fields_ = [
        ("UAType", DRIP_uatype_t),
        ("IDType", DRIP_idtype_t),
        ("UASID", c_char * (DRIP_ID_SIZE + 1))
    ]

# Define the DRIP_status_t enum
class DRIP_status_t(ctypes.c_int):
    VALID = 0
    INVALID = 1
    NO_VALUE = 2
    UNKNOWN = 3

# Define the DRIP_Height_reference_t enum
class DRIP_Height_reference_t(ctypes.c_int):
    WGS84 = 0
    BARO_PRESSURE = 1

# Define the DRIP_Horizontal_accuracy_t enum
class DRIP_Horizontal_accuracy_t(ctypes.c_int):
    UNKNOWN = 0
    EXCELLENT = 1
    GOOD = 2
    MODERATE = 3
    FAIR = 4
    POOR = 5

# Define the DRIP_Vertical_accuracy_t enum
class DRIP_Vertical_accuracy_t(ctypes.c_int):
    UNKNOWN = 0
    EXCELLENT = 1
    GOOD = 2
    MODERATE = 3
    FAIR = 4
    POOR = 5

# Define the DRIP_Speed_accuracy_t enum
class DRIP_Speed_accuracy_t(ctypes.c_int):
    UNKNOWN = 0
    EXCELLENT = 1
    GOOD = 2
    MODERATE = 3
    FAIR = 4
    POOR = 5

# Define the DRIP_Timestamp_accuracy_t enum
class DRIP_Timestamp_accuracy_t(ctypes.c_int):
    UNKNOWN = 0
    EXCELLENT = 1
    GOOD = 2
    MODERATE = 3
    FAIR = 4
    POOR = 5

# Define the DRIP_Location_data struct
class DRIP_Location_data(Structure):
    _fields_ = [
        ("Status", DRIP_status_t),
        ("Direction", c_float),
        ("SpeedHorizontal", c_float),
        ("SpeedVertical", c_float),
        ("Latitude", c_double),
        ("Longitude", c_double),
        ("AltitudeBaro", c_float),
        ("AltitudeGeo", c_float),
        ("HeightType", DRIP_Height_reference_t),
        ("Height", c_float),
        ("HorizAccuracy", DRIP_Horizontal_accuracy_t),
        ("VertAccuracy", DRIP_Vertical_accuracy_t),
        ("BaroAccuracy", DRIP_Vertical_accuracy_t),
        ("SpeedAccuracy", DRIP_Speed_accuracy_t),
        ("TSAccuracy", DRIP_Timestamp_accuracy_t),
        ("TimeStamp", c_float)
    ]

# Define the DRIP_authtype_t enum
class DRIP_authtype_t(ctypes.c_int):
    NONE = 0
    UAS_ID_SIGNATURE = 1
    OPERATOR_ID_SIGNATURE = 2
    MESSAGE_SET_SIGNATURE = 3
    NETWORK_REMOTE_ID = 4
    SPECIFIC_AUTHENTICATION = 5
    # Add more values here

# Define the DRIP_Auth_data struct
class DRIP_Auth_data(Structure):
    _fields_ = [
        ("DataPage", c_uint8),
        ("AuthType", c_uint8),
        ("LastPageIndex", c_uint8),
        ("Length", c_uint8),
        ("Timestamp", c_uint32),
        ("AuthData", c_uint8 * (DRIP_AUTH_PAGE_NONZERO_DATA_SIZE + 1))
    ]

class DRIP_Auth_encoded_page_zero(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("ProtoVersion", ctypes.c_uint8, 4),
        ("MessageType", ctypes.c_uint8, 4),
        ("DataPage", ctypes.c_uint8, 4),
        ("AuthType", ctypes.c_uint8, 4),
        ("LastPageIndex", ctypes.c_uint8),
        ("Length", ctypes.c_uint8),
        ("Timestamp", ctypes.c_uint32),
        ("AuthData", ctypes.c_uint8 * DRIP_AUTH_PAGE_ZERO_DATA_SIZE)
    ]

class DRIP_Auth_encoded_page_non_zero(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        # Define the fields for page_non_zero
    ]

class DRIP_Auth_encoded(ctypes.Union):
    _fields_ = [
        ("page_zero", DRIP_Auth_encoded_page_zero),
        ("page_non_zero", DRIP_Auth_encoded_page_non_zero)
    ]

# Define the DRIP_desctype_t enum
class DRIP_desctype_t(ctypes.c_int):
    TEXT = 0
    EMERGENCY = 1
    EXTENDED_STATUS = 2
    # 3 to 200 reserved
    # 201 to 255 available for private use

# Define the DRIP_SelfID_data struct
class DRIP_SelfID_data(Structure):
    _fields_ = [
        ("DescType", DRIP_desctype_t),
        ("Desc", c_char * (DRIP_STR_SIZE + 1))  # Additional byte to allow for null term in normative form
    ]

# Define the DRIP_operator_location_type_t enum
class DRIP_operator_location_type_t(ctypes.c_int):
    TAKEOFF = 0,
    LIVE_GNSS = 1,
    FIXED = 2
    # 3 to 255 reserved

# Define the DRIP_classification_type_t enum
class DRIP_classification_type_t(ctypes.c_int):
    UNDECLARED = 0
    EU = 1
    # 2 to 7 reserved

from ctypes import c_int

class DRIP_category_EU_t(ctypes.c_int):
    DRIP_CATEGORY_EU_UNDECLARED = 0
    DRIP_CATEGORY_EU_OPEN = 1
    DRIP_CATEGORY_EU_SPECIFIC = 2
    DRIP_CATEGORY_EU_CERTIFIED = 3
    # 4 to 15 reserved

# Define the DRIP_System_data struct
class DRIP_System_data(Structure):
    _fields_ = [
        ("OperatorLocationType", DRIP_operator_location_type_t),
        ("ClassificationType", DRIP_classification_type_t),
        ("OperatorLatitude", c_double),
        ("OperatorLongitude", c_double),
        ("AreaCount", c_uint16),
        ("AreaRadius", c_uint16),
        ("AreaCeiling", c_float),
        ("AreaFloor", c_float),
        ("CategoryEU", c_uint8),
        ("ClassEU", DRIP_category_EU_t),
        ("OperatorAltitudeGeo", c_float),
        ("Timestamp", c_uint16)
    ]

class DRIP_operatorIdType_t(ctypes.c_int):
    DRIP_OPERATOR_ID = 0

class DRIP_OperatorID_data(Structure):
    _fields_ = [
        ("OperatorIdType", DRIP_operatorIdType_t),
        ("OperatorId", c_char * (DRIP_ID_SIZE + 1))
    ]

# Define the DRIP_UAS_Data struct
class DRIP_UAS_Data(Structure):
    _fields_ = [
        ("BasicID", DRIP_BasicID_data),
        ("Location", DRIP_Location_data),
        ("Auth", DRIP_Auth_data),
        ("SelfID", DRIP_SelfID_data),
        ("System", DRIP_System_data),  # Use DRIP_System_Data structure
        ("OperatorID", c_void_p),
        ("BasicIDValid", c_uint8 * DRIP_BASIC_ID_MAX_MESSAGES),
        ("LocationValid", c_uint8),
        ("AuthValid", c_uint8 * DRIP_AUTH_MAX_PAGES),
        ("SelfIDValid", c_uint8),
        ("SystemValid", c_uint8),
        ("OperatorIDValid", c_uint8)
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

    if len(raw_data) < DRIP_MESSAGE_SIZE_BASIC_ID:
        return DRIP_FAIL

    # Populate BasicID fields
    uas_data.BasicID.UAType = DRIP_uatype_t(raw_data[0] & 0x0F)
    uas_data.BasicID.IDType = DRIP_idtype_t(raw_data[1] & 0x0F)
    uas_data.BasicID.UASID = raw_data[2:22]

    # Set BasicID validity
    uas_data.BasicIDValid[0] = 1

    return DRIP_SUCCESS

def decode_basic_id(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) < DRIP_MESSAGE_SIZE_BASIC_ID:
        return DRIP_FAIL

    if uas_data.BasicIDValid[0] == 1:
        return DRIP_SUCCESS

    # Convert raw_data to bytes
    raw_bytes = bytes(raw_data)

    # Populate BasicID fields
    uas_data.BasicID.UAType = (raw_bytes[1] >> 4) & 0x0F
    uas_data.BasicID.IDType = raw_bytes[1] & 0x0F
    uas_data.BasicID.UASID = raw_bytes[2:22]

    # Set BasicID validity
    uas_data.BasicIDValid[0] = 1

    # Print field values
    print("UAType:", uas_data.BasicID.UAType.value)
    print("IDType:", uas_data.BasicID.IDType.value)
    print("UASID:", uas_data.BasicID.UASID)

    return DRIP_SUCCESS

def decodeHorizontalAccuracy(Accuracy):
    if Accuracy == 0:
        return 18520
    elif Accuracy == 1:
        return 18520
    elif Accuracy == 2:
        return 7808
    elif Accuracy == 3:
        return 3704
    elif Accuracy == 4:
        return 1852
    elif Accuracy == 5:
        return 926
    elif Accuracy == 6:
        return 555.6
    elif Accuracy == 7:
        return 185.2
    elif Accuracy == 8:
        return 92.6
    elif Accuracy == 9:
        return 30
    elif Accuracy == 10:
        return 10
    elif Accuracy == 11:
        return 3
    elif Accuracy == 12:
        return 1
    else:
        return 18520


def decodeVerticalAccuracy(Accuracy):
    if Accuracy == 0:
        return 150
    elif Accuracy == 1:
        return 150
    elif Accuracy == 2:
        return 45
    elif Accuracy == 3:
        return 25
    elif Accuracy == 4:
        return 10
    elif Accuracy == 5:
        return 3
    elif Accuracy == 6:
        return 1
    else:
        return 150


def decodeSpeedAccuracy(Accuracy):
    if Accuracy == 0:
        return 10
    elif Accuracy == 1:
        return 10
    elif Accuracy == 2:
        return 3
    elif Accuracy == 3:
        return 1
    elif Accuracy == 4:
        return 0.3
    else:
        return 10


def decodeTimestampAccuracy(Accuracy):
    if Accuracy == 0:
        return 0.0
    elif Accuracy == 1:
        return 0.1
    elif Accuracy == 2:
        return 0.2
    elif Accuracy == 3:
        return 0.3
    elif Accuracy == 4:
        return 0.4
    elif Accuracy == 5:
        return 0.5
    elif Accuracy == 6:
        return 0.6
    elif Accuracy == 7:
        return 0.7
    elif Accuracy == 8:
        return 0.8
    elif Accuracy == 9:
        return 0.9
    elif Accuracy == 10:
        return 1.0
    elif Accuracy == 11:
        return 1.1
    elif Accuracy == 12:
        return 1.2
    elif Accuracy == 13:
        return 1.3
    elif Accuracy == 14:
        return 1.4
    elif Accuracy == 15:
        return 1.5
    else:
        return 0.0

def decodeTimeStamp(Seconds_enc):
    if Seconds_enc == DRIP_INV_TIMESTAMP:
        return DRIP_INV_TIMESTAMP
    else:
        return Seconds_enc / 10.0

def decode_location(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) < 25:
        return DRIP_FAIL

    # Convert raw_data to bytes
    raw_bytes = bytes(raw_data)

    struct_format = "<BBBbbbbiiHHHBBH"
    unpacked_data = struct.unpack(struct_format, raw_bytes)

    uas_data.Location.Status = unpacked_data[1] >> 4
    uas_data.Location.HeightType = (unpacked_data[1] >> 1) & 0x01
    uas_data.Location.Direction = unpacked_data[2]
    uas_data.Location.SpeedHorizontal = unpacked_data[3]
    uas_data.Location.SpeedVertical = unpacked_data[4]

    # Convert the bytes to a signed 32-bit integer in little-endian byte order
    latitude_bytes = raw_bytes[5:9]
    latitude_value = struct.unpack("<i", latitude_bytes)[0]
    latitude = latitude_value / 10000000.0

    # Convert the bytes to a signed 32-bit integer in little-endian byte order
    longitude_bytes = raw_bytes[9:13]
    longitude_value = struct.unpack("<i", longitude_bytes)[0]
    longitude = longitude_value / 10000000.0

    uas_data.Location.Latitude = latitude
    uas_data.Location.Longitude = longitude

    #uas_data.Location.AltitudeBaro = unpacked_data[7]
    AltitudeBaro_bytes = raw_bytes[13:15]
    AltitudeBaro_value = struct.unpack("<H", AltitudeBaro_bytes)[0]
    uas_data.Location.AltitudeBaro = (AltitudeBaro_value * DRIP_ALT_DIV) - DRIP_ALT_ADDER

    AltitudeGeo_bytes = raw_bytes[15:17]
    AltitudeGeo_value = struct.unpack("<H", AltitudeGeo_bytes)[0]
    uas_data.Location.AltitudeGeo = (AltitudeGeo_value * DRIP_ALT_DIV) - DRIP_ALT_ADDER

    Height_bytes = raw_bytes[17:19]
    Height_value = struct.unpack("<H", Height_bytes)[0]
    uas_data.Location.Height = (Height_value * DRIP_ALT_DIV) - DRIP_ALT_ADDER

    HorizVertAccuracy_bytes = raw_bytes[19:20]
    HorizVertAccuracy_value = struct.unpack("<B", HorizVertAccuracy_bytes)[0]
    uas_data.Location.HorizAccuracy = decodeHorizontalAccuracy(HorizVertAccuracy_value & 0xF)
    uas_data.Location.VertAccuracy =  decodeVerticalAccuracy(HorizVertAccuracy_value >> 4)

    SpeedBaroAccuracy_bytes = raw_bytes[20:21]
    SpeedBaroAccuracy_bytes = struct.unpack("<B", SpeedBaroAccuracy_bytes)[0]
    uas_data.Location.SpeedAccuracy = decodeSpeedAccuracy(SpeedBaroAccuracy_bytes & 0xF)
    uas_data.Location.BaroAccuracy =  decodeVerticalAccuracy(SpeedBaroAccuracy_bytes >> 4)


    TS_bytes = raw_bytes[21:23]
    TS_value = struct.unpack("<H", TS_bytes)[0]
    uas_data.Location.TimeStamp = decodeTimeStamp(TS_value)

    TSAccuracy_bytes = raw_bytes[21:22]
    TSAccuracy_bytes = struct.unpack("<B", TSAccuracy_bytes)[0]
    uas_data.Location.TSAccuracy = decodeSpeedAccuracy(TSAccuracy_bytes & 0xF)

    # Print decoded fields
    print("Status:", uas_data.Location.Status.value)
    print("HeightType:", uas_data.Location.HeightType.value)
    print("Direction:", uas_data.Location.Direction)
    print("SpeedHorizontal:", uas_data.Location.SpeedHorizontal)
    print("SpeedVertical:", uas_data.Location.SpeedVertical)
    print("Latitude:", uas_data.Location.Latitude)
    print("Longitude:", uas_data.Location.Longitude)
    print("AltitudeBaro:", uas_data.Location.AltitudeBaro)
    print("AltitudeGeo:", uas_data.Location.AltitudeGeo)
    print("Height:", uas_data.Location.Height)
    print("Timestamp:", uas_data.Location.TimeStamp)
    print("HorizAccuracy:", uas_data.Location.HorizAccuracy.value)
    print("VertAccuracy:", uas_data.Location.VertAccuracy.value)
    print("SpeedAccuracy:", uas_data.Location.SpeedAccuracy.value)
    print("BaroAccuracy:", uas_data.Location.BaroAccuracy.value)
    print("TSAccuracy:", uas_data.Location.TSAccuracy.value)

    return DRIP_SUCCESS

def decode_authentication(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) < DRIP_MESSAGE_SIZE_AUTH:
        return DRIP_FAIL

    return DRIP_SUCCESS

def decode_self_id(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) < DRIP_MESSAGE_SIZE_SELF_ID:
        return DRIP_FAIL

    return DRIP_SUCCESS


def decode_system(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    if len(raw_data) < DRIP_MESSAGE_SIZE_SYSTEM:
        return DRIP_FAIL

    # Convert raw_data to bytes
    raw_bytes = bytes(raw_data)

    uas_data.System.OperatorLocationType = raw_bytes[1] & 0x03
    uas_data.System.ClassificationType = (raw_bytes[1] >> 2) & 0x07

    uas_data.System.OperatorLatitude = (int.from_bytes(raw_bytes[2:6], byteorder='little', signed=True))/10000000.0
    uas_data.System.OperatorLongitude = (int.from_bytes(raw_bytes[6:10], byteorder='little', signed=True))/10000000.0

    uas_data.System.AreaCount = int.from_bytes(raw_bytes[10:12], byteorder='little')
    uas_data.System.AreaRadius = raw_bytes[12] * 10
    uas_data.System.AreaCeiling = (int.from_bytes(raw_bytes[13:15], byteorder='little') * DRIP_ALT_DIV) - DRIP_ALT_ADDER
    uas_data.System.AreaFloor = (int.from_bytes(raw_bytes[15:17], byteorder='little') * DRIP_ALT_DIV) - DRIP_ALT_ADDER

    uas_data.System.ClassEU = raw_bytes[17] & 0x0F
    uas_data.System.CategoryEU = (raw_bytes[17] >> 4) & 0x0F

    uas_data.System.OperatorAltitudeGeo = (int.from_bytes(raw_bytes[18:20], byteorder='little') * DRIP_ALT_DIV) - DRIP_ALT_ADDER
    uas_data.System.Timestamp = int.from_bytes(raw_bytes[20:24], byteorder='little')


    # Print the decoded values
    print(f"Operator Location Type: {uas_data.System.OperatorLocationType.value}")
    print(f"Classification Type: {uas_data.System.ClassificationType.value}")
    print(f"Operator Latitude: {uas_data.System.OperatorLatitude}")
    print(f"Operator Longitude: {uas_data.System.OperatorLongitude}")
    print(f"Area Count: {uas_data.System.AreaCount}")
    print(f"Area Radius: {uas_data.System.AreaRadius}")
    print(f"Area Ceiling: {uas_data.System.AreaCeiling}")
    print(f"Area Floor: {uas_data.System.AreaFloor}")
    print(f"Class EU: {uas_data.System.ClassEU.value}")
    print(f"Category EU: {uas_data.System.CategoryEU}")
    print(f"Operator Altitude Geo: {uas_data.System.OperatorAltitudeGeo}")
    print(f"Timestamp: {uas_data.System.Timestamp}")

    return DRIP_SUCCESS


def decode_operatorid(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    return DRIP_SUCCESS

def decode_drone_id(uas_data, raw_data):
    if not uas_data or not raw_data:
        return DRIP_FAIL

    message_size = len(raw_data)

    if DRIP_MESSAGE_SIZE <= message_size:
        msg_type = raw_data[0] >> 4
        message_type_bytes = struct.pack('B', raw_data[0])

        if msg_type == DRIP_MESSAGE_BASIC_ID:
            print("DRIP_MESSAGE_BASIC_ID")
            # Decode basic ID message
            decode_basic_id(uas_data, raw_data[:DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == DRIP_MESSAGE_LOCATION:
            print("DRIP_MESSAGE_LOCATION")
            # Decode location message
            decode_location(uas_data, raw_data[:DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == DRIP_MESSAGE_AUTH:
            print("DRIP_MESSAGE_AUTH")
            # Decode authentication message
            decode_authentication(uas_data, raw_data[:DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == DRIP_MESSAGE_SELF_ID:
            print("DRIP_MESSAGE_SELF_ID")
            # Decode self ID message
            decode_self_id(uas_data, raw_data[:DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == DRIP_MESSAGE_SYSTEM:
            print("DRIP_MESSAGE_SYSTEM")
            # Decode system message
            decode_system(uas_data, raw_data[:DRIP_MESSAGE_SIZE])
            print("*********************")

        else:
            return DRIP_FAIL

    return DRIP_SUCCESS

def decode_message_pack(uas_data, pack, data):
    if not uas_data or not pack or pack.MessageType != DRIP_MESSAGETYPE_PACKED:
        decode_drone_id(uas_data, data)
        return DRIP_SUCCESS

    if pack.SingleMessageSize != DRIP_MESSAGE_SIZE:
        return DRIP_FAIL


    for i in range(pack.MsgPackSize):
        if DRIP_DEBUG:
            print("Raw Data:", ' '.join([hex(byte) for byte in pack.Messages[i].rawData[:DRIP_MESSAGE_SIZE]]))
        decode_drone_id(uas_data, pack.Messages[i].rawData)

    return DRIP_SUCCESS

def decodeMessagePack(data):
    uasData = DRIP_UAS_Data()
    pack = DRIP_MessagePack_encoded()
    ctypes.memmove(ctypes.addressof(pack), data, ctypes.sizeof(pack))
    ret = decode_message_pack(uasData, pack, data)

    return uasData

def print_uas_data(uas_data):
    if not uas_data:
        print("No data available.")
        return

    print("==== Location ====")
    if uas_data.LocationValid:
        location_data = uas_data.Location
        for field in dir(location_data):
            if not field.startswith("_"):
                value = getattr(location_data, field)
                print(f"{field}: {value}")

    print("==== Basic ID ====")
    if uas_data.BasicIDValid:
        basic_id_data = uas_data.BasicID
        for field in dir(basic_id_data):
            if not field.startswith("_"):
                value = getattr(basic_id_data, field)
                print(f"{field}: {value}")

    print("==== Authentication ====")
    auth_data = uas_data.Auth
    if uas_data.AuthValid[auth_data.DataPage]:
        print(f"DataPage: {auth_data.DataPage}")
        print(f"Timestamp: {auth_data.Timestamp}")
        for field in dir(auth_data):
            if not field.startswith("_"):
                value = getattr(auth_data, field)
                print(f"{field}: {value}")

    print("==== Self ID ====")
    if uas_data.SelfIDValid:
        self_id_data = uas_data.SelfID
        for field in dir(self_id_data):
            if not field.startswith("_"):
                value = getattr(self_id_data, field)
                print(f"{field}: {value}")

    print("==== System ====")
    if uas_data.SystemValid:
        system_data = uas_data.System
        for field in dir(system_data):
            if not field.startswith("_"):
                value = getattr(system_data, field)
                print(f"{field}: {value}")

    print("==== Operator ID ====")
    if uas_data.OperatorIDValid:
        operator_id_data = uas_data.OperatorID.contents
        for field in dir(operator_id_data):
            if not field.startswith("_"):
                value = getattr(operator_id_data, field)
                print(f"{field}: {value}")

if __name__ == '__main__':

    file_path = '/opt/rid-test-vectors'

    with open(file_path) as file:
        for line in file:
            dri_bytes = bytes.fromhex(line)
            if DRIP_CUSTOM:
                msg = decodeMessagePack(dri_bytes[1:])
            else:
                msg = decodeMessagePack(dri_bytes)

