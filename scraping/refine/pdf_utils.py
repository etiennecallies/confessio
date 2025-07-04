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


def extract_text_from_doc(doc) -> str | None:
    text = ''
    for page_num in range(len(doc)):
        page = doc[page_num]
        text += page.get_text('text', sort=True) + '\n'

    doc.close()

    return convert_text_to_html(text)


def extract_text_from_pdf_file(pdf_file: str) -> str | None:
    doc = pymupdf.open(pdf_file)
    return extract_text_from_doc(doc)


def extract_text_from_pdf_bytes(raw_content: bytes) -> str | None:
    doc = pymupdf.open(stream=raw_content, filetype="pdf")
    return extract_text_from_doc(doc)
