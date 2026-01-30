from home.utils.log_utils import info, log_stack_trace, start_log_buffer
from scheduling.models import Scheduling, Log
from background_task import background
from background_task.tasks import TaskSchedule

from scheduling.services.log_service import save_buffer


@background(queue='main', schedule=TaskSchedule(priority=1))
def worker_prune_scheduling(scheduling_uuid: str):
    print(f'Starting worker_prune_scheduling for {scheduling_uuid}')
    try:
        scheduling = Scheduling.objects.get(uuid=scheduling_uuid)
    except Scheduling.DoesNotExist:
        info(f'Scheduling {scheduling_uuid} does not exist for worker_prune_scheduling')
        return

    start_log_buffer()
    from scheduling.process import prune_scheduling
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
    from scheduling.process import parse_scheduling
    try:
        parse_scheduling(scheduling)
    except Exception:
        info(f'Exception while parsing scheduling {scheduling.uuid}')
        log_stack_trace()
        save_buffer(scheduling.website, Log.Type.PARSING, Log.Status.FAILURE)
        return

    save_buffer(scheduling.website, Log.Type.PARSING)
