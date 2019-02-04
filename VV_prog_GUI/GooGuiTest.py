import sys
#
from gooey import Gooey, GooeyParser


def parse_args_and_execute():
    """ Parse args and run bg-process(es) """
    #
    parser = GooeyParser()
    # DropDown list-arg:
    parser.add_argument('--dropdown',
                        choices=["one", "two"], default="two", widget='Dropdown')
    parser.add_argument('--listboxie',
                        nargs='+',
                        default=['Option three', 'Option four'],
                        choices=['Option one', 'Option two', 'Option three',
                                 'Option four'],
                        widget='Listbox',
                        gooey_options={
                            'height': 300,
                            'validate': '',
                            'heading_color': '',
                            'text_color': '',
                            'hide_heading': True,
                            'hide_text': True,
                        }
                        )
    # Simple arg(s):
    parser.add_argument('--erase', '-e', action="store", dest="erase_first", type=str, default="yes",
                        help='Erase target Flash before programming')

    #
    cli_args = parser.parse_args(sys.argv[1:])
    #
    print("Completed arg-handling.")


@Gooey(advanced=True)
def gui_wrapper():
    parse_args_and_execute()


# ***************** MAIN ************************
if __name__ == "__main__":
    gui_wrapper()







