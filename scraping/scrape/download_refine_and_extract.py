from scraping.download.download_content import get_content_from_url
from scraping.extract.extract_content import extract_paragraphs_lines_and_indices, DummyTagInterface
from scraping.refine.refine_content import refine_confession_content


def get_extracted_html_list(html_content: str) -> list[str] | None:
    refined_content = refine_confession_content(html_content)
    if refined_content is None:
        return None

    paragraphs_lines_and_indices = extract_paragraphs_lines_and_indices(refined_content,
                                                                        DummyTagInterface())
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
    confession_pages = [
        # 'https://paroissesaintbruno.pagesperso-orange.fr/messes.html',
        # 'http://www.paroisses-pentes-et-saone.fr/soiree-confessions-avec-adoration/',
        # 'https://www.paroissesainteclaire.com/evenements.html',
        # 'https://www.espace-saint-ignace.fr/?page_id=1252',
        # 'https://www.paroisse-st-martin-largentiere.fr',
        # 'https://paroissesaintalexandre.fr/etapes-de-la-vie/pardon-reconciliation/',
        # 'https://paroisserambouillet.fr/+-Sacrement-+',
        # 'https://www.paroissedevaise.fr/se-confesser/',
        # 'https://paroisse-sceaux.fr/wp-content/uploads/2023/12/priere-universelle-2eme-dimanche-de-lAvent.pdf',
        # 'https://www.paroisse-meudonlaforet.fr/reconciliation/',
        # 'https://paroissedemontrouge.com/etapes-de-la-vie-chretienne-reconciliation/',
        # 'https://saintbenoitdugrandcaux.wordpress.com/le-sacrement-de-la-reconciliation/',
        # 'https://meulan-triel.fr/index.php/reconciliation-confession/',
        'https://paroisse-sevres.fr/les-etapes-de-la-vie-chretienne/confession/',
    ]

    for url_ in confession_pages:
        extracted_html_list = get_fresh_extracted_html_list(url_)

        print()
        print(url_)
        print(extracted_html_list)
