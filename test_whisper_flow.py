import asyncio
import websockets
import numpy as np
import sys

WS_URL = "ws://localhost:8000/ws/whisper"

async def test_whisper_flow():
    """Test the complete flow: mic → websocket → audio buffer → processing → result"""
    print("=" * 70)
    print("Testing /ws/whisper flow")
    print("=" * 70)
    print()
    
    try:
        # Connect to WebSocket
        print(f"Connecting to {WS_URL}...")
        async with websockets.connect(WS_URL, ping_interval=30, ping_timeout=30) as websocket:
            print("✓ Connected successfully!\n")
            
            # Generate synthetic audio (simulating microphone input)
            # Create a simple sine wave as test audio
            sample_rate = 16000
            duration = 5  # 5 seconds of audio
            frequency = 440  # A4 note
            
            print("Generating test audio (5 seconds, 440 Hz sine wave)...")
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio = np.sin(2 * np.pi * frequency * t) * 0.3  # Reduced amplitude
            
            # Convert to int16 format (as if coming from microphone)
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Send audio in chunks (simulating real-time streaming)
            chunk_size = 1600  # 100ms chunks at 16kHz
            num_chunks = len(audio_int16) // chunk_size
            
            print(f"Sending {num_chunks} audio chunks ({chunk_size} samples each)...")
            print("-" * 70)
            
            # Create tasks for sending and receiving
            async def send_audio():
                for i in range(num_chunks):
                    start_idx = i * chunk_size
                    end_idx = start_idx + chunk_size
                    chunk = audio_int16[start_idx:end_idx]
                    
                    await websocket.send(chunk.tobytes())
                    print(f"[Sent chunk {i+1}/{num_chunks}] {len(chunk.tobytes())} bytes")
                    
                    # Simulate real-time streaming (100ms per chunk)
                    await asyncio.sleep(0.1)
                
                print(f"\n✓ Finished sending {num_chunks} chunks")
            
            async def receive_results():
                try:
                    while True:
                        response = await websocket.recv()
                        print(f"\n🎯 [RESULT RECEIVED]: {response}")
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"\nReceiver stopped: {e}")
            
            # Run both tasks concurrently
            receiver_task = asyncio.create_task(receive_results())
            await send_audio()
            
            # Wait a bit more for final processing
            print("\n⏳ Waiting for final processing...")
            await asyncio.sleep(3)
            
            # Cancel receiver and close
            receiver_task.cancel()
            try:
                await receiver_task
            except asyncio.CancelledError:
                pass
            
            print("\n-" * 70)
            print("✓ Test completed!")
            print("\nExpected flow:")
            print("  1. Audio chunks sent → WebSocket")
            print("  2. Chunks converted to float32 → AudioRingBuffer")
            print("  3. Buffer accumulates 4 seconds of audio")
            print("  4. Whisper model processes every 1 second")
            print("  5. Transcription results sent back")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure the server is running:")
        print("  uvicorn main:app --reload")
    except ConnectionRefusedError:
        print("❌ Connection refused")
        print("\nMake sure the server is running:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_with_silence():
    """Test with silent audio (should not produce transcription)"""
    print("\n" + "=" * 70)
    print("Testing with silent audio")
    print("=" * 70)
    print()
    
    try:
        print(f"Connecting to {WS_URL}...")
        async with websockets.connect(WS_URL, ping_interval=30) as websocket:
            print("✓ Connected!\n")
            
            sample_rate = 16000
            duration = 5
            
            # Generate silence
            audio_int16 = np.zeros(int(sample_rate * duration), dtype=np.int16)
            
            chunk_size = 1600
            num_chunks = len(audio_int16) // chunk_size
            
            print(f"Sending {num_chunks} chunks of silence...")
            
            async def send_audio():
                for i in range(num_chunks):
                    start_idx = i * chunk_size
                    end_idx = start_idx + chunk_size
                    chunk = audio_int16[start_idx:end_idx]
                    await websocket.send(chunk.tobytes())
                    await asyncio.sleep(0.1)
                print("✓ Finished sending silence")
            
            async def receive_results():
                try:
                    while True:
                        response = await websocket.recv()
                        print(f"🎯 [RESULT]: {response}")
                except asyncio.CancelledError:
                    pass
            
            receiver_task = asyncio.create_task(receive_results())
            await send_audio()
            await asyncio.sleep(2)
            receiver_task.cancel()
            
            print("\n✓ Silence test completed")
            print("(May produce empty transcriptions or '[BLANK_AUDIO]' from Whisper)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("\n🎤 WebSocket /ws/whisper Flow Test\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "silence":
        asyncio.run(test_with_silence())
    else:
        asyncio.run(test_whisper_flow())
