from registry.models import Website


def set_emails_for_website(website: Website, emails: set[str]):
    sorted_emails = list(sorted(emails))

    if website.contact_emails != sorted_emails:
        website.contact_emails = sorted_emails
        website.save()
