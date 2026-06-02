import time
class segmentBuffer:

    def __init__(self,silence_timeout = 0.6):
        self.tokens = []
        self.silence_timeout = silence_timeout
        self.last_audio_time = time.time()
    
    def add_partial(self,token):
        self.tokens.append(token)
        self.last_audio_time = time.time()
    
    def should_finalize(self):
        return (time.time() - self.last_audio_time)>self.silence_timeout
    
    def finalize(self):
        final_text = " ".join(self.tokens)
        self.tokens = []
        return final_text
    def reset(self):
        self.tokens = []
        self.last_audio_time = time.time()