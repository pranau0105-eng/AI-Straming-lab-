import asyncio
import time
from batcher import Batcher
from model import sentimentModel

async def test_batcher():
    """Test the batcher with multiple concurrent requests"""
    model = sentimentModel()
    batcher = Batcher(model, max_batch_size=4, max_wait_ms=100)
    
    # Give the batch_worker time to start
    await asyncio.sleep(0.1)
    
    print("Testing Batcher with multiple requests...\n")
    
    # Test 1: Send multiple requests concurrently
    print("Test 1: Sending 6 concurrent requests")
    test_texts = [
        "This is good",
        "This is bad", 
        "This is neutral",
        "Very good product",
        "Terrible and bad",
        "Just okay"
    ]
    
    start_time = time.time()
    
    # Send all requests concurrently
    tasks = [batcher.add_request(text) for text in test_texts]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    print(f"Results received in {end_time - start_time:.2f} seconds:")
    for text, result in zip(test_texts, results):
        print(f"  Text: '{text}' -> {result}")
    
    print(f"\nExpected ~2 batches (4 + 2 items) with ~100ms wait time between batches")
    print(f"Total time should be around 2-2.2 seconds (2 batch predictions + wait times)\n")
    
    # Test 2: Send requests one by one with delay
    print("\nTest 2: Sending requests with delays")
    start_time = time.time()
    
    result1 = await batcher.add_request("good morning")
    print(f"  Request 1 result: {result1}")
    
    await asyncio.sleep(0.15)  # Wait longer than max_wait_ms
    
    result2 = await batcher.add_request("bad news")
    print(f"  Request 2 result: {result2}")
    
    end_time = time.time()
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print("Expected: Each request processed in separate batch\n")
    
    # Test 3: Test batching efficiency
    print("\nTest 3: Testing batching efficiency (10 requests)")
    start_time = time.time()
    
    tasks = [batcher.add_request(f"test message {i}") for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"Processed 10 requests in {end_time - start_time:.2f} seconds")
    print(f"Expected ~3 batches: 4 + 4 + 2 items")
    print(f"Results count: {len(results)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Batcher Test Suite")
    print("=" * 60 + "\n")
    asyncio.run(test_batcher())
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)
