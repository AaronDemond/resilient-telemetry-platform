@echo off
setlocal

pushd "%~dp0.."

if exist ".env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        set "%%A=%%B"
    )
)

docker compose down
popd
