from __future__ import annotations

import click
from flask import Flask

from app.db import init_db


@click.command("init-db")
def init_db_command() -> None:
    """Inicjalizuje bazę danych wraz z danymi przykładowymi."""
    created = init_db()
    if created:
        click.echo("Baza danych została utworzona.")
    else:
        click.echo("Baza danych już istnieje — nic nie zmieniono.")


def register_cli(app: Flask) -> None:
    app.cli.add_command(init_db_command)
