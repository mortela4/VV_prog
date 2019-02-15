import os
import subprocess


# ******************** GLOBALS ***********************

# MCU targets:
mcu_targets = {'kl16z64': ('MKL16Z64XXX4', 64),
               'kl16z128': ('MKL16Z128XXX4', 128),
               'kl16z256': ('MKL16Z256XXX4', 256),
               'kl25z64': ('MKL25Z64XXX4', 64),
               'kl25z128': ('MKL25Z128XXX4', 128),
               'kl25z256': ('MKL25Z256XXX4', 256),
               'kl26z64': ('MKL26Z64XXX4', 64),
               'kl26z128': ('MKL26Z128XXX4', 128),
               'kl26z256': ('MKL26Z256XXX4', 256),
               'kl27z64': ('MKL27Z64XXX4', 64),
               'kl27z128': ('MKL27Z128XXX4', 128),
               'kl27z256': ('MKL27Z256XXX4', 256)}

# Defaults:
fw_name = ''
mcu_name = 'kl16z256'
flash_offset_from_end = 4   # in no. of bytes - e.g: 128KB - 4bytes = address 0x3fffc

# JLink command-line for ML16Z target attach:
JLINK_EXE_FILE = 'JLink.exe'
# TODO: change in future to accomodate different devices??
JLINK_FIXED_TARGET_OPTIONS = ['-if', 'SWD', '-speed', '4000', '-autoconnect', '1']
# File names:
PRE_TASKS_CMD_FILE = "pre_tasks.tmp.jlink"
FWPROG_TASKS_CMD_FILE = "fw_prog.tmp.jlink"
POST_TASKS_CMD_FILE = "post_tasks.tmp.jlink"
#
VERIFY_SERNUM_CMD_FILE = "verify_sernum.tmp.jlink"
#
DUMMY_TASKS_CMD_FILE = "dummy_read.tmp.jlink"


# ******************* HELPERS ****************************
def get_mcu_device_specifics(mcu_type: str=None):
    if mcu_type is None:
        return None
    mcu_dev_name, mcu_flash_size = mcu_targets[mcu_type]
    #
    offset_address_numeric = (mcu_flash_size * 1024) - 4
    offset_address_hex = hex(offset_address_numeric)
    #
    return mcu_dev_name, offset_address_hex


def run_jlink_cmd_file(cmd_file_name, verbose=False):
    global mcu_name
    mcu_target = mcu_targets[mcu_name]
    #
    SUBPROC_RETVAL_STATUS_SUCCESS = 0
    status = False
    #
    cmd_with_args = list()
    cmd_with_args.append(JLINK_EXE_FILE)
    cmd_with_args.append('-device')
    cmd_with_args.append(mcu_target)
    cmd_with_args.extend(JLINK_FIXED_TARGET_OPTIONS)
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
    global fw_name
    # TODO: using globals affect testability - use arguments/locals instead!
    status = False
    # Add cmds:
    firmware_name = fw_name
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
    global mcu_name
    #
    status = False
    mcu_jlink_name, serno_flash_offset = get_mcu_device_specifics(mcu_type=mcu_name)
    if debug:
        print("Programming serial number into device '%s' at address=%s" % (mcu_jlink_name, serno_flash_offset))
    #
    with open(POST_TASKS_CMD_FILE, 'w') as fp:
        fp.write("r\n")
        fp.write("w4 " + serno_flash_offset + " " + hex(serial_number) + "\n")      # Set serial number
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


def run_fw_programming(serial_num, erase=True, cleanup=True, debug=False):
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
    global mcu_name
    #
    print("Running FW serial number verification ...", flush=True)
    status = False
    mcu_jlink_name, serno_flash_offset = get_mcu_device_specifics(mcu_type=mcu_name)
    SER_NUM_FLASH_ADDR = serno_flash_offset.lstrip('0x').upper()
    if verbose:
        print("Checking serial number of device '%s' at address=%s" % (mcu_jlink_name, SER_NUM_FLASH_ADDR))
    #
    with open(VERIFY_SERNUM_CMD_FILE, 'w') as fp:
        fp.write("r\n")
        fp.write("mem32 " + serno_flash_offset + ",1\n")
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


# ************************************ TESTING ****************************************
if __name__ == "__main__":
    mcudev, ofs = get_mcu_device_specifics(mcu_type=mcu_name)
    print("Got device specifics")
    print("=====================")
    print("MCU name: ", mcudev)
    print("Serial number offset address: %s (%s)" % (ofs, ofs.lstrip('0x').upper()))

