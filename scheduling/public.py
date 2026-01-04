from django.db.models import Q, Subquery

from home.models import Parsing, Pruning, Website, Sentence
from scheduling.models import Scheduling
from scheduling.process import init_scheduling


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


def get_websites_of_prunings(prunings: list[Pruning]) -> list[Website]:
    history_ids = Subquery(
        Pruning.history.filter(
            uuid__in=[pruning.uuid for pruning in prunings]
        ).values('history_id')
    )

    return list(
        Website.objects.filter(
            schedulings__in=Scheduling.objects.filter(
                Q(scraping_prunings__pruning_history_id__in=history_ids)
                | Q(image_prunings__pruning_history_id__in=history_ids),
                status=Scheduling.Status.INDEXED,
            )
        ).distinct()
    )


def get_websites_of_parsing(parsing: Parsing) -> list[Website]:
    history_ids = Subquery(
        parsing.history.values('history_id')
    )

    return list(
        Website.objects.filter(
            schedulings__in=Scheduling.objects.filter(
                pruning_parsings__parsing_history_id__in=history_ids,
                status=Scheduling.Status.INDEXED,
            )
        ).distinct()
    )
