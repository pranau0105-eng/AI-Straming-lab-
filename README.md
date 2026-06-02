# AI Streaming Lab

Real-time speech-to-text experimentation using FastAPI, WebSockets, Whisper, streaming audio pipelines, and transcript stabilization.

## Overview

AI Streaming Lab is a learning-focused project that explores how modern streaming speech recognition systems work internally.

Instead of sending complete audio files for transcription, audio is streamed continuously through a WebSocket connection, processed in overlapping windows, and transcribed in near real time using OpenAI Whisper.

The project focuses on understanding the engineering challenges behind production speech systems, including:

* Real-time audio streaming
* Ring buffer architectures
* Incremental transcription
* Transcript stabilization
* Silence detection
* Partial vs final results
* Streaming inference pipelines
* Async processing with FastAPI

---

## Current Status

### Phase 1 — Streaming Infrastructure ✅

Goal:

Can audio flow continuously through the system and produce usable streaming transcripts?

Implemented:

* FastAPI WebSocket server
* Real-time microphone streaming
* Audio ring buffer
* Sliding inference windows
* Overlapping context windows
* Whisper inference integration
* Async processing pipeline
* Partial transcript updates
* Final transcript emission
* Transcript stabilization using word confirmations
* Revision guard against Whisper rewrites
* Silence-based finalization

---

## Architecture

Microphone
↓
WebSocket Client
↓
FastAPI WebSocket Server
↓
Audio Ring Buffer
↓
Sliding Window Generator
↓
Whisper Inference
↓
Transcript Stabilizer
↓
Partial / Final Results

---

## Streaming Pipeline

### 1. Audio Ingestion

Audio is streamed from the client over WebSockets.

Incoming PCM chunks are continuously written into a ring buffer.

Benefits:

* Constant memory usage
* No file storage required
* Low latency processing

---

### 2. Sliding Window Processing

The system processes audio in fixed-size chunks.

Example:

* New Audio: 0.5 seconds
* Context Window: 4 seconds
* Inference Window: 4.5 seconds

This provides Whisper with enough historical context while still processing new speech incrementally.

---

### 3. Whisper Inference

Each inference window is passed through Whisper.

Configuration:

* Beam Search
* Deterministic decoding
* No previous text conditioning
* Low hallucination settings

---

### 4. Transcript Stabilization

Raw Whisper output frequently changes as more audio arrives.

Example:

Window 1:
"Hello my name is Ran..."

Window 2:
"Hello my name is Ranaf Jain"

Window 3:
"Hello my name is Pranav Jain"

To avoid unstable output:

* Consecutive matching words are tracked
* Word confirmations are counted
* Words become "stable" after multiple confirmations

Example:

Stable:
"Hello my name is"

Unstable:
"Pranav Jain and I am"

Only sufficiently confirmed words are promoted into the stable transcript.

---

### 5. Revision Guard

Whisper occasionally rewrites the beginning of the transcript.

Example:

Previous:
"Hello my name is Ranaf Jain"

New:
"My name is Pranav Jain"

Without protection:

* Confirmation counters reset
* Stable words reappear
* Transcript quality degrades

The revision guard ignores aggressive rewrites once a stable prefix has already been established.

---

### 6. Silence Detection

Audio energy is continuously monitored.

When speech energy drops below the threshold for a configured duration:

* Current transcript is finalized
* Final event is emitted
* Stabilization state resets

---

## Key Components

### audio_buffer.py

Ring buffer implementation for streaming audio storage.

### main.py

FastAPI application and WebSocket endpoints.

### decoder.py

Whisper inference logic.

### segmentBuffer.py

Streaming segment management.

### mic_client.py

Microphone streaming client.

### metrics.py

Pipeline performance metrics.

### batcher.py

Inference batching experiments.

---

## Example WebSocket Messages

Partial Transcript

```json
{
  "type": "partial",
  "text": "Hello my name is Pranav"
}
```

Final Transcript

```json
{
  "type": "final",
  "text": "Hello my name is Pranav Jain"
}
```

---

## Running the Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn main:app --reload
```

Open:

```text
http://localhost:8000
```

or connect through the provided test clients.

---

## Learning Roadmap

### Phase 1 — Streaming Infrastructure ✅

* WebSockets
* Ring Buffers
* Audio Streaming
* Whisper Integration
* Transcript Stabilization

### Phase 2 — Streaming ASR Intelligence

Planned:

* Real VAD (Voice Activity Detection)
* Timestamp alignment
* Segment tracking
* Better revision handling
* Adaptive windowing
* Smarter partial updates

### Phase 3 — Production Readiness

Planned:

* Multi-user support
* GPU worker pools
* Redis queues
* Horizontal scaling
* Observability and monitoring
* Fault tolerance

---

## Why This Project Exists

The goal is not just to use Whisper.

The goal is to understand how real-time speech recognition systems are engineered from the ground up, including buffering, streaming, stabilization, latency management, and transcript lifecycle management.

This repository serves as both a working prototype and a learning laboratory for modern AI streaming systems.
