"""
This module provides functions to decode the Operator ID message in the DRIP protocol.

The Operator ID message contains identification information about the operator of an unmanned aircraft system (UAS),
such as the operator's registration ID or certificate.

This module defines the following classes:
- OperatorIDDecoder: Class that handles the decoding of Operator ID messages.

It also defines the following constants related to the Operator ID message format:
- DRIP_OPERATOR_ID_SIZE: Size of the operator ID field.
- DRIP_MESSAGE_SIZE_OPERATOR_ID: Size of the Operator ID message.

Usage:
------
# Create an instance of OperatorIDDecoder
decoder = OperatorIDDecoder()

# Decode an Operator ID message
result = decoder.decode_operator_id(uas_data, raw_data)
if result == DRIP_SUCCESS:
    # Operator ID message decoding successful
    print("Operator ID message decoded successfully")
else:
    # Operator ID message decoding failed
    print("Operator ID message decoding failed")

Note: This module requires the 'drip_messages' module to be imported.

For more information about the DRIP protocol and the Operator ID message format, refer to the ASTM F3411 specification.
"""

import ctypes
import drip_messages as common

class OperatorIDDecoder:
    @staticmethod
    def decode_operatorid(uas_data, raw_data):
        if not uas_data or not raw_data:
            return common.DRIP_FAIL

        # Convert raw_data to bytes
        raw_bytes = bytes(raw_data)

        uas_data.OperatorID.OperatorIdType = raw_bytes[1]
        uas_data.OperatorID.OperatorId = raw_data[2:22]

        # Set BasicID validity
        uas_data.OperatorID.OperatorIDValid = 1

        # Print the decoded values
        print("OperatorIdType:", uas_data.OperatorID.OperatorIdType.value)
        print("OperatorId:", uas_data.OperatorID.OperatorId)

        return common.DRIP_SUCCESS

