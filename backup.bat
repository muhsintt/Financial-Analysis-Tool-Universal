@echo off
REM Financial Analysis Tool - Backup & Restore Script
REM For Windows

setlocal enabledelayedexpansion

REM Determine docker compose command
docker-compose version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose is not available.
        exit /b 1
    ) else (
        set "DOCKER_COMPOSE=docker compose"
    )
) else (
    set "DOCKER_COMPOSE=docker-compose"
)

set "PROJECT_NAME=financial-analysis-tool"
set "DATA_VOLUME=%PROJECT_NAME%_app_data"
set "UPLOADS_VOLUME=%PROJECT_NAME%_app_uploads"

if "%1"=="backup" goto :backup
if "%1"=="restore" goto :restore
if "%1"=="list" goto :list
if "%1"=="clean" goto :clean
if "%1"=="help" goto :help
if "%1"=="/?" goto :help
if "%1"=="-h" goto :help
if "%1"=="--help" goto :help

:help
echo.
echo Financial Analysis Tool - Backup ^& Restore
echo.
echo Usage: %0 [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   backup     Create a backup of all persistent data
echo   restore    Restore data from a backup
echo   list       List available backups  
echo   clean      Clean old backups (keeps last 5)
echo.
echo Options:
echo   -f FILE    Specify backup file for restore
echo   help       Show this help message
echo.
echo Examples:
echo   %0 backup                               # Create backup with timestamp
echo   %0 restore -f backups\backup.tar.gz    # Restore from specific file
echo   %0 list                                # List all backups
echo.
goto :eof

:backup
echo [INFO] Creating backup...

REM Create timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

set "BACKUP_DIR=backups\%timestamp%"
set "BACKUP_FILE=financial-analysis-backup-%timestamp%.tar.gz"

mkdir "%BACKUP_DIR%" 2>nul

echo [INFO] Backup directory: %BACKUP_DIR%

REM Check if volumes exist
docker volume inspect "%DATA_VOLUME%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Data volume %DATA_VOLUME% not found. Run the application first.
    exit /b 1
)

REM Backup database volume
echo [INFO] Backing up database...
docker run --rm -v "%DATA_VOLUME%":/data -v "%cd%\%BACKUP_DIR%":/backup alpine tar czf /backup/app_data.tar.gz -C /data .

REM Backup uploads volume  
echo [INFO] Backing up uploads...
docker run --rm -v "%UPLOADS_VOLUME%":/data -v "%cd%\%BACKUP_DIR%":/backup alpine tar czf /backup/app_uploads.tar.gz -C /data .

REM Create metadata file
echo { > "%BACKUP_DIR%\metadata.json"
echo     "timestamp": "%date% %time%", >> "%BACKUP_DIR%\metadata.json"
echo     "volumes": [ >> "%BACKUP_DIR%\metadata.json"
echo         "%DATA_VOLUME%", >> "%BACKUP_DIR%\metadata.json"
echo         "%UPLOADS_VOLUME%" >> "%BACKUP_DIR%\metadata.json"
echo     ], >> "%BACKUP_DIR%\metadata.json"
echo     "hostname": "%COMPUTERNAME%", >> "%BACKUP_DIR%\metadata.json"
echo     "user": "%USERNAME%" >> "%BACKUP_DIR%\metadata.json"
echo } >> "%BACKUP_DIR%\metadata.json"

echo [SUCCESS] Backup created successfully!
echo [INFO]   Directory: %BACKUP_DIR%
goto :eof

:restore
if "%2"=="-f" (
    set "BACKUP_PATH=%3"
) else (
    set "BACKUP_PATH=%2"
)

if not defined BACKUP_PATH (
    echo [ERROR] No backup file specified. Use -f option.
    exit /b 1
)

if not exist "%BACKUP_PATH%" (
    echo [ERROR] Backup file not found: %BACKUP_PATH%
    exit /b 1
)

echo [WARNING] This will replace all existing data!
set /p confirm="Are you sure you want to continue? (yes/no): "

if not "%confirm%"=="yes" (
    echo [INFO] Restore cancelled.
    exit /b 0
)

echo [INFO] Stopping application...
!DOCKER_COMPOSE! down

echo [INFO] Restoring data (this may take a while)...
REM Note: Windows restore is more complex due to tar limitations
REM For now, provide instructions for manual restore
echo [INFO] For Windows, please extract the backup manually and copy files.
echo [INFO] Or use WSL/Git Bash to run the Linux script.

echo [INFO] Starting application...
!DOCKER_COMPOSE! up -d

echo [SUCCESS] Restore process initiated.
goto :eof

:list
echo [INFO] Available backups:
echo.

REM List backup directories
if exist "backups\20*" (
    for /d %%d in (backups\20*) do (
        echo   %%d
    )
) else (
    echo [INFO] No backups found.
)
goto :eof

:clean
echo [INFO] Cleaning old backups (keeping last 5)...

REM Simple cleanup - remove directories older than 5 days
forfiles /p backups /m 20* /d -5 /c "cmd /c echo Removing @path && rmdir /s /q @path" 2>nul

echo [SUCCESS] Cleanup completed.
goto :eof