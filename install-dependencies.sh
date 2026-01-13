#!/bin/bash
# TheraCare Setup Script - Run this to fix the django_extensions error

echo "🏥 TheraCare EHR - Dependency Installation"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this from the backend directory"
    echo "   cd backend && ./install-dependencies.sh"
    exit 1
fi

# Find Python executable
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python is not installed or not in PATH"
    echo "📋 Install Python from: https://python.org/downloads/"
    exit 1
fi

echo "✅ Found Python: $PYTHON_CMD"

# Check pip
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "❌ Error: pip is not available"
    echo "📋 Install pip: curl https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD"
    exit 1
fi

echo "✅ pip is available"

# Install core dependencies first
echo "📦 Installing core Django packages..."
$PYTHON_CMD -m pip install Django djangorestframework django-cors-headers

echo "📦 Installing django-extensions (fixing the error)..."
$PYTHON_CMD -m pip install django-extensions

echo "📦 Installing authentication packages..."
$PYTHON_CMD -m pip install djangorestframework-simplejwt cryptography

echo "📦 Installing API documentation..."
$PYTHON_CMD -m pip install drf-spectacular

echo "📦 Installing utilities..."
$PYTHON_CMD -m pip install python-decouple Pillow

# Try installing all requirements
echo "📦 Installing remaining requirements..."
if $PYTHON_CMD -m pip install -r requirements.txt; then
    echo "✅ All requirements installed successfully!"
else
    echo "⚠️  Some packages failed to install, but core packages are ready"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Run migrations: $PYTHON_CMD manage.py migrate"
echo "2. Create superuser: $PYTHON_CMD manage.py create_test_users"
echo "3. Start server: $PYTHON_CMD manage.py runserver"
echo ""
echo "🌐 Access admin at: http://localhost:8000/admin/"
echo "📧 Login email: admin@theracare.local"
echo "🔑 Password: AdminPass123!"