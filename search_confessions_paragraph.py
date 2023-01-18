from utils.download_content import get_content_from_url, get_content_from_pdf
from utils.extract_content import extract_confession_part_from_content


def get_confession_pages():
    # TODO get confession_pages

    return [
        ('https://paroissechaville.com/Horaires-et-adresses', 'html_page'),
        ('https://www.diocese-annecy.fr/diocese/les-paroisses/doyenne-de-la-moyenne-vallee-de-larve/paroisse-saint-bernard-du-mont-blanc/livret-fp-hebdo-13-01-2023.pdf', 'pdf'),
        ('https://www.saintjacquesduhautpas.com/sacrements/', 'html_page'),
        ('https://www.paroisse-maisons-laffitte.com/index.php/horaires2', 'html_page'),
    ]


def get_fresh_confessions_part(url, page_type):
    if page_type == 'html_page':
        content = get_content_from_url(url)
    elif page_type == 'pdf':
        content = get_content_from_pdf(url)
    else:
        print(f'unrecognized page_type {page_type}')
        return None

    return extract_confession_part_from_content(content, page_type)


if __name__ == '__main__':
    confession_pages = get_confession_pages()

    for url, page_type in confession_pages:
        confession_part = get_fresh_confessions_part(url, page_type)

        print()
        print(url, page_type)
        print(confession_part)
