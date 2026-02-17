from registry.models import Website
from scheduling.models import Parsing, Scheduling
from scheduling.models.pruning_models import Sentence, Pruning
from scheduling.services.merging.sourced_schedules_service import SchedulingElements, \
    retrieve_scheduling_elements
from scheduling.services.scheduling.scheduling_process_service import init_scheduling
from scheduling.services.pruning.prune_scraping_service import create_pruning, \
    remove_pruning_moderation_if_orphan
from scheduling.services.scheduling.scheduling_service import get_websites_of_prunings, \
    get_websites_of_parsing, get_indexed_scheduling


###########
# PRUNING #
###########

def scheduling_create_pruning(extracted_html: str | None) -> Pruning | None:
    return create_pruning(extracted_html)


def scheduling_remove_pruning_moderation_if_orphan(pruning: Pruning):
    remove_pruning_moderation_if_orphan(pruning)


###################
# INIT SCHEDULING #
###################

def scheduling_init_scheduling(website: Website, instant_deindex: bool = False) -> Scheduling:
    return init_scheduling(website, instant_deindex)


def init_scheduling_for_sentences(sentences: list[Sentence]):
    affected_prunings = []
    for sentence in sentences:
        for pruning in sentence.prunings.all():
            if pruning not in affected_prunings:
                affected_prunings.append(pruning)

    for website in get_websites_of_prunings(affected_prunings):
        init_scheduling(website)


def init_scheduling_for_pruning(pruning: Pruning):
    websites = get_websites_of_prunings([pruning])
    for website in websites:
        init_scheduling(website)


def init_schedulings_for_parsing(parsing: Parsing):
    websites = get_websites_of_parsing(parsing)
    for website in websites:
        init_scheduling(website)


##################
# GET SCHEDULING #
##################

def scheduling_get_indexed_scheduling(website: Website) -> Scheduling | None:
    return get_indexed_scheduling(website)


###################
# RELATED OBJECTS #
###################

def scheduling_get_websites_of_parsing(parsing: Parsing) -> list[Website]:
    return get_websites_of_parsing(parsing)


def scheduling_retrieve_scheduling_elements(scheduling: Scheduling) -> SchedulingElements:
    return retrieve_scheduling_elements(scheduling)
