@echo off
setlocal
chcp 65001 >nul
set "BASE=%~dp0"
set "SCRIPT=%BASE%craw_company_contacts.py"
set "DB=SUPABASE"
if not exist "%SCRIPT%" (
  echo Khong tim thay craw_company_contacts.py
  pause
  exit /b 1
)
  echo Khong tim thay Supabase. Hay chay app truoc.
  pause
  exit /b 1
)
python -u "%SCRIPT%" db --database "%DB%" --workers 8 --timeout 15 --delay 0.25
echo.
echo Hoan tat. Du lieu lien he da duoc cap nhat truc tiep vao Supabase.
pause



