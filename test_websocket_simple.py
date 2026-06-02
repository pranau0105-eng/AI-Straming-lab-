import asyncio
import websockets

async def test_stream():
    uri = "ws://localhost:8000/ws/stt/"

    async with websockets.connect(uri) as websocket:
        print("Connected to server")

        # Simulate sending audio chunks
        for i in range(10):
            chunk = b"fake_audio_chunk"
            await websocket.send(chunk)
            print(f"Sent chunk {i+1}")

            response = await websocket.recv()
            print("Server:", response)

            await asyncio.sleep(0.1)

asyncio.run(test_stream())
