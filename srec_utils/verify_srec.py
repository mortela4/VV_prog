# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 16:29:51 2018

@author: larsenm
"""

valid_record_types = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
data_record_types = valid_record_types[1:4]
type_to_address_length = {"S1": 4, "S2": 6, "S3": 8}


class VerifySrecord:
    """
    @brief Various checks for S-Record correctness.
    Assumes any type of S-Record,
    but with '\r' and \n' characters stripped from end of string.
    """

    def __init__(self, addr_range=None, srec_type=None, srec=None):
        global type_to_address_length
        #
        if addr_range is None:
            print("ERROR: class MUST be initialized with valid (min_addr,max_addr) tuple!")
        self.addr_min, self.addr_max = addr_range
        if srec_type is None:
            self.srec_type = "S2"  # Default type = S2
        else:
            self.srec_type = srec_type
        self.address_length = type_to_address_length[self.srec_type]
        self.srec = srec
        #
        self.srec_checks = [self.check_srec_format, self.check_srec_length, self.check_srec_address,
                            self.check_srec_crc]

    def calculate_crc(self):
        """
            Compute the checksum byte of a given S-Record
            Returns: The checksum as a string hex byte (ex: "0C")
        """
        # Get the summable data from srec
        # start at 2 to remove the S* record entry
        data = self.srec[2:len(self.srec) - 2]
        sum = 0
        # For each byte, convert to int and add.
        # (step each two character to form a byte)
        for position in range(0, len(data), 2):
            current_byte = data[position: position + 2]
            int_value = int(current_byte, 16)
            sum += int_value
        # Extract the Least significant byte from the hex form
        hex_sum = hex(sum)
        least_significant_byte = hex_sum[len(hex_sum) - 2:]
        least_significant_byte = least_significant_byte.replace('x', '0')
        # turn back to int and find the 8-bit one's complement
        int_lsb = int(least_significant_byte, 16)
        computed_checksum = (~int_lsb) & 0xff
        return computed_checksum

    def check_srec_format(self, debug=False):
        """
        Check if self.srec type is correct (either of 'S1', 'S2' or 'S3').
        """
        global valid_record_types
        global data_record_types
        failed_check = False
        srec_type = self.srec[0:2]
        if srec_type in valid_record_types:
            if debug:
                print("S-Record type: %s" % srec_type)
            if srec_type in data_record_types:
                if srec_type != self.srec_type:
                    failed_check = True
        else:
            failed_check = True
        return failed_check

    def check_srec_length(self, debug=False):
        """
        Check if data is of correct length.
        """
        failed_check = False
        # data = self.srec[4+self.address_length:-2]
        count = self.srec[2:4]
        # NOTE: data_len should be multiple of 2!
        data_len = int(count, 16)
        # NOTE: 'data_len' is number of 8-bit binary values, represented as CHARACTER PAIRS in the record!
        actual_len = int((len(self.srec) - 4) / 2)
        if debug:
            print("SRec length: ", data_len)
            print("Actual length: ", actual_len)
        if data_len != actual_len:
            print("LENGTH ERROR: mismatch between actual length = %s and specified length = %s" %
                  (actual_len, data_len))
            failed_check = True
        return failed_check

    def check_srec_address(self, debug=False):
        """
        Check if address is within allowed range.
        """
        failed_check = False
        adress = self.srec[4:4 + self.address_length]
        addr_val = int(adress, 16)
        if debug:
            print("Addres of SRecord: %s" % hex(addr_val))
        if addr_val < self.addr_min or addr_val > self.addr_max:
            print(
                "Invalid address: %s (valid range: %s to %s)" % (hex(addr_val), hex(self.addr_min), hex(self.addr_max)))
            failed_check = True
        return failed_check

    def check_srec_crc(self):
        """
        Check for CRC error.
        """
        failed_check = False
        crc = self.srec[-2:]
        crc_val = int(crc, 16)
        computed_crc = self.calculate_crc()
        if computed_crc != crc_val:
            print("CRC ERROR: calculated value = %s but SRec-value = %s !" % (computed_crc, crc_val))
            failed_check = True
        return failed_check

    def verify(self, srec=None, exit_on_first_error=False, debug=False):
        """
        Run check-methods on (presumed) SRecord data(string)='srec'.
        :param srec: 
        :param exit_on_first_error: 
        :param debug: 
        :return: pass='OK' fail='NAK'
        TODO: make 'debug' a class-property instead of a method argument!
        """
        if srec is None:
            if self.srec is None:
                return "NAK"
        else:
            self.srec = srec
        #
        res = "OK"
        for failCheck in self.srec_checks:
            if debug:
                print("Running check: %s" % failCheck.__name__)
            if failCheck():
                print("FAIL! Failed check: %s" % failCheck.__name__.upper())
                res = "NAK"
                if exit_on_first_error:
                    break
        return res


# ************** TEST *********************
if __name__ == "__main__":
    #
    # Flash address range:
    MIN_ADDR = 0x6000
    MAX_ADDR = 0x3FFFF
    #
    # Define test input for S2:
    SREC2_OK_EXAMPLE = "S21400B0206C20746861742074726F75626C6520742D"
    SREC2_FAIL_CRC = "S21400B0206C20746861742074726F75626C6520742C"
    SREC2_FAIL_FORMAT1 = "S11400B0206C20746861742074726F75626C6520742D"
    SREC2_FAIL_FORMAT2 = "AB1400B0206C20746861742074726F75626C6520742D"
    SREC2_FAIL_LENGTH = "S21300B0206C20746861742074726F75626C6520742D"
    SREC2_FAIL_ADDR_LO = "S214005AAA6C20746861742074726F75626C6520742D"
    SREC2_FAIL_ADDR_HI = "S2143C00006C20746861742074726F75626C6520742D"
    #
    """
    print(calculate_crc(SREC_OK_EXAMPLE, debug=True))
    print(calculate_crc(SREC_FAIL_CRC, debug=True))
    """
    #
    valid_addr_range = (MIN_ADDR, MAX_ADDR)
    #
    UUT = VerifySrecord(addr_range=valid_addr_range, srec_type="S2")
    #
    print("Running S2 SRecord checks ...")
    print("=============================")
    #
    print(UUT.verify(SREC2_OK_EXAMPLE))
    print(UUT.verify(SREC2_FAIL_CRC))
    print(UUT.verify(SREC2_FAIL_FORMAT1))
    print(UUT.verify(SREC2_FAIL_FORMAT2))
    print(UUT.verify(SREC2_FAIL_LENGTH))
    print(UUT.verify(SREC2_FAIL_ADDR_LO))
    print(UUT.verify(SREC2_FAIL_ADDR_HI))
    #
    # Define test input for S3:
    SREC3_OK_EXAMPLE = "S30D0003C0000F0000000000000020"
    SREC3_FAIL_CRC = "S30D0003C0000F0000000000000021"
    SREC3_FAIL_FORMAT1 = "S20D0003C0000F0000000000000020"
    SREC3_FAIL_FORMAT2 = "AB0D0003C0000F0000000000000020"
    SREC3_FAIL_LENGTH = "S30E0003C0000F0000000000000020"
    SREC3_FAIL_ADDR_LO = "S30D000005AAAF0000000000000020"
    SREC3_FAIL_ADDR_HI = "S30D000040000F0000000000000020"
    #
    UUT = VerifySrecord(addr_range=valid_addr_range, srec_type="S3")
    #
    print("Running S3 SRecord checks ...")
    print("=============================")
    #
    print(UUT.verify(SREC3_OK_EXAMPLE))
    print(UUT.verify(SREC3_FAIL_CRC))
    print(UUT.verify(SREC3_FAIL_FORMAT1))
    print(UUT.verify(SREC3_FAIL_FORMAT2))
    print(UUT.verify(SREC3_FAIL_LENGTH))
    print(UUT.verify(SREC3_FAIL_ADDR_LO))
    print(UUT.verify(SREC3_FAIL_ADDR_HI))


