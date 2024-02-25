from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect

from home.models import ParishModeration


@login_required
@permission_required("home.change_sentence")
def moderate_parish(request, category, moderation_uuid=None):
    # TODO check category or 400

    if moderation_uuid is None:
        parish_moderation = ParishModeration.objects.filter(
            category=category, validated_at__isnull=True).first()
        if parish_moderation is None:
            return redirect('index')
        else:
            return redirect('moderate_one_parish',
                            category=category,
                            moderation_uuid=parish_moderation.uuid)

    try:
        parish_moderation = ParishModeration.objects.get(uuid=moderation_uuid)
    except ParishModeration.DoesNotExist:
        return HttpResponseNotFound("Page not found")

    if request.method == "POST":
        parish_moderation.validate(request.user)

        return redirect('moderate_next_parish', category=category)

    context = {
        'parish_moderation': parish_moderation,
        'parish': parish_moderation.parish,
    }

    return render(request, 'pages/moderate_parish.html', context)
