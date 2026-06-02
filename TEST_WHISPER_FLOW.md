# Testing /ws/whisper Flow

This guide helps you test the complete flow:
**Microphone → WebSocket → AudioRingBuffer → Whisper Processing → Results**

## 🔍 What Gets Tested

Your `/ws/whisper` endpoint implements:
1. **Receive audio chunks** via WebSocket
2. **Convert int16 → float32** audio format
3. **Append to AudioRingBuffer** (4-second sliding window)
4. **Process with Whisper** model every 1 second
5. **Send transcription results** back to client

## 🚀 Quick Start

### 1. Start the Server
```bash
uvicorn main:app --reload
```

### 2. Run Tests

#### Option A: Interactive Test Menu
```bash
./test_whisper.sh
```
Choose from:
- **Synthetic audio test** - No mic needed, sends test audio
- **Live microphone test** - Real-time mic streaming
- **Silent audio test** - Validates silence handling

#### Option B: Direct Python Tests

**Synthetic Audio Test** (no microphone needed):
```bash
python3 test_whisper_flow.py
```

**Live Microphone Test**:
```bash
python3 test_whisper_mic.py
```
Press Ctrl+C to stop.

**Silent Audio Test**:
```bash
python3 test_whisper_flow.py silence
```

#### Option C: Browser Test

1. Open `test_whisper.html` in a browser:
```bash
firefox test_whisper.html
# or
google-chrome test_whisper.html
```

2. Click "🎙️ Start Recording"
3. Speak into your microphone
4. Watch results appear in the log

## 📊 Expected Output

### Successful Flow
```
Connecting to ws://localhost:8000/ws/whisper...
✓ Connected successfully!

Sending audio chunks...
[Sent chunk 1/50] 3200 bytes
[Sent chunk 2/50] 3200 bytes
...

🎯 [RESULT RECEIVED]: {"type": "partial", "text": "hello world"}
```

### What You Should See on Server
```
Whisper WebSocket connected
(Processing audio in background every 1 second)
```

## 🧪 Test Files Created

| File | Purpose |
|------|---------|
| `test_whisper_flow.py` | Synthetic audio test (no mic) |
| `test_whisper_mic.py` | Live microphone streaming test |
| `test_whisper.sh` | Interactive test menu |
| `test_whisper.html` | Browser-based visual test |

## 🔧 Troubleshooting

### "Connection refused"
- Make sure server is running: `uvicorn main:app --reload`
- Check server is on port 8000

### "No audio detected"
- Check microphone permissions
- Verify microphone is working: `arecord -l` (Linux)
- Try browser test to check mic access

### "No transcription results"
- Audio buffer needs 4 seconds to fill
- Wait at least 5 seconds after speaking
- Check server logs for Whisper errors

### "Import errors"
Dependencies needed:
```bash
pip install fastapi uvicorn websockets numpy openai-whisper sounddevice
```

## 📝 Understanding the Flow

### 1. Client Side (test scripts)
```python
# Capture audio (16kHz, int16)
audio_int16 = capture_audio()

# Send to WebSocket
await websocket.send(audio_int16.tobytes())
```

### 2. Server Side (main.py)
```python
# Receive and convert
data = await ws.receive_bytes()
samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

# Append to ring buffer
audio_buffer.append(samples)

# Process every 1 second
window = audio_buffer.get_window()  # Get 4-second window
result = model.transcribe(window)

# Send result
await ws.send_json({"type": "partial", "text": transcript})
```

## ✅ Validation Checklist

Test each component:
- [ ] WebSocket connection established
- [ ] Audio chunks sent successfully
- [ ] Server receives and processes chunks
- [ ] AudioRingBuffer accumulates data
- [ ] Whisper model processes audio
- [ ] Transcription results received
- [ ] Flow works for continuous speech
- [ ] Handles silence appropriately

## 🎯 Next Steps

After confirming the flow works:
1. Add error handling for audio processing
2. Implement voice activity detection (VAD)
3. Add support for multiple clients
4. Optimize buffer size and processing interval
5. Add logging and monitoring

## 💡 Tips

- **Test with short phrases first** - "Hello world", "Test one two three"
- **Speak clearly** - Whisper works best with clear audio
- **Wait for results** - Processing takes 1-2 seconds
- **Check server logs** - Helps debug issues
- **Use browser test for debugging** - Visual feedback is helpful
