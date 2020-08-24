import sys
import os
import sys
import subprocess
# For (optional) GUI
import click
import quick_gui as quick
from resource_helper import resource_path


# Version info
# ============
VER_MAJOR = 1
VER_MINOR = 3       # J-Link commander console windows are now hidden (J-Link GUI dialogs and popups are still shown).
VER_SUBMINOR = 2    # Issue 'r' + 'SetPC 0x0' + 'go' when programming has finished.

# JLink command-line for KL27Z target attach:
# if sys.platform == 'linux':
if os.name == 'posix':
    JLINK_EXE_FILE = 'JLinkExe'
else:
    JLINK_EXE_FILE = 'JLink.exe'

# TODO: change in future to accomodate different devices??
JLINK_TARGET_OPTIONS = ['-device', 'MKL27Z256XXX4', '-if', 'SWD', '-speed', '4000', '-autoconnect', '1']
# (temporary) file names:
PRE_TASKS_CMD_FILE = "VV_pre_tasks.tmp.jlink"
BL_TASKS_CMD_FILE = "VV_bl_tasks.tmp.jlink"
FW1_TASKS_CMD_FILE = "VV_fw1_prog.tmp.jlink"
FW2_TASKS_CMD_FILE = "VV_fw2_prog.tmp.jlink"
POST_TASKS_CMD_FILE = "VV_post_tasks.tmp.jlink"
FW_PROG_CMD_FILE = "VV_fw_prog_cmdfile.tmp.jlink"
#
VERIFY_IMAGENUM_CMD_FILE = "VV_verify_imagenum.tmp.jlink"
VERIFY_SERNUM_CMD_FILE = "VV_verify_sernum.tmp.jlink"
#
DUMMY_TASKS_CMD_FILE = "VV_dummy_read.tmp.jlink"


use_gui = True
srec_path = None


def run_jlink_cmd_file(cmd_file_name, verbose=True):
    SUBPROC_RETVAL_STATUS_SUCCESS = 0
    status = False
    #
    cmd_with_args = []
    cmd_with_args.append(resource_path(JLINK_EXE_FILE))
    cmd_with_args.extend(JLINK_TARGET_OPTIONS)
    cmd_with_args.append(cmd_file_name)
    #
    print("Running: " + str(cmd_with_args))
    try:
        # if sys.plaform == 'win32':
        if os.name != 'posix':
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            startup_info.wShowWindow = subprocess.SW_HIDE
            #
            p1 = subprocess.Popen(cmd_with_args,
                                  shell=False,
                                  stdin=subprocess.DEVNULL,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  startupinfo=startup_info)
        else:
            p1 = subprocess.Popen(cmd_with_args,
                                  shell=False,
                                  stdin=subprocess.DEVNULL,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        # Run the command
        output = p1.communicate(timeout=30)[0]
    except subprocess.TimeoutExpired:
        print("ERROR: timeout from running J-Link!")
        return status

    lines = output.splitlines()
    lines_out = []
    for line in lines:
        line_str = line.decode('latin1', 'ignore')
        lines_out.append(line_str)
        if verbose:
            print(line_str)

    status = (p1.returncode == SUBPROC_RETVAL_STATUS_SUCCESS)
    #
    return status, lines_out


# ********************* Flash prog tasks **********************

def fw_pre_task(erase=True, cleanup=True, verbose=True, debug=False):
    status = False
    #
    with open(PRE_TASKS_CMD_FILE, 'w') as fp:
        fp.write("halt\n")
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


def fw_bl_prog(security=False, cleanup=True, verbose=True, debug=False):
    global srec_path
    #
    status = False
    #
    bootloader_srec = os.path.join(srec_path, "IrrigationSensorBootld.srec")
    if not os.path.exists(bootloader_srec):
        print(f"Could not write bootloader to Flash memory - SREC file '{bootloader_srec}' missing!", flush=True)
    else:
        print(f"Writing bootloader firmware '{bootloader_srec}' to boot Flash memory ...", flush=True)
        with open(BL_TASKS_CMD_FILE, 'w') as fp:
            fp.write("halt\n")
            fp.write("r\n")
            fp.write("loadfile %s\n" % bootloader_srec)
            fp.write("q\n")
        # Run JLink w. file input:
        if not debug:
            status, out_text = run_jlink_cmd_file(BL_TASKS_CMD_FILE)
        # Remove file if specified:
        if cleanup:
            try:
                os.remove(BL_TASKS_CMD_FILE)
            except OSError:
                pass
    #
    return status


def fw_app_prog(num=None, cleanup=True, verbose=True, debug=False):
    global srec_path
    #
    status = False
    if num == 1:
        file_name = FW1_TASKS_CMD_FILE
        fw_srec_name = "IrrigationSensorAppl_FW1.srec"
    elif num == 2:
        file_name = FW2_TASKS_CMD_FILE
        fw_srec_name = "IrrigationSensorAppl_FW2.srec"
    else:
        print("ERROR: must specify FW-number as 1 or 2!")
        return False
    # Add cmds:
    fw_name = os.path.join(srec_path, fw_srec_name)
    if not os.path.exists(fw_name):
        print(f"Could not write firmware no.{num} to Flash memory - SREC file '{fw_name}' missing!", flush=True)
    else:
        print(f"Writing firmware no.{num} ('{fw_name}') to main Flash memory ...", flush=True)
        with open(file_name, 'w') as fp:
            fp.write("halt\n")
            fp.write("r\n")
            fp.write("loadfile " + fw_name + "\n")
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


def fw_post_task(serial=None, cleanup=True, verbose=True, debug=False):
    status = False
    #
    with open(POST_TASKS_CMD_FILE, 'w') as fp:
        fp.write("halt\n")
        fp.write("r\n")
        fp.write("w4 0x5c00 0x00000001\n")              # Set image-number=1
        fp.write("w4 0x5c08 " + hex(serial) + "\n")      # Set serial number
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


def fw_prepare_target(erase=True, keep_serno=False, serial=0, cleanup=True, verbose=True, debug=False):
    status = False
    #
    with open(PRE_TASKS_CMD_FILE, 'w') as fp:
        fp.write("halt\n")
        fp.write("r\n")
        # If required, ERASE target ...
        if erase:
            fp.write("unlock Kinetis\n")      # Needed if device is programmed 1st time!
            fp.write("erase\n")
        # Set image-number =1(=FW1 startup as default):
        fp.write("w4 0x5c00 0x00000001\n")  # Set image-number=1
        # Default write given serial number into config-sector in Flash:
        if not keep_serno:
            if serial in range(1, 65355):
                fp.write("w4 0x5c08 " + hex(serial) + "\n")  # Set serial number
            else:
                print(f"Serial number = {serial} is OUT OF RANGE! Cannot use ...")
        # Readback config-values from Flash:
        fp.write("mem32 0x00005c00,1\n")
        fp.write("mem32 0x00005c08,1\n")
        fp.write("q\n")
    # Run JLink w. file input:
    if not debug:
        cmd_status, jlink_output = run_jlink_cmd_file(PRE_TASKS_CMD_FILE)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(PRE_TASKS_CMD_FILE)
        except OSError:
            pass
    #
    if cmd_status:
        # Verify image number:
        status = verify_image_number(out_text=jlink_output)
        # Verify serial number:
        do_serno_verification = not keep_serno
        serno_status, serial_num_read = verify_serial_number(out_text=jlink_output, verify=do_serno_verification, serial=serial)
        if not keep_serno:
            status = status and serno_status
        else:
            serial_num_read = serial
            status = False
    #
    return status, serial_num_read


def run_fw_programming(fw_type, cleanup=True, debug=False):
    #
    # Commit action:
    with open(FW_PROG_CMD_FILE, 'w') as fp:
        fp.write("halt\n")
        # fp.write("r\n")
        # Fill in step for FW1 if relevant:
        if fw_type == '1' or fw_type == 'all':
            fw1_srec = os.path.join(srec_path, "IrrigationSensorAppl_FW1.srec")
            if not os.path.exists(fw1_srec):
                print(f"Could not write FW1 to Flash memory - SREC file '{fw1_srec}' missing!",
                      flush=True)
            else:
                print(f"Writing FW1 firmware '{fw1_srec}' to boot Flash memory ...", flush=True)
                fp.write("loadfile %s\n" % fw1_srec)
        # Fill in step for FW2 if relevant:
        if fw_type == '2' or fw_type == 'all':
            fw2_srec = os.path.join(srec_path, "IrrigationSensorAppl_FW2.srec")
            if not os.path.exists(fw2_srec):
                print(f"Could not write FW2 to Flash memory - SREC file '{fw1_srec}' missing!",
                      flush=True)
            else:
                print(f"Writing FW2 firmware '{fw2_srec}' to boot Flash memory ...", flush=True)
                fp.write("loadfile %s\n" % fw2_srec)
        # Fill in step for BootLoader if relevant:
        if fw_type == 'bl' or fw_type == 'all':
            bootloader_srec = os.path.join(srec_path, "IrrigationSensorBootld.srec")
            if not os.path.exists(bootloader_srec):
                print(f"Could not write bootloader to Flash memory - SREC file '{bootloader_srec}' missing!",
                      flush=True)
            else:
                print(f"Writing bootloader firmware '{bootloader_srec}' to boot Flash memory ...", flush=True)
                fp.write("loadfile %s\n" % bootloader_srec)

        # Finalize:
        fp.write("rnh\n")
        fp.write("qc\n")
    # Run J-Link command scriptfile:
    status, jlink_output = run_jlink_cmd_file(FW_PROG_CMD_FILE)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(FW_PROG_CMD_FILE)
        except OSError:
            pass
    #
    return status


# ******************** FW verification ***********************************

def verify_image_number(out_text=None, img_num=1, verbose=True):
    status = False
    IMAGE_NUM_FLASH_ADDR = "00005C00"
    #
    print("")
    print("Output analysis:", flush=True)
    print("---------------------", flush=True)
    for line in out_text:
        if line.startswith(IMAGE_NUM_FLASH_ADDR):
            addr_content = line.split('=')[-1]      # First field is address, last field is value
            print(f"Content of address {IMAGE_NUM_FLASH_ADDR} = {addr_content}", flush=True)
            try:
                val = int(addr_content, 16)
                if val == img_num:
                    print(f"Readback-value={val} is equal to expected(={img_num}).", flush=True)
                    status = True
                else:
                    print(f"Readback-value={val} is equal to expected(={img_num}).", flush=True)
            except ValueError:
                print(f"{addr_content} is not a valid HEX-string!", flush=True)
    #
    return status


def verify_serial_number(out_text=None, verify=True, serial=0, verbose=True):
    status = False
    readout = serial
    SER_NUM_FLASH_ADDR = "00005C08"
    #
    print("")
    print("Output analysis:", flush=True)
    print("---------------------", flush=True)
    for line in out_text:
        if line.startswith(SER_NUM_FLASH_ADDR):
            addr_content = line.split('=')[-1]  # First field is address, last field is value
            print("Content of address %s = %s" % (SER_NUM_FLASH_ADDR, addr_content))
            try:
                val = int(addr_content, 16)
                if val == serial and 0 != serial:
                    print(f"Readback serno={val} is equal to expected(={serial}).", flush=True)
                    status = True
                else:
                    if verify:
                        print(f"Readback serno={val} is NOT equal to expected(={serial})!!", flush=True)
                    else:
                        status = True
                # Readback value:
                readout = val
            except ValueError:
                print(f"{addr_content} is not a valid HEX-string!", flush=True)
    #
    return status, readout


def fw_verify_imagenumber(img_num=1, cleanup=True, verbose=True):
    status = False
    IMAGE_NUM_FLASH_ADDR = "00005C00"
    #
    with open(VERIFY_IMAGENUM_CMD_FILE, 'w') as fp:
        fp.write("r\n")
        fp.write("mem32 0x00005c00,1\n")
        fp.write("q\n")
    # Run JLink w. file input:
    cmd_status, out_text = run_jlink_cmd_file(VERIFY_IMAGENUM_CMD_FILE)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(VERIFY_IMAGENUM_CMD_FILE)
        except OSError:
            pass
    #
    if cmd_status:
        print("")
        print("Output analysis:", flush=True)
        print("---------------------", flush=True)
        for line in out_text:
            if line.startswith(IMAGE_NUM_FLASH_ADDR):
                addr_content = line.split('=')[-1]      # First field is address, last field is value
                print("Content of address %s = %s" % (IMAGE_NUM_FLASH_ADDR, addr_content))
                try:
                    val = int(addr_content, 16)
                    if val == 1:
                        print("Readback-value=%s is equal to expected(=1)." % val)
                        status = True
                    else:
                        print("ERROR: Readback-value=%s is NOT equal to expected(=1)!" % val)
                except ValueError:
                    print("%s is not a valid HEX-string!")
    return status


def fw_verify_serialnumber(snum, cleanup=True, verbose=True):
    print("Running FW serial number verification ...", flush=True)
    status = False
    SER_NUM_FLASH_ADDR = "00005C08"
    #
    with open(VERIFY_SERNUM_CMD_FILE, 'w') as fp:
        fp.write("halt\n")
        fp.write("mem32 0x00005c08,1\n")
        # fp.write("rsettype 2\n")
        fp.write("rnh\n")
        # fp.write("g\n")       # Or, 'go' ...
        fp.write("qc\n")
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
        print("")
        print("Output analysis:", flush=True)
        print("---------------------", flush=True)
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
        fp.write("mem32 0x5c00,12\n")
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
            os.remove(DUMMY_TASKS_CMD_FILE)
        except OSError:
            pass
    #
    return status


def run_fw_verification(serial_num):
    #
    # Run (optional) dummy:
    # fw_dummy_task()
    #
    s1 = fw_verify_imagenumber()
    print("")
    print("")
    print("")
    s2 = fw_verify_serialnumber(snum=serial_num)
    #
    status = s1 and s2
    if status:
        print("FW-verification: PASS")
    else:
        print("FW-verification: FAIL!")
    #
    return status


# ******************** Generic stuff *************************************

# ------------------------------ Click setup -------------------------------
@click.command()
@click.option("--path",
              type=click.Path(file_okay=False, dir_okay=True),
              help="Path to folder containing *.SREC programming files",
              default=".")
@click.option("--serial",
              count=True,
              help="Sensor serial number")
@click.option("--fw_type",
              type=click.Choice(['all', '1', '2', 'bl']),
              default='all',
              help="Sensor FW: '1' = FW1, '2' = FW2, 'bl' = boot-loader, 'all' = bl + 1 + 2")
@click.option('--erase/--no_erase',
              default=True,
              help="Erase entire Flash memory before programming")
# The command itself:
def run_irrigation_sensor_programming(path, serial, fw_type, erase) -> bool:
    # NOTE: no doc-block here to avoid Quick picking it up and use for window title!
    #
    global srec_path
    #
    click.echo("Startup ...")
    # Run:
    click.echo(f"path={path}, fw_type={fw_type}, serial={serial}, erase={erase} ...")
    #
    if path is None or fw_type is None or serial is None or erase is None:
        raise Exception("Not all options specified!")
    elif fw_type not in ['all', '1', '2', 'bl']:
        raise Exception("Invalid value for FW-type argument!\nLegal values: '1', '2', 'bl', 'all' ")
    elif serial is None:
        raise Exception("No value given for serial number!\nLegal values: 1-65535")
    else:
        srec_path = path
        # Test only example:
        # ret_val = run_fw_programming(fw_type, serial_num, erase_flash_first, cleanup=False, debug=True)
        # Non-test environment:
        """
        status1 = fw_pre_task(erase=erase)    # Is ALWAYS used! ('s1' always gets assigned)
        status2 = fw_post_task(serial=serial)
        status3 = run_fw_verification(serial_num=serial)
        """
        status1 = fw_prepare_target(erase=erase, keep_serno=False, serial=serial)
        status4 = run_fw_programming(fw_type=fw_type)
        #
        # total_status = status1 and status2 and status3 and status4
        total_status = status1 and status4
        if total_status:
            quick.set_app_status(status='success')
        else:
            quick.set_app_status(status='error')
        #
        print("")
        print("")
        print("================================")
        #
        if total_status:
            print("PASS: successful programming.")
        else:
            print("FAIL: programming error!!")
        print("================================")
        print("")
    #
    print("Completed FW-programming.")
    #
    return total_status


# ***************** MAIN ************************

if __name__ == "__main__":
    prog_func = run_irrigation_sensor_programming
    prog_func.__setattr__("name", f"Irrigation Sensor Programming Tool ver.{VER_MAJOR}.{VER_MINOR}.{VER_SUBMINOR}")
    quick.gui_it(prog_func,
           run_exit=False,
           new_thread=False,
           style="qdarkstyle",
           output="gui",
           width=650,
           height=750,
           left=100,
           top=100)

