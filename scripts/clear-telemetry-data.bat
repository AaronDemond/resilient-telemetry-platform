@echo off
setlocal enabledelayedexpansion

pushd "%~dp0.."

if exist ".env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        set "%%A=%%B"
    )
)

set "PGDATABASE=%POSTGRES_DB%"
if "%PGDATABASE%"=="" set "PGDATABASE=telemetry"

set "PGUSER=%POSTGRES_USER%"
if "%PGUSER%"=="" set "PGUSER=telemetry"

echo Clearing all telemetry rows from database '%PGDATABASE%'...

docker compose exec -T postgres psql -U %PGUSER% -d %PGDATABASE% -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE telemetry_messages RESTART IDENTITY;"
if errorlevel 1 (
    echo Failed to clear telemetry data.
    echo Check that the Docker Postgres container is running and that the project database is available.
    popd
    exit /b 1
)

echo Telemetry data cleared successfully.
popd
exit /b 0
