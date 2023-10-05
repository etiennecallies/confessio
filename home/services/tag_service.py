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


def update_sentence(sentence, checked_per_tag):
    for tag_name, checked in checked_per_tag.items():
        if tag_name == 'period':
            sentence.is_period = checked
        if tag_name == 'date':
            sentence.is_date = checked
        if tag_name == 'schedule':
            sentence.is_schedule = checked
        if tag_name == 'confession':
            sentence.is_confession = checked
        if tag_name == 'place':
            sentence.is_place = checked
        if tag_name == 'spiritual':
            sentence.is_spiritual = checked
        if tag_name == 'other':
            sentence.is_other = checked
