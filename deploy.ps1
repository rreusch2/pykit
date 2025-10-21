# PowerShell Deployment Script for Professor Lock ChatKit Server
# Run this from the pykit directory

Write-Host "🚀 Deploying Professor Lock ChatKit Server" -ForegroundColor Green
Write-Host "=========================================="

# Check if we're in the right directory
if (!(Test-Path "pp_server.py")) {
    Write-Host "❌ Please run this script from the pykit directory" -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (!(Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "📝 Please edit .env with your actual values" -ForegroundColor Yellow
    } else {
        Write-Host "❌ .env.example not found. Creating basic .env..." -ForegroundColor Red
        @"
# Database Configuration
DATABASE_URL=postgresql://localhost/chatkit
SUPABASE_URL=https://iriaegoipkjtktitpary.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key

# API Keys
OPENAI_API_KEY=your_openai_api_key
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_google_cx

# Backend URLs
NEXT_PUBLIC_BACKEND_URL=https://zooming-rebirth-production-a305.up.railway.app
FRONTEND_URL=https://www.predictive-play.com

# Server Configuration
PORT=8000
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
    }
}

# Install dependencies if virtual environment doesn't exist
if (!(Test-Path "venv")) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Blue
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Blue
pip install -r requirements.txt

# Install package in development mode
Write-Host "🔗 Installing ChatKit package..." -ForegroundColor Blue
pip install -e .

# Check if Railway CLI is installed
Write-Host "🚂 Checking Railway CLI..." -ForegroundColor Blue
try {
    railway --version | Out-Null
    Write-Host "✅ Railway CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Railway CLI not found. Installing..." -ForegroundColor Red
    npm install -g @railway/cli
}

# Login to Railway if needed
Write-Host "🔐 Checking Railway authentication..." -ForegroundColor Blue
try {
    railway status | Out-Null
    Write-Host "✅ Already logged in to Railway" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Please login to Railway:" -ForegroundColor Yellow
    railway login
}

# Deploy to Railway
Write-Host "🚀 Deploying to Railway..." -ForegroundColor Green
Write-Host "This will deploy your Professor Lock ChatKit server with:" -ForegroundColor Cyan
Write-Host "- Advanced betting analysis tools" -ForegroundColor Cyan
Write-Host "- Interactive parlay builders" -ForegroundColor Cyan
Write-Host "- StatMuse integration" -ForegroundColor Cyan
Write-Host "- Live odds comparison widgets" -ForegroundColor Cyan

$confirm = Read-Host "Continue with deployment? (y/N)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    railway up
    
    Write-Host ""
    Write-Host "🎉 Deployment complete!" -ForegroundColor Green
    Write-Host "Your Professor Lock server is now live on Railway" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Note your Railway deployment URL" -ForegroundColor White
    Write-Host "2. Update your web app to use this custom server" -ForegroundColor White
    Write-Host "3. Test the integration with /professor-lock/test" -ForegroundColor White
    
} else {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 To test locally first, run:" -ForegroundColor Cyan
Write-Host "uvicorn app:app --reload --port 8000" -ForegroundColor White
