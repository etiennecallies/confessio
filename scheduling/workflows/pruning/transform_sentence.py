import threading
from abc import abstractmethod

TRANSFORMER_NAME = "dangvantuan/sentence-camembert-base"


class TransformerInterface:
    @abstractmethod
    def transform(self, sentence: str) -> list:
        """Transform a sentence into a vector"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the transformer"""
        pass


class CamembertTransformer(TransformerInterface):
    def __init__(self):
        print('loading SentenceTransformer')
        from sentence_transformers import SentenceTransformer
        print('loading camembert transformer...')
        self.name = TRANSFORMER_NAME
        self.model = SentenceTransformer(self.name)

    def transform(self, sentence: str) -> list:
        return self.model.encode([sentence])[0]

    def get_name(self) -> str:
        return self.name


_transformer = None
_transformer_lock = threading.Lock()


def get_transformer() -> TransformerInterface:
    global _transformer
    if _transformer is None:
        with _transformer_lock:
            if _transformer is None:
                _transformer = CamembertTransformer()

    return _transformer
