import sys
import os
import sys
import time
import subprocess
# For (optional) GUI
import click
import quick_gui as quick
from resource_helper import resource_path


# Version info
# ============
VER_MAJOR = 1
VER_MINOR = 6       # Choosing between sensor-types (so far AA, or AB) is now an option.
VER_SUBMINOR = 2    # Fix: closed issue#2 = handling 'target-prepare' for 'AB'-type sensor w. K32L2A41 MCU (setting imgNum=1 and serialNo in CONFI-sector of Flash).    

# JLink command-line for KL27Z target attach:
# if sys.platform == 'linux':
if os.name == 'posix':
    JLINK_EXE_FILE = 'JLinkExe'
else:
    JLINK_EXE_FILE = 'JLink.exe'

# Generic Flash-definitions (CONFIG-sector only --> firmware-adresses are all contained in SREC):
CONFIG_SECTOR_IMAGENUM_OFFSET = 0       # Occupies 4 bytes - signifies whether FW1 or FW2 shall be started by bootloader
CONFIG_SECTOR_UPGBIT_OFFSET = 4         # Occupies 4 bytes (even though only bit0 from LSB is used to signify an upgrade=FOTA to be performed by bootloader)
CONFIG_SECTOR_SERIALNO_OFFSET = 8       # 2 doublewords for IMAGENUM(=field no.0) and UPG(=field no.1) fields respectively, correspond to 8 bytes offset before field no.2 = SERNO

# 'AA'-type sensor definitions:
IRRIGATION_SENSOR_REV_AA_MCU = 'MKL27Z256XXX4'
IRRIGATION_SENSOR_REV_AA_CONFIG_START = 0x00005C00   # Max. bootloader size is 23KB --> FW1 starts at 23+1 = 24KB = 0x6000 offset (CONFIG=1KB)
# 'AB'-type sensor definitions:
IRRIGATION_SENSOR_REV_AB_MCU = 'K32L2A41XXXXA'
IRRIGATION_SENSOR_REV_AB_CONFIG_START = 0x00008C00   # Max. bootloader size is 35KB --> FW1 starts at 35+1 = 36KB = 0x9000 offset (CONFIG=1KB)

JLINK_TARGET_MCU_OPTION_IDX = 1   # Relates to position in list below. TODO: rather use dictionary?
JLINK_TARGET_OPTIONS = ['-device', IRRIGATION_SENSOR_REV_AA_MCU, '-if', 'SWD', '-speed', '4000', '-autoconnect', '1']     # Default: assume 'rev.AA' sensor = KL27Z256 MCU

MAP_SENSOR_TYPE_TO_MCU = { 'AA': IRRIGATION_SENSOR_REV_AA_MCU,
                            'AB': IRRIGATION_SENSOR_REV_AB_MCU}
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
        return status, None

    lines = output.splitlines()
    lines_out = []
    for line in lines:
        line_str = line.decode('latin1', 'ignore')
        lines_out.append(line_str)
        if verbose:
            print(line_str)
        # Check for J-Link NOT connected, or connection problems:
        if line_str.startswith("Cannot connect to target") or line_str.startswith("Connecting to J-Link via USB...FAILED"):
            return status, lines_out
        # Check for WRITE-errors:
        if line_str.startswith("Could not write"):
            return status, lines_out
        # Check for 'Error'/'ERROR' in output:
        if line_str.find('Error') > 0 or line_str.find('ERROR') > 0:
            return status, lines_out
        # Check for 'Error'/'ERROR' in output:
        if line_str.find('Error') > 0 or line_str.find('ERROR') > 0:
            return status, lines_out
    # If 'normal' output - or NO output at all - the return value is used to decide 'status':
    status = (p1.returncode == SUBPROC_RETVAL_STATUS_SUCCESS)
    #
    return status, lines_out


# ********************* FRAM erase task ***********************
def vv_fram_erase(cleanup=True, verbose=True, debug=False):
    """
    Erase FRAM on irrigation-sensor target (VV).
    Note that erase-application START-address is NOT equal to RAM-startaddr!
    Instead, the 'ResetISR' symbol is located 212 bytes ABOVE the vector table, at addr=0x1FFFE0D4.
    """
    FRAM_ERASE_JLINK_CMD_FILE = "FRAM_erase.tmp.jlink"
    FRAM_ERASE_APP_SREC = resource_path("VV_FRAM_eraser.srec")      # TODO: must have a separate, K32L-specific application(=SREC) in order to erase FRAM on 'AB'-type!!
    FRAM_ERASE_APP_START_ADDR = 0x1FFFE0D4                          # NOTE: location of '.init' symbol read from .MAP-file --> app loaded in SRAM!
    #
    with open(FRAM_ERASE_JLINK_CMD_FILE, 'w') as fp:
        fp.write("halt\n")
        fp.write("r\n")
        fp.write(f"loadfile {FRAM_ERASE_APP_SREC}\n")
        fp.write(f"setpc {hex(FRAM_ERASE_APP_START_ADDR)}\n")
        fp.write("g\n")
        fp.write("sleep 6000\n")   # Must ensure we sleep at least 5sec to allow erase-app to run to finish!
        fp.write("q\n")
    # Need to sleep at least 5sec to allow FRAM-erase process to complete.
    # TODO: check when erase-app has finished blanking FRAM!
    #  (but, tricky without serial port connection ...)
    # TODO: also determine end result of FRAM-erase (PASS or FAIL)!
    cmd_status, jlink_output = run_jlink_cmd_file(FRAM_ERASE_JLINK_CMD_FILE)
    # Remove file if specified:
    if cleanup:
        try:
            os.remove(FRAM_ERASE_JLINK_CMD_FILE)
        except OSError:
            pass
    #
    return cmd_status, jlink_output


# ********************* Flash prog tasks **********************

def fw_prepare_target(erase=True, keep_serno=False, serial=0, cleanup=True, verbose=True, debug=False):
    status = False
    serial_num_read = 0
    mcu_type = JLINK_TARGET_OPTIONS[JLINK_TARGET_MCU_OPTION_IDX]
    # Determine MCU-type from sensor-type:
    if IRRIGATION_SENSOR_REV_AA_MCU == mcu_type:
        config_sector_offset_addr = IRRIGATION_SENSOR_REV_AA_CONFIG_START
    elif IRRIGATION_SENSOR_REV_AB_MCU == mcu_type:
        config_sector_offset_addr = IRRIGATION_SENSOR_REV_AB_CONFIG_START
    else:
        print("ERROR: no valid MCU-type specified! Just assuming sensor-type is 'AA' ...")
        config_sector_offset_addr = IRRIGATION_SENSOR_REV_AA_CONFIG_START
    #
    with open(PRE_TASKS_CMD_FILE, 'w') as fp:
        fp.write("halt\n")
        fp.write("r\n")
        # If required, ERASE target ...
        if erase:
            fp.write("unlock Kinetis\n")      # Needed if device is programmed 1st time!
            fp.write("erase\n")
        # Set image-number =1(=FW1 startup as default):
        fp.write(f"w4 0x{config_sector_offset_addr:X} 0x00000001\n")  # Set image-number=1
        # Default write given serial number into config-sector in Flash:
        if not keep_serno:
            if serial in range(1, 65355):
                fp.write(f"w4 0x{config_sector_offset_addr + CONFIG_SECTOR_SERIALNO_OFFSET:X} " + hex(serial) + "\n")  # Set serial number
            else:
                print(f"Serial number = {serial} is OUT OF RANGE! Cannot use ...")
        # Readback config-values from Flash:
        fp.write(f"mem32 0x{config_sector_offset_addr:X},1\n")
        fp.write(f"mem32 0x{config_sector_offset_addr + CONFIG_SECTOR_SERIALNO_OFFSET:X},1\n")
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
                print(f"Could not write FW2 to Flash memory - SREC file '{fw1_srec}' missing!", flush=True)
            else:
                print(f"Writing FW2 firmware '{fw2_srec}' to boot Flash memory ...", flush=True)
                fp.write("loadfile %s\n" % fw2_srec)
        # Fill in step for BootLoader if relevant:
        if fw_type == 'bl' or fw_type == 'all':
            bootloader_srec = os.path.join(srec_path, "IrrigationSensorBootld.srec")
            if not os.path.exists(bootloader_srec):
                print(f"Could not write bootloader to Flash memory - SREC file '{bootloader_srec}' missing!", flush=True)
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
    mcu_type = JLINK_TARGET_OPTIONS[JLINK_TARGET_MCU_OPTION_IDX]
    # Determine MCU-type from sensor-type:
    if IRRIGATION_SENSOR_REV_AA_MCU == mcu_type:
        IMAGE_NUM_FLASH_ADDR = f"{IRRIGATION_SENSOR_REV_AA_CONFIG_START:08X}"
    elif IRRIGATION_SENSOR_REV_AB_MCU == mcu_type:
        IMAGE_NUM_FLASH_ADDR = f"{IRRIGATION_SENSOR_REV_AB_CONFIG_START:08X}"
    else:
        print("ERROR: no valid MCU-type specified! Just assuming sensor-type is 'AA' ...")
        IMAGE_NUM_FLASH_ADDR = f"{IRRIGATION_SENSOR_REV_AA_CONFIG_START:08X}"
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
    mcu_type = JLINK_TARGET_OPTIONS[JLINK_TARGET_MCU_OPTION_IDX]
    # Determine MCU-type from sensor-type:
    if IRRIGATION_SENSOR_REV_AA_MCU == mcu_type:
        SER_NUM_FLASH_ADDR = f"{IRRIGATION_SENSOR_REV_AA_CONFIG_START + CONFIG_SECTOR_SERIALNO_OFFSET:08X}"
    elif IRRIGATION_SENSOR_REV_AB_MCU == mcu_type:
        SER_NUM_FLASH_ADDR = f"{IRRIGATION_SENSOR_REV_AB_CONFIG_START + CONFIG_SECTOR_SERIALNO_OFFSET:08X}"
    else:
        print("ERROR: no valid MCU-type specified! Just assuming sensor-type is 'AA' ...")
        SER_NUM_FLASH_ADDR = f"{IRRIGATION_SENSOR_REV_AA_CONFIG_START + CONFIG_SECTOR_SERIALNO_OFFSET:08X}"
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
@click.option('--fram_erase/--no_fram_erase',
              default=False,
              help="Erase entire FRAM config-memory (set to all zero) on target before programming")
@click.option('--erase/--no_erase',
              default=True,
              help="Erase entire Flash memory before programming")
@click.option('--sensor_type',
              type=click.Choice(['AA', 'AB']),
              default='all',
              help="IrrigationSensor type. Set to 'AA' if rev.A HW-platform, set to 'AB' if rev.B HW-platform(w. pressure-sensor interface).")
# The command itself:
def run_irrigation_sensor_programming(path, serial, fw_type, fram_erase, erase, sensor_type) -> bool:
    # NOTE: no doc-block here to avoid Quick picking it up and use for window title!
    #
    global srec_path
    global JLINK_TARGET_OPTIONS

    mcu_type = MAP_SENSOR_TYPE_TO_MCU[sensor_type]
    # Modify J-Link setup to match target MCU:
    JLINK_TARGET_OPTIONS[JLINK_TARGET_MCU_OPTION_IDX] = mcu_type

    print("Startup ...", flush=True)
    # Run:
    print(f"path={path}, fw_type={fw_type}, serial={serial}, fram_erase={fram_erase}, erase={erase},  MCU={mcu_type}...", flush=True)
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
        config_status = fw_prepare_target(erase=erase, keep_serno=False, serial=serial)
        fram_status = True
        if fram_erase:
            # Task will wait to allow FRAM-eraser application to run on target ....
            print("FRAM erase: 5 seconds is required to allow FRAM on target to be erased ...", flush=True)
            fram_status = vv_fram_erase()
            print("FRAM on target is now erased - continuing ...", flush=True)
        fw_prog_status = run_fw_programming(fw_type=fw_type)
        #
        # total_status = status1 and status2 and status3 and status4
        total_status = config_status and fw_prog_status and fram_status
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
           top=100,
           app_icon=resource_path("7sense-7-hvit.png"))

