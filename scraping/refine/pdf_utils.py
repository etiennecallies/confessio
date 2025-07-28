import string

import pymupdf


def convert_text_to_html(raw_text: str) -> str:
    """Change \n to <br> and remove extra spaces."""
    # Remove extra spaces
    cleaned_text = ' '.join(raw_text.split(sep=' '))

    # Replace new lines with <br>, if starting or ending with a punctuation
    lines = []
    for line in cleaned_text.split('\n'):
        if not line:
            lines.append('<br>')
            continue

        has_digit = any(map(lambda c: c.isdigit(), line))
        if line[0] in string.punctuation or has_digit:
            lines.append('<br>')

        lines.append(' ')
        lines.append(line)

        if line[-1] in string.punctuation or has_digit:
            lines.append('<br>')

    return ''.join(lines)


def extract_text_from_doc(doc) -> str:
    text = ''
    for page_num in range(len(doc)):
        page = doc[page_num]
        text += extract_text_from_pdf_page(page) + '\n'

    doc.close()

    return convert_text_to_html(text)


def blocks_are_in_natural_order(blocks):
    coords = [b[:2] for b in blocks]

    max_x = coords[0][0]
    max_y = coords[0][1]
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]

        if not (y2 > y1 or x2 > x1) or not (x2 > max_x or y2 > max_y):
            return False

        max_x = max(max_x, x2)
        max_y = max(max_y, y2)

    return True


def extract_text_from_pdf_page(page) -> str:
    non_empty_text_blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
    if not non_empty_text_blocks:
        return ''

    sort = not blocks_are_in_natural_order(non_empty_text_blocks)

    return page.get_text('text', sort=sort)


def extract_text_from_pdf_file(pdf_file: str) -> str:
    doc = pymupdf.open(pdf_file)
    return extract_text_from_doc(doc)


def extract_text_from_pdf_bytes(raw_content: bytes) -> str:
    doc = pymupdf.open(stream=raw_content, filetype="pdf")
    return extract_text_from_doc(doc)
