# 🏥 ClinDocs - Django Clinical Study Management Application

A comprehensive Django application for managing clinical studies, researchers, and patient data with role-based access control and RESTful API support.

## 📋 Overview

ClinDocs is a production-ready Django application designed to streamline clinical study management. It provides a user-friendly interface for managing multiple clinical studies, tracking researchers, and handling sensitive patient data with proper access controls.

## ✨ Features

### Core Features
- ✅ **Role-Based Access Control** - Admin, Researcher, and Patient roles with granular permissions
- ✅ **Clinical Study Management** - Create, manage, and archive multiple studies
- ✅ **User Management** - Custom user model with role assignments and department tracking
- ✅ **Research Profiles** - Detailed researcher information, credentials, and affiliations
- ✅ **Dashboard** - Overview of studies and user statistics
- ✅ **Admin Panel** - Full Django admin interface for system management

### Technical Features
- ✅ **RESTful API** - Complete Django REST Framework integration with authentication
- ✅ **Production Ready** - Security headers, HTTPS support, environment-based configuration
- ✅ **Database Support** - SQLite for development, PostgreSQL for production
- ✅ **Static File Optimization** - WhiteNoise for efficient CSS/JS/image serving
- ✅ **Docker Support** - Complete Docker and Docker Compose setup
- ✅ **Comprehensive Documentation** - Setup, deployment, and API guides

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (production) or SQLite (development)
- Git
- Virtual environment

### Local Development Setup

1. **Clone the Repository**
```bash
git clone https://github.com/Ironnatron/django-clindocs.git
cd django-clindocs
```

2. **Create Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Create Environment File**
```bash
# Copy template
cp .env.template .env

# Edit .env with your settings
```

5. **Run Migrations**
```bash
python manage.py migrate
```

6. **Create Superuser**
```bash
python manage.py createsuperuser
```

7. **Collect Static Files**
```bash
python manage.py collectstatic --noinput
```

8. **Run Development Server**
```bash
python manage.py runserver
```

Visit: http://localhost:8000 and sign in with your superuser credentials.

## 🐳 Docker Setup

### Using Docker Compose (Recommended for Development)

```bash
# Build and start services
docker-compose up

# Run migrations in another terminal
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

Visit: http://localhost:8000

### Production Docker Build

```bash
# Build image
docker build -t clindocs .

# Run container
docker run -p 8000:8000 \
  -e DJANGO_SECRET_KEY=your-secret-key \
  -e DJANGO_DEBUG=False \
  -e POSTGRES_DB=clindocs \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_HOST=your-db-host \
  clindocs
```

## 🚀 Deployment

### Railway (Recommended for Beginners)
See [RAILWAY_SETUP.md](RAILWAY_SETUP.md) for step-by-step Railway deployment.

**Quick Deploy:**
```bash
# Generate secret key
python generate_secret_key.py

# Go to https://railway.app
# Create project → Upload code → Add PostgreSQL → Deploy
```

### Heroku
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for Heroku deployment.

### Other Platforms
- **Render**: See DEPLOYMENT_GUIDE.md
- **AWS/EC2**: Docker + manual setup
- **Google Cloud**: Cloud Run or Compute Engine
- **DigitalOcean**: App Platform or Droplet
- **Azure**: App Service or Container Instances

## 🔧 Configuration

### Environment Variables

**Required for Production:**
```env
DJANGO_SECRET_KEY=your-very-long-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_DB=clindocs_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=strong-random-password
POSTGRES_HOST=database-host
POSTGRES_PORT=5432
```

**Optional Security Settings:**
```env
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
```

**Email Configuration:**
```env
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_DEFAULT_FROM_EMAIL=noreply@yourdomain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

For local development, copy `.env.template` to `.env` and customize as needed.

## 📦 Project Structure

```
django-clindocs/
├── mysite/                      # Project configuration
│   ├── settings.py             # Django settings (production-ready)
│   ├── urls.py                 # URL routing
│   ├── wsgi.py                 # WSGI application
│   └── asgi.py                 # ASGI application
│
├── polls/                      # Main Django application
│   ├── models.py               # Database models
│   ├── views.py                # View functions
│   ├── api_views.py            # REST API views
│   ├── serializers.py          # DRF serializers
│   ├── urls.py                 # App URL routing
│   ├── api_urls.py             # API URL routing
│   ├── admin.py                # Admin configuration
│   ├── signals.py              # Django signals
│   ├── api_permissions.py      # Custom permissions
│   ├── migrations/             # Database migrations
│   ├── templates/              # HTML templates
│   ├── static/                 # Static files (CSS, JS)
│   └── tests.py                # Unit tests
│
├── Docker & Deployment
│   ├── Dockerfile              # Production container definition
│   ├── docker-compose.yml      # Local development setup
│   ├── Procfile                # Heroku process definition
│   ├── runtime.txt             # Python version
│   └── .dockerignore           # Files to exclude from Docker
│
├── Configuration & Scripts
│   ├── manage.py               # Django management script
│   ├── requirements.txt        # Python dependencies
│   ├── generate_secret_key.py  # Security key generator
│   ├── deployment_checklist.py # Pre-deployment verification
│   └── .env.template           # Environment variables template
│
├── Documentation
│   ├── README.md               # This file
│   ├── RAILWAY_SETUP.md        # Railway deployment guide
│   ├── RAILWAY_DEPLOYMENT.md   # Detailed Railway guide
│   ├── DEPLOYMENT_GUIDE.md     # Multi-platform guide
│   ├── SETTINGS_CHANGES.md     # Configuration details
│   └── INDEX.md                # Complete file index
│
└── Database Files
    └── db.sqlite3             # SQLite database (development only)
```

## 🗄️ Database Models

### CustomUser
Extended Django User model:
- Email (unique, used for login)
- First name, Last name
- Role assignment
- Department affiliation
- Active status

### ClinicalStudy
Clinical research study representation:
- Study name and description
- Start date, end date
- Status (Active, Completed, On Hold)
- Researcher assignments
- Created/Updated timestamps

### ResearcherProfile
Researcher information:
- User association
- Credentials and certifications
- Specialization
- Department
- Contact information
- Biography

### Roles & Permissions
Role-based access control:
- Admin role - Full system access
- Researcher role - Study management
- Patient role - Data viewing rights

## 📡 API Documentation

### Authentication Endpoints
```
POST   /login/                 - User login
GET    /logout/                - User logout
GET    /profile/               - Current user profile
POST   /password-reset/        - Request password reset
POST   /password-reset-confirm/ - Confirm password reset
```

### Studies API
```
GET    /api/studies/           - List all studies
POST   /api/studies/           - Create new study
GET    /api/studies/{id}/      - Study details
PUT    /api/studies/{id}/      - Update study
DELETE /api/studies/{id}/      - Archive study
GET    /api/studies/{id}/members/ - Study members
```

### Users API
```
GET    /api/users/             - List users
GET    /api/users/{id}/        - User details
PUT    /api/users/{id}/        - Update user
POST   /api/users/{id}/activate/   - Activate user
POST   /api/users/{id}/deactivate/ - Deactivate user
```

### Other Endpoints
```
GET    /api/roles/             - List roles
GET    /api/permissions/       - List permissions
GET    /api/departments/       - List departments
GET    /api/designations/      - List designations
GET    /api/organizations/     - List organizations
```

Visit `/api/` (when logged in) for interactive API browsing.

## 🔐 Security Features

### Built-In Security
- ✅ CSRF protection on all forms
- ✅ SQL injection prevention via ORM
- ✅ XSS protection in templates
- ✅ Secure password hashing (PBKDF2)
- ✅ Session-based authentication
- ✅ Permission-based access control

### Production Security
- ✅ HTTPS/SSL support (auto-enabled on Railway)
- ✅ Security headers (HSTS, CSP, X-Frame-Options)
- ✅ Secure cookies (HttpOnly, Secure, SameSite)
- ✅ Environment-based secrets
- ✅ Debug mode disabled in production
- ✅ Allowed hosts validation

### Best Practices
- Never commit secrets to repository
- Use strong, unique passwords
- Enable two-factor authentication (if supported)
- Regular security updates
- Audit logs for sensitive operations

## 🧪 Testing

Run all tests:
```bash
python manage.py test
```

Run specific test module:
```bash
python manage.py test polls.tests
```

Run specific test class:
```bash
python manage.py test polls.tests.ClinicalStudyTestCase
```

Run with coverage:
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## 🔄 Database Migrations

Create new migration after model changes:
```bash
python manage.py makemigrations
```

Apply pending migrations:
```bash
python manage.py migrate
```

List all migrations:
```bash
python manage.py showmigrations
```

Rollback to specific migration:
```bash
python manage.py migrate app_name migration_name
```

## 📊 Admin Interface

Access at: `http://localhost:8000/admin/`

Features:
- User management and role assignment
- Study creation and management
- Permission administration
- System-wide data browsing
- Bulk actions and filtering
- Search functionality

## 🐛 Troubleshooting

### Static Files Not Loading
```bash
python manage.py collectstatic --clear --noinput
```

### Database Migration Errors
```bash
python manage.py migrate --fake-initial
python manage.py migrate --plan  # See what will run
```

### Permission Denied Errors
- Check user role assignments in Admin
- Verify @login_required decorators
- Check API permission classes

### 502 Bad Gateway (Production)
- Check application logs
- Verify environment variables
- Check database connection
- Review error logs on deployment platform

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 👥 Author

**Ajit Singh** (GitHub: [@Ironnatron](https://github.com/Ironnatron))

## 📞 Support

### Documentation
- [RAILWAY_SETUP.md](RAILWAY_SETUP.md) - Railway deployment guide
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - All deployment methods
- [INDEX.md](INDEX.md) - Complete file index
- [SETTINGS_CHANGES.md](SETTINGS_CHANGES.md) - Configuration details

### External Resources
- [Django Docs](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Railway Docs](https://docs.railway.app/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

## ⭐ Show Your Support

If you found this project helpful, please star this repository!

---

**Made with ❤️ by Ajit Singh**  
Last Updated: November 2024  
Status: ✅ Production Ready