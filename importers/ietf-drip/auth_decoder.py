"""
This module provides functions to decode the Authentication message in the DRIP protocol.

The Authentication message contains information related to the authentication of unmanned aircraft systems (UAS)
and is used for secure communication between UAS and ground control.

This module defines the following classes:
- AuthDecoder: Class that handles the decoding of Authentication messages.

It also defines the following constants related to the Authentication message format:
- DRIP_AUTH_DESC_SIZE: Size of the Authentication description field.
- DRIP_AUTH_PAGE_ZERO_DATA_SIZE: Size of the data in the first page of the Authentication message.
- DRIP_AUTH_PAGE_NONZERO_DATA_SIZE: Size of the data in each subsequent page of the Authentication message.
- DRIP_AUTH_MAX_PAGES: Maximum number of pages in the Authentication message.
- MAX_AUTH_LENGTH: Maximum length of the Authentication message.

Usage:
------
# Create an instance of AuthDecoder
decoder = AuthDecoder()

# Decode an Authentication message
result = decoder.decode_auth(uas_data, raw_data)
if result == DRIP_SUCCESS:
    # Authentication message decoding successful
    print("Authentication message decoded successfully")
else:
    # Authentication message decoding failed
    print("Authentication message decoding failed")

Note: This module requires the 'drip_messages' module to be imported.

For more information about the DRIP protocol and the Authentication message format, refer to the ASTM F3411 specification.
"""

from ctypes import Structure, c_uint8, c_uint16, c_uint32, c_char, c_float, c_double, c_void_p, sizeof, POINTER
import struct
import ctypes
import drip_messages as common

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

        common.printAuthData(uasData, pageNum)
        return common.DRIP_SUCCESS

    @staticmethod
    def getAuthPageNum(inEncoded):
        if not inEncoded or \
                inEncoded.page_zero.MessageType != common.DRIP_MESSAGE_AUTH or \
                not common.intInRange(inEncoded.page_zero.AuthType, 0, 15) or \
                not common.intInRange(inEncoded.page_zero.DataPage, 0, common.DRIP_AUTH_MAX_PAGES - 1):

            return common.DRIP_FAIL

        return inEncoded.page_zero.DataPage

    def decode_authentication(uas_data, raw_data):
        if not uas_data or not raw_data:
            return common.DRIP_FAIL

        if len(raw_data) < common.DRIP_MESSAGE_SIZE_AUTH:
            return common.DRIP_FAIL

        auth_encoded = common.DRIP_Auth_encoded()
        ctypes.memmove(ctypes.addressof(auth_encoded), bytes(raw_data), ctypes.sizeof(auth_encoded))

        page = AuthDecoder.getAuthPageNum(auth_encoded)
        print('AuthPage:' + str(page))

        if AuthDecoder.decodeAuthMessage(uas_data, auth_encoded, page) == common.DRIP_SUCCESS:
            uas_data.AuthValid[page] = 1
        else:
            return common.DRIP_FAIL

        return common.DRIP_SUCCESS
