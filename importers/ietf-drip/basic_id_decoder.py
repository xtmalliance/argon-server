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

