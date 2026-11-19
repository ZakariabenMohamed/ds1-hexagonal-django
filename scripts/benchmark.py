"""Compare les deux adaptateurs de persistance sur les mêmes demandes.

Usage (depuis la racine du projet) :   python scripts/benchmark.py [N]

Le cœur (cas d'usage + règles) est identique ; seul l'adaptateur change :
mémoire contre Django ORM (SQLite en mémoire). Les temps dépendent de votre
machine : relancez le script chez vous et citez VOS mesures dans la présentation.
"""
import os
import re
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_DB_NAME"] = ":memory:"  # base jetable : ne touche pas db.sqlite3

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402

from loan_adapters.clock import SystemClock  # noqa: E402
from loan_adapters.memory import InMemoryLoanRepository  # noqa: E402
from loan_adapters.scoring import SimulatedCreditBureau  # noqa: E402
from loan_core.application.use_cases import SubmitLoanApplication, SubmitLoanCommand  # noqa: E402
from loans.repository import DjangoLoanRepository  # noqa: E402


def run(repository, count: int) -> float:
    use_case = SubmitLoanApplication(repository, SimulatedCreditBureau(), SystemClock())
    start = time.perf_counter()
    for n in range(count):
        use_case.execute(
            SubmitLoanCommand(f"Client {n}", f"CLI-{n}", Decimal("20000"), 60, Decimal("2000"))
        )
    return time.perf_counter() - start


def time_suite(keyword: str) -> float | None:
    """Durée (secondes, mesurée par pytest) de la suite de scénarios pour un adaptateur."""
    root = Path(__file__).resolve().parents[1]
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_DB_NAME"}
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/scenarios", "-k", keyword, "-p", "no:cacheprovider"],
        cwd=root, capture_output=True, text=True, env=env,
    )
    match = re.search(r"(\d+) passed.* in ([0-9.]+)s", run.stdout)
    return float(match.group(2)) if match else None


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    call_command("migrate", verbosity=0)

    memory = run(InMemoryLoanRepository(), count)
    orm = run(DjangoLoanRepository(), count)

    print(f"{count} demandes évaluées et enregistrées avec le MÊME cœur :")
    print(f"  adaptateur mémoire    : {memory * 1000:9.1f} ms  ({memory / count * 1000:.3f} ms/demande)")
    print(f"  adaptateur Django ORM : {orm * 1000:9.1f} ms  ({orm / count * 1000:.3f} ms/demande)")
    if memory > 0:
        print(f"  rapport ORM / mémoire : x{orm / memory:.1f}")

    fake, real = time_suite("fake_repo"), time_suite("orm_repo")
    print("\nSuite de scénarios (mêmes 13 cas, un seul adaptateur changé) :")
    print(f"  faux dépôt en mémoire : {fake} s")
    print(f"  Django ORM + SQLite   : {real} s")
    if fake and real:
        print(f"  rapport               : x{real / fake:.1f}")


if __name__ == "__main__":
    main()
