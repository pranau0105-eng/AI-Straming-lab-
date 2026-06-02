import asyncio
import random

class FakeSpeechDecoder:
    def __init__(self):
        self.full_tokens = "hello world this is streaming speech recognition".split()
        self.tokens = []
        self.index = 0
        self.finalized = False

    async def decode_chunk(self, chunk: bytes):
        if self.finalized:
            return None

        await asyncio.sleep(0.1)

        # If finished
        if self.index >= len(self.full_tokens):
            self.finalized = True
            return {
                "type": "final",
                "text": " ".join(self.tokens),
                "confidence": 1.0
            }

        token = self.full_tokens[self.index]

        # Initialize token if first time
        if len(self.tokens) <= self.index:
            self.tokens.append(token)
            advance = False
        else:
            # 🔁 Revision phase
            if random.random() < 0.6:
                self.tokens[self.index] = token
                advance = False
            else:
                advance = True  # token stabilized

        if advance:
            self.index += 1

        confidence = round((self.index / len(self.full_tokens)), 2)

        return {
            "type": "partial",
            "text": " ".join(self.tokens),
            "confidence": confidence
        }
    
    def reset_partial_state(self):
        """Reset internal state so decoder can start a new segment."""
        self.tokens = []
        self.index = 0
        self.finalized = False
    
    
class StreamingSpeechDecoder:
    def __init__(self):
        self.words = "hello world this is streaming speech recognition".split()
        self.index = 0

    async def decode_chunk(self, chunk: bytes):
        await asyncio.sleep(0.1)  # fake model compute

        if self.index < len(self.words):
            token = self.words[self.index]
            self.index += 1
            return token

        return None

    def reset_partial_state(self):
        self.index = 0