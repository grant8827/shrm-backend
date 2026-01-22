#!/bin/bash
# Script to check Railway environment variables

echo "=========================================="
echo "RAILWAY ENVIRONMENT VARIABLES CHECK"
echo "=========================================="

# Check if railway CLI is logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway CLI"
    echo "Run: railway login"
    exit 1
fi

echo ""
echo "Current Railway project:"
railway status

echo ""
echo "=========================================="
echo "ENVIRONMENT VARIABLES"
echo "=========================================="

# Get all environment variables
railway variables

echo ""
echo "=========================================="
echo "CHECKING KEY VARIABLES"
echo "=========================================="

# Check specific important variables
echo ""
echo "Checking DATABASE_URL..."
if railway variables | grep -q "DATABASE_URL"; then
    echo "✓ DATABASE_URL is set"
    railway variables | grep DATABASE_URL
else
    echo "❌ DATABASE_URL is NOT set"
fi

echo ""
echo "Checking DB_CONNECTION..."
if railway variables | grep -q "DB_CONNECTION"; then
    echo "⚠️  DB_CONNECTION is set (individual DB config)"
    railway variables | grep "DB_"
else
    echo "✓ DB_CONNECTION is NOT set (using DATABASE_URL)"
fi

echo ""
echo "Checking DEBUG..."
if railway variables | grep -q "DEBUG"; then
    railway variables | grep DEBUG
else
    echo "DEBUG not explicitly set (will use default)"
fi

echo ""
echo "=========================================="
echo "RECOMMENDATIONS"
echo "=========================================="
echo ""
echo "For Railway PostgreSQL, you should have:"
echo "  ✓ DATABASE_URL=postgresql://..."
echo "  ✗ DB_CONNECTION, DB_HOST, etc. (not needed)"
echo ""
echo "If DATABASE_URL is missing or different, your app"
echo "is connecting to a different database!"
echo ""
