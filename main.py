import json
from sys import prefix
import time
from fastapi import FastAPI, Depends, HTTPException, WebSocket,WebSocketDisconnect
from pydantic import BaseModel
import decoder
from dependencies import get_model
import jobs
from model import sentimentModel
from metrics import metrics
from jobs import create_job,set_running,set_done,get_job, submit_background_job,stream_job_generator
from fastapi.responses import StreamingResponse
from  decoder import FakeSpeechDecoder,  StreamingSpeechDecoder
import segmentBuffer
import asyncio
import numpy as np
import whisper
import re
from  audio_buffer import AudioRingBuffer

app = FastAPI()
segment = segmentBuffer.segmentBuffer()
SAMPLE_RATE = 16000
CHUNK_SEC = 0.5
OVERLAP_SEC = 4.0

CHUNK_SAMPLES = int(
    CHUNK_SEC * SAMPLE_RATE
)

OVERLAP_SAMPLES = int(
    OVERLAP_SEC * SAMPLE_RATE
)
BUFFER_SECONDS = 6
# audio_buffer = AudioRingBuffer(SAMPLE_RATE, BUFFER_SECONDS)
SILENCE_THRESHOLD = 0.01  # Adjust based on your audio levels
SILENCE_DURATION = 1.2  # Seconds of silence to consider end of segment
PROCESS_INTERVAL = 0.8  # Seconds between processing audio buffer

# Load Whisper model at startup (not per connection)
print("Loading Whisper model...")
whisper_model = whisper.load_model("small")
print("Whisper model loaded successfully!")
class PredictionRequest(BaseModel):
    texts: str
    
# class batchPredictRequest(BaseModel):
#     texts: list[str]

class PredictResult(BaseModel):
    label: str
    score: float

class PredictionResponse(BaseModel):
    results: list[PredictResult]

class jobRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}

@app.post("/predict", response_model=PredictResult)
async def predict(
    request: PredictionRequest,
   batcher = Depends(get_model)
):
    result = await batcher.add_request(request.texts)
    return result

@app.get("/metrics")
def get_metrics():
    """Get batching performance metrics"""
    return metrics.summery()

@app.post("/submit-job")
async def submit_job(request:jobRequest, model=Depends(get_model)):
    job_id = create_job(job_type='background', text=request.text)
    submit_background_job(job_id, model)
    return {"job_id": job_id,"type": "background", "status": "Job submitted"}

@app.get("/job-status/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job['status'] != 'done':
        return {"status": job['status'],"message":"Job is still processing"}
    return job

@app.post("/submit_stream_job")
async def submit_stream_job(request:jobRequest):
    job_id = create_job("streaming", request.text)

    return {
        "job_id": job_id,
        "type": "streaming",
        "message": "Call /stream_job/{job_id} to start streaming"
    }
@app.get("/stream_job/{job_id}")
async def stream_job(job_id: str,model=Depends(get_model)):
    job = get_job(job_id)
    if not job:
        return {"error": "Job not found"}

    if job["type"] != "streaming":
        return {"error": "This job is not a streaming job"}

    return StreamingResponse(
        stream_job_generator(job_id, model),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
@app.websocket("/ws/audio/")
async def audio_stream(ws: WebSocket):
    await ws.accept()
    print("WebSocket connection accepted")
    decoder = FakeSpeechDecoder()
    try:
        while True:
            data = await ws.receive_bytes()
            partial_text = await decoder.decode_chunk(data)
            # Process the received audio data here
            if partial_text:
                await ws.send_json(partial_text)
    except WebSocketDisconnect:
        print("WebSocket disconnected")

@app.websocket("/ws/stt")
async  def websocker_stt(ws: WebSocket):
    await ws.accept()
    print("WebSocket STT connection accepted")
    decoder = StreamingSpeechDecoder()
    try:
        # continuously receive audio chunks and stream partial/final results
        while True:
            try:
                # wait for a short period for incoming audio; if none, this will raise TimeoutError
                # debug: log waiting
                # print a short timestamp before waiting
                print(f"[STT] waiting for chunk at {time.time():.3f}")
                chunk = await asyncio.wait_for(ws.receive_bytes(), timeout=0.1)
            except asyncio.TimeoutError:
                # no audio received recently: if silence detected, finalize segment
                try:
                    if segment.should_finalize() and segment.tokens:
                        final_text = segment.finalize()
                        print(f"[STT] finalize at {time.time():.3f}: {final_text}")
                        await ws.send_text(json.dumps({
                            "type": "final",
                            "text": final_text
                        }))
                        # reset both segment buffer and decoder for next utterance
                        segment.reset()
                        # try:
                        #     decoder.reset_partial_state()
                        # except Exception:
                        #     pass
                except Exception:
                    # ignore finalization errors and continue listening
                    pass
                continue
            # debug: we received a chunk
            print(f"[STT] received chunk at {time.time():.3f} (len={len(chunk) if chunk else 0})")
            # we received a chunk; decode and emit partials
            try:
                token = await decoder.decode_chunk(chunk)
            except Exception as e:
                print(f"Decoder error: {e}")
                continue

            if token:
                segment.add_partial(token)
                print(f"[STT] partial at {time.time():.3f}: {' '.join(segment.tokens)}")
                await ws.send_text(json.dumps({
                    "type": "partial",
                    "text": " ".join(segment.tokens)
                }))

    except WebSocketDisconnect:
        print("WebSocket STT disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await ws.close()
        except Exception:
            pass
@app.websocket("/ws/realaudio")
async def audio_ws(ws:WebSocket):
    await ws.accept()
    print("websocket connected")
    total_bytes = 0
    start = time.time()
    try:
        while True:
            data = await ws.receive_bytes()
            total_bytes += len(data)
            duration = total_bytes / (16000 * 2)  # Assuming 16kHz, 16-bit audio (2 bytes per sample)
            msg = {
                "bytes": len(data),
                "total_bytes": total_bytes,
                "duration_sec": round(duration, 2)
            }
            await ws.send_json(msg)
    except Exception as e:
        print(f"Client Disconnected: {e}")
def normalize_word(word):
    return re.sub(r"[^\w]", "", word).lower()
def common_prefix_length(old_words, new_words):

    count = 0

    for old_word, new_word in zip(old_words, new_words):

        if normalize_word(old_word) == normalize_word(new_word):
            count += 1
        else:
            break

    return count
def find_word_overlap(old_words, new_words):

    max_overlap = min(
        len(old_words),
        len(new_words)
    )

    for size in range(max_overlap, 0, -1):

        old_tail = [
            normalize_word(w)
            for w in old_words[-size:]
        ]

        new_head = [
            normalize_word(w)
            for w in new_words[:size]
        ]

        if old_tail == new_head:
            return size

    return 0
@app.websocket("/ws/whisper")
async def whisper_ws(ws: WebSocket):
    await ws.accept()
    print("Whisper WebSocket connected")
    
    # Event-driven streaming configuration
    audio_buffer = AudioRingBuffer(window_sec=15.0)  # Keep 4 seconds for context
    HOP_SAMPLES = int(16000 * 0.8)  # Process every 0.8 seconds of new audio
    CONTEXT_SAMPLES = int(16000 * 1.0)  # Use 1.0 second of context
    
    # Event-driven variables
    new_audio_event = asyncio.Event()
    pending_samples = 0
    
    last_transcript = ""
    silence_time = 0.0  
    finalized_text = ""
    total_samples = 0
    stable_words = []
    unstable_words = []
    word_confirmations = []
    STABLE_THRESHOLD = 3
    last_whisper_words = []
    async def receive_audio():
        nonlocal total_samples, pending_samples
        try:
            while True:
                data = await ws.receive_bytes()
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                
                audio_buffer.append(samples)
                total_samples += len(samples)
                pending_samples += len(samples)
                
                # Log every 0.5 seconds of audio received
                if total_samples % 8000 == 0:
                    print(f"📥 Received {total_samples} samples ({total_samples/16000:.1f}s of audio)")
                
                # 🔔 Notify processor immediately when we have enough audio
                if pending_samples >= HOP_SAMPLES:
                    new_audio_event.set()
                    
        except WebSocketDisconnect:
            print("Client disconnected from receive_audio")
    
    async def process_audio():

        nonlocal last_transcript, silence_time, finalized_text,stable_words,word_confirmations,last_whisper_words,unstable_words

        # 🎯 Timeline cursor
        # Absolute sample position already processed
        # Wait until some audio exists

        while audio_buffer.total_samples_written < CHUNK_SAMPLES:
            await asyncio.sleep(0.05)

        read_cursor = max(
            0,
            audio_buffer.total_samples_written
            - audio_buffer.max_samples
        )

        print(
            f"🎯 Starting cursor at "
            f"{read_cursor/16000:.2f}s"
        )

        try:

            while True:

                # --------------------------------------------------
                # STEP 1: Wait until enough NEW audio exists
                # --------------------------------------------------

                available_audio = (
                    audio_buffer.total_samples_written
                )

                required_audio = (
                    read_cursor
                    + CHUNK_SAMPLES
                )

                if available_audio < required_audio:

                    print(
                        f"⏳ Waiting for audio... "
                        f"({available_audio}/{required_audio})"
                    )

                    await asyncio.sleep(0.05)
                    continue

                # --------------------------------------------------
                # STEP 2: Get NEW audio chunk
                # --------------------------------------------------

                new_audio = audio_buffer.get_chunk(
                    start_sample=read_cursor,
                    size=CHUNK_SAMPLES
                )

                if new_audio is None:

                    print("⚠️ Chunk overwritten before processing")
                    await asyncio.sleep(0.05)
                    continue

                # --------------------------------------------------
                # STEP 3: Get overlap context
                # --------------------------------------------------

                context_start = max(
                    0,
                    read_cursor - OVERLAP_SAMPLES
                )

                context_size = (
                    read_cursor
                    - context_start
                )

                context_audio = audio_buffer.get_chunk(
                    start_sample=context_start,
                    size=context_size
                )

                # --------------------------------------------------
                # STEP 4: Build final inference window
                # --------------------------------------------------

                if context_audio is not None:

                    window = np.concatenate((
                        context_audio,
                        new_audio
                    ))

                else:
                    window = new_audio

                # --------------------------------------------------
                # STEP 5: Energy / silence detection
                # --------------------------------------------------

                energy = np.sqrt(
                    np.mean(window ** 2)
                )

                print(
                    f"\n🔄 Processing window:"
                )

                print(
                    f"   Context: "
                    f"{len(context_audio)/16000 if context_audio is not None else 0:.2f}s"
                )

                print(
                    f"   New Audio: "
                    f"{len(new_audio)/16000:.2f}s"
                )

                print(
                    f"   Total Window: "
                    f"{len(window)/16000:.2f}s"
                )

                print(
                    f"📊 Energy: {energy:.4f}"
                )

                # --------------------------------------------------
                # STEP 6: Silence tracking
                # --------------------------------------------------

                if energy < SILENCE_THRESHOLD:

                    silence_time += CHUNK_SEC

                    print(
                        f"🔇 Silence: "
                        f"{silence_time:.1f}s"
                    )
                if energy < 0.010:
                    read_cursor += CHUNK_SAMPLES
                    continue
                else:

                    silence_time = 0.0

                    print(
                        "🎤 Speech detected"
                    )

                # --------------------------------------------------
                # STEP 7: Whisper transcription
                # --------------------------------------------------

                loop = asyncio.get_event_loop()

                result = await loop.run_in_executor(
                    None,
                    lambda: whisper_model.transcribe(
                        window,
                        language="en",
                        fp16=False,
                        beam_size=5,
                        best_of=5,
                        temperature=0.0,
                        condition_on_previous_text=False,
                        no_speech_threshold=0.6
                    )
                )

                transcript = (
                    result["text"]
                    .strip()
                )
                if not transcript:
                    print("⚠️ Empty transcript - skipping")
                    read_cursor += CHUNK_SAMPLES
                    continue
                print(
                    f"📝 Transcript: "
                    f"'{transcript}'"
                )
                # Ignore very short hallucinations
                if len(transcript.split()) < 2:
                    print(f"⚠️ Tiny transcript ignored: '{transcript}'")
                    read_cursor += CHUNK_SAMPLES
                    continue
                current_words = transcript.split()
                print("PREV:", last_whisper_words)
                print("CURR:", current_words)
                
                prefix_len = common_prefix_length(
                    last_whisper_words,
                    current_words
                )
                
                print(f"📌 Common Prefix: {prefix_len}")
                # REVISION GUARD
                # Ignore Whisper if it rewrites the beginning
                # of an already stable sentence
                # --------------------------------------------------

                if (
                    stable_words
                    and prefix_len < len(stable_words)
                ):
                    print(
                        f"🛡 Revision ignored "
                        f"(prefix={prefix_len}, "
                        f"stable={len(stable_words)})"
                    )

                    read_cursor += CHUNK_SAMPLES
                    continue

                print(f"📌 Common Prefix: {prefix_len}")

                new_confirmations = []

                for i, word in enumerate(current_words):

                    if (
                        i < prefix_len
                        and i < len(word_confirmations)
                    ):
                        new_confirmations.append(
                            word_confirmations[i] + 1
                        )
                    else:
                        new_confirmations.append(1)

                word_confirmations = new_confirmations

                unstable_words = current_words.copy()

                stable_count = 0

                for count in word_confirmations:

                    if count >= STABLE_THRESHOLD:
                        stable_count += 1
                    else:
                        break

                if stable_count > 0:

                    stable_words = current_words[:stable_count]
                    unstable_words = current_words[stable_count:]

                last_whisper_words = current_words.copy()
                print(
                    f"✅ Confirmations: "
                    f"{word_confirmations}"
                )
                print(
                    f"🟢 Stable: "
                    f"{stable_words}"
                )

                print(
                    f"🟡 Unstable: "
                    f"{unstable_words}")

                # display_text = " ".join(
                #     merged_words
                # )
                display_text = " ".join(
                    stable_words
                    +
                    unstable_words
                )
                #-----------------------------
                # STEP 8: Send PARTIAL updates
                # -----------------------------

                if (
                    display_text
                    and display_text != last_transcript
                ):

                    await ws.send_json({
                        "type": "partial",
                        "text": display_text
                    })

                    print(
                        f"✅ Partial sent:"
                        f" {display_text}"
                    )

                    last_transcript = display_text

                # --------------------------------------------------
                # STEP 9: Finalization after silence
                # --------------------------------------------------

                if (
                    silence_time >= SILENCE_DURATION
                    and last_transcript
                ):

                    await ws.send_json({
                        "type": "final",
                        "text": last_transcript
                    })
                    
                    print(
                        f"✅ Final sent: "
                        f"'{last_transcript}'"
                    )

                    finalized_text += (
                        " " + last_transcript
                    )
                  
                    last_transcript = ""
                    silence_time = 0.0
                    stable_words = []
                    unstable_words = []
                    word_confirmations = []
                    last_whisper_words = []
                # --------------------------------------------------
                # STEP 10: Advance cursor
                # --------------------------------------------------

                read_cursor += CHUNK_SAMPLES

                print(
                    f"➡️ Cursor advanced to "
                    f"{read_cursor/16000:.2f}s"
                )

        except WebSocketDisconnect:

            print(
                "Client disconnected "
                "from process_audio"
            )

        except Exception as e:

            print(
                f"Error in process_audio: {e}"
            )

            import traceback
            traceback.print_exc()
    
    try:
        await asyncio.gather(receive_audio(), process_audio())
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("Whisper WebSocket disconnected")