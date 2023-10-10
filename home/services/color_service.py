from scraping.utils.extract_content import split_and_tag, prune_lines
from scraping.utils.prune_content import SentenceFromDbTagInterface
from scraping.utils.tagging import Tag


def get_colored_pieces(confession_html: str):
    lines_and_tags = split_and_tag(confession_html, SentenceFromDbTagInterface())
    kept_indices = prune_lines(lines_and_tags)

    tag_colors = {
        Tag.PERIOD: 'warning',
        Tag.DATE: 'black',
        Tag.SCHEDULE: 'purple',
        Tag.CONFESSION: 'success',
        Tag.PLACE: 'info',
        Tag.SPIRITUAL: 'danger',
        Tag.OTHER: 'gray',
    }

    colored_pieces = []
    for i, (text, text_without_link, tags) in enumerate(lines_and_tags):
        new_tags = {}
        for tag, color in tag_colors.items():
            new_tags[tag] = {
                'id': f'{i}-{tag}',
                'checked': tag in tags,
                'color': color
            }

        colored_pieces.append(
            {
                "text": text,
                "text_without_link": text_without_link,
                "color": '' if i in kept_indices else 'text-warning',
                "tags": new_tags
            }
        )

    return colored_pieces
