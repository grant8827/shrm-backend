# TheraCare Backend Setup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ installed
- pip package manager

### Setup Steps

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run setup script**:
   ```bash
   python setup.py
   ```

   Or run commands individually:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py create_test_users
   ```

5. **Start the server**:
   ```bash
   python manage.py runserver
   ```

## 👤 Default Users Created

The setup creates these test accounts:

| Role | Email (Login) | Password | Access Level |
|------|---------------|----------|--------------|
| **Admin** | `admin@theracare.local` | `AdminPass123!` | Full system access |
| **Therapist** | `dr.smith@theracare.local` | `TherapistPass123!` | Clinical access |
| **Staff** | `staff@theracare.local` | `StaffPass123!` | Administrative access |
| **Client** | `john.doe@email.com` | `ClientPass123!` | Patient portal access |

> 📧 **Important**: Login uses EMAIL ADDRESS, not username!

## 🔧 Manual Superuser Creation

If you prefer to create your own superuser:

```bash
python manage.py create_superuser
```

Or use Django's built-in command:
```bash
python manage.py createsuperuser
```

## 🌐 Access Points

- **API Base**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/

## 🔒 Security Notes

⚠️ **Important**: Change default passwords before production deployment!

The test users are created for development purposes only. In production:
1. Use strong, unique passwords
2. Enable two-factor authentication
3. Implement proper access controls
4. Regular security audits

## 🗄️ Database

The system uses SQLite by default for development. For production, configure PostgreSQL in `settings.py`.

## 📋 Environment Variables

Create a `.env` file in the backend directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional for development)
DATABASE_URL=sqlite:///db.sqlite3

# Security
ENCRYPTION_KEY=your-encryption-key-here

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## 🧪 Running Tests

```bash
# Run all tests
python manage.py test

# With coverage
pytest --cov=.

# Run specific test
python manage.py test users.tests
```

## 📦 Production Deployment

For production deployment:

1. Set `DEBUG=False`
2. Configure proper database (PostgreSQL)
3. Set up proper email backend
4. Configure HTTPS
5. Set up proper logging
6. Use environment variables for secrets

## 🔍 Troubleshooting

### Common Issues:

1. **ImportError**: Make sure virtual environment is activated
2. **Database errors**: Run migrations (`python manage.py migrate`)
3. **Permission denied**: Check file permissions
4. **Port already in use**: Use different port (`python manage.py runserver 8001`)

### Getting Help:

- Check Django logs in `logs/` directory
- Enable debug mode for detailed error messages
- Review the Django documentation

## 📊 Project Structure

```
backend/
├── manage.py              # Django management script
├── setup.py              # Quick setup script
├── requirements.txt      # Python dependencies
├── theracare/           # Main Django project
│   ├── settings.py      # Django settings
│   ├── urls.py          # URL configuration
│   └── wsgi.py          # WSGI application
├── users/               # User management app
├── patients/            # Patient management app
├── appointments/        # Appointment scheduling app
├── core/               # Core utilities
└── templates/          # Email templates
```