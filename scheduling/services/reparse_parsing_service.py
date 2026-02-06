from background_task import background
from background_task.tasks import TaskSchedule

from core.utils.log_utils import info
from scheduling.models import Parsing
from scheduling.public_service import init_schedulings_for_parsing
from scheduling.services.parse_pruning_service import parse_parsing_preparation, \
    prepare_reparsing


def reparse_parsing(parsing: Parsing):
    worker_reparse_parsing(str(parsing.uuid))


@background(queue='main', schedule=TaskSchedule(priority=3))
def worker_reparse_parsing(parsing_uuid: str):
    try:
        parsing = Parsing.objects.get(uuid=parsing_uuid)
    except Parsing.DoesNotExist as e:
        info(f'Parsing {parsing_uuid} does not exist: {e}')
        return

    info(f'worker_reparse_parsing: parsing {parsing_uuid}')
    parsing_preparation = prepare_reparsing(parsing)
    parse_parsing_preparation(parsing_preparation)
    init_schedulings_for_parsing(parsing)
