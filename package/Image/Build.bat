@echo off
rem Build a docker image from a product declaration.
rem Usage: Build.bat ProductName   (reads products\ProductName\product.json and products\ProductName\Dockerfile)
rem The image name is the product name in lower case.
setlocal
if "%~1"=="" (
  echo Usage: Build.bat ProductName
  exit /b 1
)
set "PRODUCT=%~1"
set "ROOT=%~dp0..\.."
set "DECL=%ROOT%\products\%PRODUCT%\product.json"
if not exist "%DECL%" (
  echo Not found: %DECL%
  exit /b 1
)
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "(Get-Content -Raw '%DECL%' | ConvertFrom-Json).source"`) do set "SOURCE=%%S"
for /f "usebackq delims=" %%N in (`powershell -NoProfile -Command "'%PRODUCT%'.ToLower()"`) do set "IMAGE=%%N"
docker build -f "%ROOT%\products\%PRODUCT%\Dockerfile" --build-arg SOURCE=%SOURCE% -t %IMAGE% "%ROOT%"
