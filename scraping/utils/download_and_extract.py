from scraping.utils.download_content import get_content
from scraping.utils.extract_content import extract_confession_part_from_content


def get_fresh_confessions_part(url, page_type):
    html_content = get_content(url, page_type)
    if html_content is None:
        return None

    return extract_confession_part_from_content(html_content)


if __name__ == '__main__':
    confession_pages = [
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
        # ('https://www.paroissedevaise.fr/evenements/categorie/pardon/jour/2023-09-01/', 'html_page'),
        # ('https://www.fourviere.org/fr/prier-notre-dame-de-fourviere/priere-et-celebrations/confessions/', 'html_page'),
        # ('https://www.paroissedevaise.fr/evenements/categorie/pardon/jour/2023-09-14/', 'html_page'),
        # ('https://www.paroissedevaise.fr/event/apres-midi-du-pardon-a-ecully/', 'html_page'),
        # ('https://notredamedeslumieres-caluire.paroisse.net/rubriques/droite/approfondir-sa-foi-1/reconciliation', 'html_page'),
        # ('http://www.paroisses-pentes-et-saone.fr/soiree-confessions-avec-adoration/', 'html_page'),
        # ('https://www.paroissesainteclaire.com/evenements.html', 'html_page'),
        # ('https://www.espace-saint-ignace.fr/?page_id=1252', 'html_page'),
        ('https://www.paroissesferreoletozanam.fr/?mailpoet_router=&endpoint=view_in_browser&action=view&data=WzExMSwiMmZkYjYyM2UzZTUwIiwwLDAsMTY3LDFd', 'html_page'),
    ]

    for url_, page_type_ in confession_pages:
        confession_part = get_fresh_confessions_part(url_, page_type_)

        print()
        print(url_, page_type_)
        print(confession_part)
