@echo off
setlocal enabledelayedexpansion

pushd "%~dp0.."

if exist ".env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        set "%%A=%%B"
    )
)

if not defined POSTGRES_PASSWORD (
    echo POSTGRES_PASSWORD is not set.
    echo Copy .env.example to .env and set the local value before running this script.
    popd
    exit /b 1
)

docker compose up -d
if errorlevel 1 goto :compose_failed

echo Waiting for PostgreSQL...
:wait_pg
docker compose exec -T postgres grep -qx postgres /proc/1/comm >nul 2>&1
if errorlevel 1 (
    ping 127.0.0.1 -n 2 >nul
    goto wait_pg
)

docker compose exec -T postgres pg_isready -U telemetry -d telemetry >nul 2>&1
if errorlevel 1 (
    ping 127.0.0.1 -n 2 >nul
    goto wait_pg
)

echo Infrastructure is ready for Phase 1.
docker compose ps
popd
exit /b 0

:compose_failed
echo ERROR: Docker Compose failed. Infrastructure was not started.
popd
exit /b 1
