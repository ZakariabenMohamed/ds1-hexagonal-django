@echo off
rem Lance toutes les vérifications du projet (environnement virtuel activé).
echo === Django system check ===
python manage.py check || exit /b 1
echo.
echo === Architecture (import-linter) ===
lint-imports || exit /b 1
echo.
echo === Tests (pytest) ===
pytest || exit /b 1
echo.
echo === Garde de vitesse du coeur ===
python scripts\check_core_speed.py || exit /b 1
echo.
echo Toutes les verifications sont passees.
