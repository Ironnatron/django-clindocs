@echo off
REM Deploy to Heroku without pushing to git using container registry

echo ================================
echo Heroku Container Deployment
echo ================================
echo.

REM Check if heroku CLI is installed
where heroku >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.❌ Heroku CLI is not installed. Install it from https://devcenter.heroku.com/articles/heroku-cli
    exit /b 1
)

REM Check if app name is provided
if "%1"=="" (
    echo Usage: deploy_heroku.bat your-app-name
    echo.
    echo This script will:
    echo 1. Build a Docker image
    echo 2. Push to Heroku container registry
    echo 3. Release the container
    echo 4. Run migrations
    echo.
    exit /b 1
)

set APP_NAME=%1

echo 🚀 Starting deployment to %APP_NAME%...
echo.

echo 📦 Building Docker image...
call heroku container:push web --app=%APP_NAME%
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker push failed
    exit /b 1
)

echo.
echo 🚀 Releasing container...
call heroku container:release web --app=%APP_NAME%
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Container release failed
    exit /b 1
)

echo.
echo 🗄️ Running database migrations...
call heroku run python manage.py migrate --app=%APP_NAME%
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Migration failed
    exit /b 1
)

echo.
echo ✅ Deployment complete!
echo.
echo Next steps:
echo 1. Create superuser: heroku run python manage.py createsuperuser --app=%APP_NAME%
echo 2. View logs: heroku logs --tail --app=%APP_NAME%
echo 3. Open app: heroku open --app=%APP_NAME%
echo.
