from scheduling.workflows.parsing.holidays import check_holiday_by_zone
from scheduling.workflows.parsing.liturgical import check_easter_dates
from scheduling.workflows.pruning.extract_and_join import extract_refined_content, \
    extract_v2_refined_content


###################
# EXTRACT CONTENT #
###################

def scheduling_extract_refined_content(refined_content: str) -> list[str] | None:
    return extract_refined_content(refined_content)


def scheduling_extract_v2_refined_content(refined_content: str) -> list[str] | None:
    return extract_v2_refined_content(refined_content)


##################
# NIGHTLY CHECKS #
##################

def scheduling_check_holiday_by_zone() -> bool:
    return check_holiday_by_zone()


def scheduling_check_easter_dates() -> bool:
    return check_easter_dates()
