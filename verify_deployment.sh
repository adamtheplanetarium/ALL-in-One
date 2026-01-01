#!/bin/bash

# 🚀 DEPLOYMENT VERIFICATION SCRIPT
# Run this after deployment to verify everything works

echo "=========================================="
echo "🔍 ALL-in-One Deployment Verification"
echo "=========================================="
echo ""

# Backend URL
BACKEND_URL="https://all-in-one-tdxd.onrender.com"
FRONTEND_URL="https://allinone-frontend.onrender.com"

echo "1️⃣ Checking Backend API Health..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/health)
if [ "$HEALTH_CHECK" = "200" ]; then
    echo "   ✅ Backend API is healthy"
else
    echo "   ❌ Backend API failed (Status: $HEALTH_CHECK)"
fi
echo ""

echo "2️⃣ Checking Backend API Endpoints..."
API_CHECK=$(curl -s $BACKEND_URL)
if echo "$API_CHECK" | grep -q "ALL-in-One"; then
    echo "   ✅ Backend API responding correctly"
    echo "   Available endpoints:"
    echo "$API_CHECK" | grep -o '"[^"]*": "/api/[^"]*"' | sed 's/"//g' | sed 's/^/      - /'
else
    echo "   ❌ Backend API not responding correctly"
fi
echo ""

echo "3️⃣ Checking Frontend..."
FRONTEND_CHECK=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL)
if [ "$FRONTEND_CHECK" = "200" ]; then
    echo "   ✅ Frontend is accessible"
else
    echo "   ❌ Frontend not accessible (Status: $FRONTEND_CHECK)"
fi
echo ""

echo "=========================================="
echo "📊 DEPLOYMENT STATUS SUMMARY"
echo "=========================================="
echo ""
echo "Backend API:  $BACKEND_URL"
echo "Frontend UI:  $FRONTEND_URL"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open $FRONTEND_URL"
echo "   2. Register a new account"
echo "   3. Start creating campaigns!"
echo ""
echo "=========================================="
