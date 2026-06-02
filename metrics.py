import time
from collections import defaultdict

class Metrics:
    def __init__(self):
        self.total_requests = 0
        self.total_batches = 0
        self.total_model_calls = 0

        self.bath_sizes = []
        self.latencies = []

    def record_request(self):
        self.total_requests += 1
    def record_batch(self, batch_size:int):
        self.total_batches += 1
        self.bath_sizes.append(batch_size)
    
    def record_model_call(self):
        self.total_model_calls += 1

    def record_latency(self, latency:float):
        self.latencies.append(latency)
    
    def summery(self):
        avg_batch_size = sum(self.bath_sizes) / len(self.bath_sizes) if self.bath_sizes else 0
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0

        return {
            "total_requests": self.total_requests,
            "total_batches": self.total_batches,
            "total_model_calls": self.total_model_calls,
            "avg_batch_size": avg_batch_size,
            "avg_latency": avg_latency
        }
metrics = Metrics()