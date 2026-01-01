#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Install backend Node.js dependencies
cd backend
npm install
cd ..

# Install frontend dependencies and build
cd frontend
npm install
npm run build
cd ..
