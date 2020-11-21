import bincopy


def convert_to_bin_format_bytearray(fname: string=None) -> bytes:
    with open(fname, 'r') as fp:
