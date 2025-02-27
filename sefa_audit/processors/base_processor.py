import abc

class BaseProcessor(abc.ABC):
    @abc.abstractmethod
    def process(self, file_path):
        pass
