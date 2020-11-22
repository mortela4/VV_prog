"""
@file progemu.py

@brief Emulates Flash program-memory of microcontroller.
The implementation is a bytearray.
"""

import srecutils
from CRCCCITT import CRCCCITT


ONE_KB = 1024
FLASH_SIZE = ONE_KB * 116                   # VV ver.1 has 116KB image-sizes

prog_mem = bytearray([0xFF]*FLASH_SIZE)
prog_offset = 0x6000                        # TODO: support FW1-offset also (or *any* offset)


def progmem_info():
    print(f"Progmem length: {len(prog_mem)} bytes ({len(prog_mem)/ONE_KB} KB)")


def progmem_write(start_addr: int, data: bytearray):
    """
    @note 'prog_start_addr' is relative to offset=0 - therefore we need to subtract 'real' offset!
    """
    prog_start_addr = start_addr - prog_offset
    if prog_start_addr < 0:
        print(f"ERROR: START-address = 0x{start_addr:X} is below image-OFFSET = 0x{prog_offset:X}")
        raise ValueError
    #
    data_len = len(data)   # TODO: check data-length too!
    #
    for i in range(data_len):
        prog_mem[prog_start_addr + i] = data[i]
    # DEBUG:

def progmem_crc() -> int:
    crc_calc = CRCCCITT()
    check_sum = crc_calc.calculate(prog_mem)
    return check_sum


# ******************* TESTS **********************
if __name__ == "__main__":
    progmem_info()
    print(f"Initial checksum: 0x{progmem_crc():X}")
    progmem_write(0x6000, bytearray([0x0A, 0x0B, 0x0C]) )
    print(f"Second checksum: 0x{progmem_crc():X}")
    progmem_write(0x5000, bytearray([0x0A, 0x0B, 0x0C]) )



