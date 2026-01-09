from fetching.models import OClocherMatching, OClocherMatchingModeration, \
    OClocherLocation
from fetching.services.oclocher_moderations_service import add_matching_moderation
from fetching.workflows.oclocher.match_with_llm import match_oclocher_with_llm
from home.models import Church
from home.utils.list_utils import get_desc_by_id


def get_church_desc_by_id_from_churches(churches: list[Church]) -> dict[int, str]:
    church_descs = []
    for church in churches:
        church_descs.append(church.get_desc())

    return get_desc_by_id(church_descs)


def get_location_desc(oclocher_location: OClocherLocation) -> str:
    desc_parts = []
    if oclocher_location.name:
        desc_parts.append(oclocher_location.name)
    if oclocher_location.address:
        desc_parts.append(oclocher_location.address)
    location_desc = " ".join(desc_parts)
    return location_desc


def get_location_desc_by_id(locations: list[OClocherLocation]) -> dict:
    location_desc_list = []
    for location in locations:
        location_desc_list.append(get_location_desc(location))

    location_desc_by_id = {}
    for i, desc in enumerate(sorted(location_desc_list)):
        location_desc_by_id[i] = desc

    return location_desc_by_id


def get_existing_matching(church_desc_by_id: dict[int, str],
                          location_desc_by_id: dict[int, str]
                          ) -> OClocherMatching | None:
    return OClocherMatching.objects.filter(
        church_desc_by_id=church_desc_by_id,
        location_desc_by_id=location_desc_by_id
    ).first()


def match_churches_and_locations(
        churches: list[Church],
        locations: list[OClocherLocation]
) -> OClocherMatching:
    assert churches and locations

    church_desc_by_id = get_church_desc_by_id_from_churches(churches)
    location_desc_by_id = get_location_desc_by_id(locations)

    # GET OClocherMatching if any
    existing_matching = get_existing_matching(church_desc_by_id, location_desc_by_id)
    if existing_matching:
        return existing_matching

    oclocher_organization = locations[0].organization

    print(f'Matching organization {oclocher_organization.organization_id} '
          f'with {len(location_desc_by_id)} locations.')

    llm_matrix, llm_error_detail, llm_provider, llm_model, prompt_template_hash = \
        match_oclocher_with_llm(church_desc_by_id, location_desc_by_id)

    oclocher_matching = OClocherMatching(
        church_desc_by_id=church_desc_by_id,
        location_desc_by_id=location_desc_by_id,
        llm_matrix=llm_matrix.model_dump(mode='json') if llm_matrix else None,
        llm_provider=llm_provider,
        llm_model=llm_model,
        prompt_template_hash=prompt_template_hash,
        llm_error_detail=llm_error_detail,
    )
    oclocher_matching.save()

    # moderation
    if llm_error_detail:
        category = OClocherMatchingModeration.Category.LLM_ERROR
    else:
        category = OClocherMatchingModeration.Category.NEW_MATCHING

    add_matching_moderation(oclocher_organization, oclocher_matching, category)

    return oclocher_matching
