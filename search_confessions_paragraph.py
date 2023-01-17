def get_confession_pages():
    # TODO get confession_pages

    return [
        ('https://paroissechaville.com/Horaires-et-adresses', 'html_page'),
        ('https://www.diocese-annecy.fr/diocese/les-paroisses/doyenne-de-la-moyenne-vallee-de-larve/paroisse-saint-bernard-du-mont-blanc/livret-fp-hebdo-13-01-2023.pdf', 'pdf'),
        ('https://www.saintjacquesduhautpas.com/sacrements/', 'html_page'),
        ('https://www.paroisse-maisons-laffitte.com/index.php/horaires2', 'html_page'),
    ]


def get_content_from_url(url):
    print(f'getting content from url {url}')
    # TODO

    return ''


def get_content_from_pdf(url):
    print(f'getting content from pdf with url {url}')
    # TODO

    return ''


def extract_confession_part_from_content(content):
    print(f'getting content from {url}')
    # TODO

    return content


if __name__ == '__main__':
    confession_pages = get_confession_pages()

    for url, page_type in confession_pages:
        if page_type == 'html_page':
            content = get_content_from_url(url)
        elif page_type == 'pdf':
            content = get_content_from_pdf(url)
        else:
            print(f'unrecognized page_type {page_type}')
            continue

        confession_part = extract_confession_part_from_content(content)


