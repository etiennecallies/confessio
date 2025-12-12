from fetching.models import OClocherOrganization
from fetching.oclocher.fetch_oclocher_api import fetch_organization_schedules


def fetch_all_organization_schedules():
    oclocher_organizations = OClocherOrganization.objects.all()
    for oclocher_organization in oclocher_organizations:
        fetch_organization_schedules(oclocher_organization.organization_id)

    # TODO insert / update OClocherSchedule s
