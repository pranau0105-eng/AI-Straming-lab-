#!/bin/bash

echo "=============================================="
echo "  /ws/whisper Flow Testing Suite"
echo "=============================================="
echo ""
echo "This tests the complete flow:"
echo "  Mic → WebSocket → AudioRingBuffer → Whisper → Results"
echo ""
echo "=============================================="
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "❌ Server is not running!"
    echo ""
    echo "Please start the server first:"
    echo "  uvicorn main:app --reload"
    echo ""
    exit 1
fi

echo "✅ Server is running"
echo ""
echo "Choose a test:"
echo "  1) Synthetic audio test (no microphone needed)"
echo "  2) Live microphone test"
echo "  3) Silent audio test"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "Running synthetic audio test..."
        echo ""
        python3 test_whisper_flow.py
        ;;
    2)
        echo ""
        echo "Running live microphone test..."
        echo "Make sure you have a microphone connected!"
        echo ""
        sleep 2
        python3 test_whisper_mic.py
        ;;
    3)
        echo ""
        echo "Running silent audio test..."
        echo ""
        python3 test_whisper_flow.py silence
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
