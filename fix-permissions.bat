@echo off
REM Fix Docker Volume Permissions Script - Windows
REM Run this if you're getting "unable to open database file" errors

echo ============================================
echo FIXING DOCKER VOLUME PERMISSIONS
echo ============================================

echo Stopping containers...
docker compose down

echo Starting temporary container to fix permissions...
docker compose run --rm --user root app bash -c "echo 'Current permissions:'; ls -la /app/backend/; echo; echo 'Fixing permissions...'; chown -R 1000:1000 /app/backend/data /app/backend/uploads; chmod -R 755 /app/backend/data /app/backend/uploads; echo; echo 'New permissions:'; ls -la /app/backend/; echo 'Permissions fixed!'"

echo Restarting containers...
docker compose up -d

echo ============================================  
echo PERMISSION FIX COMPLETE
echo ============================================
echo If you still get errors, try:
echo 1. docker compose logs app
echo 2. docker compose down ^&^& docker volume rm financial-analysis-tool_app_data financial-analysis-tool_app_uploads
echo 3. docker compose up -d --build
echo ============================================
pause