# WebSocket Audio Streaming Tests

## Test Methods

### Method 1: Python Test (Recommended) ⭐

**Install websockets library:**
```bash
pip3 install websockets
```

**Run the test:**
```bash
python3 test_websocket.py
```

This will run 3 automated tests:
1. Basic audio streaming (5 chunks)
2. Continuous streaming (10 chunks)
3. Large audio chunk test

---

### Method 2: Browser Test (Visual) 🌐

**Open the HTML file in your browser:**
```bash
# Option 1: Open directly
xdg-open test_websocket.html

# Option 2: Serve with Python
python3 -m http.server 8080
# Then visit: http://localhost:8080/test_websocket.html
```

**Features:**
- Connect/Disconnect buttons
- Send individual audio chunks
- Start/Stop continuous streaming
- Adjust chunk size and interval
- Real-time log display

---

### Method 3: Bash Script (CLI)

**Requires websocat:**
```bash
sudo snap install websocat
```

**Run the test:**
```bash
./test_websocket.sh
```

---

## Your WebSocket Endpoint

**URL:** `ws://localhost:8000/ws/audio/`

**What it does:**
- Accepts WebSocket connections
- Receives binary audio data chunks
- Sends back acknowledgment for each chunk
- Counts chunks received

**Current implementation:**
```python
@app.websocket("/ws/audio/")
async def audio_stream(ws: WebSocket):
    await ws.accept()
    chunk_count = 0
    try:
        while True:
            data = await ws.receive_bytes()
            chunk_count += 1
            response = f"received audio chunk {chunk_count}"
            await ws.send_text(response)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
```

---

## Quick Start

1. **Start your server:**
   ```bash
   uvicorn main:app --reload
   ```

2. **Run the test:**
   ```bash
   python3 test_websocket.py
   ```

3. **Expected output:**
   ```
   Connecting to ws://localhost:8000/ws/audio/...
   ✓ Connected successfully!
   
   [Chunk 1] Sending 100 bytes...
   [Chunk 1] Server response: received audio chunk 1
   [Chunk 2] Sending 100 bytes...
   [Chunk 2] Server response: received audio chunk 2
   ...
   ```

---

## Troubleshooting

### Error: "websockets library not installed"
```bash
pip3 install websockets
```

### Error: "Connection refused"
Make sure your FastAPI server is running:
```bash
uvicorn main:app --reload
```

### Browser test not connecting
- Check that server is running on port 8000
- Open browser console (F12) to see errors
- Make sure WebSocket URL is correct: `ws://localhost:8000/ws/audio/`
