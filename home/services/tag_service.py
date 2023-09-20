def color_pieces(confession_pieces):
    tag_colors = {
        'period': 'warning',
        'date': 'black',
        'schedule': 'purple',
        'confession': 'success',
        'place': 'info',
        'spiritual': 'danger',
        'other': 'gray',
    }

    colored_pieces = []
    for i, (text, tags) in enumerate(confession_pieces):
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
                "tags": new_tags
            }
        )

    return colored_pieces
