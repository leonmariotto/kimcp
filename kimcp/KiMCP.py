import click


@click.command()
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    default=False,
    show_default=True,
    help="Enable debug output.",
)
def run_server(debug: int):
    while 1:
        continue
