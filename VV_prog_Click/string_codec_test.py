import sys
import os
import subprocess


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def run_exe_file(exe_file_name, verbose=True):
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

    lines = output.splitlines()
    lines_out = []
    for line in lines:
        try:
            line_str = line.decode('ascii')
        except Exception as e:
            print(f"Exception trying to decode as ASCII (naive): {e}")
            try:
                line_str = line.decode('utf-8')
            except Exception as e:
                print(f"Exception trying to decode as UTF-8: {e}")
                try:
                    line_str = line.decode('latin1')
                except Exception as e:
                    print(f"Exception trying to decode as ISO LATIN-1: {e}")
                    line_str = "..."
        finally:
            lines_out.append(line_str)
        if verbose:
            print(line_str)

    status = (p1.returncode == SUBPROC_RETVAL_STATUS_SUCCESS)
    #
    return status, lines_out


if __name__ == "__main__":
    status, outp = run_exe_file('streng_codec.exe')
    print(f"Status: {status}\nOutput: {outp}")

