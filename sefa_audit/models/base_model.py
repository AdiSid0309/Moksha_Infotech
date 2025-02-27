import abc

# Define a common interface for AI models
class BaseModel(abc.ABC):
    @abc.abstractmethod
    def predict(self, prompt):
        pass
