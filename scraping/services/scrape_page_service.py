from home.models import Page, Scraping


def upsert_scraping(page: Page, confession_part: str) -> Scraping:
    # Compare result to last scraping
    last_scraping = page.get_latest_scraping()
    if last_scraping is not None \
            and last_scraping.confession_html == confession_part:
        # If a scraping exists and is identical to last one
        last_scraping.nb_iterations += 1
        last_scraping.save()

        return last_scraping

    new_scraping = Scraping(
        confession_html=confession_part,
        nb_iterations=1,
        page=page,
    )
    new_scraping.save()

    return new_scraping



