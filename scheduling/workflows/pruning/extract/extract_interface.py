from abc import abstractmethod
from enum import Enum


class ExtractMode(str, Enum):
    EXTRACT = 'extract'
    PRUNE = 'prune'


class BaseExtractInterface:
    @abstractmethod
    def extract_paragraphs_lines_and_indices(
            self,
            refined_content: str,
            extract_mode: ExtractMode
    ) -> list[tuple[list[str], list[int]]]:
        pass
