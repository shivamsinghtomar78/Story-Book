#!/usr/bin/env bash
# Strict error handling
set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Enable debugging output
set -x

echo "=========================================="
echo "🚀 Starting Render Build Process"
echo "=========================================="

# Print environment info
echo "📋 Environment Information:"
echo "  - Working Directory: $(pwd)"
echo "  - User: $(whoami)"
echo "  - Shell: $SHELL"
echo "  - PATH: $PATH"

# Store the project root directory
PROJECT_ROOT="$(pwd)"
echo "  - Project Root: $PROJECT_ROOT"

# ==========================================
# 1. INSTALL PYTHON DEPENDENCIES
# ==========================================
echo ""
echo "=========================================="
echo "📦 Step 1: Installing Python Dependencies"
echo "=========================================="

if [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: requirements.txt not found in $PROJECT_ROOT"
    exit 1
fi

pip install -r requirements.txt
echo "✅ Python dependencies installed"

# ==========================================
# 2. BUILD FRONTEND
# ==========================================
echo ""
echo "=========================================="
echo "🎨 Step 2: Building Frontend Application"
echo "=========================================="

# Define frontend directory
FRONTEND_DIR="$PROJECT_ROOT/frontend"
echo "  - Frontend Directory: $FRONTEND_DIR"

# Verify frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ ERROR: Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Change to frontend directory
cd "$FRONTEND_DIR" || {
    echo "❌ ERROR: Failed to change to frontend directory"
    exit 1
}

echo "✅ Changed to frontend directory: $(pwd)"

# Check Node.js and npm availability
echo ""
echo "📍 Checking Node.js Environment:"
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js is not installed or not in PATH"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ ERROR: npm is not installed or not in PATH"
    exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "  ✅ Node.js: $NODE_VERSION"
echo "  ✅ npm: $NPM_VERSION"

# Verify package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ ERROR: package.json not found in $FRONTEND_DIR"
    exit 1
fi

echo "  ✅ package.json found"

# Clean previous build artifacts (if any)
echo ""
echo "🧹 Cleaning previous build artifacts..."
if [ -d "dist" ]; then
    rm -rf dist
    echo "  ✅ Removed old dist/ folder"
fi

if [ -d "node_modules" ]; then
    echo "  ℹ️  node_modules/ exists (will be updated by npm install)"
fi

# Install npm dependencies
echo ""
echo "📥 Installing npm dependencies..."
npm ci --prefer-offline --no-audit || npm install

echo "✅ npm dependencies installed"

# List installed packages (for debugging)
echo ""
echo "📦 Installed packages:"
npm list --depth=0 || true  # Don't fail if some packages missing

# Run the build
echo ""
echo "🔨 Building frontend with Vite..."
NODE_ENV=production npm run build || {
    echo "❌ ERROR: Frontend build failed!"
    echo "📂 Frontend directory contents:"
    ls -laR
    exit 1
}

# ==========================================
# 3. VERIFY BUILD OUTPUT
# ==========================================
echo ""
echo "=========================================="
echo "🔍 Step 3: Verifying Build Output"
echo "=========================================="

# Check if dist directory was created
if [ ! -d "dist" ]; then
    echo "❌ FATAL ERROR: dist/ folder was NOT created!"
    echo "📂 Contents of frontend directory:"
    ls -laR
    exit 1
fi

echo "✅ dist/ folder exists"

# Check if index.html exists
if [ ! -f "dist/index.html" ]; then
    echo "❌ FATAL ERROR: dist/index.html was NOT created!"
    echo "📂 Contents of dist/ directory:"
    ls -laR dist/
    exit 1
fi

echo "✅ dist/index.html exists"

# Show dist contents
echo ""
echo "📂 Build Output (dist/ contents):"
ls -lah dist/
echo ""
echo "📄 Files in dist/:"
find dist/ -type f -exec ls -lh {} \;

# ==========================================
# 4. RETURN TO PROJECT ROOT
# ==========================================
cd "$PROJECT_ROOT" || {
    echo "❌ ERROR: Failed to return to project root"
    exit 1
}

echo ""
echo "✅ Returned to project root: $(pwd)"

# ==========================================
# 5. FINAL VERIFICATION
# ==========================================
echo ""
echo "=========================================="
echo "✅ Build Completed Successfully!"
echo "=========================================="
echo "📊 Summary:"
echo "  ✅ Python dependencies installed"
echo "  ✅ Frontend built successfully"
echo "  ✅ dist/index.html verified"
echo "  ✅ Ready for deployment"
echo "=========================================="
