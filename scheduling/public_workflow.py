from scheduling.workflows.pruning.extract_and_join import extract_refined_content, \
    extract_v2_refined_content


###################
# EXTRACT CONTENT #
###################

def scheduling_extract_refined_content(refined_content: str) -> list[str] | None:
    return extract_refined_content(refined_content)


def scheduling_extract_v2_refined_content(refined_content: str) -> list[str] | None:
    return extract_v2_refined_content(refined_content)
