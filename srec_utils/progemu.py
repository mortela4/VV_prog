"""
@file progemu.py

@brief Emulates Flash program-memory of microcontroller.
The implementation is a bytearray.
"""

from srecutils import get_srec_addr_and_data
from CRCCCITT import CRCCCITT


ONE_KB = 1024
FLASH_SIZE = ONE_KB * 116                   # VV ver.1 has 116KB image-sizes


class ProgMem:
    def __init__(self, image_offset=0x6000, pmem_size=FLASH_SIZE, debug: bool = False):
        self.prog_mem = bytearray([0xFF]*pmem_size)
        self.prog_offset = image_offset       
        self.psize = pmem_size
        self.debug = debug                 

    def progmem_info(self):
        print(f"Progmem length: {len(self.prog_mem)} bytes ({len(self.prog_mem)/ONE_KB} KB)")

    def progmem_fill(self, val: int = 0xFF):
        self.prog_mem = bytearray([val]*self.psize)

    def progmem_erase(self):
        self.progmem_fill()

    def progmem_write(self, start_addr: int, data: bytearray):
        """
        @note 'prog_start_addr' is relative to offset=0 - therefore we need to subtract 'real' offset!
        """
        prog_start_addr = start_addr - self.prog_offset
        if prog_start_addr < 0:
            print(f"ERROR: START-address = 0x{start_addr:X} is below image-OFFSET = 0x{self.prog_offset:X}")
            raise ValueError
        #
        data_len = len(data)   # TODO: check data-length too!
        end_addr = prog_start_addr + (data_len - 1)
        #
        for i in range(data_len):
            self.prog_mem[prog_start_addr + i] = data[i]
        # DEBUG:
        if self.debug:
            print(f"Wrote {data_len} bytes to address range 0x{prog_start_addr:X} - 0x{end_addr:X}")
        #
        return data_len

    def progmem_crc(self) -> int:
        crc_calc = CRCCCITT()
        check_sum = crc_calc.calculate(self.prog_mem)
        return check_sum

    def progmem_load(self, filename: str):
        with open(filename, 'r') as srec_file:
            s_records = srec_file.readlines()
        # Program:
        total_bytes_programmed = 0
        for s_record in s_records:
            if s_record.startswith('S2'):                     # DATA-record (w. 24-bit address)?
                addr, data = get_srec_addr_and_data(s_record)
                total_bytes_programmed += self.progmem_write(addr, data)
        #
        print(f"\nFINISHED programming! Wrote {total_bytes_programmed} bytes to program memory.")



# ******************* TESTS **********************
if __name__ == "__main__":
    pmem = ProgMem(debug=True)
    pmem.progmem_info()
    print(f"Initial checksum: 0x{pmem.progmem_crc():X}")
    pmem.progmem_write( 0x6000, bytearray([0x0A, 0x0B, 0x0C]) )
    print(f"Second checksum: 0x{pmem.progmem_crc():X}")
    pmem.progmem_erase()
    print(f"Erased pmem checksum: 0x{pmem.progmem_crc():X}")
    pmem.progmem_load("srec_utils/FW1.srec")
    print(f"Programmed pmem checksum: 0x{pmem.progmem_crc():X}")
    # Must set new offset=0x23000 when using FW2:
    pmem = ProgMem(image_offset=0x23000, debug=True)
    print(f"Erased pmem checksum: 0x{pmem.progmem_crc():X}")
    pmem.progmem_load("srec_utils/FW2.srec")
    print(f"Programmed pmem checksum: 0x{pmem.progmem_crc():X}")
    #pmem.progmem_write( 0x5000, bytearray([0x0A, 0x0B, 0x0C]) )
    



