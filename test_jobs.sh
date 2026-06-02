#!/bin/bash

echo "============================================================"
echo "Testing Job Queue with Worker Pool"
echo "============================================================"
echo ""
echo "Make sure your server is running: uvicorn main:app --reload"
echo ""

BASE_URL="http://localhost:8000"

# Test 1: Submit a single job
echo "Test 1: Submit a single job"
echo "----------------------------"
response=$(curl -X POST "$BASE_URL/submit-job?text=This%20is%20a%20good%20product" -s)
echo "Response: $response"
job_id=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $job_id"
echo ""

# Wait a bit and check status
echo "Waiting 2 seconds..."
sleep 2
echo "Checking job status:"
curl -X GET "$BASE_URL/job-status/$job_id" -s | python3 -m json.tool
echo ""
echo ""

# Test 2: Submit multiple jobs concurrently (more than MAX_WORKERS)
echo "Test 2: Submit 5 jobs concurrently (MAX_WORKERS=2)"
echo "---------------------------------------------------"
echo "Submitting jobs..."

start_time=$(date +%s)

# Submit 5 jobs in parallel
job1=$(curl -X POST "$BASE_URL/submit-job?text=good%20product" -s | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" &)
job2=$(curl -X POST "$BASE_URL/submit-job?text=bad%20service" -s | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" &)
job3=$(curl -X POST "$BASE_URL/submit-job?text=excellent%20quality" -s | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" &)
job4=$(curl -X POST "$BASE_URL/submit-job?text=terrible%20experience" -s | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" &)
job5=$(curl -X POST "$BASE_URL/submit-job?text=neutral%20item" -s | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" &)

wait

echo "Jobs submitted!"
echo ""

# Check all job statuses immediately
echo "Checking statuses immediately (should show pending/running):"
curl -X GET "$BASE_URL/job-status/$job1" -s | python3 -m json.tool 2>/dev/null &
curl -X GET "$BASE_URL/job-status/$job2" -s | python3 -m json.tool 2>/dev/null &
curl -X GET "$BASE_URL/job-status/$job3" -s | python3 -m json.tool 2>/dev/null &
curl -X GET "$BASE_URL/job-status/$job4" -s | python3 -m json.tool 2>/dev/null &
curl -X GET "$BASE_URL/job-status/$job5" -s | python3 -m json.tool 2>/dev/null &
wait
echo ""

# Poll for completion instead of fixed wait
echo "Polling for job completion..."
max_wait=10
for i in $(seq 1 $max_wait); do
    sleep 1
    done_count=0
    
    for job in "$job1" "$job2" "$job3" "$job4" "$job5"; do
        status=$(curl -X GET "$BASE_URL/job-status/$job" -s 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
        if [ "$status" = "done" ]; then
            done_count=$((done_count + 1))
        fi
    done
    
    echo "  [${i}s] Completed: $done_count/5"
    
    if [ $done_count -eq 5 ]; then
        echo "All jobs completed!"
        break
    fi
done
echo ""

# Check final statuses
echo "Final job statuses:"
echo "-------------------"
echo "Job 1:"
curl -X GET "$BASE_URL/job-status/$job1" -s | python3 -m json.tool
echo ""
echo "Job 2:"
curl -X GET "$BASE_URL/job-status/$job2" -s | python3 -m json.tool
echo ""
echo "Job 3:"
curl -X GET "$BASE_URL/job-status/$job3" -s | python3 -m json.tool
echo ""
echo "Job 4:"
curl -X GET "$BASE_URL/job-status/$job4" -s | python3 -m json.tool
echo ""
echo "Job 5:"
curl -X GET "$BASE_URL/job-status/$job5" -s | python3 -m json.tool
echo ""

end_time=$(date +%s)
elapsed=$((end_time - start_time))

echo "-------------------"
echo "Total time: ${elapsed} seconds"
echo ""
echo "Analysis:"
echo "  - MAX_WORKERS = 2 (only 2 jobs can run simultaneously)"
echo "  - 5 jobs × 1 second each = 5 seconds total"
echo "  - Expected time: ~3 seconds (jobs processed in batches of 2)"
echo "  - Actual time: ${elapsed} seconds"
echo ""
echo "============================================================"
