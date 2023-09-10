from scraping.utils.download_content import get_content
from scraping.utils.extract_content import extract_confession_part_from_content

def get_confession_pages():

    return [
        # ('https://paroissechaville.com/Horaires-et-adresses', 'html_page'),
        # ('https://www.diocese-annecy.fr/diocese/les-paroisses/doyenne-de-la-moyenne-vallee-de-larve/paroisse-saint-bernard-du-mont-blanc/livret-fp-hebdo-13-01-2023.pdf', 'pdf'),
        # ('https://www.saintjacquesduhautpas.com/sacrements/', 'html_page'),
        # ('https://www.paroisse-maisons-laffitte.com/index.php/horaires2', 'html_page'),
        # ('https://jeannedarc-versailles.com/horaires/', 'html_page'),
        # ('https://paroissesaintbruno.pagesperso-orange.fr/messes.html', 'html_page'),
        # ('https://www.eglise-saintgermaindespres.fr/sacrements/reconciliation/', 'html_page'),  # Bof un peu large...
        # ('https://notredameversailles.fr/vie-chretienne/vivre-les-sacrements/sacrement-de-penitence-et-de-reconciliation/', 'html_page'),  # Bof, un peu large aussi...
        # ('https://paroissecroixrousse.fr/pour-le-temps-de-noel/', 'html_page'),
        # ('https://www.eglise-saintgermaindespres.fr/l_eglise/horaires/', 'html_page'),
        # ('https://paroissecroixrousse.fr/pour-le-temps-de-noel/', 'html_page'),
        ('https://www.paroissedevaise.fr/evenements/categorie/pardon/jour/2023-09-01/', 'html_page'),
    ]


def get_fresh_confessions_part(url, page_type):
    html_content = get_content(url, page_type)
    if html_content is None:
        return None

    return extract_confession_part_from_content(html_content)


if __name__ == '__main__':
    confession_pages = get_confession_pages()

    for url, page_type in confession_pages:
        confession_part = get_fresh_confessions_part(url, page_type)

        print()
        print(url, page_type)
        print(confession_part)
