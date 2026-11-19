@echo off
rem Verifie tout le projet dans Docker (Docker Desktop doit etre demarre).
docker version >nul 2>&1
if errorlevel 1 (
  echo Docker n'est pas disponible. Demarrez Docker Desktop puis relancez.
  exit /b 1
)
echo === Construction de l'image ===
docker compose --profile check build check || exit /b 1
echo.
echo === Verifications (Django check, import-linter, pytest, vitesse du coeur) ===
docker compose --profile check run --rm check || exit /b 1
echo.
echo Toutes les verifications sont passees dans Docker.
