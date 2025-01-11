from typing import List
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.graph import GraphComponent
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.constants import TEXT
import re

@DefaultV1Recipe.register([GraphComponent], is_trainable=False)
class CleanInput(GraphComponent):
    def __init__(self, config: dict):
        self.config = config

    @staticmethod
    def create(config: dict, model_storage: ModelStorage, resource: Resource):
        return CleanInput(config)

    def process(self, messages: List[Message]):  # Use typing.List for compatibility
        for message in messages:
            text = message.get(TEXT, "")
            clean_text = re.sub(r'\b(please|pls|plz|kindly)\b', '', text.lower())
            clean_text = re.sub(r'[?.]', '', clean_text)  # Remove punctuation
            message.set(TEXT, clean_text.strip())
        return messages


