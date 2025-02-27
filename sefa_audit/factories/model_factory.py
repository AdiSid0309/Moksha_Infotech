from models.openai_model import OpenAIModel
from models.llama3_model import LLaMA3Model
from models.huggingface_model import HuggingfaceAIModel

# Model Factory
class ModelFactory:
    @staticmethod
    def get_model(model_name, api_key=None):
        if model_name.lower() == "llama3":
            return LLaMA3Model(model_name="llama3")
        elif model_name.lower() == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required for OpenAI model.")
            return OpenAIModel(api_key=api_key)
        elif model_name.lower() == "huggingface":
            if not api_key:
                raise ValueError("Huggingface API key is required for huggingface model.")
            return HuggingfaceAIModel(api_key=api_key)
        else:
            raise ValueError(f"Model {model_name} is not recognized.")
