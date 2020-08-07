import sys
import os
import subprocess


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def decode_byte_arr(data: bytes, utf_encode: bool = False, verbose: bool = True) -> str:
    lines_in = data.splitlines()
    lines_out = []
    for line in lines_in:
        try:
            line_str = line.decode('ascii')
        except UnicodeDecodeError as e:
            print(f"Exception trying to decode as ASCII (naive): {e}")
            try:
                line_str = line.decode('utf-8')
            except UnicodeDecodeError as e:
                print(f"Exception trying to decode as UTF-8: {e}")
                try:
                    line_str = line.decode('latin1')
                except UnicodeDecodeError as e:
                    print(f"Exception trying to decode as ISO LATIN-1: {e}")
                    line_str = "..."
        finally:
            if utf_encode:
                # Ensure output string is UTF-8:
                line_str = line_str.encode('utf-8').decode('utf-8')
            lines_out.append(line_str)
        if verbose:
            print(line_str)
    #
    return lines_out


def run_exe_file(exe_file_name, utf_encode: bool = False, verbose: bool = True):
    SUBPROC_RETVAL_STATUS_SUCCESS = 0
    status = False
    #
    exe_file = resource_path(exe_file_name)
    #
    print(f"Running: {exe_file}")
    try:
        p1 = subprocess.Popen(exe_file, stdout=subprocess.PIPE)
        # Run the command
        output = p1.communicate(timeout=30)[0]
    except subprocess.TimeoutExpired:
        print(f"ERROR: timeout from running '{exe_file}'")
        return status

    lines_out = decode_byte_arr(output, utf_encode=utf_encode)
    status = (p1.returncode == SUBPROC_RETVAL_STATUS_SUCCESS)
    #
    return status, lines_out


if __name__ == "__main__":
    stivei = resource_path('streng_codec.exe')
    print(f"Path to 'streng_codec.exe': {stivei}")
    #
    stivei = resource_path('JLink.exe')
    print(f"Path to 'JLink.exe': {stivei}")
    #
    status, outp = run_exe_file('streng_codec.exe')
    print(f"Status: {status}\nOutput: {outp}")
    #
    status, outp = run_exe_file('streng_codec.exe', utf_encode=True)
    print(f"Status: {status}\nOutput: {outp}")
    #
    # Tests directly on non-UTF8 byte-array data:
    byte_str = ['\xF8', '\xF8', '\xF8', '\xF8', '\xF8']
    print(f"{byte_str}")
    print(str(byte_str))
    byte_arr = bytes([0xF8, 0xF8, 0xF8, 0xF8, 0xF8])
    print(decode_byte_arr(byte_arr))
    print(byte_arr.decode('latin1').encode('utf-8').decode('utf-8'))


