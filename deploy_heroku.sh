#!/bin/bash
# Deploy to Heroku without pushing to git using container registry

set -e

echo "================================"
echo "Heroku Container Deployment"
echo "================================"
echo ""

# Check if heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Install it from https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in to Heroku
if ! heroku apps 2>/dev/null | grep -q "."; then
    echo "📝 You need to login to Heroku"
    heroku login
fi

# Check if app name is provided
if [ -z "$1" ]; then
    echo "Usage: ./deploy_heroku.sh your-app-name"
    echo ""
    echo "This script will:"
    echo "1. Build a Docker image"
    echo "2. Push to Heroku container registry"
    echo "3. Release the container"
    echo "4. Run migrations"
    echo ""
    exit 1
fi

APP_NAME=$1

echo "🚀 Starting deployment to $APP_NAME..."
echo ""

# Check if app exists
if ! heroku apps:info --app=$APP_NAME &>/dev/null; then
    echo "🆕 Creating Heroku app: $APP_NAME"
    heroku create $APP_NAME
else
    echo "✓ App $APP_NAME already exists"
fi

echo ""
echo "📦 Building Docker image..."
heroku container:push web --app=$APP_NAME

echo ""
echo "🚀 Releasing container..."
heroku container:release web --app=$APP_NAME

echo ""
echo "🗄️ Running database migrations..."
heroku run python manage.py migrate --app=$APP_NAME

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Create superuser: heroku run python manage.py createsuperuser --app=$APP_NAME"
echo "2. View logs: heroku logs --tail --app=$APP_NAME"
echo "3. Open app: heroku open --app=$APP_NAME"
echo ""
