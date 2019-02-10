import argparse
import sys
#
from FW_prog.fwprog import mcu_targets, run_fw_programming, run_fw_verification


# ******************** Generic stuff *************************************
def parse_args_and_execute():
    """ Parse args and run bg-process(es) """
    global fw_path
    global fw_name
    global mcu_name
    #
    parser = argparse.ArgumentParser(description="'fwprogcli' command-line utility.\r\n \
                                                     Pre-requisites: FW-file (.srec or .hex) must reside in run-folder.")
    parser.add_argument('--path', '-p', action="store", dest="fw_dir", type=str, help='FW pathname')
    # Std.args NOT needing 'special handling':
    parser.add_argument('--serial', '-s', action="store", dest="ser_num", type=int,
                        help='Serial number to be programmed into upper 4 bytes of Flash')
    parser.add_argument('--fw', action="store", dest="fw_name", type=str, default="firmware.hex",
                        help="Firmware HEX/SREC file name (default: 'firmware.hex')")
    parser.add_argument('--device', '-d', action="store", dest="mcu_name", type=str, default="kl16z256",
                        help='MCU device type: kl16z64, kl16z128, kl16z256, kl25z64, kl25z128, kl25z256, kl26z64, kl26z128, kl26z256, kl27z64, kl27z128, kl27z256')
    parser.add_argument('--erase', '-e', action="store", dest="erase_first", type=str, default="yes",
                        help='Erase target Flash before programming')

    cli_args = parser.parse_args(sys.argv[1:])
    # Assign program arguments to variables:
    # ======================================
    # FW directory:
    if cli_args.fw_dir is None:
        print("Using '.' for default firmware-path ...")
    else:
        fw_path = cli_args.fw_dir
        print("Using %s as firmware-path ..." % fw_path)
    # FW serial number:
    if cli_args.ser_num is None:
        print("Argument '-s' ('--serial') is required - a serial number MUST be specified!")
        sys.exit(1)
    else:
        serial_num = cli_args.ser_num
    # FW file name:
    if cli_args.fw_name is None:
        # Should NEVER happen - maybe simplify this?
        print("Using 'firmware.hex' for default firmware-name ...")
        fw_name = 'firmware.hex'   # TODO: assess - rather have this as required field???
    else:
        fw_name = cli_args.fw_name
        print("Using %s as firmware-name ..." % fw_name)
    # MCU device:
    if cli_args.mcu_name is None:
        # Should NEVER happen - maybe simplify this?
        print("Using 'kl16z256' for default MCU device-name ...")
        mcu_name = 'kl16z256'   # TODO: assess - rather have this as required field???
    else:
        fw_name = cli_args.fw_name
        print("Using %s as firmware-name ..." % fw_name)
    # Erase (via MassErase) target Flash first or not:
    erase_flash_first = cli_args.erase_first

    # Run:
    if erase_flash_first not in ['yes', 'no']:
        print("Invalid value for '--erase' option!\nLegal values: 'yes' or 'no' ")
        sys.exit(1)
    else:
        # Test only:
        # ret_val = run_fw_programming(fw_name, serial_num, erase_flash_first, cleanup=False, debug=True)
        # Non-test environment:
        status1 = run_fw_programming(fw_name, serial_num, erase_flash_first)
        status2 = run_fw_verification(serial_num)
        #
        print("\r\n\r\n================================")
        if status1 and status2:
            print("PASS: successful programming.")
        else:
            print("FAIL: programming error!!")
        print("================================\r\n")
    #
    print("Completed FW-programming.")


# ***************** MAIN ************************
if __name__ == "__main__":
    parse_args_and_execute()







