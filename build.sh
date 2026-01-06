#!/usr/bin/env bash
set -o errexit

echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Build frontend
echo "🎨 Building frontend..."
cd frontend

# Check Node version
echo "📍 Node version: $(node --version)"
echo "📍 NPM version: $(npm --version)"

# Install and build
npm install
npm run build

# Verify dist was created
if [ ! -d "dist" ]; then
    echo "❌ ERROR: dist folder was not created!"
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    echo "❌ ERROR: dist/index.html was not created!"
    exit 1
fi

echo "✅ Frontend build successful - dist folder created"
ls -la dist/

cd ..

echo "✅ Build completed successfully!"
