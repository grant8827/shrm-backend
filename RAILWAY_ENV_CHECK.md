# Railway Environment Variables Check Guide

## How to Check Your Railway Environment Variables

### Option 1: Railway Dashboard (Easiest)
1. Go to https://railway.app/dashboard
2. Click on your backend project (shrm-backend or similar)
3. Click on "Variables" tab
4. Check which variables are set

### Option 2: Railway CLI
```bash
cd backend
railway login
railway link  # Select your backend project
railway variables
```

## What to Look For

### ✅ CORRECT Configuration (PostgreSQL via DATABASE_URL)
Your Railway environment should have:
- ✓ `DATABASE_URL=postgresql://postgres:cIEHVGVBrmKtceHzOhyiNeBNCOJxdWma@gondola.proxy.rlwy.net:16249/railway`
- ✓ `DEBUG=False`
- ✓ `ALLOWED_HOSTS=...` (should include your Railway domain)
- ✗ NO individual DB_* variables (DB_CONNECTION, DB_HOST, DB_PORT, etc.)

### ❌ PROBLEM Configuration
If you see these in Railway:
- `DB_CONNECTION=postgresql`
- `DB_HOST=gondola.proxy.rlwy.net`
- `DB_PORT=16249`
- `DB_DATABASE=railway`
- `DB_USERNAME=postgres`
- `DB_PASSWORD=...`

**AND** `DATABASE_URL` is missing or different, this means:
- Your app is using a different database configuration
- The user might not exist in that database
- You need to either:
  1. Remove the DB_* variables and keep only DATABASE_URL
  2. OR create the user in whatever database it's connecting to

## Quick Fix

If `DATABASE_URL` is missing or wrong in Railway:

1. Add/Update the variable in Railway dashboard:
   ```
   DATABASE_URL=postgresql://postgres:cIEHVGVBrmKtceHzOhyiNeBNCOJxdWma@gondola.proxy.rlwy.net:16249/railway
   ```

2. Remove these if they exist:
   - DB_CONNECTION
   - DB_HOST
   - DB_PORT
   - DB_DATABASE
   - DB_USERNAME
   - DB_PASSWORD

3. Redeploy the backend service

## Check Current Database Connection

Run this locally to see what database your production is using:
```bash
curl https://shrm-backend-production.up.railway.app/api/health/
```

The response or logs should show which database it's connecting to.
