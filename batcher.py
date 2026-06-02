import asyncio
from typing import List, Tuple
import time
from metrics import metrics

class Batcher:
    def __init__(self,model,max_batch_size:int=4, max_wait_ms=10):
        self.model = model
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.queue: List[Tuple[str,asyncio.Future, float]] = []
        self.lock = asyncio.Lock()
        asyncio.create_task(self.batch_worker())
    
    async def add_request(self,text:str):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        start_time = time.time()
        metrics.record_request()
        async with self.lock:
            self.queue.append((text,future, start_time))
        return await future

    async def batch_worker(self):
        while True:
            await asyncio.sleep(self.max_wait_ms / 1000)
            async with self.lock:
                if not self.queue:
                    continue
                batch = self.queue[:self.max_batch_size]
                self.queue = self.queue[self.max_batch_size:]
            text = [item[0] for item in batch]
            futures = [item[1] for item in batch]
            start_times = [item[2] for item in batch]
            metrics.record_batch(len(batch))
            metrics.record_model_call()
            results = await self.model.predict_batch(text)
            for future, result, start_time in zip(futures, results, start_times):
                latency = time.time() - start_time
                metrics.record_latency(latency)
                future.set_result(result)