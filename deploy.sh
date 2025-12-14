#!/bin/bash

# Quick deployment script for serverless platforms
# Supports Vercel and Netlify deployment

set -e

PLATFORM=""
ENVIRONMENT="development"
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    --env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      echo "Usage: $0 --platform <vercel|netlify> [--env <development|staging|production>] [--verbose]"
      echo ""
      echo "Deploy to serverless platforms with pre-configured settings"
      echo ""
      echo "Options:"
      echo "  --platform    Platform to deploy to (vercel or netlify)"
      echo "  --env         Environment to deploy to (development, staging, or production)"
      echo "  --verbose     Enable verbose output"
      echo "  --help        Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0 --platform vercel --env production"
      echo "  $0 --platform netlify --env staging --verbose"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Validate platform
if [[ -z "$PLATFORM" ]]; then
    echo "❌ Error: Platform must be specified"
    echo "Use --platform <vercel|netlify>"
    exit 1
fi

if [[ "$PLATFORM" != "vercel" && "$PLATFORM" != "netlify" ]]; then
    echo "❌ Error: Platform must be 'vercel' or 'netlify'"
    exit 1
fi

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo "❌ Error: Environment must be 'development', 'staging', or 'production'"
    exit 1
fi

echo "🚀 Starting deployment to $PLATFORM ($ENVIRONMENT)"
echo "=========================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [[ $NODE_VERSION -lt 18 ]]; then
    echo "❌ Node.js version $NODE_VERSION is too old. Please install Node.js 18+."
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION detected"

# Check package managers
if [[ "$PLATFORM" == "vercel" ]]; then
    if ! command -v vercel &> /dev/null; then
        echo "📦 Installing Vercel CLI..."
        npm install -g vercel
    fi
    echo "✅ Vercel CLI detected"
elif [[ "$PLATFORM" == "netlify" ]]; then
    if ! command -v netlify &> /dev/null; then
        echo "📦 Installing Netlify CLI..."
        npm install -g netlify-cli
    fi
    echo "✅ Netlify CLI detected"
fi

# Install dependencies
echo "📦 Installing dependencies..."

# Frontend dependencies
if [[ ! -d "frontend/node_modules" ]]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
else
    echo "✅ Frontend dependencies already installed"
fi

# Backend dependencies
if [[ ! -d "venv" ]]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Installing backend dependencies..."
source venv/bin/activate
pip install -r requirements-serverless.txt

if [[ $VERBOSE == true ]]; then
    echo "✅ Dependencies installed (verbose mode)"
else
    echo "✅ Dependencies installed"
fi

# Build project
echo "🔨 Building project..."

if [[ "$PLATFORM" == "vercel" ]]; then
    ./build-vercel.sh
elif [[ "$PLATFORM" == "netlify" ]]; then
    ./build-netlify.sh
fi

# Deploy based on platform
echo "🚀 Deploying to $PLATFORM..."

if [[ "$PLATFORM" == "vercel" ]]; then
    if [[ "$ENVIRONMENT" == "production" ]]; then
        vercel --prod --yes
    else
        vercel --confirm
    fi
elif [[ "$PLATFORM" == "netlify" ]]; then
    if [[ "$ENVIRONMENT" == "production" ]]; then
        cd frontend
        netlify deploy --build --prod --confirm
        cd ..
    else
        cd frontend
        netlify deploy --build --confirm
        cd ..
    fi
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Check the deployment URL in the output above"
echo "2. Set environment variables in the platform dashboard"
echo "3. Test the health endpoints:"
echo "   - Health check: /api/health/serverless"
echo "   - Binary status: /api/binaries/status"
echo "4. Monitor logs for any issues"
echo ""
echo "For troubleshooting, see DEPLOYMENT.md"
echo ""
echo "Environment variables to set in platform dashboard:"
echo "• PYTHONPATH"
echo "• PROJECT_ROOT"  
echo "• TMPDIR"
echo "• HOME"