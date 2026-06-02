"""
Test script for streaming jobs - shows real-time streaming
"""

import urllib.request
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def submit_streaming_job(text):
    """Submit a streaming job"""
    url = f"{BASE_URL}/submit_stream_job"
    data = json.dumps({"text": text}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result['job_id']
    except Exception as e:
        print(f"Error submitting job: {e}")
        return None

def stream_job_results(job_id):
    """Stream job results in real-time"""
    url = f"{BASE_URL}/stream_job/{job_id}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            print("\n--- Streaming Output (real-time) ---")
            print("=" * 50)
            
            # Read byte by byte to show streaming
            while True:
                chunk = response.read(1)  # Read 1 byte at a time
                if not chunk:
                    break
                
                # Print immediately without buffering
                sys.stdout.write(chunk.decode('utf-8', errors='ignore'))
                sys.stdout.flush()
            
            print("\n" + "=" * 50)
            print("--- Streaming Complete ---\n")
            
    except Exception as e:
        print(f"Error streaming job: {e}")

def test_streaming():
    print("=" * 60)
    print("Streaming Job Test")
    print("=" * 60)
    print()
    
    # Test case 1: Negative sentiment
    print("Test 1: Streaming with negative words")
    print("-" * 60)
    text = "This is a terrible and bad product with awful quality"
    print(f"Input text: '{text}'")
    
    job_id = submit_streaming_job(text)
    if not job_id:
        print("Failed to submit job")
        return
    
    print(f"Job ID: {job_id}")
    print(f"Starting stream...\n")
    
    start_time = time.time()
    stream_job_results(job_id)
    elapsed = time.time() - start_time
    
    print(f"Total streaming time: {elapsed:.2f} seconds")
    print()
    
    # Test case 2: Positive sentiment
    print("\n" + "=" * 60)
    print("Test 2: Streaming with positive text")
    print("-" * 60)
    text2 = "This is a good product"
    print(f"Input text: '{text2}'")
    
    job_id2 = submit_streaming_job(text2)
    if not job_id2:
        print("Failed to submit job")
        return
    
    print(f"Job ID: {job_id2}")
    print(f"Starting stream...\n")
    
    start_time = time.time()
    stream_job_results(job_id2)
    elapsed = time.time() - start_time
    
    print(f"Total streaming time: {elapsed:.2f} seconds")
    print()

if __name__ == "__main__":
    print("\n🚀 Make sure your FastAPI server is running on http://localhost:8000")
    print()
    
    try:
        test_streaming()
        print("=" * 60)
        print("✓ Streaming test completed!")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
