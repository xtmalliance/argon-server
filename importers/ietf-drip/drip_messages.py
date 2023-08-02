"""
drip_messages.py - DRIP Message Definitions

This module defines the data structures and constants for DRIP (Drone Remote ID Protocol) messages.

Module Contents:
- DRIP Message Types
- DRIP Protocol Versions
- DRIP String Sizes
- DRIP Data Structures

Usage:
Import this module to access the DRIP message definitions and use them in your code.

Example:
import drip_messages as common

# Access the DRIP message types
message_type = common.DRIP_MessageType.DRIP_MESSAGE_TYPE_SELF_ID

# Access the DRIP protocol versions
protocol_version = common.DRIP_ProtocolVersion.DRIP_PROTO_VERSION_1

# Access the DRIP string sizes
string_size = common.DRIP_STR_SIZE

# Access the DRIP data structures
uas_data = common.UAS_Data()
uas_data.SelfID.DescType = common.DRIP_DescType.DRIP_DESC_TYPE_STANDARD
uas_data.SelfID.Desc = "My UAS"

"""
from ctypes import Structure, c_uint8, c_uint16, c_uint32, c_char, c_float, c_double, c_void_p, sizeof, POINTER
import struct
import ctypes

# Size constants for DRIP messages
DRIP_ID_SIZE = 20
"""Size of DRIP ID"""

DRIP_STR_SIZE = 23
"""Size of DRIP string"""

DRIP_MESSAGE_SIZE = 25
"""Size of DRIP message"""

DRIP_MESSAGE_SIZE_BASIC_ID = 25
"""Size of DRIP message for basic ID"""

DRIP_MESSAGE_SIZE_LOCATION = 16
"""Size of DRIP message for location"""

DRIP_MESSAGE_SIZE_AUTH = 22
"""Size of DRIP message for authentication"""

DRIP_MESSAGE_SIZE_SELF_ID = 23
"""Size of DRIP message for self ID"""

DRIP_MESSAGE_SIZE_SYSTEM = 14
"""Size of DRIP message for system"""

DRIP_MESSAGE_BASIC_ID = 0x0
"""DRIP message type for basic ID"""

DRIP_MESSAGE_LOCATION = 0x1
"""DRIP message type for location"""

DRIP_MESSAGE_AUTH = 0x2
"""DRIP message type for authentication"""

DRIP_MESSAGE_SELF_ID = 0x3
"""DRIP message type for self ID"""

DRIP_MESSAGE_SYSTEM = 0x4
"""DRIP message type for system"""

DRIP_MESSAGETYPE_OPERATOR_ID = 0x5
"""DRIP message type for operator ID"""

DRIP_MESSAGETYPE_PACKED = 0xF
"""DRIP message type for packed"""

DRIP_MAX_AREA_COUNT = 4
"""Maximum area count for DRIP"""

DRIP_BASIC_ID_MAX_MESSAGES = 2
"""Maximum number of basic ID messages"""

DRIP_PACK_MAX_MESSAGES = 9
"""Maximum number of packed messages"""

DRIP_AUTH_MAX_PAGES = 16
"""Maximum number of authentication pages"""

DRIP_AUTH_PAGE_ZERO_DATA_SIZE = 17
"""Size of authentication page zero data"""

DRIP_AUTH_PAGE_NONZERO_DATA_SIZE = 23
"""Size of authentication page non-zero data"""

MAX_AUTH_LENGTH =(DRIP_AUTH_PAGE_ZERO_DATA_SIZE + \
                         DRIP_AUTH_PAGE_NONZERO_DATA_SIZE * (DRIP_AUTH_MAX_PAGES - 1))
"""Maximum authentication length"""

DRIP_SUCCESS = 0
"""DRIP success code"""

DRIP_FAIL = -1
"""DRIP failure code"""

DRIP_ALT_DIV = 0.5
"""Altitude division factor for DRIP"""

DRIP_ALT_ADDER = 1000
"""Altitude adder for DRIP"""

DRIP_INV_TIMESTAMP = 0xFFFF
"""Invalid timestamp value for DRIP"""

DRIP_ALT_DIV = 10
"""Updated altitude division factor for DRIP"""

DRIP_ALT_ADDER = 1000
"""Updated altitude adder for DRIP"""

DRIP_DEBUG = False
"""Debug flag for DRIP"""

DRIP_CUSTOM = True
"""Custom flag for DRIP"""

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

# Define the DRIP ID type struct
class DRIP_idtype_t(ctypes.c_int):
    DRIP_IDTYPE_NONE = 0,
    DRIP_IDTYPE_SERIAL_NUMBER = 1,
    DRIP_IDTYPE_CAA_REGISTRATION_ID = 2, # Civil Aviation Authority
    DRIP_IDTYPE_UTM_ASSIGNED_UUID = 3,   # UAS (Unmanned Aircraft System) Traffic Management
    DRIP_IDTYPE_SPECIFIC_SESSION_ID = 4, # The exact id type is specified by the first byte of UASID and these type
                                         # values are managed by ICAO. 0 is reserved. 1 - 224 are managed by ICAO.
                                         # 225 - 255 are available for private experimental usage only
    # 5 to 15 reserved

# Define the DRIP_BasicID_data struct
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

# Define the DRIP_Auth_data page0 encoded struct
class DRIP_Auth_encoded_page_zero(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("ProtoVersion", ctypes.c_uint8, 4),
        ("MessageType", ctypes.c_uint8, 4),
        ("DataPage", ctypes.c_uint8, 4),
        ("AuthType", ctypes.c_uint8, 4),
        ("LastPageIndex", c_uint8),
        ("Length", c_uint8),
        ("Timestamp", c_uint32),
        ("AuthData", c_uint8 * DRIP_AUTH_PAGE_ZERO_DATA_SIZE)
    ]

# Define the DRIP_Auth_data non zero page encoded struct
class DRIP_Auth_encoded_page_non_zero(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("ProtoVersion", ctypes.c_uint8, 4),
        ("MessageType", ctypes.c_uint8, 4),
        ("DataPage", ctypes.c_uint8, 4),
        ("AuthType", ctypes.c_uint8, 4),
        ("AuthData", c_uint8 * DRIP_AUTH_PAGE_NONZERO_DATA_SIZE)
    ]

# Define the DRIP_Auth_data encoded paged struct
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

# Define the DRIP operator ID type struct
class DRIP_operatorIdType_t(ctypes.c_int):
    DRIP_OPERATOR_ID = 0

# Define the DRIP_OperatorID_data struct
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
        ("Auth", DRIP_Auth_data * DRIP_AUTH_MAX_PAGES),
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

# Define the DRIP_UAS_Data encoded raw struct
class DRIP_Message_encoded(ctypes.Structure):
    _fields_ = [
        ("rawData", ctypes.c_uint8 * DRIP_MESSAGE_SIZE),
    ]

# Define the DRIP_UAS_Data message pack encoded struct
class DRIP_MessagePack_encoded(ctypes.Structure):
    _fields_ = [
        ('ProtoVersion', ctypes.c_uint8, 4),
        ('MessageType', ctypes.c_uint8, 4),
        ("SingleMessageSize", ctypes.c_uint8),
        ("MsgPackSize", ctypes.c_uint8),
        ("Messages", DRIP_Message_encoded * DRIP_PACK_MAX_MESSAGES),
    ]

# check if value is in INT range
def intInRange(value, min_value, max_value):
    """
    Checks if the given value is within the specified range.
    Returns True if the value is within the range, False otherwise.
    """
    return min_value <= value <= max_value

# Print Auth page data
def printAuthData(uasData, pageNum):
    authData = uasData.Auth[pageNum].AuthData
    print("AuthData (hex):", end=" ")
    for element in authData:
        print(hex(element), end=" ")
    print()  # Print a newline at the end


