from fetching.models import OClocherOrganization, OClocherMatching
from fetching.oclocher.match_with_llm import match_oclocher_with_llm


def get_existing_matching(oclocher_organization: OClocherOrganization
                          ) -> OClocherMatching | None:
    # TODO
    pass


def match_all_organizations_locations():
    oclocher_organizations = OClocherOrganization.objects.all()
    for oclocher_organization in oclocher_organizations:
        # If there are no locations, no point in matching
        if not oclocher_organization.locations.exists():
            continue

        # GET OClocherMatching if any
        existing_matching = get_existing_matching(oclocher_organization)
        if existing_matching:
            if oclocher_organization.matching != existing_matching:
                oclocher_organization.matching = existing_matching
                oclocher_organization.save()
            continue

        match_oclocher_with_llm()
        # TODO insert OClocherMatching and link it to OClocherOrganization
