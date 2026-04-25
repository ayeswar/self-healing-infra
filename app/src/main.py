from fastapi import FastAPI, Response, status
from prometheus_fastapi_instrumentator import Instrumentator
import time
import math
import random

app = FastAPI(title="Target Application")

# Instrument the FastAPI app for Prometheus
Instrumentator().instrument(app).expose(app)

# Global variables to simulate leaks
memory_leak_list = []
error_mode = False

@app.get("/")
def read_root():
    return {"message": "App is running smoothly."}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/stress-cpu")
def stress_cpu(duration: int = 5):
    """Simulates CPU stress by running a computationally expensive loop."""
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = math.factorial(500)
    return {"message": f"CPU stressed for {duration} seconds."}

@app.get("/memory-leak")
def memory_leak(megabytes: int = 50):
    """Simulates a memory leak by appending to a global list."""
    global memory_leak_list
    # Append random string data
    memory_leak_list.append("A" * (1024 * 1024 * megabytes))
    return {"message": f"Leaked {megabytes} MB of memory. Total chunks: {len(memory_leak_list)}"}

@app.get("/toggle-error-spike")
def toggle_error_spike():
    """Toggles an error mode where subsequent requests fail randomly."""
    global error_mode
    error_mode = not error_mode
    return {"message": f"Error mode is now {'ON' if error_mode else 'OFF'}"}

@app.get("/random-task")
def random_task(response: Response):
    """A normal endpoint that fails if error_mode is true."""
    global error_mode
    if error_mode and random.random() < 0.8:  # 80% error rate when in error mode
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "Internal Server Error occurred!"}
    
    return {"data": "Task completed successfully"}
