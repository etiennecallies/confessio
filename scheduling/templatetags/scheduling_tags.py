import json

from django.template.defaulttags import register
from django.template.loader import render_to_string

from scheduling.workflows.parsing.explain_schedule import get_explanation_from_schedule
from scheduling.workflows.parsing.schedules import ScheduleItem


@register.simple_tag
def explain_schedule(schedule: ScheduleItem, church_desc_by_id_json: str):
    church_desc_by_id = {int(k): v for (k, v) in json.loads(church_desc_by_id_json).items()}
    if schedule.church_id in church_desc_by_id:
        church_desc = church_desc_by_id[schedule.church_id]
    elif schedule.church_id == -1:
        church_desc = 'Autre église'
    else:
        church_desc = 'Église inconnue'
    explained_schedule = get_explanation_from_schedule(schedule)
    return render_to_string('displays/explained_schedule_display.html', {
        'explained_schedule': explained_schedule,
        'church_desc': church_desc,
    })
