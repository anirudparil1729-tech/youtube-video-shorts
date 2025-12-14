# Serverless Deployment Guide

This guide provides complete instructions for deploying the Video Processing API to serverless platforms (Vercel and Netlify) with both frontend and backend components.

## Overview

The project consists of:

- **Frontend**: Next.js 14 application with React, TypeScript, Tailwind CSS
- **Backend**: FastAPI Python application with AI/ML capabilities
- **Deployment**: Serverless functions with on-demand binary downloads for FFmpeg and Whisper

## Prerequisites

### Required Tools

```bash
# Node.js 18+ and npm
npm --version  # Should be 8+

# Python 3.9+ and pip
python --version  # Should be 3.9+
pip --version

# Platform CLIs (optional, for CLI deployment)
npm install -g vercel  # Vercel CLI
npm install -g netlify-cli  # Netlify CLI
```

### Environment Variables

Create `.env.local` files in the appropriate directories:

**For Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=https://your-domain.vercel.app/api
NEXT_PUBLIC_WS_URL=wss://your-domain.vercel.app
```

**For Backend** (set in platform dashboard):
```env
PYTHONPATH=/api
PROJECT_ROOT=/
TMPDIR=/tmp
HOME=/tmp
```

## Deployment Options

### Option 1: Vercel Deployment

Vercel provides the best integration for this Next.js + FastAPI setup.

#### 1. Prepare Environment

```bash
# Clone and setup project
git clone <repository>
cd video-processing-app
npm install
pip install -r requirements-serverless.txt
```

#### 2. Configure Vercel

**Automatic Setup:**
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Initialize project
vercel

# Set environment variables
vercel env add PYTHONPATH production
# Enter: /api

vercel env add PROJECT_ROOT production  
# Enter: /

vercel env add TMPDIR production
# Enter: /tmp

vercel env add HOME production
# Enter: /tmp
```

**Manual Setup:**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Import your repository
3. Configure project settings:
   - Framework Preset: Next.js
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/.next`
   - Install Command: `cd frontend && npm install && pip install -r requirements-serverless.txt`

#### 3. Deploy

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

#### 4. Verify Deployment

Visit your deployment URL and check:
- Frontend loads at `/`
- API health check at `/api/health/serverless`
- Binary status at `/api/binaries/status`

### Option 2: Netlify Deployment

Netlify also supports serverless functions with Python runtime.

#### 1. Prepare Environment

```bash
# Same as Vercel setup
git clone <repository>
cd video-processing-app
npm install
```

#### 2. Configure Netlify

**Automatic Setup:**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Initialize project
netlify init

# Build and deploy
netlify deploy --build --prod
```

**Manual Setup:**
1. Go to [Netlify Dashboard](https://app.netlify.com/)
2. New site from Git
3. Connect your repository
4. Configure build settings:
   - Build command: `cd frontend && npm run build`
   - Publish directory: `frontend/.next`
   - Functions directory: `netlify/functions`

#### 3. Environment Variables

In Netlify dashboard, go to Site Settings > Environment Variables:

```env
PYTHONPATH=/opt/python
TMPDIR=/tmp
HOME=/tmp
```

#### 4. Verify Deployment

Visit your site and check the same endpoints as Vercel.

## Build Scripts

Pre-configured build scripts are available:

### Vercel Build Script
```bash
./build-vercel.sh
```

### Netlify Build Script
```bash
./build-netlify.sh
```

These scripts create optimized builds in `vercel-build/` and `netlify-build/` directories.

## Architecture Details

### Serverless Function Architecture

The `api/index.py` file serves as a serverless adapter that:

1. **Binary Management**: Downloads FFmpeg on-demand on first use
2. **Environment Setup**: Configures Python path and temp directories  
3. **FastAPI Integration**: Mounts the main FastAPI application
4. **Health Monitoring**: Provides binary status endpoints

### Binary Download Strategy

Large binaries are handled via on-demand download:

```python
# Downloads happen on first API call
FFMPEG_PATH = None

def ensure_binaries():
    global FFMPEG_PATH
    if not FFMPEG_PATH:
        FFMPEG_PATH = setup_ffmpeg(temp_dir)
```

**Benefits:**
- Reduces cold start times
- Minimizes deployment package size
- Enables use of latest binary versions
- Reduces memory footprint

### Limitations & Workarounds

#### Cold Start Performance
- **Issue**: First request takes 10-30 seconds (binary download)
- **Workaround**: Use平台的预热功能 (Vercel: Hobby/Pro, Netlify: Pro)

#### Memory Constraints  
- **Issue**: 1024MB memory limit
- **Workaround**: Optimized dependencies, streaming processing

#### Execution Time
- **Issue**: 300 second timeout limit
- **Workaround**: Async processing, chunked uploads

#### Response Size
- **Issue**: 10MB (Vercel) / 6MB (Netlify) response limit
- **Workaround**: Streaming responses, external storage

## CI/CD Integration

GitHub Actions workflow is configured in `.github/workflows/ci-cd.yml`:

### Automated Checks
- **Backend**: Linting, type checking, tests
- **Frontend**: Linting, type checking, tests
- **Docker**: Build and security scanning
- **Deployment**: Automatic deployment on push

### Setup Required
Add these secrets to your GitHub repository:

```bash
# Vercel
VERCEL_TOKEN=<your-vercel-token>
VERCEL_ORG_ID=<your-org-id>
VERCEL_PROJECT_ID=<your-project-id>

# Netlify  
NETLIFY_AUTH_TOKEN=<your-auth-token>
NETLIFY_SITE_ID=<your-site-id>

# Docker Hub
DOCKERHUB_USERNAME=<your-username>
DOCKERHUB_TOKEN=<your-token>
```

### Workflow Triggers
- **Push to develop**: Deploys to Vercel staging
- **Push to main**: Deploys to Netlify
- **Tags v***: Deploys to Vercel production

## Monitoring & Debugging

### Health Checks

```bash
# Serverless platform health
curl https://your-domain.vercel.app/api/health/serverless

# Binary dependencies status
curl https://your-domain.vercel.app/api/binaries/status

# Full API health
curl https://your-domain.vercel.app/api/health
```

### Platform Logs

**Vercel:**
- Dashboard > Functions > View Function Logs
- CLI: `vercel logs <deployment-url>`

**Netlify:**
- Dashboard > Functions > View Logs
- CLI: `netlify functions:log`

### Common Issues

#### Import Errors
```python
# Ensure PYTHONPATH is set correctly
PYTHONPATH=/api
```

#### Binary Download Failures
```bash
# Check temp directory permissions
TMPDIR=/tmp
HOME=/tmp
```

#### Memory Issues
- Monitor with binary status endpoint
- Consider reducing model sizes
- Implement streaming for large files

## Security Considerations

### Environment Variables
- Store sensitive data in platform dashboards
- Never commit `.env` files
- Use different variables per environment

### CORS Configuration
Headers are pre-configured for development. Update for production:

```json
{
  "Access-Control-Allow-Origin": "https://your-domain.com"
}
```

### Rate Limiting
Consider implementing rate limiting for production:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

## Performance Optimization

### Caching Strategy
- Binary downloads cached in `/tmp`
- Consider CDN for static assets
- Enable Next.js image optimization

### Bundle Optimization
- Serverless dependencies minimized in `requirements-serverless.txt`
- Frontend uses Next.js automatic optimization

## Troubleshooting

### Deployment Issues
1. Check build logs in platform dashboard
2. Verify environment variables are set
3. Test locally with build scripts

### Runtime Issues
1. Check function logs for errors
2. Verify binary download success
3. Monitor memory and timeout metrics

### Performance Issues
1. Enable function logs for cold start analysis
2. Consider platform plan upgrades for better performance
3. Implement connection pooling for database calls

## Support

For issues related to:
- **Platform deployment**: Check respective documentation
  - [Vercel Docs](https://vercel.com/docs)
  - [Netlify Functions](https://docs.netlify.com/functions/overview/)
- **Application issues**: Check API logs and binary status endpoints
- **CI/CD issues**: Check GitHub Actions workflow logs

## Next Steps

1. Deploy to staging environment first
2. Run end-to-end tests
3. Configure monitoring and alerts  
4. Set up custom domain
5. Enable SSL certificates
6. Configure backup strategies