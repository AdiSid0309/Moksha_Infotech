import pandas as pd
import os
from utils.logger import log_info, log_error
from langchain_community.llms import Ollama
from models.base_model import BaseModel

# Ollama LLaMA 3 Model Implementation
class LLaMA3Model(BaseModel):
    def __init__(self, model_name="llama3"):
        """
        Initialize the LLaMA 3 model via Ollama.
        Args:
            model_name (str): The name of the model hosted on Ollama (default: "llama3").
        """
        self.llm = Ollama(model=model_name)

    def predict(self, prompt):
        """
        Generate a response from the LLaMA 3 model.
        Args:
            prompt (str): The input prompt.
        Returns:
            str: The generated response.
        """
        response = self.llm(prompt)
        return response.split("\n")
