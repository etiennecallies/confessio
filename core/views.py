from django.db.models import Count, Q
from django.http import HttpResponseBadRequest, HttpResponseNotFound, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from registry.models import ModerationMixin, Diocese
from registry.models.base_moderation_models import BUG_DESCRIPTION_MAX_LENGTH
from scheduling.utils.date_utils import datetime_to_ts_us, ts_us_to_datetime


def get_moderation_url(moderation: ModerationMixin):
    return reverse(f'moderate_one_' + moderation.resource,
                   kwargs={
                       'category': moderation.category,
                       'is_bug': moderation.marked_as_bug_at is not None,
                       'moderation_uuid': moderation.uuid,
                       'diocese_slug': moderation.get_diocese_slug(),
                   })


def redirect_to_moderation(moderation: ModerationMixin, category: str, resource: str, is_bug: bool,
                           diocese_slug: str):
    if moderation is None:
        return redirect('index')
    else:
        return redirect(f'moderate_one_' + resource,
                        category=category,
                        is_bug=is_bug,
                        moderation_uuid=moderation.uuid,
                        diocese_slug=diocese_slug)


class ModerationPostError(Exception):
    response: HttpResponse

    def __init__(self, response: HttpResponse):
        self.response = response


def get_next_url(request, moderation: ModerationMixin, diocese_slug: str) -> str:
    created_at_ts_us = datetime_to_ts_us(moderation.created_at)
    back_path = request.GET.get('backPath', '')
    if back_path:
        return back_path

    next_url = \
        reverse('moderate_next_' + moderation.resource,
                kwargs={
                    'category': moderation.category,
                    'is_bug': moderation.marked_as_bug_at is not None,
                    'diocese_slug': diocese_slug,
                }) \
        + f'?created_after={created_at_ts_us}'

    related_url = request.POST.get('related_url')
    if related_url:
        return f"{related_url}?backPath={next_url}"

    return next_url


def get_position_and_count(moderation: ModerationMixin,
                           diocese: Diocese | None,
                           is_bug: bool,
                           ) -> tuple[int, int]:
    objects_filter = moderation.__class__.objects.filter(
        category=moderation.category,
        validated_at__isnull=True,
        marked_as_bug_at__isnull=not is_bug,
    )
    if diocese:
        objects_filter = objects_filter.filter(diocese=diocese)
    counts = objects_filter.aggregate(
        position=Count("uuid", filter=Q(created_at__lte=moderation.created_at)),
        total=Count("uuid"),
    )
    return counts["position"], counts["total"]


def get_moderate_response(request, category: str, resource: str, is_bug_as_str: bool,
                          diocese_slug: str, class_moderation, moderation_uuid, create_context,
                          moderation_post_process=None):
    if is_bug_as_str not in ['True', 'False']:
        return HttpResponseBadRequest(f"is_bug_as_str {is_bug_as_str} is not valid")

    is_bug = is_bug_as_str == 'True'

    if category not in class_moderation.Category.values:
        return HttpResponseBadRequest(f"category {category} is not valid for {resource}")

    if diocese_slug == 'no_diocese':
        diocese = None
    else:
        try:
            diocese = Diocese.objects.get(slug=diocese_slug)
        except Diocese.DoesNotExist:
            return HttpResponseNotFound(f"diocese {diocese_slug} not found")

    if moderation_uuid is None:
        created_after_ts = int(request.GET.get('created_after', '0'))
        created_after = ts_us_to_datetime(created_after_ts)
        objects_filter = class_moderation.objects.filter(category=category,
                                                         validated_at__isnull=True,
                                                         marked_as_bug_at__isnull=not is_bug,
                                                         created_at__gt=created_after)
        if diocese:
            objects_filter = objects_filter.filter(diocese=diocese)
        next_moderation = objects_filter.order_by('created_at').first()
        return redirect_to_moderation(next_moderation, category, resource, is_bug, diocese_slug)

    try:
        moderation = class_moderation.objects.get(uuid=moderation_uuid)
    except class_moderation.DoesNotExist:
        print(f"{resource} {moderation_uuid} not found. "
              f"Probably because problem was solved meanwhile. "
              f"Redirecting to first moderation.")
        return redirect('moderate_next_' + resource, category=category, is_bug=is_bug,
                        diocese_slug=diocese_slug)

    do_redirect = True
    next_url = get_next_url(request, moderation, diocese_slug)
    if request.method == "POST":
        if 'comment' in request.POST:
            comment = request.POST.get('comment') or None
            moderation.comment = comment
            moderation.save()
            do_redirect = False
        elif 'bug_description' in request.POST:
            bug_description = request.POST.get('bug_description')
            if bug_description is not None and len(bug_description) > BUG_DESCRIPTION_MAX_LENGTH:
                return HttpResponseBadRequest(f"bug_description is len {len(bug_description)} but "
                                              f"max size is {BUG_DESCRIPTION_MAX_LENGTH}")
            moderation.mark_as_bug(request.user, bug_description)
        elif 'delete_moderation' in request.POST:
            moderation.delete()
        elif moderation_post_process is not None:
            try:
                do_redirect = moderation_post_process(request, moderation)
            except ModerationPostError as e:
                return e.response

            if do_redirect:
                moderation.validate(request.user)

        if do_redirect:
            return redirect(next_url)

    position, count = get_position_and_count(moderation, diocese, is_bug)

    return render(request, f'moderations/moderate_{moderation.resource}.html', {
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
        'back_path': request.GET.get('backPath', ''),
        'position': position,
        'count': count,
    } | create_context(moderation))
