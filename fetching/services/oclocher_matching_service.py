from fetching.models import OClocherMatching, OClocherMatchingModeration, \
    OClocherLocation
from fetching.services.oclocher_moderations_service import upsert_matching_moderation
from fetching.workflows.oclocher.match_with_llm import match_oclocher_with_llm
from fetching.workflows.oclocher.oclocher_matrix import OClocherMatrix
from registry.models import Church
from scheduling.utils.hash_utils import hash_dict_to_hex
from scheduling.utils.list_utils import get_desc_by_id


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

    return get_desc_by_id(location_desc_list)


def get_oclocher_id_by_location_id(locations: list[OClocherLocation]):
    location_desc_by_id = get_location_desc_by_id(locations)
    location_by_desc = {get_location_desc(location): location for location in locations}
    return {location_id: location_by_desc[desc].location_id
            for location_id, desc in location_desc_by_id.items()}


def get_matching_matrix(oclocher_matching: OClocherMatching) -> OClocherMatrix | None:
    if oclocher_matching.human_matrix is not None:
        return OClocherMatrix(**oclocher_matching.human_matrix)

    if oclocher_matching.llm_matrix is not None:
        return OClocherMatrix(**oclocher_matching.llm_matrix)

    return None


def get_existing_matching(church_desc_by_id_hash: str,
                          location_desc_by_id_hash: str
                          ) -> OClocherMatching | None:
    return OClocherMatching.objects.filter(
        church_desc_by_id_hash=church_desc_by_id_hash,
        location_desc_by_id_hash=location_desc_by_id_hash
    ).first()


def match_churches_and_locations(
        churches: list[Church],
        locations: list[OClocherLocation]
) -> OClocherMatching:
    assert churches and locations

    church_desc_by_id = get_church_desc_by_id_from_churches(churches)
    church_desc_by_id_hash = hash_dict_to_hex(church_desc_by_id)
    location_desc_by_id = get_location_desc_by_id(locations)
    location_desc_by_id_hash = hash_dict_to_hex(location_desc_by_id)

    # GET OClocherMatching if any
    existing_matching = get_existing_matching(church_desc_by_id_hash, location_desc_by_id_hash)
    if existing_matching:
        return existing_matching

    oclocher_organization = locations[0].organization

    print(f'Matching organization {oclocher_organization.organization_id} '
          f'with {len(location_desc_by_id)} locations.')

    llm_matrix, llm_error_detail, llm_provider, llm_model, prompt_template_hash = \
        match_oclocher_with_llm(church_desc_by_id, location_desc_by_id)

    oclocher_matching = OClocherMatching(
        church_desc_by_id=church_desc_by_id,
        church_desc_by_id_hash=church_desc_by_id_hash,
        location_desc_by_id=location_desc_by_id,
        location_desc_by_id_hash=location_desc_by_id_hash,
        llm_matrix=llm_matrix.model_dump(mode='json') if llm_matrix else None,
        llm_provider=llm_provider,
        llm_model=llm_model,
        prompt_template_hash=prompt_template_hash,
        llm_error_detail=llm_error_detail,
    )
    oclocher_matching.save()

    # moderation
    if llm_error_detail:
        moderation_validated = False
        category = OClocherMatchingModeration.Category.LLM_ERROR
    else:
        moderation_validated = True
        category = OClocherMatchingModeration.Category.OK

    upsert_matching_moderation(oclocher_organization, oclocher_matching, category,
                               moderation_validated)

    return oclocher_matching
