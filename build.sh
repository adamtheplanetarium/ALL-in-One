#!/bin/bash

set -e  # Exit on error

echo "===== Starting build process ====="
echo "Current directory: $(pwd)"

# Install Python dependencies
echo "===== Installing Python dependencies ====="
pip install -r requirements.txt

# Install backend Node.js dependencies
echo "===== Installing backend dependencies ====="
cd backend
npm install
cd ..

# Install frontend dependencies and build
echo "===== Installing frontend dependencies ====="
cd frontend

# Check Node version
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"

npm install

echo "===== Building React frontend ====="
CI=false npm run build

# Verify build was successful
if [ -d "build" ]; then
    echo "✅ Build folder created successfully!"
    echo "Build folder location: $(pwd)/build"
    echo "Build folder contents:"
    ls -la build/ | head -20
    
    # Verify index.html exists
    if [ -f "build/index.html" ]; then
        echo "✅ index.html found in build folder"
    else
        echo "❌ ERROR: index.html not found in build folder!"
        exit 1
    fi
else
    echo "❌ ERROR: Build folder not created!"
    echo "Current directory: $(pwd)"
    echo "Directory contents:"
    ls -la
    exit 1
fi

cd ..

echo "===== Verifying final structure ====="
echo "Root directory: $(pwd)"
echo "Checking frontend/build/index.html..."
if [ -f "frontend/build/index.html" ]; then
    echo "✅ Frontend build verified at: $(pwd)/frontend/build/"
else
    echo "❌ ERROR: frontend/build/index.html not found at root level!"
    exit 1
fi

echo "===== Build process finished! ====="
