"""Garde de vitesse : les tests du cœur doivent être nombreux, rapides ET sans Django.

Usage (depuis la racine du projet) :   python scripts/check_core_speed.py

Exigences de la fiche du sujet 13 : 50+ tests unitaires du domaine en moins de 0,2 s
avec des faux dépôts en mémoire. On lance donc ``tests/core`` SANS le plugin
pytest-django (``-p no:django``) et on vérifie en plus que ``django`` n'est jamais
importé pendant l'exécution.

Variables : CORE_MIN_TESTS (défaut 50), CORE_MAX_SECONDS (défaut 0.2).
Le chrono est celui de pytest (collecte et exécution), sans le démarrage de Python.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_TESTS = int(os.environ.get("CORE_MIN_TESTS", "50"))
MAX_SECONDS = float(os.environ.get("CORE_MAX_SECONDS", "0.2"))

RUNNER = """
import io, json, re, sys, contextlib, pytest
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    code = pytest.main(["tests/core", "-p", "no:django", "-p", "no:cacheprovider",
                        "-W", "ignore::pytest.PytestConfigWarning"])
out = buffer.getvalue()
match = re.search(r"(\\d+) passed in ([0-9.]+)s", out)
print(json.dumps({"code": int(code), "passed": int(match.group(1)) if match else 0,
                  "seconds": float(match.group(2)) if match else None,
                  "django_imported": "django" in sys.modules, "output": out[-600:]}))
"""


def main() -> int:
    run = subprocess.run([sys.executable, "-c", RUNNER], cwd=ROOT, capture_output=True, text=True)
    try:
        result = json.loads(run.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        print("Impossible de lire le résultat de pytest :\n", run.stdout, run.stderr)
        return 1

    print(f"tests du cœur réussis : {result['passed']} (minimum {MIN_TESTS})")
    print(f"durée pytest          : {result['seconds']} s (maximum {MAX_SECONDS} s)")
    print(f"django importé        : {result['django_imported']} (attendu : False)")

    problems = []
    if result["code"] != 0:
        problems.append("des tests du cœur échouent :\n" + result["output"])
    if result["passed"] < MIN_TESTS:
        problems.append(f"moins de {MIN_TESTS} tests du cœur")
    if result["seconds"] is None or result["seconds"] >= MAX_SECONDS:
        problems.append(f"durée supérieure ou égale à {MAX_SECONDS} s")
    if result["django_imported"]:
        problems.append("Django a été importé par les tests du cœur")
    if problems:
        print("\nÉCHEC :", *problems, sep="\n  - ")
        return 1
    print("\nOK : cœur rapide, nombreux tests, aucune dépendance à Django.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
