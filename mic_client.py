import asyncio
import sounddevice as sd
import numpy as np
import websockets

WS_URL = "ws://localhost:8000/ws/whisper"

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 0.03  # 30ms
BLOCK_SIZE = int(SAMPLE_RATE * DURATION)
SILENCE_THRESHOLD = 0.01  # RMS threshold for float32 audio (0.0 to 1.0)
audio_queue = asyncio.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print("Audio status:", status)
    
    # indata is int16, convert to float32 for RMS calculation
    audio_float = indata.astype(np.float32) / 32768.0
    rms = np.sqrt(np.mean(audio_float ** 2))

    # Only show RMS if above threshold
    if rms >= SILENCE_THRESHOLD:
        print(f"🎙 RMS: {rms:.4f}")
        print(f"➡️ Sending {len(indata.tobytes())} bytes")
        audio_queue.put_nowait(indata.tobytes())
    # Optionally uncomment to see all audio levels:
    # else:
    #     print(f"🔇 Silence: {rms:.4f}")


async def audio_sender(ws):
    chunk_count = 0
    while True:
        data = await audio_queue.get()
        await ws.send(data)
        chunk_count += 1
        if chunk_count % 10 == 0:  # Every ~0.3 seconds
            print(f"📤 Sent {chunk_count} chunks ({chunk_count * 0.03:.1f}s of audio)")

async def audio_receiver(ws):
    while True:
        msg = await ws.recv()
        print(f"\n{'='*60}")
        print(f"📝 TRANSCRIPT: {msg}")
        print(f"{'='*60}\n")

async def stream_mic():
    print(f"Connecting to {WS_URL}...")
    async with websockets.connect(WS_URL, ping_interval=60, ping_timeout=60) as ws:
        print("✓ Connected. Start speaking 🎙")

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            callback=audio_callback,
        ):
            await asyncio.gather(
                audio_sender(ws),
                audio_receiver(ws),
            )

asyncio.run(stream_mic())
