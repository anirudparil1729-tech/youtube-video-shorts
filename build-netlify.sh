#!/bin/bash

# Build script for Netlify deployment
# This script prepares the project for Netlify serverless deployment

set -e

echo "🚀 Building for Netlify serverless deployment..."

# Create build directory
BUILD_DIR="netlify-build"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Build frontend
echo "📱 Building frontend..."
cd frontend
npm ci
npm run build
cd ..

# Copy built frontend
cp -r frontend/.next $BUILD_DIR/
cp -r frontend/public $BUILD_DIR/ 2>/dev/null || true
cp -r frontend/package*.json $BUILD_DIR/

# Prepare serverless functions
echo "🐍 Preparing API for Netlify Functions..."
mkdir -p $BUILD_DIR/netlify/functions

# Copy serverless function
cp api/index.py $BUILD_DIR/netlify/functions/

# Copy requirements for serverless
cp requirements-serverless.txt $BUILD_DIR/netlify/functions/requirements.txt

# Copy main application
cp main.py $BUILD_DIR/
cp -r app $BUILD_DIR/ 2>/dev/null || true

# Create .netlifyignore
cat > $BUILD_DIR/.netlifyignore << EOF
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
.venv
venv
node_modules
.next/cache
netlify.toml
vercel.json
EOF

# Create _redirects file for Netlify
cat > $BUILD_DIR/_redirects << EOF
# API routes
/api/* /.netlify/functions/index/:splat 200

# Frontend routes
/*    /index.html   200
EOF

# Create deployment info
cat > $BUILD_DIR/DEPLOYMENT.md << EOF
# Netlify Deployment

This build is configured for Netlify serverless deployment.

## Environment Variables

Set these in your Netlify dashboard (Site Settings > Environment Variables):

- \`PYTHONPATH\` (value: /opt/python)
- \`TMPDIR\` (value: /tmp)
- \`HOME\` (value: /tmp)

## Functions Configuration

- Runtime: Python 3.11
- Memory: 1024 MB
- Timeout: 300 seconds
- Size Limit: 6 MB per function

## API Endpoints

- \`/api/*\` - Routes to Netlify Functions
- \`/api/health/serverless\` - Serverless health check
- \`/api/binaries/status\` - Binary dependencies status

## Known Limitations

- Cold starts: First request takes 10-30 seconds
- Function size: 6MB compressed limit
- Execution time: 300 seconds max
- Memory limit: 1024 MB

## Troubleshooting

Check function logs in Netlify dashboard for errors.
Binary downloads happen on first use and cache in /tmp.
EOF

echo "✅ Build completed successfully!"
echo "📦 Build output: $BUILD_DIR/"
echo ""
echo "To deploy to Netlify:"
echo "1. Install Netlify CLI: npm install -g netlify-cli"
echo "2. Run: netlify deploy --prod --dir=$BUILD_DIR"
echo "3. Set environment variables in Netlify dashboard"