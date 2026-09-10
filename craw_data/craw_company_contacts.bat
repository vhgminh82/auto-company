@echo off
setlocal
chcp 65001 >nul
set "BASE=%~dp0"
set "SCRIPT=%BASE%craw_company_contacts.py"
set "DB=%BASE%..\companies.db"
if not exist "%SCRIPT%" (
  echo Khong tim thay craw_company_contacts.py
  pause
  exit /b 1
)
if not exist "%DB%" (
  echo Khong tim thay companies.db. Hay chay app truoc.
  pause
  exit /b 1
)
python -u "%SCRIPT%" db --database "%DB%" --workers 8 --timeout 15 --delay 0.25
echo.
echo Hoan tat. Du lieu lien he da duoc cap nhat truc tiep vao companies.db.
pause
