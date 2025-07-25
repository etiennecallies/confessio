from pydantic import BaseModel

from home.models import Pruning
from scraping.refine.refine_content import replace_link_by_their_content
from scraping.utils.html_utils import split_lines


class PruningHumanPiece(BaseModel):
    id: str
    do_show: bool
    text_without_link: str


def get_pruning_human_pieces(pruning: Pruning) -> list[PruningHumanPiece]:
    indices = pruning.human_indices if pruning.human_indices is not None \
        else pruning.ml_indices

    pruning_human_pieces = []
    for i, line in enumerate(split_lines(pruning.extracted_html)):
        text_without_link = replace_link_by_their_content(line)
        pruning_human_pieces.append(PruningHumanPiece(
            id=f'{i}',
            do_show=i in indices,
            text_without_link=text_without_link
        ))

    return pruning_human_pieces
