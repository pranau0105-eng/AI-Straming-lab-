import asyncio
class sentimentModel:
    async def predict(self, text: str):
        await asyncio.sleep(1)
        # Dummy sentiment analysis logic
        if "good" in text.lower():
            return {"label": "positive", "score": 0.9}
        elif "bad" in text.lower():
            return {"label": "negative", "score": 0.1}
        else:
            return {"label": "neutral", "score": 0.5}

    async def predict_batch(self, texts):
        await asyncio.sleep(1)
        results = []
        for text in texts:
            if "good" in text.lower():
                results.append({"label": "positive", "score": 0.9})
            elif "bad" in text.lower():
                results.append({"label": "negative", "score": 0.1})
            else:
                results.append({"label": "neutral", "score": 0.5})
        return results
    
    async def predict_stream(self, text: str):
        
        await asyncio.sleep(0.4)
        yield "Analysing input text...\n"

        await asyncio.sleep(0.4)
        yield "Extracting sentiment signal...\n"

        negative_words = ["bad", "terrible", "awful", "poor","worst","hate","disappointing","late","broken","unacceptable"]
        score = 0.5
        for word in negative_words:
            if word in text.lower():
                yield f"Found negative word: {word}\n"
                score -= 0.1
        await asyncio.sleep(0.4)
        lablel = "negative" if score < 0.4 else "neutral" if score == 0.5 else "positive"
        yield f"Final sentiment: {lablel} (score: {score:.2f})\n"