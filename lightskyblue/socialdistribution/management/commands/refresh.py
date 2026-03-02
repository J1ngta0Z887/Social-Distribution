import os
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = (
        "Delete db.sqlite3, clear migrations (except __init__.py), then run "
        "makemigrations, migrate, and populate_db."
    )

    def handle(self, *args, **options):
        curr_dir = Path(os.getcwd()).resolve()
        db_path = curr_dir / "db.sqlite3"
        migrations_dir = curr_dir / "socialdistribution" / "migrations"

        if db_path.exists():
            db_path.unlink()

        for path in migrations_dir.iterdir():
            if path.name == "__init__.py":
                continue
            try:
                path.unlink()
            except:
                pass

        manage_py = curr_dir / "manage.py"
        commands = [
            ["python3", str(manage_py), "makemigrations"],
            ["python3", str(manage_py), "migrate"],
            ["python3", str(manage_py), "populate_db"],
        ]

        for cmd in commands:
            subprocess.run(cmd, check=True, cwd=str(curr_dir))

        print()
        print("⛄︎ You will be prompted to create a superuser to log into the site.")
        print("⛄︎ Do not skip this step.")
        print()
        subprocess.run(["python3", str(manage_py), "createsuperuser"],
                       check=True, cwd=str(curr_dir))

        print("Finished!")
