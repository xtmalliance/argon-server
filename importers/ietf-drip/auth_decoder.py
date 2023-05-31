from ctypes import Structure, c_uint8, c_uint16, c_uint32, c_char, c_float, c_double, c_void_p, sizeof, POINTER
import struct
import ctypes
import drip_messages as common

class DRIP_AuthPageZero(ctypes.Structure):
    _fields_ = [
        ("MessageType", ctypes.c_uint8),
        ("AuthType", ctypes.c_uint8),
        ("DataPage", ctypes.c_uint8),
        ("LastPageIndex", ctypes.c_uint8),
        ("Length", ctypes.c_uint8),
        ("Timestamp", ctypes.c_uint32),
        ("AuthData", ctypes.c_uint8 * common.DRIP_AUTH_PAGE_ZERO_DATA_SIZE)
    ]

class DRIP_AuthPageNonZero(ctypes.Structure):
    _fields_ = [
        ("AuthData", ctypes.c_uint8 * common.DRIP_AUTH_PAGE_NONZERO_DATA_SIZE)
    ]

class DRIP_Auth_encoded(ctypes.Union):
    _fields_ = [
        ("page_zero", DRIP_AuthPageZero),
        ("page_non_zero", DRIP_AuthPageNonZero)
    ]

def intInRange(value, min_value, max_value):
    """
    Checks if the given value is within the specified range.
    Returns True if the value is within the range, False otherwise.
    """
    return min_value <= value <= max_value

def printAuthData(uasData, pageNum):
    authData = uasData.Auth[pageNum].AuthData
    print("AuthData (hex):", end=" ")
    for element in authData:
        print(hex(element), end=" ")
    print()  # Print a newline at the end

class AuthDecoder:
    @staticmethod
    def decodeAuthMessage(uasData, inEncoded, pageNum):
        if inEncoded.page_zero.DataPage == 0:
            if inEncoded.page_zero.LastPageIndex >= common.DRIP_AUTH_MAX_PAGES:
                return common.DRIP_FAIL

            if inEncoded.page_zero.Length > common.MAX_AUTH_LENGTH:
                return common.DRIP_FAIL

            length = common.DRIP_AUTH_PAGE_ZERO_DATA_SIZE + inEncoded.page_zero.LastPageIndex * common.DRIP_AUTH_PAGE_NONZERO_DATA_SIZE
            if length < inEncoded.page_zero.Length:
                return common.DRIP_FAIL

        uasData.Auth.AuthType = inEncoded.page_zero.AuthType
        uasData.Auth.DataPage = inEncoded.page_zero.DataPage

        if inEncoded.page_zero.DataPage == 0:
            uasData.Auth.LastPageIndex = inEncoded.page_zero.LastPageIndex
            uasData.Auth.Length = inEncoded.page_zero.Length
            uasData.Auth.Timestamp = inEncoded.page_zero.Timestamp
            ctypes.memmove(
                ctypes.addressof(uasData.Auth[pageNum].AuthData),
                inEncoded.page_zero.AuthData,
                common.DRIP_AUTH_PAGE_ZERO_DATA_SIZE
            )
        else:
            ctypes.memmove(
                ctypes.addressof(uasData.Auth[pageNum].AuthData),
                inEncoded.page_non_zero.AuthData,
                common.DRIP_AUTH_PAGE_NONZERO_DATA_SIZE
            )

        printAuthData(uasData, pageNum)
        return common.DRIP_SUCCESS

    @staticmethod
    def getAuthPageNum(inEncoded):
        if not inEncoded or \
                inEncoded.page_zero.MessageType != common.DRIP_MESSAGE_AUTH or \
                not intInRange(inEncoded.page_zero.AuthType, 0, 15) or \
                not intInRange(inEncoded.page_zero.DataPage, 0, common.DRIP_AUTH_MAX_PAGES - 1):

            return common.DRIP_FAIL

        return inEncoded.page_zero.DataPage

    def decode_authentication(uas_data, raw_data):
        if not uas_data or not raw_data:
            return common.DRIP_FAIL

        if len(raw_data) < common.DRIP_MESSAGE_SIZE_AUTH:
            return common.DRIP_FAIL

        auth_encoded = DRIP_Auth_encoded()
        ctypes.memmove(ctypes.addressof(auth_encoded), bytes(raw_data), ctypes.sizeof(auth_encoded))

        page = AuthDecoder.getAuthPageNum(auth_encoded)
        print('AuthPage:' + str(page))

        if AuthDecoder.decodeAuthMessage(uas_data, auth_encoded, page) == common.DRIP_SUCCESS:
            uas_data.AuthValid[page] = 1
        else:
            return common.DRIP_FAIL

        return common.DRIP_SUCCESS
