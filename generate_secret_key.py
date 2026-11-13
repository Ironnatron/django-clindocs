#!/usr/bin/env python
"""
Django Secret Key Generator

Generate a secure secret key for production Django deployment.
Use this to create a new SECRET_KEY for your production environment.

Usage:
    python generate_secret_key.py

The script will:
1. Generate a new cryptographically secure key
2. Display the key (copy and paste into environment variables)
3. Provide usage instructions
"""

import secrets
import string
import os
import sys
from pathlib import Path


def generate_django_secret_key(length=50):
    """
    Generate a secure Django SECRET_KEY.
    
    Django's SECRET_KEY should be a long random string. This function
    uses Python's secrets module for cryptographically secure randomness.
    
    Args:
        length: Length of the key to generate (default: 50)
    
    Returns:
        str: A secure random key suitable for Django
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    key = ''.join(secrets.choice(characters) for _ in range(length))
    return key


def generate_password(length=16):
    """
    Generate a secure password for database credentials.
    
    Args:
        length: Length of password to generate (default: 16)
    
    Returns:
        str: A secure random password
    """
    # Exclude problematic characters that might cause escaping issues
    characters = string.ascii_letters + string.digits + '-_!@#$'
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def print_banner(title):
    """Print a formatted banner."""
    width = 70
    print("\n" + "=" * width)
    print(f" {title:^{width-2}} ")
    print("=" * width)


def main():
    """Main function."""
    print_banner("Django Secret Key Generator")
    
    print("\n📝 Generating secure keys for production...\n")
    
    # Generate Django SECRET_KEY
    django_key = generate_django_secret_key()
    print("🔑 DJANGO_SECRET_KEY:")
    print("-" * 70)
    print(django_key)
    print("-" * 70)
    
    print("\n💾 Database Credentials:")
    print("-" * 70)
    
    # Generate database password
    db_password = generate_password(20)
    print(f"POSTGRES_PASSWORD: {db_password}")
    
    print("-" * 70)
    
    print("\n" + "=" * 70)
    print(" Environment Variables to Set on Your Hosting Platform")
    print("=" * 70)
    
    env_vars = f"""
DJANGO_SECRET_KEY={django_key}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_DB=clindocs_db
POSTGRES_USER=clindocs_user
POSTGRES_PASSWORD={db_password}
POSTGRES_HOST=your-database-host.com
POSTGRES_PORT=5432
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
"""
    print(env_vars)
    
    print("=" * 70)
    print("\n✅ Instructions:")
    print("-" * 70)
    print("1. Copy the DJANGO_SECRET_KEY above")
    print("2. Go to your hosting platform dashboard")
    print("3. Find Settings → Environment Variables (or similar)")
    print("4. Add each variable with its value")
    print("5. Save and deploy")
    print("-" * 70)
    
    print("\n🔐 Security Tips:")
    print("-" * 70)
    print("✓ Replace 'yourdomain.com' with your actual domain")
    print("✓ Use the generated POSTGRES_PASSWORD")
    print("✓ Never commit these values to git")
    print("✓ Store passwords in your platform's secrets manager")
    print("✓ Regenerate this key if it's ever exposed")
    print("-" * 70)
    
    print("\n📖 Platform-Specific Instructions:")
    print("-" * 70)
    print("\nHeroku:")
    print("  heroku config:set DJANGO_SECRET_KEY='<key>'")
    print("  heroku config:set DJANGO_DEBUG=False")
    print("  # ... more variables ...")
    print()
    print("Railway:")
    print("  1. Go to Settings tab")
    print("  2. Find Environment Variables section")
    print("  3. Add each variable")
    print()
    print("Render:")
    print("  1. Go to Settings")
    print("  2. Find Environment section")
    print("  3. Add each variable")
    print()
    print("Docker Environment:")
    print("  Set via: -e VAR_NAME=value or docker-compose.yml")
    print("-" * 70)
    
    print("\n✨ Next Steps:")
    print("-" * 70)
    print("1. Run: python deployment_checklist.py")
    print("2. Deploy using: deploy_heroku.bat your-app-name")
    print("3. Or follow platform-specific guide in DEPLOYMENT_GUIDE.md")
    print("-" * 70)
    
    print("\n" + "=" * 70)
    print(" 🚀 Ready to Deploy!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
