import sys
from gooey import Gooey, GooeyParser
#
from FW_prog.fwprog import mcu_targets, run_fw_programming, run_fw_verification


# ******************** Generic stuff *************************************


def parse_args_and_execute():
    """ Parse args and run bg-process(es) """
    global fw_name
    global mcu_name
    #
    parser = GooeyParser()
    #
    # Std.args NOT needing 'special handling':
    id_group = parser.add_argument_group(
        "System ID Options",
        "Customize product ID, serial number etc."
    )
    id_group.add_argument('--serial', '-s',
                        action="store",
                        dest="ser_num",
                        type=int,
                        help='Serial number to be programmed into upper 4 bytes of Flash',
                        gooey_options={
                            'height': 100,
                            'full_width': 10,
                            'hide_heading': True,
                            'columns': 1-100,
                        })
    fw_group = parser.add_argument_group(
        "Firmware Options",
        "Choose FW etc."
    )
    fw_group.add_argument('--fw',
                        action="store",
                        dest="fw_name",
                        type=str,
                        default="",
                        widget='FileChooser',
                        help="Firmware HEX/SREC file name (default: 'firmware.hex')",
                        gooey_options={
                            'height': 100,
                            'hide_heading': True,
                            'columns': 1-100,
                        })
    #
    device_group = parser.add_argument_group(
        "Device Options",
        "Choose MCU type etc."
    )
    mcu_types_list = list(mcu_targets.keys())
    device_group.add_argument('--device', '-d',
                        action="store",
                        dest="mcu_name",
                        choices=mcu_types_list,
                        type=str,
                        default="kl16z256",
                        widget='Dropdown',
                        help='Kinetis KL-family MCU type.',
                        gooey_options={
                            'height': 100,
                            'width': 8,
                            'hide_heading': True,
                            'columns': 1,
                        })
    #
    flash_group = parser.add_argument_group(
        "Flash Options",
        "Erase-before-program etc."
    )
    flash_group.add_argument("-e", "--erase",
                        action="store_true",
                        dest="erase_first",
                        default=True,
                        widget='CheckBox',
                        help='Erase target (completely) before programming',
                        gooey_options={
                            'height': 100,
                            'hide_heading': True,
                            'columns': 1,
                        })
    #
    cli_args = parser.parse_args(sys.argv[1:])
    # Assign program arguments to variables:
    # ======================================
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
        fw_name = 'firmware.hex'  # TODO: assess - rather have this as required field???
    else:
        fw_name = cli_args.fw_name
        print("Using %s as firmware-name ..." % fw_name)
    # MCU device:
    if cli_args.mcu_name is None:
        # Should NEVER happen - maybe simplify this?
        print("Using 'kl16z256' for default MCU device-name ...")
        mcu_name = 'kl16z256'  # TODO: assess - rather have this as required field???
    else:
        mcu_name = cli_args.mcu_name
        print("Using %s as MCU-name ..." % mcu_name)
    # Erase (via MassErase) target Flash first or not:
    erase_flash_first = cli_args.erase_first

    # Run:
    # ====
    # Test only:
    # ----------
    # ret_val = run_fw_programming(fw_name, serial_num, erase_flash_first, cleanup=False, debug=True)
    # ----------
    # Non-test environment:
    # ---------------------
    status1 = run_fw_programming(fw_name, serial_num, erase_flash_first)
    status2 = run_fw_verification(serial_num)
    #
    print("\r\n\r\n================================")
    if status1 and status2:
        print("PASS: successful programming.", flush=True)
    else:
        print("FAIL: programming error!!", flush=True)
    print("================================\r\n", flush=True)
    #
    print("Completed FW-programming.", flush=True)


@Gooey(advanced=True,
       program_name="Kinetis FW-Programming GUI",
       default_size=(600, 800),
       optional_cols=1,
       run_validators=True)
def gui_wrapper():
    parse_args_and_execute()


# ***************** MAIN ************************
if __name__ == "__main__":
    gui_wrapper()








