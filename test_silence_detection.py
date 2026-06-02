"""
Silence-detection streaming test for `/ws/stt` endpoint.

Requirements:
  pip3 install websockets

What it does:
- Connects to ws://localhost:8000/ws/stt
- Sends a few small audio-like chunks quickly (should produce partial tokens)
- Waits longer than silence timeout (default 0.6s) to trigger finalization
- Prints all messages received from the server (partial and final)

Run:
  python3 test_silence_detection.py
"""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("websockets library not installed. Install with: pip3 install websockets")
    sys.exit(1)

WS_URL = "ws://localhost:8000/ws/stt"

async def receiver(ws):
    try:
        async for msg in ws:
            # server sends text messages (JSON)
            try:
                data = json.loads(msg)
            except Exception:
                print("Received non-json:", msg)
                continue
            t = data.get('type')
            if t == 'partial':
                print(f"[partial] {data.get('text')}")
            elif t == 'final':
                print(f"[final] {data.get('text')}")
            else:
                print("[msg]", data)
    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed")
    except Exception as e:
        print("Receiver error:", e)

async def test_silence():
    print("Connecting to:", WS_URL)
    async with websockets.connect(WS_URL) as ws:
        print("Connected")

        recv_task = asyncio.create_task(receiver(ws))

        # Send 3 quick chunks (these should produce partial updates)
        print("Sending 3 quick chunks (0.1s apart)")
        for i in range(3):
            await ws.send(b"\x01\x02\x03")
            await asyncio.sleep(0.1)

        # Now wait shorter than silence timeout and send another chunk
        print("Waiting 0.3s and sending another chunk (still within silence)")
        await asyncio.sleep(0.3)
        await ws.send(b"\x04\x05")

        # Wait longer than typical silence timeout (0.8s) to trigger finalization
        print("Now waiting 0.8s to trigger silence finalization (should receive final)")
        await asyncio.sleep(0.8)

        # After finalization, optionally send another chunk to start a new segment
        print("Sending chunk to start new segment")
        await ws.send(b"\x06")
        await asyncio.sleep(0.1)

        print("Waiting 1s to allow finalization of second segment")
        await asyncio.sleep(1.0)

        # Close connection
        await ws.close()
        await recv_task

if __name__ == '__main__':
    try:
        asyncio.run(test_silence())
    except KeyboardInterrupt:
        print("Test interrupted")
