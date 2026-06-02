import asyncio
import websockets


WS_URL = "ws://localhost:8000/ws/audio/"

async def test_audio_streaming():
    """Test sending audio chunks via WebSocket"""
    print("=" * 70)
    print("WebSocket Audio Streaming Test")
    print("=" * 70)
    print()
    
    try:
        # Connect to WebSocket
        print(f"Connecting to {WS_URL}...")
        async with websockets.connect(WS_URL) as websocket:
            print("✓ Connected successfully!\n")
            
            # Simulate sending audio chunks
            print("Sending simulated audio chunks...")
            print("-" * 70)
            
            num_chunks = 5
            for i in range(1, num_chunks + 1):
                # Simulate audio data (just random bytes for testing)
                audio_chunk = bytes([i] * 100)  # 100 bytes of test data
                
                print(f"[Chunk {i}] Sending {len(audio_chunk)} bytes...")
                await websocket.send(audio_chunk)
                
                # Receive response from server
                response = await websocket.recv()
                print(f"[Chunk {i}] Server response: {response}")
                
                # Small delay between chunks
                await asyncio.sleep(0.5)
            
            print("-" * 70)
            print(f"\n✓ Successfully sent and received {num_chunks} audio chunks")
            
            # Close the connection gracefully
            print("\nClosing connection...")
            await websocket.close()
            print("✓ Connection closed")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure the server is running on http://localhost:8000")
    except ConnectionRefusedError:
        print("❌ Connection refused")
        print("Make sure the server is running: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_continuous_streaming():
    """Test continuous audio streaming"""
    print("\n" + "=" * 70)
    print("Continuous Audio Streaming Test")
    print("=" * 70)
    print()
    
    try:
        print(f"Connecting to {WS_URL}...")
        async with websockets.connect(WS_URL) as websocket:
            print("✓ Connected!\n")
            
            print("Simulating continuous audio stream (10 chunks)...")
            print("-" * 70)
            
            # Send chunks rapidly to simulate real audio streaming
            for i in range(1, 11):
                audio_chunk = bytes([i % 256] * 512)  # 512 bytes per chunk
                await websocket.send(audio_chunk)
                
                # Receive response
                response = await websocket.recv()
                print(f"Chunk {i:2d}: Sent {len(audio_chunk)} bytes → {response}")
                
                # Faster streaming (100ms between chunks)
                await asyncio.sleep(0.1)
            
            print("-" * 70)
            print("\n✓ Continuous streaming test completed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_large_audio_chunk():
    """Test sending a large audio chunk"""
    print("\n" + "=" * 70)
    print("Large Audio Chunk Test")
    print("=" * 70)
    print()
    
    try:
        print(f"Connecting to {WS_URL}...")
        async with websockets.connect(WS_URL) as websocket:
            print("✓ Connected!\n")
            
            # Send a large chunk (simulating 1 second of audio at 44.1kHz, 16-bit, mono)
            chunk_size = 44100 * 2  # ~88KB
            large_chunk = bytes([0] * chunk_size)
            
            print(f"Sending large audio chunk ({len(large_chunk):,} bytes)...")
            await websocket.send(large_chunk)
            
            response = await websocket.recv()
            print(f"Server response: {response}")
            print(f"✓ Successfully sent {len(large_chunk):,} bytes")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    print("\n🎵 WebSocket Audio Streaming Test Suite")
    print("Make sure your FastAPI server is running on http://localhost:8000\n")
    
    try:
        # Run all tests
        await test_audio_streaming()
        await asyncio.sleep(1)
        
        await test_continuous_streaming()
        await asyncio.sleep(1)
        
        await test_large_audio_chunk()
        
        print("\n" + "=" * 70)
        print("✓ All tests completed!")
        print("=" * 70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")

if __name__ == "__main__":
    asyncio.run(main())