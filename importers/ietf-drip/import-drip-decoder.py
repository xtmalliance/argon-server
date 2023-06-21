"""
This script imports the DRIP decoder module and perform decoding operations on DRIP messages.

The script provides the following functionalities:
- Importing the necessary DRIP decoder modules: basic_id_decoder, location_decoder, auth_decoder, operator_id_decoder, self_id_decoder, system_decoder.
- Decoding DRIP messages using the imported decoder modules.
- Printing the decoded information from DRIP messages.

Usage:
------
1. Ensure that the DRIP decoder modules (basic_id_decoder, location_decoder, auth_decoder, operator_id_decoder, self_id_decoder, system_decoder) are present in the same directory as this script.

2. Prepare a raw file containing DRIP messages, with each message in a separate line.

3. Set the 'file_path' variable to the path of the file containing DRIP messages.

4. Run the script.

Example:
--------

python3 import-drip-decoder.py '/opt/rid-test-vectors'

Note: This script requires the 'drip_messages' module and the DRIP decoder modules to be present in the same directory.

For more information about the DRIP protocol and the message decoding process, refer to the DRIP specification and the individual decoder modules.
"""

import drip_messages as common
from basic_id_decoder import BasicIDDecoder
from location_decoder import LocationDecoder
from auth_decoder import AuthDecoder
from self_id_decoder import SelfIDDecoder
from system_decoder import SystemDecoder
from operator_id_decoder import OperatorIDDecoder
import struct
import ctypes
import argparse
import os

def decode_drone_id(uas_data, raw_data):
    if not uas_data or not raw_data:
        return common.DRIP_FAIL

    message_size = len(raw_data)

    if common.DRIP_MESSAGE_SIZE <= message_size:
        msg_type = raw_data[0] >> 4
        message_type_bytes = struct.pack('B', raw_data[0])

        if msg_type == common.DRIP_MESSAGE_BASIC_ID:
            print("DRIP_MESSAGE_BASIC_ID")
            # Decode basic ID message
            BasicIDDecoder.decode_basic_id(uas_data, raw_data[:common.DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == common.DRIP_MESSAGE_LOCATION:
            print("DRIP_MESSAGE_LOCATION")
            # Decode location message
            LocationDecoder.decode_location(uas_data, raw_data[:common.DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == common.DRIP_MESSAGE_AUTH:
            print("DRIP_MESSAGE_AUTH")
            # Decode authentication message
            AuthDecoder.decode_authentication(uas_data, raw_data[:common.DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == common.DRIP_MESSAGE_SELF_ID:
            print("DRIP_MESSAGE_SELF_ID")
            # Decode self ID message
            SelfIDDecoder.decode_self_id(uas_data, raw_data[:common.DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == common.DRIP_MESSAGE_SYSTEM:
            print("DRIP_MESSAGE_SYSTEM")
            # Decode system message
            SystemDecoder.decode_system(uas_data, raw_data[:common.DRIP_MESSAGE_SIZE])
            print("*********************")

        elif msg_type == common.DRIP_MESSAGETYPE_OPERATOR_ID:
            print("DRIP_MESSAGE_OPERATOR_ID")
            # Decode operator id message
            OperatorIDDecoder.decode_operatorid(uas_data, raw_data[:common.DRIP_MESSAGE_SIZE])
            print("*********************")

        else:
            return common.DRIP_FAIL

    return common.DRIP_SUCCESS


def decode_message_pack(uas_data, pack, data):
    if not uas_data or not pack or pack.MessageType != common.DRIP_MESSAGETYPE_PACKED:
        decode_drone_id(uas_data, data)
        return common.DRIP_SUCCESS

    if pack.SingleMessageSize != common.DRIP_MESSAGE_SIZE:
        return common.DRIP_FAIL

    for i in range(pack.MsgPackSize):
        if common.DRIP_DEBUG:
            print("Raw Data:", ' '.join([hex(byte) for byte in pack.Messages[i].rawData[:common.DRIP_MESSAGE_SIZE]]))
        decode_drone_id(uas_data, pack.Messages[i].rawData)

    return common.DRIP_SUCCESS


def decodeMessagePack(data):
    uasData = common.DRIP_UAS_Data()
    pack = common.DRIP_MessagePack_encoded()
    ctypes.memmove(ctypes.addressof(pack), data, ctypes.sizeof(pack))
    ret = decode_message_pack(uasData, pack, data)

    return uasData


if __name__ == '__main__':

    # Create an argument parser
    parser = argparse.ArgumentParser(description='DRIP Test Decoder')
    #parse rid test vector path ex: '/opt/rid-test-vectors'
    parser.add_argument('file_path', type=str, help='Path to the file containing DRIP test vectors')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Get the file path from the command-line arguments
    file_path = args.file_path

    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        exit(1)

    with open(file_path) as file:
        for line in file:
            dri_bytes = bytes.fromhex(line)
            if common.DRIP_CUSTOM:
                msg = decodeMessagePack(dri_bytes[1:])
                print("++++++++++++++++++++++++++++++++++++++++")
            else:
                msg = decodeMessagePack(dri_bytes)

