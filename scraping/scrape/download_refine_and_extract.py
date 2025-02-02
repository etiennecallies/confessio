from scraping.download.download_content import get_content_from_url
from scraping.extract.extract_content import extract_paragraphs_lines_and_indices, ExtractMode
from scraping.prune.action_interfaces import DummyActionInterface
from scraping.refine.refine_content import refine_confession_content


def get_extracted_html_list(html_content: str) -> list[str] | None:
    refined_content = refine_confession_content(html_content)
    if refined_content is None:
        return None

    paragraphs_lines_and_indices = extract_paragraphs_lines_and_indices(refined_content,
                                                                        DummyActionInterface(),
                                                                        ExtractMode.EXTRACT)
    if not paragraphs_lines_and_indices:
        return None

    extracted_html_list = []
    for paragraph_lines, paragraph_indices in paragraphs_lines_and_indices:
        extracted_html_list.append('<br>\n'.join(paragraph_lines))

    return extracted_html_list


def get_fresh_extracted_html_list(url) -> list[str] | None:
    html_content = get_content_from_url(url)
    if html_content is None:
        return None

    return get_extracted_html_list(html_content)


if __name__ == '__main__':
    url_ = 'https://paroisselatriniteenbeaujolais.fr/paroisse/horaires/'
    extracted_html_list_ = get_fresh_extracted_html_list(url_)

    print()
    print(url_)
    if extracted_html_list_ is not None:
        for extracted_html_ in extracted_html_list_:
            print(extracted_html_)
