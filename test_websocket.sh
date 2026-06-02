#!/bin/bash

echo "============================================================"
echo "WebSocket Audio Streaming Test (using websocat)"
echo "============================================================"
echo ""

# Check if websocat is installed
if ! command -v websocat &> /dev/null; then
    echo "❌ websocat is not installed"
    echo ""
    echo "To install websocat:"
    echo "  - Ubuntu/Debian: sudo snap install websocat"
    echo "  - Or download from: https://github.com/vi/websocat"
    echo ""
    echo "Alternatively, use the Python test:"
    echo "  python3 test_websocket.py"
    echo ""
    exit 1
fi

WS_URL="ws://localhost:8000/ws/audio/"

echo "Connecting to $WS_URL"
echo ""
echo "Type messages and press Enter to send as binary data"
echo "Press Ctrl+C to exit"
echo "============================================================"
echo ""

# Connect to WebSocket and send text as binary
websocat $WS_URL
