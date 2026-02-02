from scheduling.models.parsing_models import Parsing
from scheduling.models.pruning_models import Sentence, Pruning
from scheduling.process import init_scheduling
from scheduling.services.scheduling_service import get_websites_of_prunings, get_websites_of_parsing


###################
# INIT SCHEDULING #
###################

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
