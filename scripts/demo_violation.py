"""Démonstration live : import-linter échoue quand le cœur importe Django.

Usage (depuis la racine du projet) :   python scripts/demo_violation.py

1. lance import-linter sur le projet propre  -> contrats respectés ;
2. ajoute volontairement ``import django`` dans le domaine -> contrat violé ;
3. supprime le fichier fautif (même en cas d'erreur) et relance -> propre à nouveau.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIOLATION = ROOT / "loan_core" / "domain" / "_demo_violation.py"
RUN_LINT = "import sys; from importlinter.cli import lint_imports; sys.exit(lint_imports(no_cache=True))"


def lint(title: str) -> int:
    print(f"\n=== {title} ===")
    result = subprocess.run([sys.executable, "-c", RUN_LINT], cwd=ROOT, capture_output=True, text=True)
    summary = [
        line for line in result.stdout.splitlines()
        if "KEPT" in line or "BROKEN" in line or "Contracts:" in line or " is not allowed" in line
        or "->" in line
    ]
    print("\n".join(summary) or result.stdout or result.stderr)
    print(f"code de sortie : {result.returncode}")
    return result.returncode


def main() -> int:
    lint("1) Projet propre")
    try:
        VIOLATION.write_text("import django  # violation volontaire\n", encoding="utf-8")
        broken = lint("2) Le domaine importe Django")
    finally:
        VIOLATION.unlink(missing_ok=True)
    clean = lint("3) Fichier fautif supprimé")
    return 0 if broken != 0 and clean == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
