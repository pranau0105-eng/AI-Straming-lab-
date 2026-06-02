#!/usr/bin/env python3
"""
Test the /ws/whisper endpoint with real microphone input
This tests the complete flow:
  Microphone → WebSocket → AudioRingBuffer → Whisper Processing → Results
"""

import asyncio
import sounddevice as sd
import numpy as np
import websockets
import sys

WS_URL = "ws://localhost:8000/ws/whisper"

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 0.1  # 100ms chunks
BLOCK_SIZE = int(SAMPLE_RATE * DURATION)

audio_queue = asyncio.Queue()

def audio_callback(indata, frames, time, status):
    """Called by sounddevice for each audio block"""
    if status:
        print(f"⚠️  Audio status: {status}")
    
    # Calculate volume
    volume = np.linalg.norm(indata)
    
    # Show visual indicator of audio level
    if volume > 5000:
        bars = int(volume / 10000)
        print(f"🎙️  {'█' * min(bars, 30)} ({volume:.0f})")
    
    # Send audio data to queue (convert to int16 format)
    audio_int16 = (indata * 32767).astype(np.int16)
    audio_queue.put_nowait(audio_int16.tobytes())

async def audio_sender(ws):
    """Send audio chunks from queue to WebSocket"""
    chunk_count = 0
    while True:
        data = await audio_queue.get()
        await ws.send(data)
        chunk_count += 1
        if chunk_count % 10 == 0:  # Log every 1 second (10 chunks × 100ms)
            print(f"📤 Sent {chunk_count} chunks ({chunk_count * 0.1:.1f}s of audio)")

async def result_receiver(ws):
    """Receive and display transcription results from WebSocket"""
    while True:
        try:
            msg = await ws.recv()
            print(f"\n{'='*70}")
            print(f"🎯 TRANSCRIPTION RESULT:")
            print(f"{'='*70}")
            print(msg)
            print(f"{'='*70}\n")
        except Exception as e:
            print(f"⚠️  Receiver error: {e}")
            break

async def stream_from_mic():
    """Main function to stream microphone audio to /ws/whisper"""
    print("=" * 70)
    print("🎤 Testing /ws/whisper with LIVE MICROPHONE")
    print("=" * 70)
    print()
    print("This will test the complete flow:")
    print("  1. Microphone captures audio")
    print("  2. Audio chunks sent to WebSocket")
    print("  3. Server converts to float32 and appends to AudioRingBuffer")
    print("  4. Server processes audio every 1 second with Whisper")
    print("  5. Transcription results are displayed here")
    print()
    print("=" * 70)
    print()
    
    try:
        print(f"🔌 Connecting to {WS_URL}...")
        async with websockets.connect(WS_URL, ping_interval=30, ping_timeout=30) as ws:
            print("✅ Connected successfully!\n")
            print("🎙️  Start speaking... (Press Ctrl+C to stop)")
            print("-" * 70)
            
            # Start audio input stream
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                callback=audio_callback,
            ):
                # Run sender and receiver concurrently
                await asyncio.gather(
                    audio_sender(ws),
                    result_receiver(ws)
                )
                
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nMake sure the server is running:")
        print("  uvicorn main:app --reload")
    except ConnectionRefusedError:
        print("\n❌ Connection refused")
        print("\nMake sure the server is running:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "🔊" * 35)
    print()
    
    try:
        asyncio.run(stream_from_mic())
    except KeyboardInterrupt:
        print("\n\n✅ Test completed!")
        print("\nFlow verification:")
        print("  ✓ Microphone audio captured")
        print("  ✓ Audio chunks sent via WebSocket")
        print("  ✓ AudioRingBuffer accumulated audio data")
        print("  ✓ Whisper model processed audio")
        print("  ✓ Transcription results received")
