#!/bin/bash

# Build script for Vercel deployment
# This script prepares the project for Vercel serverless deployment

set -e

echo "🚀 Building for Vercel serverless deployment..."

# Create build directory
BUILD_DIR="vercel-build"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Copy frontend files
echo "📱 Building frontend..."
cd frontend
npm ci
npm run build
cd ..

# Copy built frontend to build directory
cp -r frontend/.next $BUILD_DIR/frontend/
cp -r frontend/public $BUILD_DIR/frontend/ 2>/dev/null || true

# Copy API files
echo "🐍 Preparing API for serverless..."
mkdir -p $BUILD_DIR/api

# Copy essential files for serverless
cp api/index.py $BUILD_DIR/api/
cp requirements-serverless.txt $BUILD_DIR/requirements.txt

# Copy main application (for serverless adapter)
cp main.py $BUILD_DIR/
cp -r app $BUILD_DIR/ 2>/dev/null || true

# Create .vercelignore
cat > $BUILD_DIR/.vercelignore << EOF
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
.git
.gitignore
README.md
.DS_Store
*.pyc
__pycache__
.pytest_cache
.coverage
htmlcov
.venv
venv
.env
node_modules
.next/cache
EOF

# Create deployment info
cat > $BUILD_DIR/DEPLOYMENT.md << EOF
# Vercel Deployment

This build is configured for Vercel serverless deployment.

## Environment Variables

Set these in your Vercel dashboard:

- \`PYTHONPATH\` (default: /api)
- \`PROJECT_ROOT\` (default: /)
- \`TMPDIR\` (default: /tmp)
- \`HOME\` (default: /tmp)

## Functions Configuration

- Runtime: Python 3.11
- Memory: 1024 MB
- Max Duration: 300 seconds
- Max Response Size: 10 MB

## API Endpoints

- \`/api/\` - All API routes
- \`/api/health/serverless\` - Serverless health check
- \`/api/binaries/status\` - Binary dependencies status

## Known Limitations

- Cold starts: First request takes 10-30 seconds
- File size limits: 10MB per response
- Execution time: 300 seconds max
- Memory limit: 1024 MB

## Troubleshooting

Check function logs in Vercel dashboard for errors.
Binary downloads happen on first use and cache in /tmp.
EOF

echo "✅ Build completed successfully!"
echo "📦 Build output: $BUILD_DIR/"
echo ""
echo "To deploy to Vercel:"
echo "1. Install Vercel CLI: npm i -g vercel"
echo "2. Run: vercel --prod"
echo "3. Set environment variables in Vercel dashboard"