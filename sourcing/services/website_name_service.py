from home.models import Website


def remove_diocese(website_name: str) -> str:
    if "– Diocèse" in website_name:  # this is the hyphen used in the website names
        return website_name.split("– Diocèse")[0].strip()

    if "- Diocèse" in website_name:  # not the same hyphen
        return website_name.split("- Diocèse")[0].strip()

    return website_name


def clean_website_name(website: Website) -> bool:
    cleaned_website_name = remove_diocese(website.name)
    if cleaned_website_name != website.name:
        website.name = cleaned_website_name
        website.save()

        return True

    return False
