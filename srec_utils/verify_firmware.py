#!/usr/bin/python3

#  -*- coding: utf-8 -*-
"""
@file verify_firmware.py

Created on Wed Apr 26 13:04:38 2017

@todo Create class w. below functions embedded.

@author: ml
"""

from .srecutils import parse_srec


class FirmwareVerify:
    """ Firmware Updater client """
    firmware = None
    raw_data = []
    status = False
    current_address = 0
    current_rtype = 0   # 0=S0, 1=S1 and so on ...
    chunk_no = 0 
    srec_no = 0
    srec_props = None
    #
    def __init__(self, data, props=None):
        self.srec_props = props
    #
    def check_srec(self, byte_chunk):
        srec = list(byte_chunk)
        chk = False
        print("S-record no.%s: %s" % (self.srec_no, srec))
        print("-----------------")
        # SRecord parsing:
        # ===============
        # rtype = 2 bytes
        # data_len = 1 byte
        # addr = 2-4 bytes (depending on rtype)
        # data 0-255 bytes
        # checksum = 1 byte
        # -----------------
        record_type, data_len, addr, data, checksum = parse_srec(srec)
        print("Record type: %s" % record_type)
        print("Data length: %s" % data_len)
        print("Address: %s" % addr)
        print("Data: %s" % data)
        print("Checksum(Rx): %s" % checksum)
        # TODO: print calculated checksum ...
        print("-----------------\n")
        # may set 'status' depending on several criteria ...
        return chk

    #
    def verify_chunk(self, byte_chunk):
        self.raw_data += byte_chunk
        #
        arr = bytearray()
        # Traverse all bytes in chunk - build up all complete S-Records
        for byte in byte_chunk:
            # SRecords are separated by newline - file origin could mean only '\n'(POSIX) or '\r'+'\n'(WinXX)
            if byte == 0xa or byte == 0xd:
                if len(self.raw_data)>0:
                    #chk = self.check_srec( str(arr, encoding='ascii') )
                    chk = self.check_srec(arr)
                    if chk:
                        self.status = self.emulate_firmware_flashing(arr, 0)
                    else:
                        self.status = chk
                    arr.clear()
                    self.srec_no += 1
            else:
                arr.append(byte)
        #
        self.chunk_no += 1
        # 'arr' typically contain a partial SRecord as a remainder from the byte-chunk:
        self.raw_data = arr   
    #

    def emulate_firmware_flashing(srec, prev_addr):
        status = True
        # Flash logic:
        return status






