from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "--file", str(ROOT / "compose.yaml")]


def run(command: list[str], environment: dict[str, str], check: bool = True) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, env=environment, check=check)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a clean local pgvector database, seed it, and run integration tests."
    )
    parser.add_argument(
        "--keep-database",
        action="store_true",
        help="Keep the validated container and named volume instead of removing them.",
    )
    args = parser.parse_args()

    environment = os.environ.copy()
    password = environment.get("POSTGRES_PASSWORD")
    if not password:
        raise SystemExit("POSTGRES_PASSWORD must be set to a local test-only value")
    user = environment.setdefault("POSTGRES_USER", "cooling_app")
    database = environment.setdefault("POSTGRES_DB", "cooling_intelligence")
    port = environment.setdefault("POSTGRES_PORT", "5432")
    environment["DATABASE_URL"] = environment.get("DATABASE_URL") or (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@127.0.0.1:{port}/{quote_plus(database)}"
    )
    environment["RETRIEVAL_MODE"] = "postgresql"

    run(COMPOSE + ["down", "--volumes", "--remove-orphans"], environment, check=False)
    try:
        run(COMPOSE + ["up", "--detach", "--wait"], environment)
        run([sys.executable, "scripts/seed_postgres.py"], environment)
        run(
            [
                sys.executable,
                "-m",
                "pytest",
                "backend/tests/test_pgvector_integration.py",
                "-m",
                "integration",
                "-q",
            ],
            environment,
        )
    finally:
        if not args.keep_database:
            run(COMPOSE + ["down", "--volumes", "--remove-orphans"], environment, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
