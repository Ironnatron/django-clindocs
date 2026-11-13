# Django Application Deployment Guide

## Without Git Push - Manual Deployment to Cloud Platforms

This guide covers deployment to cloud platforms (Heroku, Railway, Render) without pushing code to Git.

## Option 1: Heroku Deployment (Recommended for Beginners)

### Prerequisites
- Heroku account (free tier available)
- Heroku CLI installed locally
- Your Django application files

### Steps

1. **Install Heroku CLI**
   - Download from: https://devcenter.heroku.com/articles/heroku-cli
   - Verify installation: `heroku --version`

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create a Heroku App**
   ```bash
   heroku create your-app-name
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set DJANGO_SECRET_KEY="your-very-secret-key-here"
   heroku config:set DJANGO_DEBUG=False
   heroku config:set DJANGO_ALLOWED_HOSTS="your-app-name.herokuapp.com"
   heroku config:set POSTGRES_DB=postgres
   heroku config:set POSTGRES_USER=postgres
   heroku config:set POSTGRES_PASSWORD="your-postgres-password"
   heroku config:set POSTGRES_HOST=your-postgres-host
   ```

5. **Deploy Without Git Push (Using Container Registry)**
   ```bash
   # Build the Docker image locally
   heroku container:push web
   
   # Release the container
   heroku container:release web
   ```

6. **Run Migrations**
   ```bash
   heroku run python manage.py migrate
   ```

7. **Create Superuser**
   ```bash
   heroku run python manage.py createsuperuser
   ```

8. **Collect Static Files**
   ```bash
   heroku run python manage.py collectstatic --noinput
   ```

9. **View Logs**
   ```bash
   heroku logs --tail
   ```

---

## Option 2: Railway Deployment

### Prerequisites
- Railway account (https://railway.app)
- Railway CLI installed
- Docker installed

### Steps

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Create a Project**
   ```bash
   railway init
   ```

4. **Create Dockerfile**
   Create a `Dockerfile` in your project root:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt gunicorn whitenoise

   COPY . .

   RUN python manage.py collectstatic --noinput

   CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```

5. **Deploy**
   ```bash
   railway up
   ```

6. **Configure Environment Variables in Dashboard**
   - DJANGO_SECRET_KEY
   - DJANGO_DEBUG=False
   - DJANGO_ALLOWED_HOSTS
   - Database credentials (if using PostgreSQL plugin)

---

## Option 3: Render Deployment

### Prerequisites
- Render account (https://render.com)
- GitHub or GitLab connected (for web service)
- Alternatively, use Docker image deployment

### Using Docker Without Git Push

1. **Create Dockerfile** (same as Railway)

2. **Push to Docker Registry** (Docker Hub, GitHub Registry, etc.)
   ```bash
   docker build -t yourusername/django-clindocs .
   docker login
   docker push yourusername/django-clindocs
   ```

3. **Deploy on Render Dashboard**
   - Service > New > Docker
   - Enter image URL: `yourusername/django-clindocs`
   - Configure environment variables
   - Deploy

---

## Option 4: Manual Server Deployment (VPS/Cloud VM)

### Prerequisites
- VPS with Ubuntu/Debian
- SSH access to server
- Python 3.11+, PostgreSQL, Nginx

### Steps

1. **On Local Machine - Create Deployment Package**
   ```bash
   zip -r django-app.zip . -x "*.git*" "__pycache__" "*.pyc" ".env" "venv/*"
   ```

2. **Upload to Server**
   ```bash
   scp django-app.zip user@your-server-ip:/home/user/
   ```

3. **On Server - Extract and Setup**
   ```bash
   ssh user@your-server-ip
   cd /home/user
   unzip django-app.zip
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt gunicorn
   ```

4. **Configure Database**
   ```bash
   sudo apt-get install postgresql postgresql-contrib
   # Create database and user
   ```

5. **Create Systemd Service File**
   Create `/etc/systemd/system/django.service`:
   ```ini
   [Unit]
   Description=Django ClinDocs Application
   After=network.target

   [Service]
   Type=notify
   User=www-data
   WorkingDirectory=/var/www/django-app
   Environment="PATH=/var/www/django-app/venv/bin"
   ExecStart=/var/www/django-app/venv/bin/gunicorn mysite.wsgi:application --bind unix:/run/gunicorn.sock

   [Install]
   WantedBy=multi-user.target
   ```

6. **Configure Nginx**
   Create `/etc/nginx/sites-available/django`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location /static/ {
           alias /var/www/django-app/staticfiles/;
       }

       location /media/ {
           alias /var/www/django-app/media/;
       }

       location / {
           proxy_pass http://unix:/run/gunicorn.sock;
           proxy_set_header Host $host;
       }
   }
   ```

7. **Start Services**
   ```bash
   sudo systemctl enable django
   sudo systemctl start django
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

---

## Environment Variables Reference

Create a `.env` file locally (NEVER commit this) with:

```env
DJANGO_SECRET_KEY=your-very-long-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_DB=clindocs
POSTGRES_USER=clindocs_user
POSTGRES_PASSWORD=secure-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

---

## Pre-Deployment Checklist

- [ ] Generate strong SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up PostgreSQL database
- [ ] Collect static files
- [ ] Run migrations
- [ ] Create superuser
- [ ] Test email configuration
- [ ] Set up backups
- [ ] Configure SSL/HTTPS
- [ ] Set up monitoring/logging

---

## Troubleshooting

### Static Files Not Loading
```bash
python manage.py collectstatic --clear --noinput
```

### Database Migration Issues
```bash
python manage.py migrate --noinput
```

### Permission Denied on Media Files
```bash
sudo chown -R www-data:www-data /var/www/django-app/media
```

### Check Application Logs
- Heroku: `heroku logs --tail`
- Railway: Dashboard > Logs
- Server: `sudo journalctl -u django -f`

---

## Security Notes

1. Never commit `.env` files or secrets
2. Generate a new SECRET_KEY for production
3. Use HTTPS (Let's Encrypt for free)
4. Set SECURE_SSL_REDIRECT = True in production
5. Regular backups of database
6. Keep dependencies updated

---

## Support Resources

- Django Deployment Guide: https://docs.djangoproject.com/en/6.1/howto/deployment/
- Heroku Django Support: https://devcenter.heroku.com/articles/django-app-configuration
- Railway Docs: https://docs.railway.app/
- Render Docs: https://render.com/docs/
