@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "BASE=%~dp0"
set "SCRAPER=%BASE%google-maps-scraper-stable.exe"
set "COMPLETED=%BASE%completed_queries.txt"
set "OUT_ROOT=%BASE%results"
set "PENDING_FILE=%OUT_ROOT%\pending_queries.txt"
set "BUILD_PENDING=%BASE%build_pending_queries.py"
set "MARK_COMPLETED=%BASE%mark_query_completed.py"
set "IMPORT=%BASE%import_maps_to_db.py"
set "DB=%BASE%..\companies.db"
set "PROGRESS=%OUT_ROOT%\crawl_progress.txt"
set "CLEAN_SUCCESS=1"
if not exist "%SCRAPER%" echo Khong tim thay scraper & pause & exit /b 1
if not exist "%BUILD_PENDING%" echo Khong tim thay bo tao danh sach query & pause & exit /b 1
if not exist "%MARK_COMPLETED%" echo Khong tim thay bo danh dau query & pause & exit /b 1
if not exist "%IMPORT%" echo Khong tim thay bo nhap SQLite & pause & exit /b 1
if not exist "%DB%" echo Khong tim thay companies.db - hay chay app truoc & pause & exit /b 1
if not exist "%COMPLETED%" type nul > "%COMPLETED%"
if not exist "%OUT_ROOT%" mkdir "%OUT_ROOT%"

set "CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" echo Khong tim thay Google Chrome & pause & exit /b 1
set "GOOGLE_MAPS_CHROME_PATH=%CHROME%"
for /f "delims=" %%T in ('powershell -NoProfile -Command "(Get-Date).ToString('yyyyMMdd_HHmmss')"') do set "RUN_ID=%%T"
set "RUN_DIR=%OUT_ROOT%\run_!RUN_ID!"
mkdir "!RUN_DIR!"
set "STATUS_FILE=!RUN_DIR!\query_status.csv"
>"!STATUS_FILE!" echo line,status,places,query,import_log,log
set /a TOTAL=0,INDEX=0,OK=0,FAILED=0,SKIPPED=0,COMPLETED_BEFORE=0,FOUND=0
>"%PROGRESS%" echo RUNNING^|0^|0^|^|0
python -u "%BUILD_PENDING%" --database "%DB%" --completed "%COMPLETED%" --output "%PENDING_FILE%"
if errorlevel 1 echo Khong tao duoc danh sach query & >"%PROGRESS%" echo FAILED^|0^|0^| & exit /b 1
for /f %%N in ('find /v /c "" ^< "%PENDING_FILE%"') do set "TOTAL=%%N"
for /f %%N in ('find /v /c "" ^< "%COMPLETED%"') do set "COMPLETED_BEFORE=%%N"
>"%PROGRESS%" echo RUNNING^|0^|!TOTAL!^|^|!FOUND!
set /a INDEX=0
echo Tong so dong: !TOTAL!
echo Da hoan tat truoc do: !COMPLETED_BEFORE!
echo Truy van da V se duoc bo qua theo: %COMPLETED%

for /f "usebackq delims=" %%Q in ("%PENDING_FILE%") do call :RUN_ONE "%%Q"
>"!RUN_DIR!\DONE.txt" echo STATUS=DONE
>>"!RUN_DIR!\DONE.txt" echo TOTAL=!TOTAL!
>>"!RUN_DIR!\DONE.txt" echo SUCCESS=!OK!
>>"!RUN_DIR!\DONE.txt" echo FAILED=!FAILED!
>>"!RUN_DIR!\DONE.txt" echo SKIPPED=!SKIPPED!
>>"!RUN_DIR!\DONE.txt" echo FINISHED=%DATE% %TIME%
>"%PROGRESS%" echo DONE^|!INDEX!^|!TOTAL!^|^|!FOUND!
echo.
echo Hoan tat: thanh cong !OK!, loi !FAILED!, bo qua !SKIPPED!.
echo Chi tiet: !STATUS_FILE!
echo Du lieu doanh nghiep da duoc ghi truc tiep vao companies.db.
exit /b 0

:RUN_ONE
set /a INDEX+=1
set "QUERY=%~1"
>"%PROGRESS%" echo RUNNING^|!INDEX!^|!TOTAL!^|!QUERY!^|!FOUND!
set "PAD=00000!INDEX!"
set "PAD=!PAD:~-5!"
set "ONE_QUERY=!RUN_DIR!\query_!PAD!.txt"
set "ONE_CSV=!RUN_DIR!\query_!PAD!.csv"
set "ONE_LOG=!RUN_DIR!\query_!PAD!.log"
set "ONE_IMPORT_LOG=!RUN_DIR!\query_!PAD!_import.log"
>"!ONE_QUERY!" echo !QUERY!
echo [!INDEX!/!TOTAL!] !QUERY!
"%SCRAPER%" -input "!ONE_QUERY!" -results "!ONE_CSV!" -c 1 -depth 10 -exit-on-inactivity 2m >"!ONE_LOG!" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"
set /a PLACES=0
if exist "!ONE_CSV!" for /f "delims=" %%C in ('powershell -NoProfile -Command "(Get-Content -LiteralPath $env:ONE_CSV).Count"') do set /a PLACES=%%C-1
if "!EXIT_CODE!"=="0" (
  set /a FOUND+=PLACES
  python -u "%IMPORT%" --input "!ONE_CSV!" --database "%DB%" --query "!QUERY!" >"!ONE_IMPORT_LOG!" 2>&1
  set "IMPORT_CODE=!ERRORLEVEL!"
  if "!IMPORT_CODE!"=="0" (
    set /a OK+=1
    >>"!COMPLETED!" echo !QUERY!
    python -u "%MARK_COMPLETED%" --database "%DB%" --query "!QUERY!" >nul 2>&1
    >>"!STATUS_FILE!" echo !INDEX!,V,!PLACES!,"!QUERY!",,
    echo     V - !PLACES! doanh nghiep/diem da ghi vao SQLite
    if "!CLEAN_SUCCESS!"=="1" (
      if exist "!ONE_QUERY!" del /q "!ONE_QUERY!"
      if exist "!ONE_CSV!" del /q "!ONE_CSV!"
      if exist "!ONE_LOG!" del /q "!ONE_LOG!"
      if exist "!ONE_IMPORT_LOG!" del /q "!ONE_IMPORT_LOG!"
    )
  ) else (
    set /a FAILED+=1
    >>"!STATUS_FILE!" echo !INDEX!,FAILED,!PLACES!,"!QUERY!","!ONE_IMPORT_LOG!","!ONE_LOG!"
    echo     FAILED - loi nhap SQLite !IMPORT_CODE!, xem !ONE_IMPORT_LOG!
  )
) else (
  set /a FAILED+=1
  >>"!STATUS_FILE!" echo !INDEX!,FAILED,!PLACES!,"!QUERY!","!ONE_CSV!","!ONE_LOG!"
  echo     FAILED - ma loi !EXIT_CODE!, xem !ONE_LOG!
)
exit /b
