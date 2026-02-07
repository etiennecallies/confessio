from background_task import background
from background_task.tasks import TaskSchedule

from core.utils.log_utils import info
from core.utils.log_utils import log_stack_trace, start_log_buffer
from scheduling.models import Parsing
from scheduling.models import Scheduling, Log
from scheduling.services.parsing.parse_pruning_service import parse_parsing_preparation, \
    prepare_reparsing
from scheduling.services.scheduling.log_service import save_buffer


@background(queue='main', schedule=TaskSchedule(priority=1))
def worker_prune_scheduling(scheduling_uuid: str):
    print(f'Starting worker_prune_scheduling for {scheduling_uuid}')
    try:
        scheduling = Scheduling.objects.get(uuid=scheduling_uuid)
    except Scheduling.DoesNotExist:
        info(f'Scheduling {scheduling_uuid} does not exist for worker_prune_scheduling')
        return

    start_log_buffer()
    from scheduling.services.scheduling.scheduling_process_service import prune_scheduling
    try:
        prune_scheduling(scheduling)
    except Exception:
        info(f'Exception while pruning scheduling {scheduling.uuid}')
        log_stack_trace()
        save_buffer(scheduling.website, Log.Type.PRUNING, Log.Status.FAILURE)
        return

    save_buffer(scheduling.website, Log.Type.PRUNING)


@background(queue='main', schedule=TaskSchedule(priority=2))
def worker_parse_scheduling(scheduling_uuid: str):
    print(f'Starting worker_parse_scheduling for {scheduling_uuid}')
    try:
        scheduling = Scheduling.objects.get(uuid=scheduling_uuid)
    except Scheduling.DoesNotExist:
        info(f'Scheduling {scheduling_uuid} does not exist for worker_parse_scheduling')
        return

    start_log_buffer()
    from scheduling.services.scheduling.scheduling_process_service import parse_scheduling
    try:
        parse_scheduling(scheduling)
    except Exception:
        info(f'Exception while parsing scheduling {scheduling.uuid}')
        log_stack_trace()
        save_buffer(scheduling.website, Log.Type.PARSING, Log.Status.FAILURE)
        return

    save_buffer(scheduling.website, Log.Type.PARSING)


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

    from scheduling.public_service import init_schedulings_for_parsing
    init_schedulings_for_parsing(parsing)
