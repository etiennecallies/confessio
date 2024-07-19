from abc import abstractmethod

from sentence_transformers import SentenceTransformer


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
        print('loading camembert transformer...')
        self.name = "dangvantuan/sentence-camembert-base"
        self.model = SentenceTransformer(self.name)

    def transform(self, sentence: str) -> list:
        return self.model.encode([sentence])[0]

    def get_name(self) -> str:
        return self.name


_transformer = None


def get_transformer() -> TransformerInterface:
    global _transformer
    if _transformer is None:
        _transformer = CamembertTransformer()

    return _transformer
