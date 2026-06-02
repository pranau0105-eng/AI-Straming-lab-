from model import sentimentModel
from batcher import Batcher

model = sentimentModel()
batcher = Batcher(model)
def get_model():
    return model
