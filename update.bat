@echo off
REM Financial Analysis Tool - Docker Update Script
REM For Windows

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Financial Analysis Tool - Docker Update
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose is not available. Please install Docker Compose.
        pause
        exit /b 1
    ) else (
        set "DOCKER_COMPOSE=docker compose"
    )
) else (
    set "DOCKER_COMPOSE=docker-compose"
)

echo [INFO] Using: !DOCKER_COMPOSE!

REM Navigate to the directory containing docker-compose.yml
cd /d "%~dp0"

echo [INFO] Checking current container status...
!DOCKER_COMPOSE! ps

echo.
set /p create_backup="Do you want to create a backup before updating? (y/N): "

if /i "%create_backup%"=="y" (
    echo [INFO] Creating backup of persistent data...
    
    REM Create backup directory with timestamp
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
    set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
    set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
    
    set "BACKUP_DIR=backups\%timestamp%"
    mkdir "%BACKUP_DIR%" 2>nul
    
    REM Export volume data
    echo [INFO] Backing up database and uploads...
    docker run --rm -v financial-analysis-tool_app_data:/data -v "%cd%\%BACKUP_DIR%":/backup alpine tar czf /backup/app_data.tar.gz -C /data .
    docker run --rm -v financial-analysis-tool_app_uploads:/data -v "%cd%\%BACKUP_DIR%":/backup alpine tar czf /backup/app_uploads.tar.gz -C /data .
    
    echo [SUCCESS] Backup created in: %BACKUP_DIR%
)

echo.
echo [INFO] Stopping containers...
!DOCKER_COMPOSE! down

echo [INFO] Pulling latest images...
!DOCKER_COMPOSE! pull

echo [INFO] Rebuilding containers...
!DOCKER_COMPOSE! build --no-cache --pull

echo [INFO] Starting updated containers...
!DOCKER_COMPOSE! up -d

echo [INFO] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Health check
echo [INFO] Performing health check...
curl -f -s http://localhost/api/status >nul 2>&1
if !errorlevel! equ 0 (
    echo [SUCCESS] Application is running successfully!
    echo [INFO] Access your application at:
    echo   HTTP:  http://localhost
    echo   HTTPS: https://localhost ^(if SSL is enabled^)
) else (
    curl -f -s http://localhost:80/api/status >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] Application is running successfully!
        echo [INFO] Access your application at: http://localhost
    ) else (
        echo [WARNING] Application may still be starting up...
        echo [INFO] Check status with: !DOCKER_COMPOSE! logs
    )
)

echo.
echo [INFO] Update completed! Container logs:
!DOCKER_COMPOSE! logs --tail=20

echo.
echo [SUCCESS] =========================================
echo [SUCCESS]  Update Complete!
echo [SUCCESS] =========================================
echo.
pause