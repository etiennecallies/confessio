from home.models import Website
from home.utils.log_utils import get_log_buffer
from scheduling.models import Log


def save_buffer(website: Website, log_type: Log.Type, status: Log.Status = Log.Status.DONE):
    buffer_value = get_log_buffer()
    log = Log(type=log_type,
              website=website,
              content=buffer_value,
              status=status,
              )
    log.save()
