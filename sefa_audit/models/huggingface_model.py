from utils.logger import log_info, log_error
from huggingface_hub import InferenceClient
from transformers import AutoTokenizer
from dotenv import load_dotenv, find_dotenv
import os
import pandas as pd
from models.base_model import BaseModel
import re
import json
# from huggingface_hub import login


# OpenAI Model Implementation
class HuggingfaceAIModel(BaseModel):
    def __init__(self, api_key):
        """
        Initialize the OpenAI model using LangChain.
        Args:
            api_key (str): OpenAI API key.
            model="gpt-3.5-turbo-0125"
        """
        # login(token="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")
        os.environ["Huggingface_API_KEY"] = api_key
        # self.llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=api_key)  # ChatOpenAI(name="gpt-3.5-turbo-0125")
        self.client = InferenceClient(api_key=api_key)
        self.tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-V3", use_fast=True)


    def predict(self, prompt):
        """
        Generate a response from the OpenAI model.
        Args:
            prompt (str): The input prompt.
        Returns:
            str: The generated response.
        """
        log_info(prompt)
        messages = [{"role": "user", "content": prompt}]
        completion = self.client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3", messages=messages, max_tokens=20992
        )

        response = completion.choices[0].message
        log_info(f"response:{response.content}")

        return response

        # response = self.llm.chat(prompt)
        # return response.get('choices', [{}])[0].get('text', '').strip().split("\n")
