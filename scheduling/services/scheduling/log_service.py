from django.utils import timezone

from core.utils.log_utils import get_log_buffer
from registry.models import Website
from scheduling.models import Log


def save_buffer(website: Website, log_type: Log.Type, status: Log.Status = Log.Status.DONE):
    buffer_value, buffer_started_at = get_log_buffer()
    log = Log(type=log_type,
              website=website,
              content=buffer_value,
              status=status,
              started_at=buffer_started_at,
              ended_at=timezone.now()
              )
    log.save()
