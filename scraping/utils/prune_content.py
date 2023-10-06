from scraping.utils.extract_content import extract_content


########
# MAIN #
########

def prune_content(refined_html):
    if not refined_html:
        return None

    paragraphs = extract_content(refined_html, use_sentence=True)
    if not paragraphs:
        return None

    return '<br>\n'.join(paragraphs)
