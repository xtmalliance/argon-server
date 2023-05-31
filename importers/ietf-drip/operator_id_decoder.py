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

