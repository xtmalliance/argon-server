"""
This module provides functions to decode the System message in the DRIP protocol.

The System message contains information about the DRIP protocol version and message type.

This module defines the following classes:
- SystemDecoder: Class that handles the decoding of System messages.

It also defines the following constants related to the System message format:
- DRIP_MESSAGE_SIZE_SYSTEM: Size of the System message.

Usage:
------
# Create an instance of SystemDecoder
decoder = SystemDecoder()

# Decode a System message
result = decoder.decode_system(uas_data, raw_data)
if result == DRIP_SUCCESS:
    # System message decoding successful
    print("System message decoded successfully")
else:
    # System message decoding failed
    print("System message decoding failed")

Note: This module requires the 'drip_messages' module to be imported.

For more information about the DRIP protocol and the System message format, refer to the ASTM F3411 specification.
"""

import ctypes
import drip_messages as common

class SystemDecoder:
    @staticmethod
    def decode_system(uas_data, raw_data):
        if not uas_data or not raw_data:
            return common.DRIP_FAIL

        if len(raw_data) < common.DRIP_MESSAGE_SIZE_SYSTEM:
            return common.DRIP_FAIL

        # Convert raw_data to bytes
        raw_bytes = bytes(raw_data)

        uas_data.System.OperatorLocationType = raw_bytes[1] & 0x03
        uas_data.System.ClassificationType = (raw_bytes[1] >> 2) & 0x07

        uas_data.System.OperatorLatitude = (int.from_bytes(raw_bytes[2:6], byteorder='little', signed=True))/10000000.0
        uas_data.System.OperatorLongitude = (int.from_bytes(raw_bytes[6:10], byteorder='little', signed=True))/10000000.0

        uas_data.System.AreaCount = int.from_bytes(raw_bytes[10:12], byteorder='little')
        uas_data.System.AreaRadius = raw_bytes[12] * 10
        uas_data.System.AreaCeiling = (int.from_bytes(raw_bytes[13:15], byteorder='little') * common.DRIP_ALT_DIV) - common.DRIP_ALT_ADDER
        uas_data.System.AreaFloor = (int.from_bytes(raw_bytes[15:17], byteorder='little') * common.DRIP_ALT_DIV) - common.DRIP_ALT_ADDER

        uas_data.System.ClassEU = raw_bytes[17] & 0x0F
        uas_data.System.CategoryEU = (raw_bytes[17] >> 4) & 0x0F

        uas_data.System.OperatorAltitudeGeo = (int.from_bytes(raw_bytes[18:20], byteorder='little') * common.DRIP_ALT_DIV) - common.DRIP_ALT_ADDER
        uas_data.System.Timestamp = int.from_bytes(raw_bytes[20:24], byteorder='little')

        uas_data.SystemValid = 1

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

        return common.DRIP_SUCCESS
