"""
This module provides functions to decode the Location message in the DRIP protocol.

The Location message contains geographic location information about unmanned aircraft systems (UAS),
such as latitude, longitude, and altitude.

This module defines the following classes:
- LocationDecoder: Class that handles the decoding of Location messages.

It also defines the following constants related to the Location message format:
- DRIP_LATITUDE_SIZE: Size of the latitude field.
- DRIP_LONGITUDE_SIZE: Size of the longitude field.
- DRIP_ALTITUDE_SIZE: Size of the altitude field.
- DRIP_MESSAGE_SIZE_LOCATION: Size of the Location message.

Usage:
------
# Create an instance of LocationDecoder
decoder = LocationDecoder()

# Decode a Location message
result = decoder.decode_location(uas_data, raw_data)
if result == DRIP_SUCCESS:
    # Location message decoding successful
    print("Location message decoded successfully")
else:
    # Location message decoding failed
    print("Location message decoding failed")

Note: This module requires the 'drip_messages' module to be imported.

For more information about the DRIP protocol and the Location message format, refer to the ASTM F3411 specification.
"""

import drip_messages as common
import ctypes
import struct

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
    if Seconds_enc == common.DRIP_INV_TIMESTAMP:
        return common.DRIP_INV_TIMESTAMP
    else:
        return Seconds_enc / 10.0

class LocationDecoder:
    @staticmethod
    def decode_location(uas_data, raw_data):
        if not uas_data or not raw_data:
            return common.DRIP_FAIL

        if len(raw_data) < 25:
            return common.DRIP_FAIL

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

        # uas_data.Location.AltitudeBaro = unpacked_data[7]
        AltitudeBaro_bytes = raw_bytes[13:15]
        AltitudeBaro_value = struct.unpack("<H", AltitudeBaro_bytes)[0]
        uas_data.Location.AltitudeBaro = (AltitudeBaro_value * common.DRIP_ALT_DIV) - common.DRIP_ALT_ADDER

        AltitudeGeo_bytes = raw_bytes[15:17]
        AltitudeGeo_value = struct.unpack("<H", AltitudeGeo_bytes)[0]
        uas_data.Location.AltitudeGeo = (AltitudeGeo_value * common.DRIP_ALT_DIV) - common.DRIP_ALT_ADDER

        Height_bytes = raw_bytes[17:19]
        Height_value = struct.unpack("<H", Height_bytes)[0]
        uas_data.Location.Height = (Height_value * common.DRIP_ALT_DIV) - common.DRIP_ALT_ADDER

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

        uas_data.LocationValid = 1

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

        return common.DRIP_SUCCESS

