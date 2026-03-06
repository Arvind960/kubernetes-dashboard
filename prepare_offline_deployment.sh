#!/bin/bash

# Script to prepare Kubernetes Dashboard for offline/restricted deployment

echo "================================================"
echo "Kubernetes Dashboard - Offline Deployment Prep"
echo "================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create libs directory
echo "[1/4] Creating static/libs directory..."
mkdir -p static/libs/webfonts

# Download vis-network (required for topology)
echo "[2/4] Downloading vis-network library..."
if [ -f "static/libs/vis-network.min.js" ]; then
    echo "  ✓ vis-network.min.js already exists"
else
    wget -q https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js \
         -O static/libs/vis-network.min.js
    if [ $? -eq 0 ]; then
        echo "  ✓ Downloaded vis-network.min.js ($(du -h static/libs/vis-network.min.js | cut -f1))"
    else
        echo "  ✗ Failed to download vis-network.min.js"
    fi
fi

# Download Bootstrap (optional but recommended)
echo "[3/4] Downloading Bootstrap..."
if [ -f "static/libs/bootstrap.min.css" ]; then
    echo "  ✓ Bootstrap CSS already exists"
else
    wget -q https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css \
         -O static/libs/bootstrap.min.css
    [ $? -eq 0 ] && echo "  ✓ Downloaded bootstrap.min.css" || echo "  ✗ Failed"
fi

if [ -f "static/libs/bootstrap.bundle.min.js" ]; then
    echo "  ✓ Bootstrap JS already exists"
else
    wget -q https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js \
         -O static/libs/bootstrap.bundle.min.js
    [ $? -eq 0 ] && echo "  ✓ Downloaded bootstrap.bundle.min.js" || echo "  ✗ Failed"
fi

# Download Font Awesome (optional but recommended)
echo "[4/4] Downloading Font Awesome..."
if [ -f "static/libs/font-awesome.min.css" ]; then
    echo "  ✓ Font Awesome CSS already exists"
else
    wget -q https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css \
         -O static/libs/font-awesome.min.css
    [ $? -eq 0 ] && echo "  ✓ Downloaded font-awesome.min.css" || echo "  ✗ Failed"
fi

# Download Font Awesome fonts
for font in fa-solid-900.woff2 fa-regular-400.woff2 fa-brands-400.woff2; do
    if [ -f "static/libs/webfonts/$font" ]; then
        echo "  ✓ $font already exists"
    else
        wget -q https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/$font \
             -O static/libs/webfonts/$font
        [ $? -eq 0 ] && echo "  ✓ Downloaded $font" || echo "  ✗ Failed"
    fi
done

echo ""
echo "================================================"
echo "Summary"
echo "================================================"
echo "Downloaded libraries:"
ls -lh static/libs/ | grep -v "^d" | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "Font files:"
ls -lh static/libs/webfonts/ 2>/dev/null | grep -v "^d" | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "✓ Dashboard is now ready for offline deployment!"
echo ""
echo "To deploy to production:"
echo "  1. Create tarball: tar -czf k8s-dashboard.tar.gz ."
echo "  2. Transfer to server: scp k8s-dashboard.tar.gz user@server:/tmp/"
echo "  3. Extract: tar -xzf k8s-dashboard.tar.gz"
echo "  4. Run: ./setup_service.sh"
echo ""
