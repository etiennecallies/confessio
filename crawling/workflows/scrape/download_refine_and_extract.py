from crawling.workflows.download.download_content import get_content_from_url
from crawling.workflows.refine.refine_content import refine_confession_content
from scheduling.public_workflow import extract_refined_content
from scheduling.workflows.pruning.extract.extract_interface import BaseExtractInterface


def get_extracted_html_list(html_content: str,
                            extract_interface: BaseExtractInterface = None) -> list[str] | None:
    refined_content = refine_confession_content(html_content)
    if refined_content is None:
        return None

    return extract_refined_content(refined_content, extract_interface)


def get_fresh_extracted_html_list(url) -> list[str] | None:
    html_content = get_content_from_url(url)
    if html_content is None:
        return None

    return get_extracted_html_list(html_content)


if __name__ == '__main__':
    url_ = ('https://strasbourg.fraternites-jerusalem.org/agenda-de-la-semaine/')
    extracted_html_list_ = get_fresh_extracted_html_list(url_)

    print()
    print(url_)
    if extracted_html_list_ is not None:
        for extracted_html_ in extracted_html_list_:
            print(extracted_html_)
    else:
        print('Empty extracted html list')
