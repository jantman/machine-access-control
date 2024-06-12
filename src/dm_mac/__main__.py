"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Machine_Access_Control."""


if __name__ == "__main__":
    main(prog_name="machine_access_control")  # pragma: no cover
