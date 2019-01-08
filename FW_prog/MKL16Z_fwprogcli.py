import sys
import os
import argparse
import subprocess



# JLink command-line for ML16Z target attach:
JLINK_EXE_FILE = 'JLink.exe'
# TODO: change in future to accomodate different devices??
JLINK_TARGET_OPTIONS = ['-device', mcu_targets[mcu_name], '-if', 'SWD', '-speed', '4000', '-autoconnect', '1']
# File names:
PRE_TASKS_CMD_FILE = "pre_tasks.tmp.jlink"
FWPROG_TASKS_CMD_FILE = "fw_prog.tmp.jlink"
POST_TASKS_CMD_FILE = "post_tasks.tmp.jlink"
#
VERIFY_SERNUM_CMD_FILE = "verify_sernum.tmp.jlink"
#
DUMMY_TASKS_CMD_FILE = "dummy_read.tmp.jlink"


# MCU targets:
mcu_targets = {'kl16z64': 'MKL16Z64XXX4',
               'kl16z128': 'MKL16Z128XXX4',
               'kl16z256': 'MKL16Z256XXX4',
               'kl25z64': 'MKL25Z64XXX4',
               'kl25z128': 'MKL25Z128XXX4',
               'kl25z256': 'MKL25Z256XXX4',
               'kl26z64': 'MKL26Z64XXX4',
               'kl26z128': 'MKL26Z128XXX4',
               'kl26z256': 'MKL26Z256XXX4',
               'kl27z64': 'MKL27Z64XXX4',
               'kl27z128': 'MKL27Z128XXX4',
               'kl27z256': 'MKL27Z256XXX4'}

# Defaults:
fw_path = '.'
fw_name = 'firmware.hex'
mcu_name = 'kl16z256'


def run_jlink_cmd_file(cmd_file_name, verbose=False):
    SUBPROC_RETVAL_STATUS_SUCCESS = 0
    status = False
    #
    cmd_with_args = list()
    cmd_with_args.append(JLINK_EXE_FILE)
    cmd_with_args.extend(JLINK_TARGET_OPTIONS)
    cmd_with_args.append(cmd_file_name)
    #
    print("Running: " + str(cmd_with_args))
    try:
        p1 = subprocess.Popen(cmd_with_args, stdout=subprocess.PIPE)
        # Run the command
        output = p1.communicate(timeout=30)[0]
    except subprocess.TimeoutExpired:
        print("ERROR: timeout from running J-Link!")
        return status

    lines = output.splitlines()
    lines_out = []
    for line in lines:
            line_str = str(line, encoding='utf-8')
            lines_out.append(line_str)
            if verbose:
                print(line_str)

    status = (p1.returncode == SUBPROC_RETVAL_STATUS_SUCCESS)
    #
    return status, lines_out


# ********************* Flash prog tasks **********************

def fw_pre_task(erase=True, cleanup=True, debug=False):
    status = False
    #
    with open(PRE_TASKS_CMD_FILE, 'w') as fp:
        fp.write("r\n")
        if erase:
            fp.write("unlock Kinetis\n")      # Needed if device is programmed 1st time!
            fp.write("erase\n")
        fp.write("q\n")
    # Run JLink w. file input:
    if not debug:
        status, out_text = run_jlink_cmd_file(PRE_TASKS_CMD_FILE)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(PRE_TASKS_CMD_FILE)
        except OSError:
            pass
    #
    return status


def fw_app_prog(cleanup=True, debug=False):
    global fw_path
    global fw_name
    # TODO: using globals affect testability - use arguments/locals instead!
    status = False
    # Add cmds:
    firmware_name = fw_path + "\\" + fw_name
    #
    file_name = FWPROG_TASKS_CMD_FILE
    with open(file_name, 'w') as fp:
        fp.write("r\n")
        fp.write("loadfile " + firmware_name + "\n")
        fp.write("q\n")
    # Run JLink w. file input:
    if not debug:
        status, out_text = run_jlink_cmd_file(file_name)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(file_name)
        except OSError:
            pass
    #
    return status


def fw_post_task(serial_number=None, cleanup=True, debug=False):
    status = False
    #
    with open(POST_TASKS_CMD_FILE, 'w') as fp:
        fp.write("r\n")
        fp.write("w4 0x3fffc " + hex(serial_number) + "\n")      # Set serial number
        fp.write("q\n")
    # Run JLink w. file input:
    if not debug:
        status, out_text = run_jlink_cmd_file(POST_TASKS_CMD_FILE)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(POST_TASKS_CMD_FILE)
        except OSError:
            pass
    #
    return status


def run_fw_programming(firmware_name, serial_num, erase=True, cleanup=True, debug=False):
    #
    s1 = fw_pre_task(erase=erase, cleanup=cleanup, debug=debug)
    s2 = fw_app_prog(cleanup=cleanup, debug=debug)
    s3 = fw_post_task(serNo=serial_num, cleanup=cleanup, debug=debug)
    #
    status = s1 and s2 and s3
    #
    return status


# ******************** verification ***********************************
def fw_verify_serial_number(snum, cleanup=True, verbose=False):
    print("Running FW serial number verification ...", flush=True)
    status = False
    SER_NUM_FLASH_ADDR = "0003FFFC"
    #
    with open(VERIFY_SERNUM_CMD_FILE, 'w') as fp:
        fp.write("r\n")
        fp.write("mem32 0x0003fffc,1\n")
        fp.write("q\n")
    # Run JLink w. file input:
    cmd_status, out_text = run_jlink_cmd_file(VERIFY_SERNUM_CMD_FILE)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(VERIFY_SERNUM_CMD_FILE)
        except OSError:
            pass
    #
    if verbose:
        print("Cmd-output:", flush=True)
        for txt in out_text:
            print(txt)
    #
    if cmd_status:
        print("\r\nOutput analysis:", flush=True)
        print("----------------", flush=True)
        for line in out_text:
            if line.startswith(SER_NUM_FLASH_ADDR):
                addr_content = line.split('=')[-1]      # First field is address, last field is value
                print("Content of address %s = %s" % (SER_NUM_FLASH_ADDR, addr_content))
                try:
                    val = int(addr_content, 16)
                    if val == snum:
                        print("Readback-value=%s is equal to given serial number." % val)
                        status = True
                    else:
                        print("ERROR: Readback-value=%s is NOT equal to given serial number(=snum)." % val)
                except ValueError:
                    print("%s is not a valid HEX-string!")    #
    return status


def fw_dummy_task(cleanup=True, debug=False, verbose=True):
    status = False
    #
    with open(DUMMY_TASKS_CMD_FILE, 'w') as fp:
        fp.write("r\n")
        fp.write("mem32 0x3fffc,1\n")
        fp.write("q\n")
    # Run JLink w. file input:
    if not debug:
        status, out_text = run_jlink_cmd_file(DUMMY_TASKS_CMD_FILE)
    if verbose:
        for line in out_text:
            print(line)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(POST_TASKS_CMD_FILE)
        except OSError:
            pass
    #
    return status


def run_fw_verification(serial_num):
    #
    # Run dummy first:
    fw_dummy_task()
    print("\r\n\r\n")
    status = fw_verify_serial_number(snum=serial_num)
    #
    if status:
        print("FW-verification: PASS")
    else:
        print("FW-verification: FAIL!")
    #
    return status


# ******************** Generic stuff *************************************

def parse_args_and_execute():
    """ Parse args and run bg-process(es) """
    global fw_path
    global fw_name
    global mcu_name
    #
    parser = argparse.ArgumentParser(description="'MKL16Z_fwprogcli' command-line utility.\r\n \
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







