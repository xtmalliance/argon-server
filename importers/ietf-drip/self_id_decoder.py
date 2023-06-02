"""
This module provides functions to decode the Self ID message in the DRIP protocol.

The Self ID message contains identification information about the unmanned aircraft system (UAS) itself,
such as the UAS type, operator's contact information, and additional description.

This module defines the following classes:
- SelfIDDecoder: Class that handles the decoding of Self ID messages.

It also defines the following constants related to the Self ID message format:
- DRIP_SELF_ID_DESC_SIZE: Size of the Self ID description field.
- DRIP_MESSAGE_SIZE_SELF_ID: Size of the Self ID message.

Usage:
------
# Create an instance of SelfIDDecoder
decoder = SelfIDDecoder()

# Decode a Self ID message
result = decoder.decode_self_id(uas_data, raw_data)
if result == DRIP_SUCCESS:
    # Self ID message decoding successful
    print("Self ID message decoded successfully")
else:
    # Self ID message decoding failed
    print("Self ID message decoding failed")

Note: This module requires the 'drip_messages' module to be imported.

For more information about the DRIP protocol and the Self ID message format, refer to the ASTM F3411 specification.
"""

import ctypes
import drip_messages as common

def printselfIDdesc(uas_data):
    print("selfID (hex):", end=" ")
    for element in uas_data.SelfID.Desc:
        print(hex(element), end=" ")
    print()  # Print a newline at the end

class SelfIDDecoder:
    def decode_self_id(uas_data, raw_data):
        if not uas_data or not raw_data:
            return common.DRIP_FAIL

        if len(raw_data) < common.DRIP_MESSAGE_SIZE_SELF_ID:
            return common.DRIP_FAIL

        # Create an instance of the DRIP_SelfID_data struct
        self_id_data = common.DRIP_SelfID_data()

        # Populate the struct from raw data using indexing
        self_id_data.DescType = common.DRIP_desctype_t(raw_data[1])
        self_id_data.Desc = bytes(raw_data[2:common.DRIP_STR_SIZE + 2])

        # Assign the populated struct to uas_data
        uas_data.SelfID = self_id_data
        uas_data.SelfIDValid = 1
        printselfIDdesc(uas_data)

        return common.DRIP_SUCCESS

