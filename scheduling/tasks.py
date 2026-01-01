from home.utils.log_utils import info
from scheduling.models import Scheduling
from background_task import background
from background_task.tasks import TaskSchedule


@background(queue='main', schedule=TaskSchedule(priority=1))
def worker_prune_scheduling(scheduling_uuid: str):
    print(f'Starting worker_prune_scheduling for {scheduling_uuid}')
    try:
        scheduling = Scheduling.objects.get(uuid=scheduling_uuid)
    except Scheduling.DoesNotExist:
        info(f'Scheduling {scheduling_uuid} does not exist for worker_prune_scheduling')
        return

    from scheduling.process import prune_scheduling
    prune_scheduling(scheduling)


@background(queue='main', schedule=TaskSchedule(priority=2))
def worker_parse_scheduling(scheduling_uuid: str):
    print(f'Starting worker_parse_scheduling for {scheduling_uuid}')
    try:
        scheduling = Scheduling.objects.get(uuid=scheduling_uuid)
    except Scheduling.DoesNotExist:
        info(f'Scheduling {scheduling_uuid} does not exist for worker_parse_scheduling')
        return

    from scheduling.process import parse_scheduling
    parse_scheduling(scheduling)
