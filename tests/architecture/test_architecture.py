"""Les règles d'architecture sont vérifiées automatiquement par import-linter.

Deux niveaux de preuve :
1. le vrai projet respecte les contrats ;
2. les contrats détectent bien une violation (on teste le test).
"""
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUN_LINT = "import sys; from importlinter.cli import lint_imports; sys.exit(lint_imports(no_cache=True))"


def run_lint(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", RUN_LINT], cwd=cwd, capture_output=True, text=True, timeout=120
    )


def test_project_respects_all_architecture_contracts():
    result = run_lint(PROJECT_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "bad_import, expected_contract",
    [
        ("import django", "Core must not depend on Django"),
        ("from loan_core.application import ports", "Layered architecture"),
        ("from loan_adapters import memory", "Core must not depend on Django or on outer layers"),
    ],
)
def test_contracts_detect_violations(tmp_path, bad_import, expected_contract):
    for package in ("loan_core", "loan_core/domain", "loan_core/application", "loan_adapters", "loans"):
        (tmp_path / package).mkdir(parents=True, exist_ok=True)
        (tmp_path / package / "__init__.py").write_text("")
    (tmp_path / "loan_adapters" / "memory.py").write_text("")
    (tmp_path / "loan_core" / "application" / "ports.py").write_text("")
    (tmp_path / "loan_core" / "domain" / "bad.py").write_text(textwrap.dedent(bad_import) + "\n")
    shutil.copy(PROJECT_ROOT / ".importlinter", tmp_path / ".importlinter")

    result = run_lint(tmp_path)

    assert result.returncode != 0
    assert expected_contract in result.stdout
