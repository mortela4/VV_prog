import sys
#
from gooey import Gooey, GooeyParser


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


def parse_args_and_execute():
    """ Parse args and run bg-process(es) """
    #
    parser = GooeyParser()
    # DropDown list-arg:
    mcu_types = list(mcu_targets.keys())
    parser.add_argument('--mcutype',
                        choices=mcu_types,
                        default="kl25z128",
                        action="store",
                        dest="mcu_type",
                        widget='Dropdown')
    #
    cli_args = parser.parse_args(sys.argv[1:])
    #
    mcu_type = cli_args.mcu_type
    print("Completed arg-handling. MCU type: %s" % mcu_type)


@Gooey(advanced=True)
def gui_wrapper():
    parse_args_and_execute()


# ***************** MAIN ************************
if __name__ == "__main__":
    gui_wrapper()







