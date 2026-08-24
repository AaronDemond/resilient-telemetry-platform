@echo off
setlocal enabledelayedexpansion

pushd "%~dp0.."

if exist ".env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        set "%%A=%%B"
    )
)

echo WARNING: This will destroy local Docker volumes and recreate the Phase 1 seed.
set /p choice="Type CONFIRM to proceed: "

if /I not "%choice%"=="CONFIRM" (
    echo Cancelled.
    popd
    exit /b 1
)

docker compose down --volumes --remove-orphans
if errorlevel 1 goto :compose_failed

docker compose up -d
if errorlevel 1 goto :compose_failed

echo Waiting for PostgreSQL initialization...
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

docker compose exec -T postgres psql -U telemetry -d telemetry -c "SELECT id FROM phase1_environment_marker ORDER BY id;"
if errorlevel 1 goto :seed_failed

echo Clean Phase 1 seed complete.
popd
exit /b 0

:compose_failed
echo ERROR: Docker Compose failed. Clean seed was not completed.
popd
exit /b 1

:seed_failed
echo ERROR: PostgreSQL seed verification failed. Clean seed was not completed.
docker compose logs postgres --tail=50
popd
exit /b 1
