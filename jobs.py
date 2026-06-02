import uuid
import asyncio
from typing import Dict, Any

# ---------------------------
# Global Job Store
# ---------------------------
jobs: Dict[str, Dict[str, Any]] = {}

# ---------------------------
# Worker Limiting
# ---------------------------
MAX_WORKERS = 2
worker_semaphore = asyncio.Semaphore(MAX_WORKERS)

# Track background tasks only
job_tasks = []

# ---------------------------
# JOB CREATION
# ---------------------------
def create_job(job_type: str, text: str):
    """
    job_type: 'background' | 'streaming'
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "type": job_type,
        "text": text,
        "status": "pending",
        "result": ""
    }
    return job_id

# ---------------------------
# STATUS HELPERS
# ---------------------------
def set_running(job_id: str):
    jobs[job_id]["status"] = "running"

def set_done(job_id: str, result: str):
    jobs[job_id]["status"] = "done"
    jobs[job_id]["result"] = result

def set_failed(job_id: str, error: str):
    jobs[job_id]["status"] = "failed"
    jobs[job_id]["result"] = error

def get_job(job_id: str):
    return jobs.get(job_id)

# ---------------------------
# BACKGROUND JOB EXECUTION
# ---------------------------
async def run_background_job(job_id: str, model):
    """
    Executes NON-STREAMING jobs.
    Detached from request.
    """
    async with worker_semaphore:
        set_running(job_id)
        try:
            result = await model.predict(jobs[job_id]["text"])
            set_done(job_id, result)
        except Exception as e:
            set_failed(job_id, str(e))

def submit_background_job(job_id: str, model):
    """
    Fire-and-forget execution.
    """
    task = asyncio.create_task(run_background_job(job_id, model))
    job_tasks.append(task)
    return task

# ---------------------------
# STREAMING JOB EXECUTION
# ---------------------------
async def stream_job_generator(job_id: str, model):
    """
    Async generator for streaming jobs.
    MUST be used inside request context.
    """
    async with worker_semaphore:
        set_running(job_id)
        collected_output = ""

        try:
            async for chunk in model.predict_stream(jobs[job_id]["text"]):
                collected_output += chunk
                yield chunk

            set_done(job_id, collected_output)

        except Exception as e:
            set_failed(job_id, str(e))
            yield f"ERROR: {str(e)}\n"
