import asyncio

from scraping.download.download_content import get_content_from_url
from scraping.extract.extract_content import ExtractV1Interface
from scraping.extract.extract_interface import ExtractMode, BaseExtractInterface
from scraping.prune.action_interfaces import DummyActionInterface
from scraping.refine.refine_content import refine_confession_content


def get_extracted_html_list(html_content: str,
                            extract_interface: BaseExtractInterface = None) -> list[str] | None:
    refined_content = refine_confession_content(html_content)
    if refined_content is None:
        return None

    if extract_interface is None:
        extract_interface = ExtractV1Interface(DummyActionInterface())

    paragraphs_lines_and_indices = extract_interface.extract_paragraphs_lines_and_indices(
        refined_content, ExtractMode.EXTRACT)
    if not paragraphs_lines_and_indices:
        return None

    extracted_html_list = []
    for paragraph_lines, paragraph_indices in paragraphs_lines_and_indices:
        extracted_html_list.append('<br>\n'.join(paragraph_lines))

    return extracted_html_list


async def get_fresh_extracted_html_list(url) -> list[str] | None:
    html_content = await get_content_from_url(url)
    if html_content is None:
        return None

    return get_extracted_html_list(html_content)


if __name__ == '__main__':
    url_ = ('https://www.croixglorieuse68.com/')
    extracted_html_list_ = asyncio.run(get_fresh_extracted_html_list(url_))

    print()
    print(url_)
    if extracted_html_list_ is not None:
        for extracted_html_ in extracted_html_list_:
            print(extracted_html_)
    else:
        print('Empty extracted html list')
