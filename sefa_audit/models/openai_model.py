import pandas as pd
import os

from utils.logger import log_info, log_error
# from langchain.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from models.base_model import BaseModel
from langchain.schema import HumanMessage

# OpenAI Model Implementation
class OpenAIModel(BaseModel):
    def __init__(self, api_key):
        """
        Initialize the OpenAI model using LangChain.
        Args:
            api_key (str): OpenAI API key.
            model="gpt-3.5-turbo-0125"
        """      
        os.environ["OPENAI_API_KEY"] = api_key
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=api_key) #ChatOpenAI(name="gpt-3.5-turbo-0125")

    def predict(self, prompt):
        """
        Generate a response from the OpenAI model.
        Args:
            prompt (str): The input prompt.
        Returns:
            str: The generated response.
        """
        log_info(prompt)
        
        response = self.llm([HumanMessage(content=prompt)])
        log_info(f"response:{response.content}")
        
        return response.content

        #response = self.llm.chat(prompt)
        #return response.get('choices', [{}])[0].get('text', '').strip().split("\n")
