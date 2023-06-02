"""
This module provides functions to decode the Basic ID message in the DRIP protocol.

The Basic ID message contains basic identification information about unmanned aircraft systems (UAS),
such as the UAS ID and the operator ID.

This module defines the following classes:
- BasicIDDecoder: Class that handles the decoding of Basic ID messages.

It also defines the following constants related to the Basic ID message format:
- DRIP_BASIC_ID_DESC_SIZE: Size of the Basic ID description field.
- DRIP_UAS_ID_SIZE: Size of the UAS ID field.
- DRIP_OPERATOR_ID_SIZE: Size of the operator ID field.
- DRIP_MESSAGE_SIZE_BASIC_ID: Size of the Basic ID message.

Usage:
------
# Create an instance of BasicIDDecoder
decoder = BasicIDDecoder()

# Decode a Basic ID message
result = decoder.decode_basic_id(uas_data, raw_data)
if result == DRIP_SUCCESS:
    # Basic ID message decoding successful
    print("Basic ID message decoded successfully")
else:
    # Basic ID message decoding failed
    print("Basic ID message decoding failed")

Note: This module requires the 'drip_messages' module to be imported.

For more information about the DRIP protocol and the Basic ID message format, refer to the ASTM F3411 specification.
"""

import drip_messages as common

class BasicIDDecoder:
    @staticmethod
    def decode_basic_id(uas_data, raw_data):
        if not uas_data or not raw_data:
            return common.DRIP_FAIL

        if len(raw_data) < common.DRIP_MESSAGE_SIZE_BASIC_ID:
            return common.DRIP_FAIL

        if uas_data.BasicIDValid[0] == 1:
            return common.DRIP_SUCCESS

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

        return common.DRIP_SUCCESS

