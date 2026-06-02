#!/bin/bash

# Test script for FastAPI with Batcher using curl
# This script sends multiple concurrent requests to demonstrate batching

echo "============================================================"
echo "Testing FastAPI with Batcher Integration (using curl)"
echo "============================================================"
echo ""
echo "Make sure your server is running: uvicorn main:app --reload"
echo ""

BASE_URL="http://localhost:8000"

# Test 1: Single request
echo "Test 1: Single request"
echo "----------------------"
curl -X POST "$BASE_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"texts":"This is a good product"}' \
  -s | python3 -m json.tool
echo ""

# Test 2: Multiple concurrent requests (they should be batched)
echo ""
echo "Test 2: Sending 6 concurrent requests (should be batched)"
echo "---------------------------------------------------------"
echo "Starting requests..."

start_time=$(date +%s.%N)

# Send requests in parallel using background processes
curl -X POST "$BASE_URL/predict" -H "Content-Type: application/json" -d '{"texts":"good product"}' -s > /tmp/result1.json &
curl -X POST "$BASE_URL/predict" -H "Content-Type: application/json" -d '{"texts":"bad service"}' -s > /tmp/result2.json &
curl -X POST "$BASE_URL/predict" -H "Content-Type: application/json" -d '{"texts":"neutral item"}' -s > /tmp/result3.json &
curl -X POST "$BASE_URL/predict" -H "Content-Type: application/json" -d '{"texts":"excellent quality"}' -s > /tmp/result4.json &
curl -X POST "$BASE_URL/predict" -H "Content-Type: application/json" -d '{"texts":"terrible experience"}' -s > /tmp/result5.json &
curl -X POST "$BASE_URL/predict" -H "Content-Type: application/json" -d '{"texts":"average performance"}' -s > /tmp/result6.json &

# Wait for all background processes to complete
wait

end_time=$(date +%s.%N)
elapsed=$(echo "$end_time - $start_time" | bc)

echo ""
echo "Results:"
for i in {1..6}; do
    echo "Request $i: $(cat /tmp/result$i.json | python3 -m json.tool)"
done

echo ""
echo "Total time: ${elapsed} seconds"
echo ""
echo "Analysis:"
echo "  - Without batching: ~6 seconds (6 requests × 1 second each)"
echo "  - With batching: ~${elapsed} seconds"
echo "  - Requests are batched in groups of max 4, with 100ms wait time"
echo ""
echo "============================================================"

# Cleanup
rm -f /tmp/result*.json

# Fetch and display metrics
echo ""
echo "============================================================"
echo "METRICS SUMMARY"
echo "============================================================"
curl -X GET "$BASE_URL/metrics" -s | python3 -m json.tool
echo ""
echo "============================================================"
