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

