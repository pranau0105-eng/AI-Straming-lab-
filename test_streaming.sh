#!/bin/bash

echo "============================================================"
echo "Testing Streaming Job"
echo "============================================================"
echo ""

BASE_URL="http://localhost:8000"

# Step 1: Submit a streaming job
echo "Step 1: Submitting streaming job..."
response=$(curl -X POST "$BASE_URL/submit_stream_job" \
  -H "Content-Type: application/json" \
  -d '{"text":"This is a terrible and bad product"}' \
  -s)

echo "Response: $response"
job_id=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $job_id"
echo ""

# Step 2: Stream the job results
echo "Step 2: Streaming results (should appear word by word)..."
echo "-----------------------------------------------------------"
echo ""

# Use curl with --no-buffer to see streaming in real-time
curl -X GET "$BASE_URL/stream_job/$job_id" --no-buffer

echo ""
echo ""
echo "============================================================"
echo "Test completed!"
echo "============================================================"
