"""
Test script for Job Queue with Worker Pool
Tests the async job submission and worker pool functionality
"""

import time
import asyncio
import sys

# Simple HTTP client using urllib instead of httpx
import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000"

def submit_job(text):
    """Submit a job and return the job_id"""
    url = f"{BASE_URL}/submit-job?text={urllib.parse.quote(text)}"
    try:
        with urllib.request.urlopen(url, data=b'', timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['job_id']
    except Exception as e:
        print(f"Error submitting job: {e}")
        return None

def get_job_status(job_id):
    """Get the status of a job"""
    url = f"{BASE_URL}/job-status/{job_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": "Job not found"}
        return {"error": str(e)}
    except Exception as e:
        print(f"Error getting job status: {e}")
        return {"error": str(e)}

def test_single_job():
    """Test 1: Submit and track a single job"""
    print("=" * 70)
    print("Test 1: Single Job Submission")
    print("=" * 70)
    
    text = "This is a good product"
    print(f"\nSubmitting job with text: '{text}'")
    
    job_id = submit_job(text)
    if not job_id:
        print("Failed to submit job")
        return
    
    print(f"Job submitted! Job ID: {job_id}")
    
    # Poll for job completion
    print("\nPolling job status...")
    for i in range(10):
        time.sleep(0.5)
        status = get_job_status(job_id)
        print(f"  [{i*0.5:.1f}s] Status: {status.get('status', 'unknown')}")
        
        if status.get('status') == 'done':
            print(f"\n✓ Job completed!")
            print(f"  Result: {status.get('result')}")
            break
    else:
        print("\n✗ Job did not complete in time")
    
    print()

def test_multiple_jobs():
    """Test 2: Submit multiple jobs to test worker pool"""
    print("=" * 70)
    print("Test 2: Multiple Jobs (Worker Pool Test)")
    print("=" * 70)
    print(f"\nMAX_WORKERS = 2")
    print(f"Submitting 5 jobs concurrently...\n")
    
    test_texts = [
        "good product",
        "bad service", 
        "excellent quality",
        "terrible experience",
        "neutral item"
    ]
    
    start_time = time.time()
    
    # Submit all jobs
    job_ids = []
    for i, text in enumerate(test_texts, 1):
        job_id = submit_job(text)
        if job_id:
            job_ids.append((job_id, text))
            print(f"  Job {i} submitted: {job_id[:8]}... (text: '{text}')")
    
    print(f"\n{len(job_ids)} jobs submitted in {time.time() - start_time:.2f}s")
    
    # Check immediate status
    print("\n--- Immediate Status Check ---")
    for job_id, text in job_ids:
        status = get_job_status(job_id)
        print(f"  {job_id[:8]}: {status.get('status', 'unknown')}")
    
    # Wait and check progress
    print("\n--- Waiting for completion ---")
    completed = set()
    
    for check in range(12):
        time.sleep(1)
        statuses = {}
        for job_id, _ in job_ids:
            if job_id not in completed:
                status = get_job_status(job_id)
                job_status = status.get('status', 'unknown')
                statuses[job_status] = statuses.get(job_status, 0) + 1
                if job_status == 'done':
                    completed.add(job_id)
        
        status_str = ", ".join([f"{k}: {v}" for k, v in statuses.items()])
        print(f"  [{check+1}s] {status_str} (completed: {len(completed)}/{len(job_ids)})")
        
        if len(completed) == len(job_ids):
            break
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Final results
    print("\n--- Final Results ---")
    for i, (job_id, text) in enumerate(job_ids, 1):
        status = get_job_status(job_id)
        result = status.get('result', 'N/A')
        print(f"  Job {i} ({text}): {status.get('status')} - {result}")
    
    print(f"\n📊 Performance:")
    print(f"  Total jobs: {len(job_ids)}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Expected: ~3s (with 2 workers processing 5 jobs)")
    print(f"  Completed: {len(completed)}/{len(job_ids)}")
    print()

def test_queue_behavior():
    """Test 3: Test queue behavior - jobs should wait if workers are busy"""
    print("=" * 70)
    print("Test 3: Queue Behavior")
    print("=" * 70)
    print("\nSubmitting 6 jobs rapidly to observe queuing...\n")
    
    job_ids = []
    for i in range(6):
        job_id = submit_job(f"test message {i}")
        if job_id:
            job_ids.append(job_id)
            print(f"  Submitted job {i+1}: {job_id[:8]}...")
    
    print(f"\n{len(job_ids)} jobs submitted")
    print("\nObserving execution pattern (should show max 2 running at a time):")
    
    for check in range(8):
        time.sleep(1)
        running = 0
        pending = 0
        done = 0
        
        for job_id in job_ids:
            status = get_job_status(job_id).get('status', 'unknown')
            if status == 'running':
                running += 1
            elif status == 'pending':
                pending += 1
            elif status == 'done':
                done += 1
        
        print(f"  [{check+1}s] Running: {running}, Pending: {pending}, Done: {done}")
        
        if done == len(job_ids):
            break
    
    print()

if __name__ == "__main__":
    print("\n🚀 Job Queue & Worker Pool Test Suite")
    print("=" * 70)
    print("Make sure your FastAPI server is running on http://localhost:8000")
    print("Start it with: uvicorn main:app --reload")
    print()
    
    try:
        # Run tests
        test_single_job()
        time.sleep(1)
        
        test_multiple_jobs()
        time.sleep(1)
        
        test_queue_behavior()
        
        print("=" * 70)
        print("✓ All tests completed!")
        print("=" * 70)
        
    except urllib.error.URLError:
        print("\n❌ Error: Could not connect to the API server")
        print("   Please start the server first with: uvicorn main:app --reload")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
        sys.exit(1)
