# Pre-Deployment Checklist Script
# Run this script before deploying to verify everything is configured correctly

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def check_requirements_file():
    """Check if requirements.txt exists and contains necessary packages."""
    req_file = BASE_DIR / 'requirements.txt'
    if not req_file.exists():
        return False, "requirements.txt not found"
    
    with open(req_file) as f:
        content = f.read()
    
    required = ['Django', 'djangorestframework', 'gunicorn', 'whitenoise', 'psycopg']
    missing = [pkg for pkg in required if pkg not in content]
    
    if missing:
        return False, f"Missing packages in requirements.txt: {', '.join(missing)}"
    return True, "requirements.txt OK"

def check_settings():
    """Check if settings.py is deployment-ready."""
    settings_file = BASE_DIR / 'mysite' / 'settings.py'
    if not settings_file.exists():
        return False, "settings.py not found"
    
    with open(settings_file) as f:
        content = f.read()
    
    checks = [
        ('whitenoise.middleware.WhiteNoiseMiddleware' in content, "WhiteNoise middleware configured"),
        ('os.environ.get' in content, "Environment variables configured"),
        ('STATIC_ROOT' in content, "STATIC_ROOT configured"),
    ]
    
    for check, msg in checks:
        if not check:
            return False, f"Missing: {msg}"
    
    return True, "settings.py OK"

def check_deployment_files():
    """Check if deployment files exist."""
    files = {
        'Procfile': 'Heroku deployment config',
        'Dockerfile': 'Docker deployment config',
        'runtime.txt': 'Python version specification',
        'DEPLOYMENT_GUIDE.md': 'Deployment documentation',
    }
    
    missing = []
    for filename, description in files.items():
        if not (BASE_DIR / filename).exists():
            missing.append(f"{filename} ({description})")
    
    if missing:
        return False, f"Missing deployment files: {', '.join(missing)}"
    return True, "All deployment files present"

def check_secret_key():
    """Check if SECRET_KEY needs to be set."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    from django.conf import settings
    
    if settings.SECRET_KEY.startswith('django-insecure'):
        return False, "SECRET_KEY is not set in environment variables (required for production)"
    return True, "SECRET_KEY configured"

def check_debug():
    """Check if DEBUG is set to False for production."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    from django.conf import settings
    
    if settings.DEBUG:
        return False, "DEBUG is True (must be False in production)"
    return True, "DEBUG is False"

def check_allowed_hosts():
    """Check if ALLOWED_HOSTS is configured."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    from django.conf import settings
    
    if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['localhost', '127.0.0.1']:
        return False, "ALLOWED_HOSTS not configured for production domain"
    return True, "ALLOWED_HOSTS configured"

def run_checks():
    """Run all checks and report results."""
    print("=" * 60)
    print("Django Deployment Pre-Flight Checklist")
    print("=" * 60)
    print()
    
    checks = [
        ("Requirements File", check_requirements_file),
        ("Settings Configuration", check_settings),
        ("Deployment Files", check_deployment_files),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            status, message = check_func()
            results.append((name, status, message))
            symbol = "✓" if status else "✗"
            print(f"{symbol} {name}: {message}")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"✗ {name}: {str(e)}")
    
    print()
    print("=" * 60)
    print("Environment Variable Checklist (Required for Deployment)")
    print("=" * 60)
    print()
    
    required_env_vars = [
        ('DJANGO_SECRET_KEY', 'Secret key for Django (generate new for production)'),
        ('DJANGO_DEBUG', 'Set to False for production'),
        ('DJANGO_ALLOWED_HOSTS', 'Your domain name'),
        ('POSTGRES_DB', 'Database name'),
        ('POSTGRES_USER', 'Database user'),
        ('POSTGRES_PASSWORD', 'Database password'),
        ('POSTGRES_HOST', 'Database host'),
    ]
    
    print("Before deploying, set these environment variables:")
    print()
    for var, description in required_env_vars:
        value = os.environ.get(var, 'NOT SET')
        symbol = "✓" if os.environ.get(var) and os.environ.get(var) != 'NOT SET' else "○"
        print(f"  {symbol} {var}: {description}")
    
    print()
    print("=" * 60)
    print("Quick Start Deployment Commands")
    print("=" * 60)
    print()
    print("For Heroku:")
    print("  heroku create your-app-name")
    print("  heroku container:push web")
    print("  heroku container:release web")
    print("  heroku run python manage.py migrate")
    print()
    print("For Railway:")
    print("  railway init")
    print("  railway up")
    print()
    print("For Docker (local testing):")
    print("  docker build -t clindocs .")
    print("  docker run -p 8000:8000 clindocs")
    print()

if __name__ == '__main__':
    run_checks()
