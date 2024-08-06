from home.models import Page, Scraping
from scraping.services.prune_scraping_service import prune_scraping_and_save


def upsert_scraping(page: Page, confession_part: str) -> ():
    # Compare result to last scraping
    scraping = page.get_latest_scraping()
    if scraping is not None \
            and scraping.confession_html == confession_part:
        # If a scraping exists and is identical to last one
        scraping.nb_iterations += 1
        scraping.save()
    else:
        if scraping is not None:
            # If a scraping exists and is different from last one, we delete it
            scraping.delete()

        scraping = Scraping(
            confession_html=confession_part,
            nb_iterations=1,
            page=page,
        )

    prune_scraping_and_save(scraping)
