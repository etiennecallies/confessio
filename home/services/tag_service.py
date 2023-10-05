from scraping.utils.tagging import Tag


def color_pieces(confession_pieces):
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
    for i, (text, text_without_link, tags) in enumerate(confession_pieces):
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
                "tags": new_tags
            }
        )

    return colored_pieces
