"""
Demonstrate mapping variables to dictionary keys
"""

from quick import gui_it
import click


@click.command()
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name', help='The person to greet.')
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        click.echo('Hello %s!' % name)


if __name__ == '__main__':
    gui_it(hello,
           run_exit=False,
           new_thread=True,
           output="gui",
           style="qdarkstyle",
           width=500)



