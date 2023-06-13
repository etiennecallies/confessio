from bs4 import BeautifulSoup


##############
# REMOVE IMG #
##############

def remove_img(soup: BeautifulSoup):
    for s in soup.select('img'):
        s.extract()

    return soup


########
# MAIN #
########

def refine_confession_content(content_html):
    if content_html is None:
        return None

    soup = BeautifulSoup(content_html, 'html.parser')
    soup = remove_img(soup)

    return soup.prettify()
