"""
Test script to demonstrate FastAPI with Batcher integration

This shows how multiple concurrent API requests are batched together
for efficient processing.
"""

import asyncio
import httpx
import time

async def test_api_with_batcher():
    """Send multiple concurrent requests to the API"""
    base_url = "http://localhost:8000"
    
    # Test data
    test_texts = [
        "This product is good",
        "This product is bad",
        "This product is neutral",
        "Amazing and good experience",
        "Terrible and bad service",
        "Just okay, nothing special",
        "Excellent quality",
        "Poor performance",
        "Average product",
        "Wonderful and good"
    ]
    
    print("=" * 70)
    print("Testing FastAPI with Batcher Integration")
    print("=" * 70)
    print(f"\nSending {len(test_texts)} concurrent requests...\n")
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create tasks for concurrent requests
        tasks = [
            client.post(
                f"{base_url}/predict",
                json={"texts": text}
            )
            for text in test_texts
        ]
        
        # Send all requests concurrently
        responses = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Display results
    print("Results:")
    print("-" * 70)
    for i, (text, response) in enumerate(zip(test_texts, responses), 1):
        result = response.json()
        print(f"{i}. '{text}'")
        print(f"   → {result['label']} (score: {result['score']})")
    
    print("-" * 70)
    print(f"\n📊 Performance Summary:")
    print(f"   Total requests: {len(test_texts)}")
    print(f"   Total time: {total_time:.2f} seconds")
    print(f"   Avg time per request: {total_time/len(test_texts):.2f} seconds")
    
    print(f"\n💡 Batching Benefits:")
    print(f"   Without batcher: ~{len(test_texts)} seconds (sequential)")
    print(f"   With batcher: ~{total_time:.2f} seconds (batched)")
    print(f"   Speedup: ~{len(test_texts)/total_time:.1f}x faster!")
    
    print("\n" + "=" * 70)

async def test_single_request():
    """Test a single request"""
    base_url = "http://localhost:8000"
    
    print("\nTesting single request...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/predict",
            json={"texts": "This is a good product"}
        )
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("\n🚀 Make sure your FastAPI server is running on http://localhost:8000")
    print("   Start it with: uvicorn main:app --reload\n")
    
    try:
        asyncio.run(test_api_with_batcher())
    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to the API server")
        print("   Please start the server first with: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
