#!/bin/bash

echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install backend Node.js dependencies
echo "Installing backend dependencies..."
cd backend
npm install
cd ..

# Install frontend dependencies and build
echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Building React frontend..."
npm run build

echo "Build complete! Checking build folder..."
ls -la build/

cd ..

echo "Build process finished!"
